# From a storyboard to a shot spec

A storyboard is a richer intake than a one-line brief, and a poorer one than it looks. It gives
you the scene list, the composition and the action. It almost never gives you **duration**, and
without that there is no spec.

This file is the conversion. Read it when the intake is a storyboard — a URL, a PDF, a deck, or
a folder of numbered frames.

---

## Read it first, ask second

Extract the scene list before asking anything. A storyboard viewer usually renders one panel per
scene as `title + description + image`; pull the text and count the panels.

```js
// browser: scene text
document.body.innerText
// browser: one image per panel
[...document.querySelectorAll('img')].map(i => i.src)
```

For a PDF or a deck, read the pages. For a folder, sort by filename.

Then you know the scene count, and you can ask the four questions that a storyboard cannot
answer, **in one message**:

> 15 scenes. Four things the board doesn't say:
> **1.** Total duration?
> **2.** One continuous take, or cuts?
> **3.** The burst/splash scenes — block the solid objects and leave the fluid as gaps, or leave
> the whole beat black?
> **4.** Anything organic (a hand, a face) — blocked as a box, or left to the model?

Everything else you derive. Do not ask about camera, colour, palette or set — those have
defaults and the board itself usually implies them.

---

## Distribute the duration

Divide the total across scenes by **weight of action**, not evenly. A logo holding still and a
five-element burst are not the same length.

| scene does | weight |
|---|---|
| a hold — logo, packshot, settled group | 3–4 s |
| a simple swap — one object comes forward | 2–2.5 s |
| a burst, a reveal, a multi-element event | 4.5–5 s |
| a compound action — a hand picking up and passing an object | 8+ s |
| an establishing arrangement — a group forming | 4–6 s |

Sum it and check it lands on the total exactly. Print the table and show it before writing the
spec — a wrong timing is cheap here and expensive after a render.

```
SCENE  1   0.0- 3.0  ( 3.0s)  logo opens
SCENE  2   3.0- 7.0  ( 4.0s)  five-flavour carousel
...
TOTAL 60.0s
```

---

## Map scenes to beats, not to shots

A `shots` entry is a camera. A `beats` entry is a moment in the film. **A 15-scene storyboard
shot as one continuous take is ONE shot and FIFTEEN beats** — not fifteen shots.

```python
"shots": [ {"t0": 0.0, "t1": 60.0, "name": "oner", "camera": {...}} ],
"beats": [ (0.0, "SCENE 1 — ..."), (3.0, "SCENE 2 — ..."), ... ],
```

Only split `shots` when the board actually calls for a cut. Cuts are hard by construction — the
solver gates each shot independently and nothing interpolates across a boundary.

---

## The subject problem: ensemble films

The solver tracks ONE subject. Many storyboards — product carousels, ensemble scenes, anything
where three to six things share the screen as equals — have no single hero.

Do not pick one arbitrarily; its framing gates will be meaningless for the others. Instead
declare a **carrier**: a static proxy at the centre of the arrangement, sized like a typical
member of the ensemble.

```python
"subject": {
    "mode": "profile",
    "size": [0.60, 0.60, 1.60],       # one typical member
    "axis": "y",
    "start": [0.0, 0.0, 0.0],
    "speed": [(0.0, 0.0), (T, 0.0)],   # static: the ensemble moves around it
},
```

The carrier gives the camera something to hold and the gates something to measure. **Say so in
the spec comment** — a future reader must not mistake it for a real object, and it is never
built in Blender.

**Know what this costs.** With a static carrier and a locked-off rig, the camera gates all pass
trivially: `travel 0.00 m · rot 0.0 deg/s · speed 0.0 m/s`. Nothing is being proven. For that
kind of film the real risk is the choreography, and that is what `carousel_gate.py` checks —
run it as well, never instead.

---

## Blocking what the board shows

**Solid, named objects → block them.** A pan, a knife, a platter, a crisp, a hand. Primitives
are fine: `slab` for a pan or a knife, `cyl` for a bowl or a can, a flat disc for a crisp or a
slice, a box for a hand.

**Fluids and particle masses → leave the gap black.** Sizzling fat, a tomato splash, falling
crumbs, smoke, sprinkled herbs. The doctrine holds: never block a fluid.

But a beat that is *mostly* fluid still needs its solids blocked, or the blocking covers less of
the film than it appears to. In a "burst out" beat, the pan, the crisp and the bowl are blocked
and move; only the sizzle and the crumbs are absent. Say which is which in the beat text so the
prompt writer knows what has a lock and what needs a containment rule:

