#!/usr/bin/env python3
"""Inline the ramp subset of JetBrains Mono into ascii.svg.

The portrait is a one-off artifact — a photo pushed through a character ramp —
so unlike the stat graphics it isn't regenerated on a schedule. Run this after
ever rebuilding it.

Why it matters: the character grid bakes in an advance width of exactly 0.600 em
(CHAR_W 7.74 at font-size 12.9). JetBrains Mono is 600/1000 units, so the
geometry is unchanged, but a viewer whose default monospace is narrower —
Consolas is about 0.55 — would otherwise see the portrait roughly 7% too narrow.
Inlining pins it for everyone. An external font URL is not an option: the SVG is
loaded through <img>, and browsers refuse subresource fetches for image
documents.

Idempotent: running it twice changes nothing.
"""
import base64
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
FAMILY = ("JBMono,ui-monospace,SFMono-Regular,Menlo,Consolas,"
          "&apos;Liberation Mono&apos;,monospace")


def pick_font(svg):
    """The ramp subset for a portrait, basic latin for anything with words.

    A portrait is nothing but ramp characters, so its 1 KB subset is the whole
    alphabet it needs. A wordmark carries a tagline in real letters, and those
    would silently fall back to the viewer's own monospace.
    """
    ramp = set(" .`:-=+*cs#%@")
    body = re.sub(r"<style>.*?</style>", "", svg, flags=re.S)
    body = re.sub(r"<[^>]*>", "", body)
    if set(body) - ramp - set("\n\t"):
        return os.path.join(FONTS, "jbmono-400.woff2")
    return os.path.join(FONTS, "jbmono-ramp.woff2")


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(HERE), "ascii.svg")
    with open(target, encoding="utf-8") as f:
        svg = f.read()

    FONT = pick_font(svg)

    if "JBMono" in svg:
        print(f"{target}: already carries the font")
        return

    with open(FONT, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    rule = (f"@font-face{{font-family:JBMono;font-style:normal;"
            f"font-weight:400;font-display:block;"
            f"src:url(data:font/woff2;base64,{b64}) format('woff2')}}")

    if "<style>" not in svg:
        raise SystemExit(f"{target}: no <style> block to extend")
    svg = svg.replace("<style>", f"<style>{rule}", 1)

    # point the whole document at the embedded face
    swapped, n = re.subn(r'font-family="[^"]*"', f'font-family="{FAMILY}"', svg)
    if not n:
        raise SystemExit(f"{target}: no font-family to replace")

    with open(target, "w", encoding="utf-8") as f:
        f.write(swapped)
    print(f"{target}: embedded {len(b64) // 1024} KB of base64 font")


if __name__ == "__main__":
    main()
