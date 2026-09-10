#!/usr/bin/env python3
"""
carousel_gate.py -- offline CHOREOGRAPHY gate for the seedance-blocking skill.

Runs with plain python3. NO bpy, NO Blender.

solve_shot.py proves the CAMERA is valid. On a locked-off ensemble film -- a
product carousel, three objects taking turns in front, anything where the camera
holds still and the subjects move in depth -- the camera gates all pass
trivially (travel 0.00 m, rot 0.0 deg/s) and prove nothing. The risk in that
film is the CHOREOGRAPHY, and this gate measures it.

Measured failure it exists to catch: a three-product depth carousel came back as
a static product line-up -- one left, one centre, one right, all fully visible,
never overlapping -- with only the sizes changing. The swap order was right and
the film still read wrong, because "in front" had become "in the middle seat".

    python3 carousel_gate.py myshot.py

Exit 0 = every gate passed. 1 = a gate failed; read the report, fix the spec.
The spec needs a "cast" block; a spec without one is skipped, not failed.

SPEC FORMAT
-----------
    "cast": {
      "bacon":  {"size": [0.60, 0.60, 1.60], "color": "red"},
      "cheese": {"size": [0.60, 0.60, 1.60], "color": "cyan"},
      ...
      "logo":   {"size": [1.40, 0.05, 0.40], "color": "white", "role": "graphic"},
    },
    "choreography": [
      # (t, name, [x, y, z], scale)  -- y is depth, smaller y = nearer camera
      (7.0,  "bacon",  [0.0, -1.2, 0.0], 1.00),
      (9.5,  "bacon",  [0.0, -1.2, 0.0], 1.00),
      (14.5, "bacon",  [-1.6, 1.4, 0.0], 0.55),
      ...
    ],
    "front_zone": {"depth": 0.0, "solo_until": 41.5},   # optional, defaults below

Keys are sampled and linearly interpolated between them, exactly as the bake
does. A member absent before its first key or after its last is OFF-SCREEN and
is not counted -- that is how objects enter and leave.
"""
import sys, math, os, importlib.util
sys.dont_write_bytecode = True

FPS_DEFAULT   = 24
SOLO_EPS      = 0.15   # scale margin: front must beat the rest by this fraction
OVERLAP_MIN   = 0.08   # front silhouette must cover this fraction of a rival's width
POP_MAX       = 0.60   # a scale jump larger than this between keys is a pop
SWAP_WINDOW   = 1.20   # seconds two members may read the same size while crossing


