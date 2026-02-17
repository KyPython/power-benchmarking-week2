# LinkedIn carousel drafts — Power Benchmarking Suite vs Alternatives

Location: `social/linkedin_carousel/`

Contents:
- `slide01.svg` … `slide12.svg` — 12 draft SVG slides sized 1080×1080 for LinkedIn carousels.
- `caption.txt` — post caption, CTA and hashtags ready for copy/paste.

Usage:
- Preview in a browser by opening any SVG file.
- Convert to PNG (recommended for LinkedIn) using Inkscape or ImageMagick. Example commands:

```bash
# Inkscape (recommended for lossless export)
inkscape slide01.svg --export-type=png --export-filename=slide01.png --export-width=1080 --export-height=1080

# ImageMagick (if installed)
rsvg-convert -w 1080 -h 1080 slide01.svg -o slide01.png
convert slide01.svg -resize 1080x1080 slide01.png
```

Next steps I can take for you:
- Convert all SVGs to PNGs and package into a zip.
- Finalize copy and schedule the post for Feb 18 10:00 AM (I will need scheduler access).
- Iterate slide design (colors, fonts, branding) per your style guide.
