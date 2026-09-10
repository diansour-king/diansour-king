#!/usr/bin/env python3
"""Draw ascii.svg as a self-typing ASCII wordmark.

This is the no-photo route to the graphic at the top of the README. Its sibling,
scripts/make_portrait.py, does the same job from a photograph; both write
ascii.svg and both are one-off — neither runs on a schedule.

    python3 scripts/make_wordmark.py "BIKASH" "KUMAR SHAH" \
        --tagline "cse @ nit rourkela  ~  batch of 2027"
    python3 scripts/embed_portrait_font.py     # inline the font, see below

The letterforms are hand-built here rather than rasterised from a real typeface.
A 7-row glyph is about twelve pixels tall, and at that size a threshold pass over
rendered text loses the strokes that separate B from 8 and K from X. Hand-drawn
cells stay legible because every stroke is deliberate. The cost is the glyph
table below; the benefit is that this script has no dependencies at all, so it
runs anywhere Python does.

The grid assumes an advance width of exactly 0.600 em (CHAR_W / FONT_SIZE), so
run scripts/embed_portrait_font.py afterwards to inline JetBrains Mono. Without
it a viewer whose default monospace is narrower - Consolas is about 0.55 - sees
the wordmark roughly 7% too narrow, and the two lines stop agreeing on width.

Motion is SMIL because GitHub strips <script> from READMEs: each row is revealed
by a clipPath wipe with a cursor block riding its edge, staggered top to bottom,
frozen at the end so it types once and stops.
"""
import argparse

