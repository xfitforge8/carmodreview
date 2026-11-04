# Photos

Drop real photographs here and they appear on the site at the next build. Nothing
in this folder is required — the site builds and looks complete without it.

The build only publishes image files. This README and any `.txt` caption files
stay out of the published site.

## How to add a photo to an article

1. Make a folder named after the article slug. The slug is the `slug:` line at
   the top of the article file, e.g. `silverado-rst-leveling-kit`.

   ```
   content/photos/silverado-rst-leveling-kit/
   ```

2. Put the image in it. All of these extensions work:

   `.jpg` `.jpeg` `.png` `.webp` `.avif`

3. Optionally, add a caption. Create a text file with the same name as the image
   but a `.txt` extension:

   ```
   content/photos/silverado-rst-leveling-kit/front-spring.jpg
   content/photos/silverado-rst-leveling-kit/front-spring.txt
   ```

   The `.txt` holds one line of plain text, which becomes the caption. **With no
   `.txt` the figure still appears but carries no caption.** No caption is ever
   generated for you — an invented one would be a claim the photo does not
   support.

4. Run `python3 build.py`.

Photos appear in filename order, all on the English article page. They land
after the diagrams, distributed between the article's section headings.

## How to add a photo to the homepage

Make a folder named `home` instead:

```
content/photos/home/
```

Same rules apply.

## What to photograph

Anything you actually own and can point a camera at. Useful frames for an
install or fitment guide:

- the part on the vehicle, in daylight
- the mounting point before the part goes on
- a measurement against a tape or a rule
- the part next to the stock component for scale
- a warning sign worth showing — a scored rotor, a worn pad, a cracked boot

## What not to do

Do not put stock photography or images from a manufacturer's website here. They
are not licensed for this use, and a photo that implies first-hand testing when
there was none is exactly the kind of claim this site exists to avoid.

If a photo is not yours, leave it out and cite the source in the article text
instead.
