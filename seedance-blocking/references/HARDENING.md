# Hardening — failures measured in production, and what stops them

`SEEDANCE_PROMPT.md` gives the prompt its skeleton. These are the ways a correct-looking
prompt still comes back wrong, each one measured on a real job. Apply the ones your shot can
hit; skip the rest.

Two of them are **blocking** rules — they change what you build, not what you write. Those are
marked ⚙️ and no amount of prose fixes them after the fact.

---

## 1 — The tie-breaker

The single most load-bearing sentence in a long prompt, and `SEEDANCE_PROMPT.md` §3 already
requires it. Stated here because everything below assumes it:

> If any text in this prompt appears to disagree with `@Video` on camera, framing, direction,
> motion, timing or object placement, `@Video` wins.

A 1000-word prompt will contradict the blocking somewhere. Without explicit precedence the model
resolves the conflict on its own, usually by believing the text and drifting off the lock.

## 2 — Count from the frames, every time

Countable constraints (`SEEDANCE_PROMPT.md` §5) only work if the number is right. **A count with
the wrong number is worse than no count** — it actively instructs the model to drop or invent an
element.

You have the spec, so most counts are already exact. The ones that are not — how many pieces an
object breaks into, how many cuts cross a surface, how many proxies are on screen at t — must be
read off an **enlarged frame** at the moment the objects are most separated, never off the
moment they overlap and never carried over from a previous prompt.

Measured failure: "six cuts, seven pieces" copied from an earlier job onto a blocking that had
seven cuts and eight pieces. The prompt then told the model to omit a slice, and it did.

## 3 — ⚙️ Colour cannot carry the identity of an ambiguous shape

`PALETTE` colours are identity — but only within a limit that costs a re-render when crossed.

Measured, same frame, same prompt: magenta **discs** became yellow lemon slices, while magenta
**spheres** stayed pink. The disc's silhouette reads as *slice of fruit*, so the model applied
the translation. The sphere's reads as nothing — a sphere can be a berry, a ball, an ornament —
so the model kept the only signal it had, the colour. Text lost, despite the map being stated
three times: **the prompt enters once, the colour is present in every frame at exact pixel
coordinates.**

> **Colour may select a *variant* of an object whose shape already says what it is. It may not
> carry the *identity* of an object whose shape says nothing.**

Six cylinders in six hues reading as six flavours of can: fine — the cylinder already says
"can". A sphere that must become a lemon: not fine.

When a proxy's shape is ambiguous, **block it near its final colour** and separate objects by
value and saturation instead of hue — bright saturated hero, duller mid-tone for the crowd,
near-cream for slices. You lose nothing: they stay tellable apart in the viewport, and nothing
needs translating.

## 4 — ⚙️ Aspect is a build setting, not a prompt setting

Render the blocking at the aspect you will deliver in. `motion_render()` does 1920×1080; a
viewport capture at some arbitrary size does not.

Measured: a 1132×822 blocking (1.377:1) with a prompt asking for 16:9 (1.778:1). The model
reconciled the 29% difference by cropping height — exactly the axis the subject moved along —
and the returned framing matched nothing. No wording fixes this; it is geometry.

If a mismatch is unavoidable, state the axis so the crop lands somewhere harmless:

> If the output aspect differs from `@Video`, fit the source without cropping — never cut the
> top or bottom, since the subject's motion runs vertically.

## 5 — Never name a cause that is not in frame

The counterpart to §5's "name what each proxy must never become", and the easier mistake to make
yourself.

The blocking shows a **result**: cuts appear on a surface, an object splits, a lid pops. Writing
the cause is natural — "six blades pass through", "a hand twists the cap" — but nothing in the
blocking shows that cause, and **the model reads a named object as an object to render.** Six
blades arrive in frame.

Wrong:

> SIX blades pass through the fruit at once.

Right — the result, plus the cause explicitly refused:

> The fruit slices ITSELF: six clean wet cuts open across the peel simultaneously, as if by
> invisible blades. **No knife, blade, hand or tool is ever visible in any frame.**

Check every verb: if its subject is not in the blocking, rewrite so the visible object is the
subject, or state the subject is never seen. Carry the refusal into §8 — this is the class of
thing the model reintroduces late. It applies to audio too: "six wet knife passes" in the sound
design puts the knife back.

## 6 — A void is not a studio, and light cannot touch it

When the checkerboard is replaced by nothing — a subject in pure black — two words destroy it:
`studio` and `seamless`. Both name a physical surface, a surface can be lit, so the model lights
it and the background drifts from black to grey, worst on a push-in as the fill spills onto the
wall the words invented.

Wrong — every clause implies geometry:

> shot on a black seamless, dramatic studio lighting, a hard rim from behind, deep clean blacks
> with no lift

`deep clean blacks` is worse than useless: it describes a **grade**, which reads as "dark", not
as "nothing is there".

Right, three moves:

