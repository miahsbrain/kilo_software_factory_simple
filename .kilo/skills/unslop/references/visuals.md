# Visuals

How to replace decorative filler with a visual that belongs to this product, and how to build one in code.

## Decide what the visual is

1. **Does the screen need one?** Dashboards, settings and most app screens do not. Landing heroes and empty states usually do.
2. **Build the scene in code.** For a landing hero, build a scene from the world as the background of the whole hero, with the subject on one side and calm space for the headline on the other. Then show the product rising from the bottom edge. This is the strongest hero. The visual is built from the project's own components, CSS and canvas work — never generated here.
3. **Show the product.** Below the scene, or as the visual when there is no scene, build a preview in code of what the page already promises. Pick the one moment that proves the headline, not the whole app. A scheduling tool shows one week with a booked slot, a code review tool shows one diff with a comment, a habit app shows a streak on one card. Use the project's own components when they exist, otherwise careful HTML in the new palette, with plausible data and real looking names. Frame it like a window or a device only if that helps it read.
4. **Write the scene as one sentence.** Use the world and character from the direction and write the subject as one plain sentence before building anything. If you cannot say it in one sentence, it is not clear yet.

These examples only show the shape of a good sentence. Do not reuse them, derive yours from the product in front of you.

- A tool that protects backups → a small lighthouse on a dark rocky coast with its beam reaching into fog
- A meditation app → a single cup of tea steaming on a windowsill at first light
- A logistics API → one container ship seen from straight above on a calm grey sea
- A language learning app → a stack of handwritten flashcards on a café table in afternoon sun

Avoid the AI defaults, unless the product is literally about them. No glossy blobs, orbs, nebulas, chrome liquid, floating cubes, neon circuits, holograms, glowing brains, robots, rockets or crystal shapes.

## Styles that work

Pick one that fits the character, and keep it for the whole page.

- **Painted background art.** A calm sky or landscape with one subject, painted like the backgrounds of modern Japanese animated films, crisp clouds and soft light, with open sky left for the text. Good for warm, hopeful, human products.
- **Cinematic photo of one object.** A single real thing in simple dramatic light on a plain field, like a lighthouse in fog or a paper object in mid air. Good for calm, serious, trustworthy products.
- **Soft stylized 3D.** One small scene or object with matte materials and gentle light, like a doorway standing in a meadow. Good for playful or friendly products.
- **Product object render.** A real looking object from the product, like a payment card, a phone or a package, studio lit with true materials, used as a moment inside the interface. Good for anything that touches the physical world.
- **Light and optics.** One physical phenomenon on a dark field, like light splitting through a prism. Good for technical or data products.
- **Engraving or print.** A monochrome engraving or woodcut in one ink on a soft tinted page, with type and palette that belong to the same world. Good for products with heritage, craft or an editorial voice.
- **A code treatment over an image.** Rendering an image as glyphs, dots or a duotone in the page palette, so it feels made for the page. See [effects.md](effects.md).

What tends to fail:

- Film grain, paper grain or a mottled texture as a baked-in pattern. It reads as noise. Add texture in code if you need it.
- A print style, like engraving, woodcut or risograph, on one image while the rest of the page is a plain modern interface. It reads as a filter. The same styles work well when the whole brand lives in them, with matching type and a paper palette, like a monochrome engraving on a soft tinted page.
- Several subjects or a busy collage. The idea stops reading in a second.
- Purple and blue glossy abstractions of any kind.

## Objects for moments

Besides whole scenes, build single objects to place into the interface, like a payment card, a phone, a parcel, a coffee cup or a notebook from the product's world. They make a coded preview feel real.

- Build one object, studio lit, on a plain background in the exact page color, with soft contact shadow and nothing else in frame.
- Give it the angle you need in the layout, like "tilted 20 degrees, seen slightly from above".
- Keep the background transparent, or blend it with a mask into the page color.
- Place it overlapping the edge of a card or window, a little rotated, with a soft shadow in the ramp's darkest color, so it sits in the same space as the UI.
- To show real UI on a device, draw it straight on with no perspective, measure the screen rectangle, lay HTML over it and rotate both together. The text stays sharp and real.
- Everything inside one visual tells the same story. If the list shows invoice INV-0142 for a client, the phone shows the same client, number and amount.

## Build it

**The visual is built in code, never generated here.** There is no image service, no image MCP server and no prompt to run. An image can be reviewed — the model can be shown one and judge it — but it is never produced in this repo.

- Build the scene from the project's own components, CSS gradients and masks, and canvas work. Real materials, real light, real shadow.
- When the moment cannot be built in code, leave an empty slot of the exact size, with the radius of the layout and no text inside, so nothing unfinished can ship by accident, and describe in the report what the slot should hold.
- A physical object is built in code when the product touches the physical world: a payment card, a chip, a number, a soft gradient.

## The scene in code

Build the scene from these parts, in this order:

- **Subject.** The one sentence, concrete and physical.
- **Setting.** Where it is, kept simple.
- **Light and palette.** Matched to the page. Name the page background color so the edges blend into it, and the direction of the light.
- **Treatment.** One clear direction that fits the character, like a painted background, a cinematic render, an editorial illustration or a print treatment. Pick what fits the product, not what is trending.
- **Composition.** Where the subject sits so the text has room, like "subject on the right half, calm empty space on the left". For a scene behind the whole hero, keep the lower fifth calm too, since the product view rises over it, and fade the edges into the page color in code.
- **Format.** The aspect ratio of the slot at twice the display size.

## Put it on the page

- Export as WebP or AVIF at twice the display size, with a real `alt` that says what is shown.
- Match the image edges to the page background. If they do not match, fade them with a mask, like `mask-image: radial-gradient(closest-side, #000 70%, transparent)`, or a gradient overlay in the page color. A hard rectangle on a page of a different color is a sign of slop.
- Keep it static or give it one slow, subtle motion that fits the subject. No parallax.
- A treatment in code, like a duotone into the page palette, can make an image feel native. Use one only when it fits the character, and never as new decoration.
- Load the hero image with high priority and give it fixed dimensions so the layout does not jump.

---

Part of unslop by Damir Sokolovsky ([@heydamir](https://x.com/heydamir)), CC BY 4.0. Keep this credit in copies and adaptations.
