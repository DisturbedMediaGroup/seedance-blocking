#!/usr/bin/env python3
"""
solve_shot.py -- offline shot solver for the seedance-blocking skill.

Runs with plain python3. NO bpy, NO Blender, NO round trip.
Reads a shot spec, solves the subject path + camera route + lens for EVERY shot
in the sequence, AUDITS each one, and writes bake.json for load_bake().
One continuous shot is just a sequence of length 1.

Why this exists: every expensive previz mistake (camera whip, subject cropped
out of frame, camera inside a wall, set too short for the lens) is discoverable
from arithmetic alone. Discovering it in Blender costs a build + a render + a
re-plan. Discovering it here costs 0.2 seconds.

    python3 solve_shot.py myshot.py            # solve + audit + write bake.json
    python3 solve_shot.py myshot.py --report   # audit only, write nothing

Exit code 0 = every gate passed. 1 = a gate failed; read the report, fix the
spec, run again. Do not open Blender until this exits 0.
"""
import sys, json, math, os, importlib.util
sys.dont_write_bytecode = True   # keep the skill folder clean for read-only installs

SENSOR_W, SENSOR_H = 36.0, 20.25          # 36mm horizontal, 16:9

# ================================================================== RIGS ====
# A camera move is only "wrong" relative to the machine carrying it. A 76 deg/s
# whip is a bug on a gimbal and the entire point on a robot arm; a dead stop is a
# mistake on a drone and the signature move on a Bolt. So the LIMITS ARE THE RIG.
# Pick one at intake from the brief's own words; everything below gates from it.
#
#   note  -- the character to author toward
#   lens  -- typical range, guidance only, never gated
#   mute  -- advisories that are meaningless for this rig
RIGS = {
 "gimbal": dict(  # DEFAULT
   note="smooth flowing operator-carried move; never whips, never stops dead",
   lens=[24, 50], mute=[],
   limits=dict(max_deg_per_s=30.0, min_subject_distance=2.6,
               min_cam_speed=0.05, max_cam_speed=3.0)),
 "steadicam": dict(
   note="heavier and calmer than a gimbal; long floating takes, gentle arcs",
   lens=[21, 40], mute=[],
   limits=dict(max_deg_per_s=25.0, min_subject_distance=2.0,
               min_cam_speed=0.05, max_cam_speed=2.5)),
 "handheld": dict(
   note="looser, can jerk and correct; sits close, breathes with the subject",
   lens=[18, 35], mute=[],
   limits=dict(max_deg_per_s=45.0, min_subject_distance=1.2,
               min_cam_speed=0.02, max_cam_speed=3.0)),
 "tripod": dict(
   note="pan/tilt ONLY -- the head turns, the camera never translates",
   lens=[24, 85], mute=["static_rel", "size"],
   limits=dict(max_deg_per_s=40.0, min_subject_distance=2.0,
               min_cam_speed=0.0, max_cam_speed=0.0)),
 "dolly": dict(
   note="straight track, very calm; the move is translation, not rotation",
   lens=[28, 75], mute=["lens"],
   limits=dict(max_deg_per_s=20.0, min_subject_distance=2.5,
               min_cam_speed=0.05, max_cam_speed=2.0)),
 "crane": dict(
   note="big smooth arcs through height; slow rotation, wide coverage",
   lens=[24, 65], mute=[],
   limits=dict(max_deg_per_s=25.0, min_subject_distance=3.0,
               min_cam_speed=0.05, max_cam_speed=4.0)),
 "robo_arm": dict(
   note="motion control (Bolt/Cinebot): controlled WHIPS, lens within arm's "
        "reach, slams in and STOPS DEAD on the frame. Repeatable, machine-precise",
   lens=[14, 100], mute=["lens", "size"],   # incl. product macro work
   limits=dict(max_deg_per_s=140.0, min_subject_distance=0.8,
               min_cam_speed=0.0, max_cam_speed=6.0)),
 "fpv_drone": dict(
   note="never hovers mid-move; dives, rolls, threads gaps, carries huge speed "
        "and a very wide lens. Proximity is the whole effect",
   lens=[12, 18], mute=["lens"],
   limits=dict(max_deg_per_s=180.0, min_subject_distance=1.2,
               min_cam_speed=0.4, max_cam_speed=25.0)),
 "cable_cam": dict(
   note="straight line at speed, dead smooth, cannot deviate off its wire",
   lens=[18, 40], mute=["lens"],
   limits=dict(max_deg_per_s=25.0, min_subject_distance=3.0,
               min_cam_speed=1.0, max_cam_speed=12.0)),
 "probe_macro": dict(
   note="rigid snorkel/probe lens on a motion-control arm, working in CENTIMETRES: "
        "gets inside objects, wide lens millimetres from the subject, deep focus. "
        "Usually shot high-speed and played slow, so on-screen rates are gentle",
   lens=[12, 24], mute=["size", "lens"],     # a probe lens is a PRIME; it does not zoom
   limits=dict(max_deg_per_s=90.0, min_subject_distance=0.012,
               min_cam_speed=0.0, max_cam_speed=1.5)),
 "car_mount": dict(
   note="rigidly attached to a moving vehicle; travels fast, rotates barely",
   lens=[16, 35], mute=["lens", "size"],
   limits=dict(max_deg_per_s=20.0, min_subject_distance=2.0,
               min_cam_speed=3.0, max_cam_speed=30.0)),
}
DEFAULT_RIG = "gimbal"

