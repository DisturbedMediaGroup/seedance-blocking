# Camera rules

Numeric doctrine for blocked cameras. Every rule here exists because breaking it
produced a shot that had to be thrown away.

## Perceived smoothness is ROTATION rate, not path shape

A beautiful path with a spinning lens reads as broken. Judge the forward vector,
sampled every few frames, in degrees per second:

| °/s | reads as |
|---|---|
| ≤ 20 | serene |
| ~30 | deliberate pan — the ceiling for a continuous move |
| > 45 | a whip |
| spikes | a bug, not a style |

`solve_shot.py` gates this. Still frames cannot show it — never QC motion by eye
on stills.

## Angular rate goes as 1/distance

`rate ≈ v_perpendicular / d`. This single relation causes most whips.

- **Never let the thing you aim at come within ~2.6 m of the lens.** A subject
  passing at 1.3 m while walking 1.3 m/s spins the camera at ~57 °/s on its own.
- If you must be close, **move with the subject** so relative velocity is near
  zero. Matched speed at 1.4 m is calm; a static camera at 1.4 m is a whip.
- In a corridor the lateral offset is capped by the walls, so closeness is not
  something you can design your way out of — design the route to avoid it.

## Do not cross the subject in a narrow space

Going from in front of a subject to behind it means the sight line sweeps through
90° while the distance is at its minimum. Inside anything under ~6 m wide this
forces a choice between a whip and a lens too long to fit the subject.

**Stay on one side for the whole shot.** Get variety from height, lateral offset,
distance and lens instead — that is four axes, and it is plenty. Being behind the
subject also keeps whatever it walks toward visible as a destination.

## Derive the lens from framing, never from taste

Picking "a nice 50 mm" then discovering the subject does not fit is the single most
expensive previz error. With a 36 mm sensor at 16:9 (h = 20.25 mm):

```
subject fills fraction φ of frame height  ->  f = φ · d · 11.25   (mm)
maximum usable lens at distance d         ->  f_max = φ_max · d · 11.25
```

So a 68 mm compression shot of a 1.8 m subject needs ~11 m of separation. If your
set is not that long, **lengthen the set** — do not shorten the lens and pretend.

`solve_shot.py` caps the authored lens per frame by the subject's *true* angular
size, then smooths the cap's kink away. Authored lens is intent; the cap is the
guarantee.

## The carrot

Aim at a point projected to a **fixed distance** along the gaze direction (default
5 m), not at the subject's origin. Direction is identical; the fixed distance stops
a passing subject from injecting 1/d spin into the rig.

Smooth the subject position over ±6 frames before aiming at it. Raw position feeds
every bob and jitter straight into camera rotation.

Orientation comes from a **Track To constraint** on an aim empty — never from baked
rotation channels. Bake the aim empty's *position*; let the constraint solve the
rotation. This keeps the rig editable (drag the empty) and roll-free.

## Interpolation

**Non-uniform Catmull-Rom through all waypoints**, with time as the knot. It is C1
across waypoints, so velocity is continuous and speed is controlled by waypoint
*spacing in time*.

Do **not** smootherstep between each pair: that eases to zero velocity at every
waypoint and peaks 1.875× the average mid-segment, which turns an intended constant
crossing into a whip.

Bake per-frame with LINEAR interpolation. The smoothness is in your maths, not in
Blender's handles.

## Speed shape

- Nothing hits zero velocity mid-shot. A stalled camera reads as a mistake.
- An "accent" is a **slow-down plus a gesture** (a rise, a push-in, a lens move) —
  not a stop.

## Landing a HOLD without a bounce

A hold at the END of a shot is legitimate — it is a landing, not a stall. Two things
have to be right, and both are counter-intuitive:

**1. Duplicating the final waypoint does NOT stop the camera.** Catmull-Rom carries
momentum *through* a knot: the tangent there is set by its neighbours, so the spline
sails past the mark and eases back. Measured on a real shot: 57 mm of overshoot,
which at 1.9 m on an 84 mm lens is 25% of half-frame — a clearly visible bounce.

The fix is a **geometrically decelerating approach** — place the last few waypoints
so the distance to the mark collapses, and the incoming velocity is near zero before
the duplicates begin:

```
0.59 m -> 0.31 m -> 0.065 m -> ON THE MARK -> dup -> dup
```
That took the same shot from 57 mm of overshoot to 4.8 mm (0.15°, invisible).

**2. The `camera_never_stalls` gate has to be switched off** for that shot —
`"limits": {"min_cam_speed": 0.0}`. It is guarding against an *accidental* stall
mid-move, which is a real fault; a deliberate landing is not. The `robo_arm` preset
already ships 0.0 for exactly this reason. **The override applies to the WHOLE shot,
so nothing earlier is protected any more — check the speed profile by hand before
you rely on it.**

Verify a hold by measuring, never by eye: max deviation from the mark, camera speed,
and lens over the hold window. All three must be flat.
- Commercial rhythm: snap in fast → sag in the middle → accelerate out into the cut.
- Speed is *read* from proximity, not from m/s. 0.8 m/s at floor level 0.25 m from a
  ribbed wall on an 18 mm lens reads far faster than 2 m/s down the middle on a 50.

## Handheld

Lazy 4–6 s sway waves + a gentle breathing float + a barely perceptible tremor.
**Never fast jitter.** Livelier during orbits, lazier in over-the-shoulder holds.

## When a gate fails

| Gate | Fix |
|---|---|
| `subject_in_frame` | shorten the lens at that beat, or move the camera back. The report names the frame |
| `rotation_rate` | increase distance at the crossing, match the subject's velocity, or spread the turn over more time |
| `subject_distance` | re-route; do not "fix" it with a wider lens |
| `camera_never_stalls` | waypoints are too close in space or too far apart in time |
| `no_bounds_clamping` | pull waypoints in — the spline overshoots between them. Clamping flattens the curve and puts a kink in the motion |