# ------------------------------------------------------------------ loading --
def load_spec(path):
    spec = importlib.util.spec_from_file_location("shot", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for key in ("SHOT", "shot", "SPEC"):
        if hasattr(mod, key):
            return getattr(mod, key)
    raise SystemExit(f"{path}: no SHOT dict found")


def tracks(chore):
    """Group the flat key list into one time-sorted track per member."""
    out = {}
    for entry in chore:
        t, name, pos, scale = entry[0], entry[1], entry[2], entry[3]
        out.setdefault(name, []).append((float(t), list(pos), float(scale)))
    for name in out:
        out[name].sort(key=lambda k: k[0])
    return out


def sample(track, t):
    """Position and scale at t, or None if the member is not on screen yet/any more."""
    if not track or t < track[0][0] - 1e-9 or t > track[-1][0] + 1e-9:
        return None
    for i in range(len(track) - 1):
        t0, p0, s0 = track[i]
        t1, p1, s1 = track[i + 1]
        if t0 - 1e-9 <= t <= t1 + 1e-9:
            span = t1 - t0
            u = 0.0 if span <= 1e-9 else (t - t0) / span
            pos = [p0[k] + (p1[k] - p0[k]) * u for k in range(3)]
            return pos, s0 + (s1 - s0) * u
    return list(track[-1][1]), track[-1][2]


def apparent(size, scale, pos, cam_y):
    """Apparent half-width and screen x of a member, from a locked-off camera on -Y."""
    dist = max(0.35, abs(pos[1] - cam_y))
    half = (size[0] * scale) * 0.5 / dist
    return half, pos[0] / dist


# -------------------------------------------------------------------- gates --
def gate_solo_front(members, chore_t, solo_until, report, step):
    """Exactly one member clearly in front, except while two are crossing.

    During a swap the outgoing and incoming members necessarily pass through the
    same apparent size -- that instant is the swap, not a defect. What is a
    defect is that state PERSISTING: an ambiguous front is exactly what the
    product line-up failure looks like. So this gate measures the longest
    unbroken run of ambiguity, not the total count."""
    runs, cur = [], None
    for t, live in chore_t:
        if t > solo_until:
            continue
        actors = [m for m in live if members[m].get("role") != "graphic"]
        ambiguous = False
        detail = None
        if len(actors) >= 2:
            ranked = sorted(actors, key=lambda m: live[m]["half"], reverse=True)
            first, second = ranked[0], ranked[1]
            h1, h2 = live[first]["half"], live[second]["half"]
            if h2 > h1 * (1.0 - SOLO_EPS):
                ambiguous = True
                detail = (t, first, h1, second, h2)
        if ambiguous:
            cur = [t, t, detail] if cur is None else [cur[0], t, cur[2]]
        elif cur is not None:
            runs.append(cur)
            cur = None
    if cur is not None:
        runs.append(cur)

    worst = max(runs, key=lambda r: r[1] - r[0], default=None)
    if worst is not None and (worst[1] - worst[0] + step) > SWAP_WINDOW:
        t, a, ha, b, hb = worst[2]
        dur = worst[1] - worst[0] + step
        report.append(("FAIL", "solo_front",
            f"the front is ambiguous for {dur:.2f}s from {worst[0]:.2f}s "
            f"(limit {SWAP_WINDOW:.2f}s) -- {a} and {b} read the same size "
            f"({ha:.3f} vs {hb:.3f}, need a {SOLO_EPS:.0%} margin). "
            f"A swap may pass through this; sitting in it is the product line-up "
            f"failure -- the swap became a change of seat, not a change of depth."))
        return False
    longest = 0.0 if worst is None else (worst[1] - worst[0] + step)
    report.append(("PASS", "solo_front",
        f"one member clearly in front before {solo_until:.1f}s "
        f"(longest crossing {longest:.2f}s, limit {SWAP_WINDOW:.2f}s)"))
    return True


def gate_overlap(members, chore_t, solo_until, report):
    """The front member's silhouette must cut across the others."""
    bad = []
    for t, live in chore_t:
        if t > solo_until:
            continue
        actors = [m for m in live if members[m].get("role") != "graphic"]
        if len(actors) < 2:
            continue
        front = max(actors, key=lambda m: live[m]["half"])
        fx, fh = live[front]["x"], live[front]["half"]
        covered = 0
        for m in actors:
            if m == front:
                continue
            mx, mh = live[m]["x"], live[m]["half"]
            gap = abs(mx - fx) - (fh + mh)
            overlap = -gap
            if overlap > OVERLAP_MIN * (2 * mh):
                covered += 1
        if covered == 0:
            bad.append((t, front, len(actors) - 1))
    if bad:
        t, front, n = bad[0]
        report.append(("FAIL", "front_overlaps",
            f"{len(bad)} samples where the front member touches nothing -- "
            f"at {t:.2f}s {front} is in front of {n} others and cuts across none of them. "
            f"If no member is cutting off another, the frame reads as a line-up."))
        return False
    report.append(("PASS", "front_overlaps",
        "the front member cuts across at least one other at every sample"))
    return True


def gate_depth_order(members, chore_t, solo_until, report):
    """Nearest in depth must also be largest -- size and depth must agree."""
    bad = []
    for t, live in chore_t:
        actors = [m for m in live if members[m].get("role") != "graphic"]
        if len(actors) < 2:
            continue
        nearest = min(actors, key=lambda m: live[m]["y"])
        largest = max(actors, key=lambda m: live[m]["half"])
        if nearest != largest:
            bad.append((t, nearest, largest))
    if bad:
        t, near, large = bad[0]
        report.append(("FAIL", "depth_matches_size",
            f"{len(bad)} samples where depth and size disagree -- "
            f"at {t:.2f}s {near} is nearest the camera but {large} reads larger. "
            f"The audience reads size as depth; make them agree."))
        return False
    report.append(("PASS", "depth_matches_size",
        "the nearest member is the largest at every sample"))
    return True


def gate_no_pops(members, chore, report):
    """No member jumps in scale between adjacent keys."""
    bad = []
    for name, track in tracks(chore).items():
        for i in range(len(track) - 1):
            t0, _, s0 = track[i]
            t1, _, s1 = track[i + 1]
            if s0 <= 1e-6:
                continue
            jump = abs(s1 - s0) / s0
            span = max(1e-6, t1 - t0)
            if jump > POP_MAX and span < 0.5:
                bad.append((t0, t1, name, s0, s1))
    if bad:
        t0, t1, name, s0, s1 = bad[0]
        report.append(("FAIL", "no_scale_pops",
            f"{len(bad)} scale pops -- {name} goes {s0:.2f} to {s1:.2f} "
            f"in {t1 - t0:.2f}s. Give it time or split the change."))
        return False
    report.append(("PASS", "no_scale_pops", "no member jumps scale between keys"))
    return True


def gate_census(members, chore_t, report):
    """Report the on-screen count over time; fail if it exceeds the cast."""
    counts = {}
    over = []
    for t, live in chore_t:
        n = len(live)
        counts[n] = counts.get(n, 0) + 1
        if n > len(members):
            over.append((t, n))
    if over:
        t, n = over[0]
        report.append(("FAIL", "census",
            f"{n} members on screen at {t:.2f}s but the cast has {len(members)}"))
        return False
    span = ", ".join(f"{n}x{c}" for n, c in sorted(counts.items()))
    report.append(("PASS", "census",
        f"on-screen count never exceeds the cast of {len(members)} (samples: {span})"))
    return True


# --------------------------------------------------------------------- main --
def main():
    if len(sys.argv) < 2:
        raise SystemExit("usage: carousel_gate.py <spec.py>")
    path = sys.argv[1]
    spec = load_spec(path)

    cast = spec.get("cast")
    chore = spec.get("choreography")
    if not cast or not chore:
        print(f"\n=== {spec.get('name','shot')} : no cast/choreography block -- "
              f"choreography gate SKIPPED ===")
        print("    (add one when objects swap depth order; see references/STORYBOARD.md)\n")
        return 0

    fps = spec.get("fps", FPS_DEFAULT)
    total = float(spec.get("seconds", 0.0))
    fz = spec.get("front_zone", {})
    solo_until = float(fz.get("solo_until", total))
    cam_y = -6.5
    for sh in spec.get("shots", []):
        wps = sh.get("camera", {}).get("waypoints", [])
        if wps:
            cam_y = float(wps[0]["pos"][1])
            break

    trk = tracks(chore)
    unknown = [n for n in trk if n not in cast]
    if unknown:
        raise SystemExit(f"choreography names not in cast: {', '.join(sorted(unknown))}")

    step = 1.0 / max(1, fps // 4)
    chore_t = []
    t = 0.0
    while t <= total + 1e-9:
        live = {}
        for name, track in trk.items():
            s = sample(track, t)
            if s is None:
                continue
            pos, scale = s
            size = cast[name].get("size", [0.6, 0.6, 1.6])
            half, x = apparent(size, scale, pos, cam_y)
            live[name] = {"half": half, "x": x, "y": pos[1], "scale": scale}
        chore_t.append((t, live))
        t += step

    print(f"\n=== {spec.get('name','shot')} : choreography gate "
          f"({len(chore_t)} samples over {total:.1f}s, cast of {len(cast)}) ===")
    print(f"    front zone solo until {solo_until:.1f}s, camera at y={cam_y:.2f}")

    report = []
    ok = True
    ok &= gate_census(cast, chore_t, report)
    ok &= gate_solo_front(cast, chore_t, solo_until, report, step)
    ok &= gate_overlap(cast, chore_t, solo_until, report)
    ok &= gate_depth_order(cast, chore_t, solo_until, report)
    ok &= gate_no_pops(cast, chore, report)

    print()
    for status, name, msg in report:
        print(f"     [{status}] {name:<20} {msg}")
    print()
    print("  ALL CHOREOGRAPHY GATES PASS" if ok else "  CHOREOGRAPHY GATE FAILED")
    print()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())