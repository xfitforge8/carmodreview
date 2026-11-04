# Photos

Real photographs, placed into articles at build time. The build publishes only the
image files — this README and the `.txt` caption sidecars stay out of the site.

## What is in here now

Licensed stock photography, chosen because a real photograph of the actual component
beats a drawing. Every image must be licensed for commercial use.

Every image here must satisfy all four of these:

1. **It actually shows what the caption says it shows.** This is the one that goes
   wrong. Verify against the source page's own description, not against your memory
   of the thumbnail.
2. **The licence permits commercial use.** Many "free photo" sites do not, and
   manufacturer press images almost never do.
3. **It is never presented as evidence of our own testing.** A photo illustrates a
   component. It is not proof that we installed, measured or drove anything.

**What is still forbidden:** an image presented as first-hand work when it is not,
a stock photo of an unrelated car standing in for a specific vehicle, or a caption
describing something the frame does not contain.

## Adding a photo to an article

1. Make a folder named after the article slug — the `slug:` line at the top of the
   article file:

   ```
   content/photos/silverado-rst-leveling-kit/
   ```

2. Put the image in it. `.jpg` `.jpeg` `.png` `.webp` `.avif` all work. Name it
   `NN-<sourceid>.jpg` so the file stays traceable to where it came from. Files are
   used in filename order.

3. Add the caption as a `.txt` with the same basename:

   ```
   content/photos/silverado-rst-leveling-kit/01-33324954.jpg
   content/photos/silverado-rst-leveling-kit/01-33324954.txt
   ```

   One line of plain text. **No `.txt` means no caption** — the figure still
   appears, uncaptioned. A caption is never generated, because an invented one is
   a claim the photo does not support.

4. Run `python3 build.py`.

The first photo is the hero, above the opening prose. The rest go one per section
heading, at the end of each section. Photos appear on the English page only —
captions are written in English and are not machine-translated onto the KR/ES pages.

## Homepage and category hubs

- `content/photos/home/` — homepage figures.
- A category hub borrows the lead photo of its most representative article; the
  mapping is `CATEGORY_SOURCE` in `photos.py`.

## Checking a caption before you commit

Read the description on the page the image came from. If your caption describes
something else, the caption is wrong. Do not rely on a description of an image you
have not verified — thumbnails and memory are both unreliable, and a wrong caption
is worse than no photo.

Captions do not name the source or the photographer; they describe what is in frame.

## Image dimensions

`photos.py` reads each file's real pixel size at build time and emits matching
`width`/`height` attributes, so the page reserves the right space before the image
loads. Do not hand-write those attributes; the CSS caps tall portrait images at
620px and keeps their aspect ratio.
