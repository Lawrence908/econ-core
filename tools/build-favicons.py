#!/usr/bin/env python3
"""Build the family's favicons: one frame, eleven glyphs.

Every site in the collection gets the same near-black square in the family's
own green and paper, and its own glyph, so that eleven open tabs read as one
suite and still tell each other apart at sixteen pixels. The glyph geometry
lives here and nowhere else; the apps carry only the built files.

Writes into each sibling app directory:

    src/favicon.svg          the source, 64x64, hand-tuned at 16px
    src/favicon.ico          16/32/48, for what still asks by name
    src/apple-touch-icon.png 180px, iOS will not read the SVG

Usage:

    python3 tools/build-favicons.py            # every site
    python3 tools/build-favicons.py jobs debt  # named sites only

The SVGs are written with the standard library alone. The .ico and .png need
cairosvg and Pillow; without them this skips the raster step and says so,
rather than failing, because the built files are committed in the apps and a
regeneration is rare. Colours are the sites' own CSS custom properties, so the
tab matches the page: --series-3 for the green, --row-bg for the paper.
"""

import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIBLINGS = os.path.dirname(HERE)

INK = "#12120f"      # the square: a shade under the sites' dark --plane
GREEN = "#1baf7a"    # --series-3, the family's accent
PAPER = "#f1efe5"    # --row-bg, the family's paper white

# Every glyph is drawn on a 64x64 grid at stroke weight 7 with round caps and
# joins. Nothing finer survives a 16px tab strip; each of these was checked
# there and two were redrawn after it (yield's zero line was fading out,
# freight's wheels were merging into the body).
GLYPHS = {
    # The hub: the board itself, one green row signalling above two quiet ones.
    "econ": f"""
  <path d="M14 21h36" stroke="{GREEN}"/>
  <path d="M14 34h26" stroke="{PAPER}"/>
  <path d="M14 47h17" stroke="{PAPER}"/>""",

    # The curve dipping under its own zero line.
    "yield": f"""
  <path d="M11 27h42" stroke="{PAPER}" stroke-opacity=".8"/>
  <path d="M13 19c9 0 7 28 19 28s10-21 19-25" stroke="{GREEN}"/>""",

    # The spread: one point, two lines, the gap opening to the right.
    "credit": f"""
  <path d="M13 32 53 17" stroke="{PAPER}"/>
  <path d="M13 32 53 51" stroke="{GREEN}"/>""",

    # Standards tightening, one step down at a time.
    "lending": f"""
  <path d="M12 18h14v15h14v15h14" stroke="{GREEN}"/>""",

    # Starts and permits: a roof over a base.
    "housing": f"""
  <path d="M12 33 32 17l20 16" stroke="{PAPER}"/>
  <path d="M20 33v17h24V33" stroke="{GREEN}"/>""",

    # Payrolls, and the one that rolled over.
    "jobs": f"""
  <path d="M15 50V26" stroke="{PAPER}"/>
  <path d="M27 50V18" stroke="{PAPER}"/>
  <path d="M39 50V30" stroke="{PAPER}"/>
  <path d="M51 50V40" stroke="{GREEN}"/>""",

    # Production, and the direction the two-quarter rule argues about.
    "output": f"""
  <path d="M32 51V17" stroke="{GREEN}"/>
  <path d="M19 30 32 17l13 13" stroke="{GREEN}"/>""",

    # What they say against what they do.
    "consumer": f"""
  <path d="M13 20 51 45" stroke="{PAPER}"/>
  <path d="M13 45 51 20" stroke="{GREEN}"/>""",

    # A boxcar on its wheels.
    "freight": f"""
  <rect x="12.5" y="17.5" width="39" height="19" rx="4" stroke="{PAPER}"/>
  <circle cx="23" cy="47" r="5" fill="{GREEN}" stroke="none"/>
  <circle cx="41" cy="47" r="5" fill="{GREEN}" stroke="none"/>""",

    # The barrel's product, one drop of it.
    "diesel": f"""
  <path d="M32 13c13 17 15 23 15 27a15 15 0 0 1-30 0c0-4 2-10 15-27z"
        fill="{GREEN}" stroke="none"/>""",

    # The hockey stick.
    "debt": f"""
  <path d="M11 49h19c13 0 12-8 16-34" stroke="{GREEN}"/>""",
}

SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
  <title>{name}</title>
  <rect width="64" height="64" rx="13" fill="{ink}"/>
  <g fill="none" stroke-width="7" stroke-linecap="round" stroke-linejoin="round">{glyph}
  </g>
</svg>
"""


def rasterizer():
    """cairosvg and Pillow, or None if this machine has not got them."""
    try:
        import cairosvg
        from PIL import Image
    except ImportError:
        return None
    return cairosvg, Image


def build(name, glyph, raster):
    src = os.path.join(SIBLINGS, name, "src")
    if not os.path.isdir(src):
        print(f"  {name}: no sibling checkout, skipped")
        return False

    svg = SVG.format(name=name, ink=INK, glyph=glyph)
    with open(os.path.join(src, "favicon.svg"), "w") as fh:
        fh.write(svg)

    if raster is None:
        print(f"  {name}: favicon.svg")
        return True

    cairosvg, Image = raster
    import io

    raw = svg.encode()
    cairosvg.svg2png(bytestring=raw,
                     write_to=os.path.join(src, "apple-touch-icon.png"),
                     output_width=180, output_height=180)

    frames = []
    for size in (16, 32, 48):
        png = cairosvg.svg2png(bytestring=raw, output_width=size, output_height=size)
        frames.append(Image.open(io.BytesIO(png)).convert("RGBA"))
    frames[0].save(os.path.join(src, "favicon.ico"), format="ICO",
                   sizes=[(f.width, f.height) for f in frames],
                   append_images=frames[1:])

    print(f"  {name}: favicon.svg, favicon.ico, apple-touch-icon.png")
    return True


def main(argv):
    wanted = argv or list(GLYPHS)
    unknown = [n for n in wanted if n not in GLYPHS]
    if unknown:
        raise SystemExit(f"no glyph for: {', '.join(unknown)}. "
                         f"Known: {', '.join(GLYPHS)}")

    raster = rasterizer()
    if raster is None:
        print("cairosvg or Pillow missing: writing SVGs only, leaving any "
              "existing .ico and .png in place.\n"
              "  pip install cairosvg pillow\n")

    written = sum(build(n, GLYPHS[n], raster) for n in wanted)
    print(f"\n{written} of {len(wanted)} sites written.")

    print("\nThe apps need these three lines in <head>, once:\n"
          '  <link rel="icon" href="/favicon.ico" sizes="32x32">\n'
          '  <link rel="icon" href="/favicon.svg" type="image/svg+xml">\n'
          '  <link rel="apple-touch-icon" href="/apple-touch-icon.png">')


if __name__ == "__main__":
    main(sys.argv[1:])
