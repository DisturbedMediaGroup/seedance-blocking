---
name: seedance-blocking
description: Idea → blocked Blender previz you watch in the viewport → asset list → Seedance 2.5 prompt. Defaults to a checkerboard void when the brief names no place (one line, no set to build), composes a named environment on the spot from generic parts (there is no environment library), blocks subjects as coloured boxes, solves and audits the camera offline before touching Blender, and delivers to the viewport for notes instead of rendering. Handles one continuous shot or a multi-shot sequence with hard cuts. Takes either a full brief or a vague idea — with no brief at all it asks for one in chat, in prose, once. Carries a hardening pass of failure modes measured in production - void backgrounds drifting grey, bloom painting the frame, effects with no scale, colour that cannot carry an ambiguous proxy's identity, aspect mismatches. Use whenever someone wants to previz, block, or storyboard a shot in 3D; wants a camera move designed; wants a Seedance/Higgsfield video prompt driven by real camera motion; or hands over a STORYBOARD to turn into a blocking; or says "block this", "previz this", "camera move for this shot", "napravi blocking", "blokiraj kadar", "storyboard u blocking". NOT for finished renders, modelling, or look-dev - and NOT when a blocking video already exists and only needs a prompt written against it, which is the seedance-reskin skill.
---

# Seedance Blocking

**Blender locks the motion. Seedance builds the world around it.**

Block the shot as coloured boxes, let the user watch it in their viewport, and once
they are happy render the greybox as a motion log. That clip becomes Seedance's sole
authority for camera, cuts and timing; the prompt only *re-dresses* what the blocking
already does. Without blocking, a 30 s shot burns thousands of credits and never
matches. With it, first try.

Doctrine: `references/SEEDANCE_PROMPT.md` · camera maths: `references/CAMERA_RULES.md` ·
moves, framings and set composition: `references/SHOT_GRAMMAR.md`.

---

## Four rules that define this skill

**1. No environment named? Build the checkerboard and move on.**
`PV.checker()` is the default set: **one line**, three objects, nothing to compose
and nothing to occlusion-check. The squares streaming past are real parallax in
every axis, so height, speed, heading and ground contact all read. Add `posts=12`
if a crane or an orbit needs an off-ground reference.

**Only build a place when the brief NAMES one.** Inventing a plaza nobody asked for
costs minutes of composition and hands Seedance a location the user never wanted.
A blocked void is also more on-doctrine, not less: Blender locks the motion,
Seedance builds the world. A camera-move request is a camera-move request.

**2. When a place IS named, there is no environment library — compose it from parts.**
`previz_core` ships `checker`, `slab`, `row`, `cyl`, `ground`, `light`, `light_row`,
`sun`, `marker`, `actor`. That is all. A corridor, a city street, a subway platform, a
forest clearing and a car park are all the same six ideas arranged differently.
**Never add a named environment function to the skill.** Compose it in the shot spec —
that is the whole point, and it takes a dozen lines.

**3. Solve the camera in arithmetic before opening Blender.**
Whip pans, the hero cropped out of frame, the camera inside a wall, a set too short
for the lens — all visible in numbers. `solve_shot.py` finds them in 0.05 s. Blender
finds them after a build and a render. Solve the shot, then build the set to fit it.

**4. Deliver to the VIEWPORT, never to a render.**
Build it, call `PV.viewport_ready()`, and tell the user it is ready to play. They
watch it in Blender and give notes. **Render nothing until they approve the motion.**
Multi-shot sequences play with live cuts in the viewport too — see below.

**5. The conversation is the interface.**
Notes arrive as chat — "start slower", "get lower at the end", "make the street
narrower". You edit the spec, re-solve, rebuild, say it is ready again. The user
never opens the spec file; it is your scratch file, not their UI.

---

## Pipeline

Project folder: `~/Movies/previz_blocking/<shot>/`.

### 1 — Intake. Two modes. Always start here.

A shot is specified when you know: **action · setting · duration · camera intent ·
framing arc**.

**Mode A — there is a brief.** Anything that names an action or steers the camera
is enough. **Do not ask anything.** Fill every gap from the defaults below, restate
the shot in four lines so a misread costs a sentence, and build in the same turn.

**Mode B — there is no brief at all.** Ask for one **in chat, in prose. NEVER use
`AskUserQuestion`** — a four-question option card to collect one line of description
is friction, not a service. They type faster than they click.

