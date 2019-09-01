import codecs
from cairosvg import svg2png

def svg_to_png(in_fn, out_fn):
    with codecs.open(in_fn, "r", "utf-8") as f:
        svg_code = f.read()

    svg2png(bytestring=svg_code,
            write_to=out_fn)