def resolve_rig(SHOT):
    """rig name -> limits. An explicit `limits` block overrides the rig field by
    field, so a one-off exception never means abandoning the preset."""
    name = SHOT.get("rig", DEFAULT_RIG)
    if name not in RIGS:
        sys.exit("unknown rig %r -- known: %s\n(run with --rigs to see them)"
                 % (name, ", ".join(sorted(RIGS))))
    lim = dict(RIGS[name]["limits"])
    lim.update(SHOT.get("limits", {}))
    return name, lim, RIGS[name]



# ---------------------------------------------------------------- easing ----
def clamp(x, a, b): return a if x < a else (b if x > b else x)
def smoother(x):
    x = clamp(x, 0.0, 1.0)
    return x * x * x * (x * (6 * x - 15) + 10)

def catmull(knots, pts, t, dim):
    """Non-uniform Catmull-Rom in Hermite form. C1 continuous ACROSS waypoints,
    so velocity never pulses to zero at every control point the way
    per-segment smootherstep does."""
    n = len(knots)
    # Clamp OUTSIDE the knot range at BOTH ends. Defaulting to the last segment is
    # right above the range (s clamps to 1) and catastrophic below it: a shot whose
    # t0 is not frame-aligned -- 7.30 s at 24 fps is first evaluated at 7.2917 --
    # would evaluate the LAST segment at s=0 and teleport to a different waypoint.
    # That showed up as 1152 deg/s and 6.6 m/s on the first frame of a cut.
    i = 0 if t <= knots[0] else n - 2
    for j in range(n - 1):
        if knots[j] <= t <= knots[j + 1]:
            i = j; break
    im1, ip2 = max(i - 1, 0), min(i + 2, n - 1)
    t0, t1, t2, t3 = knots[im1], knots[i], knots[i + 1], knots[ip2]
    out = []
    for c in range(dim):
        P0, P1, P2, P3 = pts[im1][c], pts[i][c], pts[i + 1][c], pts[ip2][c]
        m1 = (P2 - P0) / max(t2 - t0, 1e-6)
        m2 = (P3 - P1) / max(t3 - t1, 1e-6)
        dt = t2 - t1
        s = clamp((t - t1) / dt, 0.0, 1.0)
        out.append((2*s**3 - 3*s**2 + 1) * P1 + (s**3 - 2*s**2 + s) * dt * m1
                   + (-2*s**3 + 3*s**2) * P2 + (s**3 - s**2) * dt * m2)
    return out

# ------------------------------------------------------------ vector bits ---
def sub(a, b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def add(a, b): return (a[0]+b[0], a[1]+b[1], a[2]+b[2])
def dot(a, b): return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]
def length(a): return math.sqrt(dot(a, a))
def norm(a):
    L = length(a)
    return (a[0]/L, a[1]/L, a[2]/L) if L > 1e-9 else (0.0, 1.0, 0.0)
def scale(a, s): return (a[0]*s, a[1]*s, a[2]*s)


def _rot(v, yaw, pitch):
    """R = Rx(tilt) . Rz(spin) -- SPIN FIRST, about the object's own axis, THEN
    tilt the whole thing. The other order (tilt then world-Z yaw) makes a tilted
    object PRECESS: the top traces a cone instead of the body spinning in place.
    Matches Blender rotation_mode 'ZYX' with euler = (tilt, 0, spin)."""
    cy, sy = math.cos(yaw), math.sin(yaw)
    x, y, z = v[0] * cy - v[1] * sy, v[0] * sy + v[1] * cy, v[2]
    cp, sp = math.cos(pitch), math.sin(pitch)
    return (x, y * cp - z * sp, y * sp + z * cp)