Ask once, short, and state the defaults so a one-line reply is always enough:

> What's the shot? Action and camera is plenty — e.g. *"block runs, camera whips
> past him at knee height"*. Unless you say otherwise: checkerboard void, 15 s,
> deliberate camera.

**One ask, ever.** If the reply is still thin, take the defaults and build — notes
on a shot they can watch are cheaper than another question. Never ask about setting,
length or camera energy separately; they all have defaults.

**Defaults when unstated:** checkerboard void · 15 s · `gimbal` rig · one
continuous shot · red block hero.

### 1b — Pick the RIG. This is the single highest-leverage choice you make.

**The limits ARE the rig.** A 76 °/s whip is a bug on a gimbal and the entire point
on a robot arm; a dead stop is a mistake on a drone and the signature move on a
Bolt. Author the wrong rig and the shot comes out polite and generic no matter how
good the waypoints are.

Read it straight out of the brief's own words and set `"rig": "<name>"` in the spec:

| brief says | rig | character |
|---|---|---|
| *(nothing about the camera)* | `gimbal` **default** | smooth, flowing, never whips or stops |
| "steadicam", "floating", "long take" | `steadicam` | heavier, calmer, gentle arcs |
| "handheld", "documentary", "raw" | `handheld` | looser, jerks and corrects, close |
| "locked off", "just a pan", "tripod" | `tripod` | pan/tilt only — **cannot translate** |
| "dolly", "track in", "push in" | `dolly` | straight track, calm, translation not rotation |
| "crane", "jib", "rises above" | `crane` | big smooth arcs through height |
| "robo arm", "motion control", "Bolt", "snappy/precise" | `robo_arm` | **whips**, lens within arm's reach, **stops dead** |
| "macro", "probe lens", "snorkel", "inside the object" | `probe_macro` | rigid probe on a motion-control arm, **centimetres** from the subject, prime lens, gentle on-screen rates |
| "FPV", "drone", "dive", "fly through" | `fpv_drone` | never hovers, huge speed, ultra-wide, proximity is the effect |
| "cable cam", "zipline", "flies alongside" | `cable_cam` | straight line at speed, dead smooth |
| "car mount", "rigged to the car", "chase" | `car_mount` | fast travel, barely rotates |

`python3 <skill>/scripts/solve_shot.py --rigs` prints the numbers. A rig gates
rotation, subject distance, **and both a speed floor and ceiling** — a gimbal
operator cannot run at 8 m/s, a drone cannot hover mid-dive, a tripod cannot move
at all. It also mutes the advisories that are meaningless for it (a robot arm does
not zoom; an orbit holds subject size on purpose).

Need one exception? Add a `limits` block — it overrides the rig **field by field**,
so a single tweak never means abandoning the preset. Unknown rig name = hard error,
never a silent fallback.

### 2 — Write the spec. The set is `checker()` unless a place was named.

Write it from the reference below — there are no example files to copy, on purpose.
**No place named → skip `SHOT_GRAMMAR.md` entirely.** Only when the brief names
somewhere do you compose a set, and only then does that file apply.

```python
SHOT = {
  "name": "myshot", "fps": 24, "seconds": 12,
  "rig": "robo_arm",              # see 1b. omit -> gimbal
  "limits": {...},                # OPTIONAL, overrides the rig field by field

  "subject": {
    "mode": "profile",            # straight-axis walk/drive. speed is the control
    "size": [0.50, 0.35, 1.80], "axis": "y", "start": [x, y, z],
    "speed": [(t, m_per_s), ...], # interpolated, integrated to a distance curve
    "anchor": {"at_t": 10.2, "coord": -4.2},   # optional: be HERE at this time
    "lateral_drift": [0.08, 4.0],              # optional: [amplitude_m, period_m]
    "yaw_events": [{"t0":9.9,"t1":11.3,"t2":12.7,"t3":14.3,"angle":0.95}],  # turn+return
  },
  # or "mode": "waypoints" with "waypoints": [(t, x, y, z), ...] for a free path.
  # A STATIC subject is "speed": [(0.0, 0.0), (T, 0.0)].

  "shots": [                      # one continuous shot == a list of length one
    {"t0": 0.0, "t1": 4.0, "name": "wide", "camera": {
        "fit": 0.88,              # 0.80 default. higher = subject fills more frame
        "aim_distance": 3.0,      # carrot distance, 5.0 default
        "subject_smooth": 6,      # +/- frames of subject smoothing before aiming
        "lens_smooth": 8,         # smooths the kink where the lens cap bites
        "bounds": {"x": [lo, hi], "z": [lo, hi]},   # optional; clamping FAILS a gate
        "waypoints": [            # times are ABSOLUTE on the master timeline
          {"t": 0.0, "pos": [x, y, z], "lens": 24, "aim": [0, 0, 0.95]},
        ]}},
  ],

  "beats": [(0.0, "what the frame says here"), ...],   # for the Seedance prompt
}
```

