# Seedance Blocking

A Claude skill that takes a rough idea to a **blocked 3D previz shot**, an **asset
list**, and a **Seedance 2.5 prompt** — in one pass, in your own Blender.

The method is the one Higgsfield and [@adilinthewild](https://x.com/adilinthewild)
teach: **Blender locks the motion, Seedance builds the world around it.** You block
the shot as coloured boxes, render the greybox as a motion log, and hand that clip
to Seedance as the sole authority for camera, cuts and timing. The prompt only
re-dresses what the blocking already does.

Without blocking, a 30 s shot burns thousands of credits and never matches the
camera you wanted. With it, first try.

## What you need

1. **Blender 5.2 LTS** or newer.
2. **The Higgsfield Blender add-on**, installed and signed in.
3. **The Higgsfield Bridge connector** in Claude, connected to that Blender.
4. **Claude Code** (or any Claude client with the bridge connector).
5. `python3` and `ffmpeg` on your PATH.

## Install

Unzip into your skills folder:

```bash
unzip seedance-blocking.zip -d ~/.claude/skills/
```

You should end up with `~/.claude/skills/seedance-blocking/SKILL.md`. Restart
Claude Code. That's it.

## Use it

Open Blender, connect the bridge, then run `/seedance-blocking`. Two ways in:

**If you know the shot, just say it:**

> block a 30 second shot: a figure walks down a corridor, stops halfway to look at
> something on the wall, then keeps going toward a lit doorway. camera alive, no cuts

**Name the rig and the gates change with it.** "robo arm", "FPV drone", "steadicam",
"tripod", "car mount", "probe macro" — eleven presets, because a 76 °/s whip is a bug on a gimbal and
the whole point on a Bolt. `solve_shot.py --rigs` lists them.

**If you don't, it asks — once, in chat:**

> /seedance-blocking make me something cool

One plain question, no option cards. Answer in a line and it builds; ignore the
question and it takes the defaults (checkerboard void, 15 s, deliberate camera)
and builds anyway.

Either way Claude writes a shot spec, solves and audits the camera **before**
touching Blender, builds the scene, audits it, and hands you the viewport to play.
Give notes in chat, and once you say go it renders the greybox clip and writes the
Seedance prompt against it.

## What you get

- `bake.json` + a shot spec you can edit and re-solve in ~0.05 s
- a blocked `.blend` you play in the viewport, backed up whenever a pass is worth keeping
- the greybox **motion clip** — this is what you attach to Seedance as `@Video`
- an **asset list**: every coloured proxy and what reference image it needs
- a **Seedance 2.5 prompt** built on the 8-section structure, timed to your beats

## Why it's fast

Every expensive previz mistake — whip pans, the hero cropped out of frame, the
camera inside a wall, a set too short for the lens — is visible in arithmetic.
`scripts/solve_shot.py` finds them in 0.05 s with six hard gates. Blender only
finds them after a build, a bake and a render.

So the loop is: **solve until it passes, then build once.** A 30 s shot goes into
Blender in about three calls.

## Defaults

The hero is **one red box**. Not a character, not a rig. A block holds framing
exactly as well and costs nothing to build or change. Colour is identity — extra
subjects get contrasting colours and the prompt maps them to reference images.

**If the brief names no place, the set is `PV.checker()` — a checkerboard void,
one line.** The squares streaming past are real parallax in every axis, so the move
reads completely, and Seedance stays free to build the world the prompt describes.
Only a brief that actually names somewhere gets a composed environment, and then
it is the simplest thing that gives the camera something to move against, because
parallax is the entire job of a blocking set.

## Layout

```
SKILL.md                     the procedure Claude follows
README.md                    this file
LICENSE                      MIT
scripts/solve_shot.py        offline solver + 6-gate camera audit + RIGS (plain python3)
scripts/carousel_gate.py     offline 5-gate CHOREOGRAPHY audit (depth order, overlap, pops)
scripts/previz_core.py       Blender-side blocking API
references/CAMERA_RULES.md   rotation limits, lens-from-framing, failure fixes
references/SHOT_GRAMMAR.md   framings, moves, ramps, markers, set design
references/SEEDANCE_PROMPT.md the 8-section prompt anatomy + asset list
references/HARDENING.md      measured failure modes + pre-flight list
references/STORYBOARD.md     storyboard intake: scenes, timing, the carrier pattern
(no examples — the spec schema lives in SKILL.md, single source)
```

## Storyboards and ensembles

`references/STORYBOARD.md` handles the other common intake: a board rather than a sentence. It
covers extracting the scene list, the four questions a board never answers (duration, take or
cuts, which fluids stay unblocked, whether organics get boxed), distributing time by weight of
action, and treating scenes as **beats** rather than shots.

It also carries the **carrier** pattern. The solver tracks one subject; a product carousel or
any ensemble has none, so you declare a static proxy at the centre for the camera to hold. That
costs something worth knowing: with a carrier and a locked-off rig every camera gate passes
trivially — `travel 0.00 m · rot 0.0 deg/s` — and proves nothing.

Which is what `scripts/carousel_gate.py` is for. Five gates over a `cast` and a `choreography`
block: exactly one member clearly in front, its silhouette actually cutting across the others,
depth agreeing with size, no scale pops, no census overflow. It exists because a three-product
depth carousel came back as a static line-up — one left, one centre, one right, nothing
overlapping, only the sizes changing — and the camera gates had nothing to say about it.

## Hardening

`references/HARDENING.md` collects the ways a structurally correct prompt still comes back
wrong. Each entry is a failure measured on a real job, not a precaution:

- a black void drifting to grey because the word `seamless` invented a wall to light
- glow painting the background because `bloom` was *described* rather than banned
- a splash filling the frame because "small" gives a model no scale — a **reach** does
- a count copied from a previous shot, telling the model to omit an element
- a cause named that was never in frame — "six blades" arriving as six visible blades
- `16:9` in the text contradicting the file's real aspect, so the model cropped the axis the
  subject moved along

Two of them are **blocking** rules, not prompt rules — they change what you build:

- **Colour cannot carry the identity of an ambiguous shape.** Magenta discs rendered as lemon
  slices while magenta spheres in the same frame stayed pink. Block ambiguous proxies near
  their final colour and separate by value, not hue.
- **Render at the delivery aspect.** No wording compensates for a mismatch.

The file ends in a pre-flight checklist. Run it before the prompt leaves your hands.

## Licence

MIT. © 2026 Thomas Lundström / Grove Media.