def corners(pos, sz, yaw, off=None, pitch=0.0):
    """The subject's 8 box corners in world space, rotated by its yaw. Sampling
    only width+height silently under-measures anything long -- a 4.4 m car reads
    as 1.8 m wide and its nose leaves frame with every gate still green. Yaw
    matters too: a drifting car presents its long side to the lens.

    off=None  -> the whole body, standing on the ground (z 0..sz[2]).
    off=[x,y,z] -> a sub-box CENTRED on that LOCAL offset, so the in-frame gate
    and the lens cap can target a DETAIL (a head, a wheel) and let the body crop."""
    hx, hy = sz[0] / 2.0, sz[1] / 2.0
    if off is None:
        # 0.02 was a "just above the ground" nudge for human-scale subjects. On a
        # 6 mm cereal hoop it sits ABOVE the whole object and the box gets measured
        # upside down, so it has to scale with the subject.
        zs, ox, oy = (min(0.02, 0.10 * sz[2]), sz[2]), 0.0, 0.0
    else:
        zs, ox, oy = (off[2] - sz[2] / 2.0, off[2] + sz[2] / 2.0), off[0], off[1]
    out = []
    for zz in zs:
        for xx in (-hx + ox, hx + ox):
            for yy in (-hy + oy, hy + oy):
                r = _rot((xx, yy, zz), yaw, pitch)
                out.append((pos[0] + r[0], pos[1] + r[1], pos[2] + r[2]))
    return out

MIN_LENS = 5.0   # below this the subject cannot fit at any focal length

def target_box(t, sz, ft):
    """Which box the framing gates and the lens cap aim at, at time t.

    A HARD switch from body to head snaps the focal length (33mm -> 86mm in one
    frame) and reads as a zoom punch; it also poisons the lens-smoothing window on
    the body side. So the target BLENDS from the whole body to the detail over
    `blend` seconds, and the subject leaves frame progressively -- which is what a
    push-in to a close-up actually looks like."""
    if not ft: return sz, None
    t0, bl = ft.get("from_t", 0.0), ft.get("blend", 1.0)
    if t <= t0: return sz, None
    body_off = [0.0, 0.0, sz[2] / 2.0]
    if bl <= 0 or t >= t0 + bl: return ft["size"], ft["offset"]
    u = smoother((t - t0) / bl)
    return ([sz[k] + (ft["size"][k] - sz[k]) * u for k in range(3)],
            [body_off[k] + (ft["offset"][k] - body_off[k]) * u for k in range(3)])

def surface_dist(pos, sz, yaw, cam, pitch=0.0):
    """Exact distance from the camera to the subject's ORIENTED BOX surface, 0 if
    inside. Centre-distance lies about anything long: a camera 2.8 m from a 4.3 m
    car's origin can be 0.6 m off its bumper, which is how a negative focal length
    gets through a green `subject_distance` gate."""
    d = (cam[0] - pos[0], cam[1] - pos[1], cam[2] - pos[2])
    # inverse of R = Rz(yaw).Rx(pitch)  ->  Rx(-pitch).Rz(-yaw)
    cp, sp = math.cos(-pitch), math.sin(-pitch)
    v = (d[0], d[1] * cp - d[2] * sp, d[1] * sp + d[2] * cp)
    c, s_ = math.cos(-yaw), math.sin(-yaw)
    lx, ly, lz = v[0] * c - v[1] * s_, v[0] * s_ + v[1] * c, v[2]
    qx = max(abs(lx) - sz[0] / 2.0, 0.0)
    qy = max(abs(ly) - sz[1] / 2.0, 0.0)
    qz = max(-lz, lz - sz[2], 0.0)
    return math.sqrt(qx * qx + qy * qy + qz * qz)

