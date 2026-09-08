# Shot grammar

Vocabulary for blocking. Pick from here rather than inventing; the point is to
choose fast and move on.

## Framings, and what each one costs

| Framing | φ (frame height) | needs |
|---|---|---|
| establishing wide | 0.10–0.20 | distance, and a set deep enough to see |
| full figure | 0.45–0.65 | the workhorse |
| medium | 0.70–0.85 | close, or a long lens |
| detail / macro | subject cropped | explicit permission — breaks "always in frame" |

A shot needs **four or five distinct framings** across 30 s. Vary them on the axes
that are free: height (floor level to ceiling), lateral offset (wall to wall),
distance, lens. Changing only one axis reads as one framing that drifts.

## Moves that survive contact with a video model

- **Retreating lead** — camera ahead, backing off as the subject advances. Reads
  as pursuit. Watch the distance: it shrinks unless the camera keeps pace.
- **Following behind** — safest for a corridor. Whatever the subject walks toward
  stays visible as a destination.
- **Rise and compress** — camera lifts while the lens lengthens. Good for a pause.
- **Floor skim** — drop to 0.4–0.6 m near a textured wall on a wide lens. The
  cheapest way to make a moderate speed read as fast.
- **Arc on the pause** — while the subject is stationary, swing laterally. Free
  angular budget, because the subject is not adding relative velocity.
- **Dolly–zoom** — dolly and lens move in opposite directions. Use once, on a beat
  that earns it.

## Speed ramps

Snap in fast → sag through the middle → accelerate out. Author it as waypoint
*spacing in time*, not as easing curves: waypoints close in time = fast, far
apart = slow. Aim for 3–5× contrast between the slowest and fastest beat.

## Pauses

A pause needs a **reason in the set** — a panel, a door, a sign, something to look
at. Put the prop in before you write the pause, and turn the subject toward it
(`yaw_events`). A pause with nothing to look at reads as a dropped frame.

The camera does **not** stop when the subject does. That is the accent: the camera
slows and does something small and deliberate.

## Cuts

Blocking one continuous shot is the default and the safest input to Seedance.

If the piece needs cuts: camera, target and lens change **strictly on the cut
frame**, zero transition frames. Declare cuts in the prompt, never edit them into
the reference clip — Seedance must receive one continuous take. Up to ~5 shots of
2–3 s each work in a single pass.

## Markers for the model

- **Black gaps** (`PV.marker(name, "gap", ...)`) — a couple of seconds of black
  volume the model fills: liquid, smoke, crowds, chaos. Never block a fluid.
- **Coloured slabs** (`PV.marker(name, "swap", ...)`) — a stand-in the prompt names
  and maps to a reference image.
- Grids and checkerboards read as explicit "replace me" surfaces.

## Set design for parallax

The set exists to give the camera something to move against. In order of value:

1. **Repeating vertical elements** — ribs, columns, posts, doorways. These carry
   the speed read.
2. **A bright destination** — a lit doorway, a window, a horizon. Anchors every
   framing and gives the shot direction.
3. **Overhead lines** — pipes, beams, strip lights. They streak on fast beats.
4. **A floor line** — a stripe or seam. Sells perspective for free.

Everything else is decoration. Build 1–4 and stop.

---

# Composing a set

There is no environment library and there must never be one. Every place is built
from the same parts in the shot spec:

| part | is | used for |
|---|---|---|
| `checker` | **the default set** | anywhere the brief did not name — one line, done |
| `slab` | one box | floors, walls, facades, kerbs, platforms, roofs, crates, steps |
| `row` | a slab arrayed N times | **the parallax workhorse** — ribs, piers, columns, lamps, parked cars, fence posts, trees, sleepers, windows |
| `cyl` | a cylinder | pipes, poles, trunks, barrels, pillars |
| `ground` | a big flat slab | any exterior |
| `light` / `light_row` / `sun` | lights | practicals, key, sky |
| `marker` | a coloured or black box | "replace me" stand-ins → asset-list lines |

`row` is doing most of the work. A 500 m colonnade is one object with an Array
modifier, so length is free.

## The method

Ask three questions of any place, in this order:

1. **What are the bounds?** Floor, and whatever encloses it (two walls, four walls,
   nothing). Two or three `slab`s.
2. **What repeats?** This is the shot. Repeating verticals at a regular spacing are
   what make camera movement legible — without them a corridor is a grey tube and a
   street is a car park. One or two `row`s.
3. **What is the destination?** One bright thing the camera can point at: a lit
   doorway, a window, a sky gap, a headlight. One emissive `slab` plus a `light`.

Anything beyond those three is decoration. Stop.

## Recipes

Part lists, not functions. Adapt the numbers.

**Before any of them: did the brief actually NAME a place?** If not, the recipe is
`PV.checker()` and you are finished — do not read further down this page. A
checkerboard is not a fallback, it is the correct answer to a camera-move request:
it reads scale, speed, height, heading and ground contact, costs one line, and
leaves Seedance free to build the world the prompt describes. Everything below is
for briefs that named somewhere.

**Interior corridor** — floor, ceiling, two walls (`slab` ×4); vertical ribs both
walls every ~2.6 m and ceiling strips every ~5.2 m (`row` ×3, strips emissive);
lit doorway at the far end (2 slabs + header + emissive panel + area light);
`light_row` of practicals under the strips.

**City street** — road slab; two raised pavement slabs + kerbs; two tall facade
slabs pushed ~6 m either side of centre (height 14–18 m, nobody sees the tops);
facade piers every ~3.6 m (`row` ×2) — *these are the parallax*; lamp posts +
emissive heads every ~13 m (`row` ×2); parked cars as a `row` of `marker`-coloured
slabs along each kerb; low `sun` for long shadows.

**Interior room** — floor, ceiling, three or four walls; one overhead area light;
a window as an emissive slab if you need a destination. Rooms have almost no
parallax, so the camera has to earn it — orbit, or put furniture slabs in the
foreground.

**Open exterior** — `ground` + `sun`. Empty ground reads as nothing at all, so the
shot lives or dies on `row`s and markers: a fence line, a treeline, pylons, a
wrecked vehicle. Place at least one thing that passes close to the lens.

**Subway platform** — platform slab raised ~1.1 m; track trench below; tiled back
wall; column `row` down the platform centre every ~4 m; strip lights overhead;
tunnel mouth as a black `marker` (the model fills it).

**Forest / colonnade** — `ground` + three `row`s of `cyl` trunks at different
spacings and lateral offsets. Offsetting the rows is what stops it looking like an
orchard.

## Scale sanity

Human 1.8 m · door 2.1 m · corridor 2.4–3.0 m wide · room ceiling 2.7–3.2 m ·
street lane 3.5 m · pavement 2.0–3.0 m · city facade 12–20 m · lamp post 4.5 m ·
car 1.8 × 4.4 × 1.45 m.

Get these right and the previz reads as a place at a glance. Get them wrong and no
camera move rescues it.