1. **Deny the surface, exhaustively.** `There is NO background surface: no backdrop, no
   seamless, no studio wall, no cyclorama, no floor, no fog, no set.`
2. **Confine the light.** `The light falls ONLY on the subject. ZERO ambient, bounce,
   atmospheric scatter or spill behind or beside it — nothing back there exists to catch light,
   so no glow, halo or falloff gradient ever appears in the void.`
3. **Lock the black as a number, across time.** `pure #000000, uniform` beats any adjective — a
   hex value has no range, "deep black" does. The failure is progressive, so state the
   invariant: `Frame 0.0s and frame 13.6s have the same background value.`

End on `an empty void, not a fade to black` — "goes to black" reads as a transition.

## 7 — Glow words paint the background

If a void still drifts grey after §6, the leak is in the words describing the **subject's**
light:

| Word | What it does |
|---|---|
| `bloom` | a post effect that **spreads into neighbouring pixels** — on black it paints the void |
| `flare`, `flaring` | a ray that travels across frame, leaving the object behind |
| `halation`, `glow` | the same, softer |
| `crisp speculars` | tiny hard highlights that, with bloom, become diamonds |
| `rim light`, `backlight`, `kicker` | light from behind always haloes the subject on black |
| `sparkle`, `glints`, `diffusion filter` | jewellery-advert look; each one radiates |

Writing "the light falls only on the subject" in one paragraph and `bloom on speculars` in
another is a contradiction, and the concrete instruction wins. **Do not describe an optic you do
not want**, not even to qualify it.

Ban them by name, kill the backlight, and give a measurable test:

> BANNED OPTICS — none of these may appear anywhere: bloom, glow, halation, lens flare,
> starburst, light rays, diffusion filter, soft-focus haze, sparkle, glints, jewellery sheen.
> Nothing radiates outward from a highlight. The pixel immediately outside the subject's
> silhouette has exactly the same value as the pixel in the far corner: pure #000000.
> Highlights stay SMALL, TIGHT and CONTAINED WITHIN the silhouette.

A model can check that; it cannot check "no glow". If the glow survives all of it, the model is
applying bloom unconditionally — fix it in post with a black-point adjustment, not more prompt.

## 8 — Do not put platform settings in the prompt

Resolution, aspect and output size are chosen in the platform's UI. Writing `8K`, `4K` or `16:9`
in the text does nothing at best, and real damage at worst: an aspect in the text that disagrees
with the blocking's actual aspect gives the model two conflicting instructions (see §4).

Belongs in the technical block: render style, lens behaviour, lighting, audio policy, the locks.
Does **not** belong: `8K`, `4K`, `1080p`, `16:9`, `9:16`, bitrate, codec, frame rate, seed,
sampler, guidance scale. If a control exists in the interface, the prompt is the wrong place.

Duration is the exception, and only when the prompt carries timestamps — `13.7s` gives
`6.5-6.7` a denominator.

## 9 — Intensity words are not a quantity; calibrate by reach

"A splash" has no upper bound, so the model picks one, and it picks big. Stacked intensifiers
compound: `BURST`, `EXPLODES`, `wide spray`, `mist`, `ribbons` and `high-detail fluid
simulation` are six requests for the same event.

Two tools, and they are not interchangeable:

**A count removes the effect.** `roughly TEN TO FIFTEEN countable beads` makes the shot dry.
Right when the user wants it gone.

**A reach sizes it and keeps it.** Measure against something in frame:

> a splash reaches at most about ONE SUBJECT-WIDTH from the object it came off, then breaks into
> separate droplets that slow and drift. Always readable as individual beads and short ribbons,
> never as a solid mass.

"Small" has no scale a model can apply; "one lemon-width", "half the can's height", "no further
than the character's shoulder" all do, because the reference object is on screen. The readability
test — *individual beads, never a solid mass* — separates *some water* from *a wall of water*
better than any adjective.

The reach figure is then the single dial: too dry → two subject-widths; too wet → half. And
delete the words that invite the simulation: `fluid simulation`, `high-detail liquid`.

Same pattern for smoke, sparks, debris, dust, petals, confetti.

---

## Pre-flight, before the prompt leaves your hands

- [ ] Tag string confirmed **verbatim by the user**, echoed in text, identical in §1/§3/§5/§8
- [ ] Every multi-view reference sheet disowns its layout **and states the real count**
- [ ] Every unblocked element has source + direction + limit
- [ ] Tie-breaker present
- [ ] Every count read off a frame **in this session**
- [ ] Every ambiguous proxy shape blocked near its final colour ⚙️
- [ ] Blocking rendered at the delivery aspect ⚙️
- [ ] Every verb's subject exists in the blocking — including in the audio section
- [ ] If the background is a void: every surface word is a denial, light confined, `#000000`
- [ ] Every glow word is a denial, not a request
- [ ] No resolution, aspect or platform setting in the text
- [ ] Every generous effect carries a count **or** a reach in subject-widths
- [ ] Word count measured with `wc -w`, not estimated