```
(9.5, "SCENE 4 — GAP: fat and crumbs are fluid, not blocked.
       Blocked: pan slab + crisp disc leave the can and return")
```

**Organic things → ask, then block as a box if the answer is yes.** A hand is a rectangular
proxy; the model dresses it. Blocking it gives the motion a lock, which for something as
recognisable as a hand is worth more than the crudeness costs.

---

## Colour, on an ensemble

`PALETTE` has thirteen entries. Assign by role, and remember the rule that costs a re-render:
**colour may select a variant of a shape that already reads as the object; it cannot carry the
identity of an ambiguous shape** (`HARDENING.md` §3).

Five cans of one product line are five cylinders — the shape already says "can", so five hues is
correct and the prompt maps each to its reference. A sphere that must become a specific fruit is
not, and gets blocked near its final colour instead.

Keep one hue clear of the ensemble for anything that must never be mistaken for a member — a
logo, a hand.

---

## The prompt at the end

The beat table is already scene-by-scene, so §4 of `SEEDANCE_PROMPT.md` writes almost directly
from it. Two things carry over from the board that the spec does not hold:

- **Reference images.** A storyboard panel is a composition, not a product sheet. Ask which
  asset each blocked proxy maps to, and get the tag string verbatim.
- **What the board describes but the blocking omits.** Every fluid you left black needs a
  containment rule naming source, direction and limit (`SEEDANCE_PROMPT.md` §5,
  `HARDENING.md` §9).

---

---

## The carousel window

`front_zone` is a **window**, not just an end time:

```python
"front_zone": {"solo_from": 8.2, "solo_until": 41.5},
```

Outside it the members may sit as equals and nothing is checked. That matters, because a
carousel film almost always has both:

- an **establishing** beat before it — five products arriving together, all the same size, no
  one in front. That is the storyboard's intent, not a defect.
- a **resolving** beat after it — the line-up, the packshot, the group standing clear.

Set `solo_from` to the moment the first member actually starts forward, and `solo_until` to just
before the last one finishes returning. Measured on a real spec: leaving the window open one
sample too long failed the gate on the single frame where the last can had already landed.

**Overlap the swaps.** The incoming member must start forward *before* the outgoing one has
finished returning, so the two cross. A gap between them is a moment with nobody in front — and
a moment with nobody in front is exactly the line-up the gate rejects. Same spec, measured: four
separate failures, one per swap, all fixed by starting each incoming can ~1.5 s earlier.

---

## Building it

`PV.load_bake()` keys the camera and the carrier. On an ensemble film that is not the
performance — the cast moving in depth is, and it lives in `choreography`:

```python
PV.wipe(prefixes=(..., "CAN_", "LOGO", "HAND"))
PV.reset(fps=24, seconds=60)
PV.sun()
for name, col in CANS.items():
    PV.cyl("CAN_" + name.upper(), radius=0.30, height=1.60, loc=(0, 1.3, 0.8), color=col)
PV.slab("LOGO", ...); PV.slab("HANDL", ...); PV.slab("HANDR", ...)

PV.load_bake("bake.json")
PV.load_choreography("myshot.py", prefix="CAN_", z_lift=0.80)
PV.audit()
PV.viewport_ready()
```

Build the objects **first**; `load_choreography` only animates what already exists and prints
MISSING for anything it cannot find. `z_lift` raises the whole ensemble off the floor, since the
choreography is authored around z=0 while a standing object sits on its own half-height.

Extend `wipe()`'s prefixes to cover your own names, or a re-run leaves the previous pass behind.

---

## Checklist

- [ ] Scene list and panel images extracted, scenes counted
- [ ] The four questions asked in one message — duration, take/cuts, fluids, organics
- [ ] Duration distributed by weight of action, summing exactly to the total, shown as a table
- [ ] One shot per real cut; scenes are beats, not shots
- [ ] Ensemble films: a carrier declared and commented as a carrier
- [ ] Solids blocked, fluids left black, each named as such in its beat
- [ ] Colours assigned by role, one hue reserved outside the ensemble
- [ ] `solve_shot.py` exits 0
- [ ] `carousel_gate.py` run too, if anything swaps depth order
- [ ] `front_zone` is a WINDOW: `solo_from` at the first step-forward, `solo_until` just before
      the last return lands
- [ ] Swaps OVERLAP — the incoming member starts forward before the outgoing one is home
- [ ] Every cast member has an object built for it before `PV.load_choreography()` runs — it
      prints MISSING for any that does not, and a missing object survives into the render