# --------------------------------------------------------------- subject ----
def solve_subject(spec, NF, fps):
    """mode 'profile': speed control points along a straight axis (walks, drives).
       mode 'waypoints': generic Catmull-Rom path.
       Returns (positions, yaws, speeds)."""
    s = spec["subject"]
    mode = s.get("mode", "profile")
    yaw_ev = s.get("yaw_events", [])

    if mode == "profile":
        cps = s["speed"]                       # [(t, v_m_per_s), ...]
        axis = s.get("axis", "y")
        def v_at(t):
            if t <= cps[0][0]: return cps[0][1]
            if t >= cps[-1][0]: return cps[-1][1]
            for i in range(len(cps) - 1):
                t0, v0 = cps[i]; t1, v1 = cps[i + 1]
                if t0 <= t <= t1:
                    return v0 + (v1 - v0) * smoother((t - t0) / (t1 - t0))
            return cps[-1][1]
        SUB = 4; dt = 1.0 / (fps * SUB)
        dist, d, t = [], 0.0, 0.0
        for i in range(NF):
            if i:
                for _ in range(SUB):
                    d += 0.5 * (v_at(t) + v_at(t + dt)) * dt
                    t += dt
            dist.append(d)
        # anchor: put a named distance-marker at a chosen world coordinate
        anchor = s.get("anchor")               # {"at_t": 10.2, "coord": -4.2}
        base = s.get("start", [0.0, 0.0, 0.0])
        if anchor:
            d_at = dist[min(int(round(anchor["at_t"] * fps)), NF - 1)]
            off = anchor["coord"] - d_at
        else:
            off = base[1] if axis == "y" else base[0]
        drift = s.get("lateral_drift", [0.0, 0.0])   # [amplitude_m, period_m]
        pos, spd = [], []
        for i in range(NF):
            t = i / fps
            dd = dist[i]
            lat = base[0]
            if drift[1] > 0:
                lat += drift[0] * math.sin(2 * math.pi * dd / drift[1])
            if axis == "y": p = (lat, off + dd, base[2])
            else:           p = (off + dd, lat, base[2])
            pos.append(p); spd.append(v_at(t))
    else:
        wps = s["waypoints"]                   # [(t, x, y, z), ...]
        kt = [w[0] for w in wps]
        pp = [(w[1], w[2], w[3]) for w in wps]
        pos = [tuple(catmull(kt, pp, i / fps, 3)) for i in range(NF)]
        spd = [0.0] + [length(sub(pos[i], pos[i-1])) * fps for i in range(1, NF)]

    # A curved path has a HEADING. Without this, `mode: waypoints` leaves the
    # block facing +Y while it drives round a corner sideways -- yaw_events would
    # have to hand-author every degree. yaw_from_path derives it from velocity;
    # yaw_events then add the SLIP on top, which is exactly what a drift is.
    base_yaw = [0.0] * NF
    if s.get("yaw_from_path"):
        k = int(s.get("yaw_smooth", 5))
        for i in range(NF):
            a, b = max(0, i - k), min(NF - 1, i + k)
            vx, vy = pos[b][0] - pos[a][0], pos[b][1] - pos[a][1]
            base_yaw[i] = (math.atan2(-vx, vy) if (vx * vx + vy * vy) > 1e-12
                           else (base_yaw[i - 1] if i else 0.0))
        for i in range(1, NF):      # unwrap: never spin the long way round
            while base_yaw[i] - base_yaw[i-1] >  math.pi: base_yaw[i] -= 2 * math.pi
            while base_yaw[i] - base_yaw[i-1] < -math.pi: base_yaw[i] += 2 * math.pi

    def _events(evs):
        out = []
        for i in range(NF):
            t = i / fps; a = 0.0
            for ev in evs:
                if   t < ev["t0"]: pass
                elif t < ev["t1"]: a += ev["angle"] * smoother((t - ev["t0"]) / (ev["t1"] - ev["t0"]))
                elif t < ev["t2"]: a += ev["angle"]
                elif t < ev["t3"]: a += ev["angle"] * (1 - smoother((t - ev["t2"]) / (ev["t3"] - ev["t2"])))
            out.append(a)
        return out
    pitches = _events(s.get("pitch_events", []))
    # pitch_steps: a STEP function, [(t, radians), ...]. The tilt is CONSTANT
    # inside a shot and only changes on a cut frame, where the hard cut hides it.
    # Use this, not pitch_events, when the product should BE tilted rather than
    # perform a tilting move.
    steps = s.get("pitch_steps")
    if steps:
        # Compare FRAME INDEX, not time. Shot boundaries use round(t0*fps); a
        # time-based test effectively ceils, so when a cut time rounds DOWN
        # (7.30 s at 24 fps -> frame 175.2 -> 175) the shot's first frame kept the
        # previous tilt for exactly one frame -- a one-frame pop on the cut.
        for i in range(NF):
            a = 0.0
            for (st, sa) in steps:
                if i >= int(round(st * fps)): a = sa
            pitches[i] += a

    yaws = []
    for i in range(NF):
        t = i / fps; y = base_yaw[i]
        for ev in yaw_ev:                      # {"t0","t1","hold","t2","t3","angle"}
            if   t < ev["t0"]:  pass
            elif t < ev["t1"]:  y += ev["angle"] * smoother((t - ev["t0"]) / (ev["t1"] - ev["t0"]))
            elif t < ev["t2"]:  y += ev["angle"]
            elif t < ev["t3"]:  y += ev["angle"] * (1 - smoother((t - ev["t2"]) / (ev["t3"] - ev["t2"])))
        # spin_rate: a CONSTANT turntable spin about the object's own axis.
        # An eased yaw_event accelerates and decelerates; a product turntable
        # should not. spin_schedule = [(t, rad_per_s), ...] changes the rate on a
        # cut -- e.g. stop it dead when the product comes to rest.
        # yaw_steps: absolute yaw, stepped on cut frames. Same trick as
        # pitch_steps -- used to set a base heading and to snap the roll on a cut.
        _ysteps = s.get("yaw_steps")
        if _ysteps:
            _a = 0.0
            for (_st, _sa) in _ysteps:
                if i >= int(round(_st * fps)): _a = _sa
            y += _a
        _sched = s.get("spin_schedule")
        if _sched:
            _a = 0.0
            for _k, (_t0, _r) in enumerate(_sched):
                _t1 = _sched[_k + 1][0] if _k + 1 < len(_sched) else 1e9
                if t <= _t0: break
                _a += _r * (min(t, _t1) - _t0)
            y += _a
        else:
            y += s.get("spin_rate", 0.0) * t
        yaws.append(y)
    return pos, yaws, spd, pitches