`pos` is **world space**; `aim` is an **offset from the subject**. Author the camera
as offsets from a moving subject and convert (`pos = [ox, y_subject(t) + oy, oz]`) —
that is how you keep a relationship legible while he moves.

**`build` and `lights` keys are inert.** The solver never reads them. Put the set
there as notes if you like, but the set is real only when you call `PV.*` in step 5.

### 2b — Storyboard intake. When the brief IS a board.

A storyboard is a richer intake than a sentence and a poorer one than it looks: it gives the
scene list, the composition and the action, and almost never gives **duration**. Read
`references/STORYBOARD.md` — it covers extracting the scenes, the four questions to ask in one
message, distributing time by weight of action, scenes-as-beats, and the **carrier** pattern for
ensemble films that have no single hero.

### 3 — Solve. Loop here, not in Blender.

```bash
python3 <skill>/scripts/solve_shot.py myshot.py
```
Six gates **per shot**: subject in frame, rotation rate, subject distance (to the
BODY, not the origin), camera never stalls, camera never exceeds the rig's speed
ceiling, no bounds clamping. Exit 0 = all passed. **Do not open Blender until it
exits 0.** Each loop is 0.05 s — iterate freely.

**If objects swap depth order, run the choreography gate as well:**

```bash
python3 <skill>/scripts/carousel_gate.py myshot.py
```

`solve_shot.py` proves the CAMERA is valid. On a locked-off ensemble film it passes trivially —
`travel 0.00 m · rot 0.0 deg/s` — and proves nothing, because the camera is not what is at risk.
Five gates over the spec's `cast` and `choreography` blocks measure what is: exactly one member
clearly in front, its silhouette actually cutting across the others, depth agreeing with size,
no scale pops, no census overflow. A spec with no `cast` block is skipped, not failed. Format in
`references/STORYBOARD.md`.

It exists because a three-product depth carousel came back as a static line-up — one left, one
centre, one right, nothing overlapping, only the sizes changing. The swap order was correct and
the film still read wrong. The gate fails that arrangement in arithmetic, before a frame is
rendered.

### 4 — Push the core into Blender (once per session).

```python
SK = "<skill path>"
mod = type(bpy)("PV"); mod.__dict__["__file__"] = SK + "/scripts/previz_core.py"
exec(open(SK + "/scripts/previz_core.py").read(), mod.__dict__)
bpy.app.driver_namespace["PV"] = mod
```
It stays resident; later calls are `PV = bpy.app.driver_namespace["PV"]` plus a line.

### 5 — Build and hand over the viewport, in ONE call.

**The default build — copy it verbatim, nothing to look up:**

```python
PV.wipe()                       # clear the previous pass, nothing else
PV.reset(fps=24, seconds=15)
PV.checker()                    # THE SET. posts=12 for a crane/orbit reference
PV.sun()
PV.actor("HERO", color="red", oriented=True)
PV.load_bake("bake.json")       # subject + one camera per shot + markers on the cuts
PV.viewport_ready()
```

Only when a place was named does `PV.checker()` become a dozen lines of parts.
`PV.audit()` re-measures rotation, distance and in-frame from Blender's *evaluated*
matrices — the only proof the bake actually landed, and it costs one call. It gates
against the **rig's** limits automatically (`load_bake` carries them across from the
bake), so nothing needs forwarding. Run it,
then tell the user: **it is ready, press Space.** Do not render.

### 6 — Take notes, re-solve, rebuild.

Edit the spec, re-run the solver, re-run the build call. Seconds per iteration.
`PV.backup("S02_camera_v2")` after anything worth keeping — copies only, never
changes the active .blend path.

### 7 — Only when they approve: render.

`PV.motion_render(path)` renders every frame and loads the machine — say so first.
1920×1080, 24 fps, MP4, greybox. Grey is correct: it is a motion log.

