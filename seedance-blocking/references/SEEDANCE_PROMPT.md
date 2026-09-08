# Seedance 2.5 prompt from a blocking pass

The blocking clip is the **structural lock**: cuts, camera, timing. The prompt is
the **style layer**: what the world looks like. Swap the style layer and you get
the same edit as photoreal, painted 2.5D, ink or toybox — frame for frame. That is
why this is worth doing: the edit is pre-approved because the foundation never moves.

Attach the greybox MP4 as `@Video`, plus reference images. Duration = blocking
length. Their working prompts run 2–4k words for 30 s and always use this skeleton.

## 1 — Reference definitions

Per reference, state what it defines **and what is not inherited**:

> `@Image 1` — appearance of the walking figure ONLY. Not its motion, not its
> framing, not the environment.
> `@Video` — camera, cuts and timing ONLY. Not colour, not styling, not content.
> `@Image 4` — active for 00:10–00:13.3 only.

**Copy the @ tag string EXACTLY, character for character.** It is a literal token,
not a description. `@prop_super_car` and `@prop_super-car` are different things and
the wrong one silently unbinds the reference — you get a plausible video with none
of your art direction in it, and no error. Ask the user for the tag before writing
the prompt, and re-check every place it appears (§1, §3, §5, §8) after any edit.

**A screenshot is not good enough — echo the string back in text and have them
confirm it.** Tags mixing underscores and hyphens (`prop_super-car`) are misread
off an image at small sizes, and that is a silent failure by definition: nothing
downstream can tell you the reference never bound.

**If an appearance reference is a multi-view sheet, say so and disown the layout.**
A product/character sheet is a GRID, and the model will happily reproduce the grid
— four cars in a row, three heads on grey. Name the trap explicitly:

> `@prop_super-car` — appearance ONLY. Do NOT inherit its grey studio background,
> its lighting, its scale, its framing or its multi-view layout. **It is one car,
> not four.**

**Decode the oriented proxy right next to `@Video`,** not buried in the rules —
it is the sentence that turns a red box into the subject:

> The red box IS the car. RED face = front, BLACK = rear, GREEN = flanks and roof.
> The black cylinders are the four wheels.

## 2 — Technical block

Aspect, duration, film-stock and lens language (e.g. Kodak 500T, anamorphic, 180°
shutter), practical SFX only, NO CGI look, non-IP, no readable text on screen.

## 3 — Video lock

Non-negotiable, near-verbatim:

> `@Video` is the SOLE authority for camera movement, cuts and timing, 1:1
> frame-aligned. If this text and the video disagree, the video wins. Any deviation
> is a failure. The previz is re-dressed, never re-imagined.

## 4 — Prompt / action timing

Every beat at its exact timestamp, each line only *dressing* what the previz
already does. Take the timestamps straight from the spec's `beats` table.

**Mine the SPEC for hard numbers — the beats table is prose, the spec is truth.**
The solver already knows the exact camera offsets, distances, lens and slip angle
at every beat. Quote them. "The drone is level with the right front wheel, about
2.5 m off the car's flank" re-dresses far more faithfully than "the drone is close
to the car", because it removes the model's freedom to reinvent the geometry:

| pull from | into the beat as |
|---|---|
| camera waypoint offsets | "roughly 14 m behind and 7 m up" |
| `surface_dist` at that frame | "about 2.5 m off its flank" |
| `yaw_events` angle | "roughly 35° of slip" |
| solved lens | "ultra-wide" / "compressed long lens" |

It costs one line per beat and it is the cheapest fidelity in the whole prompt.

End each beat with **state accounting** — running counts kill drift and duplicates:

> END 12s: figures 1 · standing · corridor lights 6 visible · door open

## 5 — Rules

Numbered hard counts and locks:

> 1. There is exactly ONE figure. No extras, no duplicates, no half-bodies at the
>    frame edges.
> 2. The corridor is straight and unbroken; no side doors appear that are not in
>    `@Video`.
> 3. Off-screen voices stay off-screen — never route the camera to a speaker.

Colour mapping from the blocking goes here: `red block = @Image 9`, `cyan block =
@Image 8`. For an oriented proxy: red face = facing direction, black = back,
green = sides and top.

**Every element you did NOT block needs its own containment rule.** This is the
one that bites. Anything absent from the greybox has no structural lock on it, so
it is the single most likely thing to drift — and the doctrine of never blocking a
fluid *guarantees* you have at least one. Pin its source, its direction and its
limit:

> 5. Tyre smoke comes ONLY from the rear wheels and always trails BEHIND the car.
>    Never in front of it, never from the front wheels, never filling the frame.

"never block a fluid" is only half a rule. The other half is writing this line.

**Name what each set proxy is, and what it must never become.** A greybox is
ambiguous by design and the model resolves ambiguity toward people. Upright
proxies are the worst offenders:

> 4. The upright posts flanking the road are low bollards. They mark the road
>    edge. They are not people and never become people.

Also lock the counts that the blocking implies but never states: exactly one
vehicle, no other traffic, no pedestrians, no side streets that are not in
`@Video`.

## 6 — Acting tasks

Per character: a shared unspoken SCENE DIRECTION, then MOTIVE / GOAL / OBSTACLE /
TACTIC, then moment-to-moment beats. Always include the safety line — "gaze
engaged, natural blink cadence, never glassy". Add **ongoing business** (small
continuous actions so nobody freezes) and **background life** (soft focus, never
crossing a speaking face).

**This section works for objects too — do not skip it for a vehicle.** A car has a
driver, therefore an intention, and stating it is what separates "controlled drift
by someone who has done it a thousand times" from a crash. Keep the same headings
and put the physics in MOMENT TO MOMENT: weight transfer, body roll, tyre
deformation under load, the suspension settling on exit. Drop the gaze/blink safety
line when there is no face; keep ongoing business and background life.

## 7 — Audio

`[Sound design]` bed · `[SFX]` timed to the second · `[Dialogue]` verbatim with
timing plus forbidden alternate phrasings · `[Music]` usually none.

## 8 — Hold for the full timeline

Close by restating every lock.

---

## Asset list

Ship this next to the prompt. One line per coloured proxy:

| proxy | becomes | reference needed |
|---|---|---|
| red block 0.5×0.35×1.8 | the walking figure | character sheet, full body, neutral |
| corridor greybox | practical location or set | style frame, lit |
| lit doorway | the destination | style frame |
| black gap 14–16 s | smoke fills the corridor | none — model fills it |

## Delivery notes

- **Deliver the prompt IN CHAT, in one fenced block — never as a file.** It gets
  pasted into Higgsfield, so it wants a copy button, not a path. The asset list
  goes in chat too, as a small table under it. Everything that is not meant to be
  pasted (tag warnings, open questions) stays outside the block.
- Cowork mode; Fable 5 on high works well for the prompt pass.
- Dialogue scenes: block seat positions and eyelines and the 180° rule holds with
  zero seat swaps.
- Never block liquid or fluid — leave the gap black and let the model fill it.