# ---------------------------------------------------------------- camera ----
def solve_camera(spec, c, subj, i0, i1, fps, yaws=None, pitches=None):
    """Solve one shot's camera over subject frames [i0, i1]. Times in the shot's
    waypoints are ABSOLUTE on the master timeline."""
    wps = c["waypoints"]        # {"t","pos":[x,y,z],"lens":mm,"aim":[dx,dy,dz]}
    kt   = [w["t"] for w in wps]
    ppos = [tuple(w["pos"]) for w in wps]
    plen = [(w["lens"],) for w in wps]
    paim = [tuple(w.get("aim", [0, 0, 0.9])) for w in wps]

    fit      = c.get("fit", 0.80)             # subject extreme sits at 80% toward the frame edge
    aim_dist = c.get("aim_distance", 5.0)     # carrot distance: kills 1/d rotation spikes
    smooth_k = c.get("subject_smooth", 6)     # frames each side; kills bob-induced camera jitter
    box      = c.get("bounds")                # {"x":[lo,hi],"y":[lo,hi],"z":[lo,hi]}
    aim_space = c.get("aim_space", "world")   # "local" = offset rides the subject
    # EXPLICIT PERMISSION TO CROP. {"offset":[x,y,z], "size":[sx,sy,sz], "from_t":s}
    # After from_t the in-frame gate and the lens cap target this sub-box instead
    # of the whole body -- the only way to reach a face close-up, because the gate
    # otherwise guarantees the whole figure stays in frame forever.
    ft = c.get("frame_target")
    sz       = spec["subject"].get("size", [0.5, 0.35, 1.8])

    NFtot = len(subj)
    subj_s = []
    for i in range(NFtot):
        a, b = max(0, i - smooth_k), min(NFtot - 1, i + smooth_k)
        n = b - a + 1
        subj_s.append(tuple(sum(subj[j][k] for j in range(a, b + 1)) / n for k in range(3)))

    cam, aim, lens_a, lens_c = [], [], [], []
    clamped = 0
    for i in range(i0, i1 + 1):
        t = i / fps
        p = list(catmull(kt, ppos, t, 3))
        if box:
            for k, key in enumerate("xyz"):
                if key in box:
                    lo, hi = box[key]
                    if p[k] < lo: p[k] = lo; clamped += 1
                    if p[k] > hi: p[k] = hi; clamped += 1
        p = tuple(p)
        ao = catmull(kt, paim, t, 3)
        if aim_space == "local":
            # rotate the offset into the subject's yawed frame: an offset to a
            # front wheel must swing WITH the car, not stay pinned to world axes
            ao = list(_rot(ao, yaws[i] if yaws else 0.0,
                           pitches[i] if pitches else 0.0))
        tgt = add(subj_s[i], tuple(ao))
        fwd = norm(sub(tgt, p))
        cam.append(p); aim.append(add(p, scale(fwd, aim_dist)))
        lens_a.append(catmull(kt, plen, t, 1)[0])

        # cap the lens by the subject's TRUE angular size from this camera, this
        # frame. This is the single check that stopped previz cropping the hero.
        th = 0.0
        _y = yaws[i] if yaws else 0.0
        _bs, _bo = target_box(t, sz, ft)
        for cpt in corners(subj[i], _bs, _y, _bo, pitches[i] if pitches else 0.0):
            v = norm(sub(cpt, p))
            th = max(th, math.acos(clamp(dot(v, fwd), -1.0, 1.0)))
        # th/fit >= pi/2 means it does not fit at ANY lens -- tan() flips sign
        # and yields a negative focal length. Clamp; the in-frame gate then fails
        # honestly instead of the shot silently carrying an impossible camera.
        ang = clamp(th / fit, 1e-4, math.pi / 2 - 1e-3)
        lens_c.append(max((SENSOR_H / 2.0) / math.tan(ang), MIN_LENS))

    N = len(lens_a)
    lens = [min(lens_a[i], lens_c[i]) for i in range(N)]
    S = c.get("lens_smooth", 8)              # smooth away the kink the cap introduces
    lens = [sum(lens[max(0, i-S):min(N, i+S+1)]) / len(lens[max(0, i-S):min(N, i+S+1)])
            for i in range(N)]
    return cam, aim, lens, clamped, sum(1 for i in range(N) if lens_a[i] > lens_c[i] + 0.01)