**Render at the delivery aspect, and never hand over a viewport capture instead.** The aspect is
a build setting no prompt can compensate for: a 1132×822 source (1.377:1) with a prompt asking
for 16:9 forces the model to reconcile a 29% difference, and it crops height — which is usually
the axis the subject moves along. `motion_render()` is 16:9; if the delivery is 9:16 or 21:9,
set the resolution before rendering, not after. `references/HARDENING.md` §4.

### 8 — Deliver the package.

The motion clip, the **asset list** (one line per coloured proxy → what it becomes,
and the reference image it needs), and the **Seedance 2.5 prompt** against the beat
table. Ask the style layer here — photoreal / stylised / animated — not at intake.

**PUT THE PROMPT IN THE CHAT, IN ONE FENCED BLOCK. Never write it to a file.**
The prompt's only destination is a paste box in Higgsfield. In chat that is one
click on the block's copy button; in a `.md` it is open the file, select all, copy,
and hope nothing was missed. Length is not a reason to move it out — it is the
deliverable, not a summary of one. Same for the **asset list**: a small table in
chat, right under the prompt.

Keep everything that is NOT for pasting out of that block — the tag warning, the
style questions, what still needs a reference. Those go in your own text around it,
so the block stays clean enough to paste blind.

**Read `references/SEEDANCE_PROMPT.md` before writing a word of the prompt.** It
carries the 8-section skeleton and four things that are easy to get wrong and
invisible when you do: copy the @ tag string character-for-character, disown a
multi-view reference sheet's layout, mine the SPEC (not the beats prose) for hard
distances and angles, and write a containment rule for every element you did not
block — the fluid you were told never to block has no lock on it at all.

**Then read `references/HARDENING.md`** and run its pre-flight list against your draft. It
covers the ways a structurally correct prompt still comes back wrong — each measured on a real
job, none visible in the prompt itself: a void that drifts to grey because a word implied a
wall, glow that paints the background because `bloom` was described rather than banned, a splash
that fills the frame because "small" has no scale, a count copied from a previous shot, a cause
named that was never in frame, and platform settings in the text that contradict the file.

---

## Multi-shot sequences

One continuous shot is a sequence of length 1, so the same machinery does both.

```python
"shots": [
  {"t0": 0.0,  "t1": 4.0,  "name": "wide",  "camera": {...}},
  {"t0": 4.0,  "t1": 9.5,  "name": "track", "camera": {...}},
  {"t0": 9.5,  "t1": 15.0, "name": "close", "camera": {...}},
]
```

`load_bake` builds **one camera per shot** and binds each to a timeline marker on its
cut frame. In camera view the active camera switches at the marker, so **the whole
sequence plays with hard cuts live in the viewport — no render.** Each shot is
solved and gated independently, and cuts are hard by construction because nothing
interpolates across a shot boundary.

Seedance 2.5 takes ~5 shots of 2–3 s in one pass. Cuts get declared in the prompt;
**always feed one continuous video file** — never an edited reel.

## Defaults — how it gets BUILT

Intake settles *what the shot is*. These settle *how it is constructed* — never ask.

- **The hero is one red box**, `0.50 × 0.35 × 1.80 m` for a person. Never a character,
  never a rig. A block holds framing exactly as well and costs nothing to change.
- **Colour is identity — but it cannot carry the identity of an ambiguous shape.** Extra
  subjects get contrasting colours from `PV.PALETTE`; the prompt maps them (`red = @Image 9,
  cyan = @Image 8`). `oriented=True` paints facing in — +Y red, −Y black, sides and top green.
  **The limit, measured:** colour may select a *variant* of an object whose shape already says
  what it is (a cylinder is a can, six hues are six flavours — the map holds). It may **not**
  carry the *identity* of an object whose shape says nothing. Magenta discs became lemon slices
  in the render while magenta spheres in the same frame stayed pink, under the same prompt,
  with the map stated three times: the disc's silhouette reads as *slice*, the sphere's reads as
  nothing, so the model kept the only signal it had. The prompt enters once; the colour is in
  every frame at exact pixel coordinates. **When a proxy's shape is ambiguous, block it near its
  final colour** and separate objects by value and saturation rather than hue. Details:
  `references/HARDENING.md` §3.
- **Build only what gives the camera parallax.** That is the entire job of a blocking
  set. Repeating verticals carry the speed read, a bright destination anchors framing,
  overhead lines streak on fast beats, a floor line sells perspective. Build those and
  stop.