# 5x7 cells. Wider than 5 and a ten-character line overflows the README column;
# narrower and the diagonals in K, M and W collapse into vertical bars.
GLYPHS = {
    "A": (" ### ", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"),
    "B": ("#### ", "#   #", "#   #", "#### ", "#   #", "#   #", "#### "),
    "C": (" ####", "#    ", "#    ", "#    ", "#    ", "#    ", " ####"),
    "D": ("#### ", "#   #", "#   #", "#   #", "#   #", "#   #", "#### "),
    "E": ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#####"),
    "F": ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#    "),
    "G": (" ####", "#    ", "#    ", "#  ##", "#   #", "#   #", " ####"),
    "H": ("#   #", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"),
    "I": ("#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "#####"),
    "J": ("#####", "    #", "    #", "    #", "    #", "#   #", " ### "),
    "K": ("#   #", "#  # ", "# #  ", "##   ", "# #  ", "#  # ", "#   #"),
    "L": ("#    ", "#    ", "#    ", "#    ", "#    ", "#    ", "#####"),
    "M": ("#   #", "## ##", "# # #", "#   #", "#   #", "#   #", "#   #"),
    "N": ("#   #", "##  #", "# # #", "#  ##", "#   #", "#   #", "#   #"),
    "O": (" ### ", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "),
    "P": ("#### ", "#   #", "#   #", "#### ", "#    ", "#    ", "#    "),
    "Q": (" ### ", "#   #", "#   #", "#   #", "# # #", "#  # ", " ## #"),
    "R": ("#### ", "#   #", "#   #", "#### ", "# #  ", "#  # ", "#   #"),
    "S": (" ####", "#    ", "#    ", " ### ", "    #", "    #", "#### "),
    "T": ("#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  "),
    "U": ("#   #", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "),
    "V": ("#   #", "#   #", "#   #", "#   #", "#   #", " # # ", "  #  "),
    "W": ("#   #", "#   #", "#   #", "#   #", "# # #", "## ##", "#   #"),
    "X": ("#   #", "#   #", " # # ", "  #  ", " # # ", "#   #", "#   #"),
    "Y": ("#   #", "#   #", " # # ", "  #  ", "  #  ", "  #  ", "  #  "),
    "Z": ("#####", "    #", "   # ", "  #  ", " #   ", "#    ", "#####"),
    "0": (" ### ", "#   #", "#  ##", "# # #", "##  #", "#   #", " ### "),
    "1": ("  #  ", " ##  ", "  #  ", "  #  ", "  #  ", "  #  ", "#####"),
    "2": (" ### ", "#   #", "    #", "   # ", "  #  ", " #   ", "#####"),
    "3": ("#####", "   # ", "  ## ", "    #", "    #", "#   #", " ### "),
    "4": ("   # ", "  ## ", " # # ", "#  # ", "#####", "   # ", "   # "),
    "5": ("#####", "#    ", "#### ", "    #", "    #", "#   #", " ### "),
    "6": (" ### ", "#   #", "#    ", "#### ", "#   #", "#   #", " ### "),
    "7": ("#####", "    #", "   # ", "  #  ", " #   ", " #   ", " #   "),
    "8": (" ### ", "#   #", "#   #", " ### ", "#   #", "#   #", " ### "),
    "9": (" ### ", "#   #", "#   #", " ####", "    #", "#   #", " ### "),
    " ": ("     ", "     ", "     ", "     ", "     ", "     ", "     "),
    "-": ("     ", "     ", "     ", " ### ", "     ", "     ", "     "),
    ".": ("     ", "     ", "     ", "     ", "     ", "     ", "  #  "),
    "'": ("  #  ", "  #  ", "     ", "     ", "     ", "     ", "     "),
}

GLYPH_H = 7
FG_LIGHT = "#6e7681"       # readable on GitHub light - the profile's grey ink
FG_DARK = "#c9d1d9"        # and its dark-mode step
DIM_LIGHT = "#8c959f"      # the tagline sits a step back from the wordmark
DIM_DARK = "#8b949e"
CHAR_W = 7.74              # 0.600 em at FONT_SIZE - keep these in step
FONT_SIZE = 12.9
LINE_H = 15
ROW_DELAY = 0.09           # per-row stagger, seconds
FAMILY = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def render_word(text):
    """One line of text as seven strings, glyphs separated by a blank column."""
    rows = [""] * GLYPH_H
    for i, char in enumerate(text.upper()):
        glyph = GLYPHS.get(char)
        if glyph is None:
            raise SystemExit(
                f"no glyph for {char!r}; add it to GLYPHS in {__file__}"
            )
        for r in range(GLYPH_H):
            rows[r] += ("" if i == 0 else " ") + glyph[r]
    return [row.rstrip() for row in rows]


def compose(words, tagline):
    """Stack the wordmark lines, then the tagline, with blank rows between.

    Returns (line, is_tagline) pairs so the caller can style the two differently
    without re-deriving which row is which.
    """
    out = []
    for i, word in enumerate(words):
        if i:
            out.append(("", False))
        out += [(row, False) for row in render_word(word)]
    if tagline:
        out.append(("", False))
        out.append((tagline, True))
    return out


def build_svg(rows):
    pad = 14
    cols = max((len(line) for line, _ in rows), default=1)
    width = int(cols * CHAR_W + pad * 2)
    height = len(rows) * LINE_H + pad * 2

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
         f'height="{height}" viewBox="0 0 {width} {height}" '
         f'font-family="{FAMILY}">',
         f'<style>.a{{fill:{FG_LIGHT}}}.b{{fill:{DIM_LIGHT}}}'
         f'@media(prefers-color-scheme:dark){{.a{{fill:{FG_DARK}}}'
         f'.b{{fill:{DIM_DARK}}}}}</style>']

    for i, (line, dim) in enumerate(rows):
        if not line:
            continue
        y = pad + i * LINE_H
        begin = f"{i * ROW_DELAY:.2f}s"
        end = f"{(i + 1) * ROW_DELAY:.2f}s"
        w = max(len(line), 1) * CHAR_W
        cls = "b" if dim else "a"
        safe = (line.replace("&", "&amp;").replace("<", "&lt;")
                    .replace(">", "&gt;"))

        p.append(f'<clipPath id="w{i}"><rect x="{pad}" y="{y}" '
                 f'height="{LINE_H}" width="0">'
                 f'<animate attributeName="width" from="0" to="{w:.1f}" '
                 f'begin="{begin}" dur="{ROW_DELAY}s" fill="freeze"/>'
                 f'</rect></clipPath>')
        p.append(f'<g clip-path="url(#w{i})"><text xml:space="preserve" '
                 f'x="{pad}" y="{y + 11.2:.1f}" class="{cls}" '
                 f'font-size="{FONT_SIZE}">{safe}</text></g>')
        # the cursor: a small block riding the wipe edge, gone once the row lands
        p.append(f'<rect y="{y + 1}" width="6" height="12" class="{cls}" '
                 f'opacity="0">'
                 f'<animate attributeName="x" from="{pad}" to="{pad + w:.1f}" '
                 f'begin="{begin}" dur="{ROW_DELAY}s" fill="freeze"/>'
                 f'<set attributeName="opacity" to="0.8" begin="{begin}"/>'
                 f'<set attributeName="opacity" to="0" begin="{end}"/></rect>')

    p.append("</svg>")
    return "".join(p)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("words", nargs="+", help="one argument per wordmark line")
    ap.add_argument("--out", default="ascii.svg")
    ap.add_argument("--tagline", default="",
                    help="a plain-text line set below the wordmark")
    ap.add_argument("--preview", action="store_true",
                    help="print the ASCII to the terminal as well")
    args = ap.parse_args()

    rows = compose(args.words, args.tagline)
    if args.preview:
        print("\n".join(line for line, _ in rows))

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(build_svg(rows))
    print(f"wrote {args.out} - {len(rows)} rows, "
          f"{max(len(line) for line, _ in rows)} columns")
    print("next: python3 scripts/embed_portrait_font.py")


if __name__ == "__main__":
    main()