# ----------------------------------------------------------------- audit ----
def audit(spec, subj, cam, aim, lens, i0, fps, clamped, capped, tag="", lim=None, mute=(), yaws=None, ft=None, pitches=None):
    sz = spec["subject"].get("size", [0.5, 0.35, 1.8])
    lim = lim if lim is not None else spec.get("limits", {})
    MAX_RATE = lim.get("max_deg_per_s", 30.0)
    MIN_DIST = lim.get("min_subject_distance", 2.6)
    MIN_SPD  = lim.get("min_cam_speed", 0.05)
    MAX_SPD  = lim.get("max_cam_speed", 1e9)

    rates, speeds, dists, margins, fracs = [], [], [], [], []
    N = len(cam)
    prev_fwd = prev_pos = None
    for j in range(N):
        i = i0 + j
        fwd = norm(sub(aim[j], cam[j]))
        if prev_fwd is not None:
            rates.append(math.degrees(math.acos(clamp(dot(fwd, prev_fwd), -1, 1))) * fps)
            speeds.append(length(sub(cam[j], prev_pos)) * fps)
        prev_fwd, prev_pos = fwd, cam[j]
        dists.append(surface_dist(subj[i], sz, yaws[i] if yaws else 0.0, cam[j],
                                  pitches[i] if pitches else 0.0))
        # analytic in-frame check: worst subject corner vs the half-FOV of this lens
        half_v = math.atan((SENSOR_H / 2.0) / lens[j])
        half_h = math.atan((SENSOR_W / 2.0) / lens[j])
        worst_v = worst_h = 0.0
        right = norm((fwd[1], -fwd[0], 0.0))
        up = (right[1] * fwd[2] - right[2] * fwd[1],
              right[2] * fwd[0] - right[0] * fwd[2],
              right[0] * fwd[1] - right[1] * fwd[0])
        _bs, _bo = target_box(i / fps, sz, ft)
        for cpt in corners(subj[i], _bs, yaws[i] if yaws else 0.0, _bo,
                           pitches[i] if pitches else 0.0):
            v = sub(cpt, cam[j])
            f = dot(v, fwd)
            if f <= 0.01:
                worst_v = worst_h = 9.9; break
            worst_v = max(worst_v, abs(math.atan(dot(v, up) / f)) / half_v)
            worst_h = max(worst_h, abs(math.atan(dot(v, right) / f)) / half_h)
        margins.append(1.0 - max(worst_v, worst_h))
        fracs.append(min(worst_v, 3.0))          # subject height as a share of half-frame

    gates = []
    def gate(name, ok, detail): gates.append({"gate": name, "pass": bool(ok), "detail": detail})
    gate("subject_in_frame", min(margins) > 0.0,
         "%sworst edge margin %.1f%% of half-frame at frame %d"
         % ("[CROP from %.1fs] " % ft["from_t"] if ft and ft.get("from_t") else "",
            min(margins) * 100, i0 + margins.index(min(margins)) + 1))
    gate("rotation_rate", max(rates) <= MAX_RATE,
         "max %.1f deg/s (limit %.0f), mean %.1f" % (max(rates), MAX_RATE, sum(rates)/len(rates)))
    gate("subject_distance", min(dists) >= MIN_DIST,
         "min %.2f m to the BODY (limit %.2f) at frame %d"
         % (min(dists), MIN_DIST, i0 + dists.index(min(dists)) + 1))
    gate("camera_never_stalls", min(speeds) >= MIN_SPD,
         "min %.2f m/s (floor %.2f), max %.2f m/s" % (min(speeds), MIN_SPD, max(speeds)))
    gate("rig_can_move_this_fast", max(speeds) <= MAX_SPD + 1e-6,
         "max %.2f m/s (ceiling %.2f for this rig)" % (max(speeds), MAX_SPD))
    gate("no_bounds_clamping", clamped == 0,
         "%d samples hit the camera bounds box (pull the waypoints in)" % clamped)
    # ADVISORIES -- never fail a build, but a shot can pass every gate and still
    # be inert. The gates prove it is not broken; these ask if it is worth watching.
    adv = []
    fr_lo, fr_hi = min(fracs), max(fracs)
    d_lo, d_hi = min(dists), max(dists)
    l_lo, l_hi = min(lens), max(lens)
    mean_rate = sum(rates) / len(rates)
    if fr_hi - fr_lo < 0.15 and "size" not in mute:
        adv.append("subject stays the same size all shot (frame share %.2f-%.2f) "
                   "-- vary distance or lens, or it reads as a locked-off plate" % (fr_lo, fr_hi))
    if fr_hi < 0.30 and "small" not in mute:
        adv.append("subject never exceeds %.0f%% of half-frame -- it may read as a "
                   "landscape with a speck in it" % (fr_hi * 100))
    if d_hi / max(d_lo, 1e-6) < 1.25 and mean_rate < 1.5 and "static_rel" not in mute:
        adv.append("camera holds a near-constant relationship to the subject "
                   "(%.1f-%.1f m, mean %.1f deg/s) -- nothing develops" % (d_lo, d_hi, mean_rate))
    if l_hi / max(l_lo, 1e-6) < 1.4 and "lens" not in mute:
        adv.append("lens barely moves (%.0f-%.0f mm) -- fine for a fixed prime, but a "
                   "lens ramp would let the frame develop" % (l_lo, l_hi))
    # A lens that climbs, DIPS, then climbs again reads as a zoom-out/zoom-in punch
    # and is almost always the whole-body fit binding while the camera closes in --
    # not something you would ever author on purpose. Catching it by eye means
    # watching the render; this catches it in the solve.
    # The fault is a V: a fall that then RECOVERS. A lens that simply climbs and
    # then widens (a push-in that ends on a wide) is a legitimate arc, so the
    # magnitude has to be min(fall-before, rise-after) -- never just the fall.
    # Only count a reversal the viewer could actually SEE. A lens change that
    # happens inside a whip is invisible -- nobody reads focal length at 100 deg/s
    # -- and flagging it makes the advisory cry wolf on every station-to-station
    # motion-control move.
    # A WHIP breaks the comparison. On a station-to-station move the lens changes
    # inside each whip, where nobody can read focal length, and sits constant on
    # every held frame -- three separate framings, not a zoom punch. So a peak on
    # one side of a whip must not pair with a trough on the other: the running
    # maxima RESET whenever the camera is whipping (55 deg/s absolute -- above any
    # smooth move, below every real whip).
    WHIP = 55.0
    def _runmax(seq, rts, rev):
        idx = range(len(seq) - 1, -1, -1) if rev else range(len(seq))
        out, m = [0.0] * len(seq), -1e9
        for i in idx:
            j = i - 1 if not rev else i
            if 0 <= j < len(rts) and rts[j] > WHIP: m = -1e9      # reset at a whip
            m = max(m, seq[i]); out[i] = m
        return out
    _pre = _runmax(lens, rates, False)
    _post = _runmax(lens, rates, True)
    _dip, _di = 0.0, 0
    for _i, _v in enumerate(lens):
        if _i and _i - 1 < len(rates) and rates[_i - 1] > WHIP: continue
        _d = min(_pre[_i] - _v, _post[_i] - _v)
        if _d > _dip: _dip, _di = _d, _i
    if _dip > 0.08 * max(lens):
        adv.append("lens REVERSES %.0f mm (%.0f%% of max) at frame %d -- it climbs, "
                   "dips to %.0f mm, then climbs again, which reads as a zoom-out/"
                   "zoom-in punch. Usually the whole-body fit binding as the camera "
                   "closes; if a frame_target is in play, start its blend EARLIER so "
                   "the target shrinks as the distance does."
                   % (_dip, 100 * _dip / max(lens), i0 + _di + 1, lens[_di]))
    if min(lens) <= MIN_LENS + 0.01:
        adv.append("lens hit the %.0fmm floor -- the camera is too close for the "
                   "subject to fit; back off or accept a crop" % MIN_LENS)
    return {
        "tag": tag,
        "advisories": adv,
        "gates": gates,
        "all_pass": all(g["pass"] for g in gates),
        "lens_mm": [round(min(lens), 1), round(max(lens), 1)],
        "lens_capped_frames": capped,
        "cam_speed": [round(min(speeds), 2), round(max(speeds), 2)],
        "rot_deg_s": [round(min(rates), 1), round(max(rates), 1)],
        "frames": [i0 + 1, i0 + N],
    }