- 24 fps, 1920×1080, EEVEE, Z-up, metres, radians.

## Hard limits the solver enforces

Six gates per shot. Four of them come from the **rig** (see 1b), so the numbers
below are the `gimbal` default, not universal law.

| Limit | gimbal default | Why |
|---|---|---|
| rotation rate | ≤ 30 °/s | above this reads as a whip — *on this rig* |
| subject distance | ≥ 2.6 m | angular rate ∝ 1/d; a close pass spins the camera |
| camera speed floor | 0.05 m/s | a stalled camera reads as a mistake — *on this rig* |
| camera speed ceiling | 3.0 m/s | an operator cannot run faster than the rig allows |
| subject in frame | every frame | rig-independent; lens is derived from framing |
| no bounds clamping | 0 samples | rig-independent; clamping kinks the curve |

## Traps that have actually cost time

- **Blender 5.2 slotted actions:** `animation_data_clear()` only *unlinks*; the next
  keyframe re-links the same action with every stale fcurve intact, so re-baking
  merges generations of keys and the camera backtracks. `PV.bake()` destroys first.
- **`action.fcurves` does not exist in 5.2** — use
  `action.layers[0].strips[0].channelbag(slot)`.
- **Lens keys live on `camera.data`**, not the object.
- **Track To rolls the frame near nadir.** Roll comes from projecting the up axis
  (world +Y) into the image plane, so once the view is within ~5 deg of straight
  down it is set by whatever tiny horizontal offset is left. Converging to dead
  centre overhead swung a shot 85 deg of roll in 1.5 s. Approach top-down along ONE
  azimuth, keep a small constant offset, and stop at ~86 deg -- it reads identically
  and the roll stays put.
- **Editing `previz_core.py` does NOT update Blender.** The module is exec'd once
  and parked in `bpy.app.driver_namespace["PV"]`; after any edit you MUST re-run
  the step-4 push or you are still calling the old code. Cost me a build that
  silently dropped a whole animated channel.
- **Blender 5.x split video out of `file_format`.** Setting `'FFMPEG'` raises
  *enum "FFMPEG" not found* until `image_settings.media_type = 'VIDEO'` is set
  first. `PV.motion_render()` handles it; anything else touching render output
  must too.
- **Catmull-Rom, not per-segment easing** — smootherstep between waypoint pairs pulses
  velocity to zero at every waypoint and spikes 1.9× mid-segment.
- **Don't cross the subject** in anything narrower than ~6 m: it forces either a whip
  or a lens too long to fit. Stay on one side; vary height, lateral, distance, lens.
- Viewport screenshots need the eye *inside* the set — a downward tilt pushes it up
  through the ceiling.
- **Never let two opaque faces share a plane.** A road slab whose top is at z=0 on
  a ground whose top is at z=0 z-fights, and it flickers in the RENDER too — same
  depth buffer, and it changes per frame so it is worse in motion. `ground()` now
  drops 2 cm clear by default; overlapping tiles need a real z stagger (~1 cm, not
  1 mm) because depth precision at 100 m is coarse.
- **Rectangles cannot tile an arc.** Curved roads built from rotated slabs leave
  wedge gaps on the outside — overlap each segment ~35% *and* stagger z.

## Reference routing

| Need | Read |
|---|---|
| writing the Seedance prompt, ref definitions, state accounting | `references/SEEDANCE_PROMPT.md` |
| a camera gate failed, or designing a move | `references/CAMERA_RULES.md` |
| framings, ramps, cuts, **or a set the brief actually named** | `references/SHOT_GRAMMAR.md` |
| the brief named no place | nothing — `PV.checker()`, do not open SHOT_GRAMMAR |
| **the intake is a storyboard** | `references/STORYBOARD.md` — scenes, timing, the carrier pattern |
| objects swap depth order, or a carousel reads wrong | `scripts/carousel_gate.py` + the `cast`/`choreography` format in STORYBOARD.md |
| **checking the prompt before it ships** | `references/HARDENING.md` — pre-flight list at the end |
| a black void, a glow that will not go, a splash that fills frame | `references/HARDENING.md` §6, §7, §9 |
| an effect that must be present but restrained | `references/HARDENING.md` §9 — a reach, not a count |
| an ambiguous proxy shape, or the delivery aspect | `references/HARDENING.md` §3, §4 — these change the BUILD |