# ------------------------------------------------------------------ main ----
def load_spec(path):
    spec = importlib.util.spec_from_file_location("shotspec", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.SHOT

def main():
    if "--rigs" in sys.argv:
        print("\nRIGS -- the limits ARE the rig. Pick from the brief's own words.\n")
        for k in sorted(RIGS):
            r = RIGS[k]; L = r["limits"]
            print("  %-10s %s" % (k + ("*" if k == DEFAULT_RIG else ""), r["note"]))
            print("  %-10s rot<=%-5.0f dist>=%-4.2f speed %.2f-%.1f m/s  lens %d-%dmm\n"
                  % ("", L["max_deg_per_s"], L["min_subject_distance"],
                     L["min_cam_speed"], L["max_cam_speed"], r["lens"][0], r["lens"][1]))
        print("  * = default\n"); sys.exit(0)
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    path = sys.argv[1]
    SHOT = load_spec(path)
    fps = SHOT.get("fps", 24)
    NF = int(round(SHOT["seconds"] * fps))
    subj, yaws, spd, pitches = solve_subject(SHOT, NF, fps)

    # one shot or many -- a single "camera" block is just a one-shot sequence
    shots = SHOT.get("shots")
    if not shots:
        shots = [{"t0": 0.0, "t1": SHOT["seconds"], "camera": SHOT["camera"]}]

    rig_name, LIM, RIG = resolve_rig(SHOT)
    print("\n=== %s : %d frames @ %dfps (%.1fs) · %d shot%s ==="
          % (SHOT.get("name", "shot"), NF, fps, NF / fps, len(shots),
             "" if len(shots) == 1 else "s"))
    print("    rig: %s — %s" % (rig_name, RIG["note"]))
    print("    gates: rot<=%.0f deg/s · dist>=%.2f m · speed %.2f-%.1f m/s · lens %d-%dmm"
          % (LIM["max_deg_per_s"], LIM["min_subject_distance"], LIM["min_cam_speed"],
             LIM["max_cam_speed"], RIG["lens"][0], RIG["lens"][1]))

    out_shots, reports, ok = [], [], True
    for n, sh in enumerate(shots):
        i0 = int(round(sh.get("t0", 0.0) * fps))
        i1 = min(int(round(sh.get("t1", SHOT["seconds"]) * fps)) - 1, NF - 1)
        if n == len(shots) - 1: i1 = NF - 1
        cam, aim, lens, clamped, capped = solve_camera(SHOT, sh["camera"], subj, i0, i1, fps, yaws, pitches)
        rep = audit(SHOT, subj, cam, aim, lens, i0, fps, clamped, capped,
                    tag=sh.get("name", "shot %d" % (n + 1)),
                    lim=LIM, mute=RIG.get("mute", ()), yaws=yaws, pitches=pitches,
                    ft=sh["camera"].get("frame_target"))
        reports.append(rep); ok = ok and rep["all_pass"]
        _ftj = sh["camera"].get("frame_target")
        out_shots.append({"f0": i0 + 1, "f1": i1 + 1, "cam": cam, "aim": aim, "lens": lens,
                          # so PV.audit() knows the crop is DELIBERATE and does not
                          # report a designed close-up as a failure
                          "crop_from_f": (int(round(_ftj.get("from_t", 0.0) * fps)) + 1
                                          if _ftj else None)})

        _ft = sh["camera"].get("frame_target")
        if _ft:
            print("\n  !! CROP ENABLED from %.1fs (blending over %.1fs): framing gates "
                  "target a %s m box at local %s, NOT the whole body. The subject "
                  "WILL leave frame."
                  % (_ft.get("from_t", 0.0), _ft.get("blend", 1.0),
                     _ft["size"], _ft["offset"]))
        print("\n  -- %s  frames %d-%d  (%.1fs)" % (rep["tag"], i0 + 1, i1 + 1, (i1 - i0 + 1) / fps))
        print("     lens %s mm · speed %s m/s · rot %s deg/s"
              % (rep["lens_mm"], rep["cam_speed"], rep["rot_deg_s"]))
        for g in rep["gates"]:
            print("     [%s] %-22s %s" % ("PASS" if g["pass"] else "FAIL", g["gate"], g["detail"]))
        for a in rep["advisories"]:
            print("     [ADVISORY] %s" % a)

    print("\n  subject travel %.2f m · %s\n"
          % (length(sub(subj[-1], subj[0])), "ALL GATES PASS" if ok else "GATES FAILED"))

    if "--report" not in sys.argv:
        out = os.path.join(os.path.dirname(os.path.abspath(path)), "bake.json")
        json.dump({"name": SHOT.get("name", "shot"), "fps": fps, "frames": NF,
                   "subject": subj, "yaw": yaws, "pitch": pitches, "shots": out_shots,
                   "rig": rig_name, "limits": LIM,
                   "report": {"all_pass": ok, "shots": reports}}, open(out, "w"))
        print("  bake -> %s\n" % out)
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
