from PIL import Image
from dataclasses import dataclass, field


@dataclass
class Font:
    error: str = ""
    max_width: int = 0
    height: int = 0
    chars: dict = field(default_factory=dict)


def load(lines):
    chars, char = {}, None
    x, y = 0, 0
    max_width = 0
    width, height, ascent, pointsize = -1, -1, -1, -1
    charset, index = -1, -1
    new_format = None

    for line in filter(bool, map(str.strip, lines)):
        error = lambda s: Font(f"{s}: {line}")
        if line.startswith("#"):
            continue
        elif line.startswith("0") or line.startswith("1"):
            if width < 0 or height < 0 or index < 0:
                return error("unexpected data")
            if width == 0 or y >= height:
                return error("too much data")
            pix = char.load()
            for x, c in enumerate(line):
                if c not in "01":
                    return error("expected binary")
                if x >= width:
                    return error("too much data")
                pix[x, y] = 0 if c != "0" else 1
            y += 1
            continue
        elif line.startswith(".") or line.startswith(":"):
            single = line[0] == "."
            if width < 0 or height < 0 or char is None:
                return error("unexpected data")
            if width == 0 or y >= height or not single and y == height - 1:
                return error("too much data")
            pix = char.load()
            for o, c in enumerate(line[1:]):
                if x + o >= width:
                    return error("too much data")
                if c == " ":
                    pass
                elif single:
                    pix[x + o, y] = 0
                elif c == "▀":
                    pix[x + o, y + 0] = 0
                elif c == "█":
                    pix[x + o, y + 0] = 0
                    pix[x + o, y + 1] = 0
                elif c == "▄":
                    pix[x + o, y + 1] = 0
                else:
                    return error("unknown character")
            y += 1 if single else 2
            continue

        k, _, v = line.partition(" ")
        v = int(v) if v and all(c in "0123456789" for c in v) else v
        error = lambda s: Font(f"{s}: {k}={v}")
        match (k, v):
            case ["facename", facename]:
                pass
            case ["copyright", copyright]:
                pass
            case ["height", height]:
                if not isinstance(height, int):
                    return error("invalid integer")
                if height > 255:
                    return error("value out of range")
            case ["ascent", ascent]:
                pass
            case ["pointsize", pointsize]:
                pass
            case ["italic", italic]:
                pass
            case ["underline", underline]:
                pass
            case ["strikeout", strikeout]:
                pass
            case ["weight", weight]:
                pass
            case ["charset", charset]:
                pass
            case ["char" | "push", index]:
                if new_format is None:
                    new_format = k == "push"
                elif new_format != (k == "push"):
                    return error("mixed formats")
                if height < 0 or width < 0 and new_format:
                    return error("unexpected property")
                if not isinstance(index, int):
                    return error("invalid integer")
                if char is not None:
                    chars[index if new_format else old_index] = char
                old_index = index
            case ["width" | "new", width]:
                if new_format is None:
                    new_format = k == "new"
                elif new_format != (k == "new"):
                    return error("mixed formats")
                if height < 0 or index < 0 and not new_format:
                    return error("unexpected property")
                if not isinstance(width, int):
                    return error("invalid integer")
                if width > 255:
                    return error("value out of range")
                max_width = max(max_width, width)
                char = Image.new("1", (width, height), 1) if width > 0 else None
                x, y = 0, 0
            case ["at", xy]:
                x, _, y = xy.partition(" ")
                if not x or not all(c in "0123456789" for c in x):
                    return error("expected two integers")
                if not y or not all(c in "0123456789" for c in y):
                    return error("expected two integers")
                x, y = int(x), int(y)
            case _:
                return error("unknown property")
    if not new_format and char is not None:
        chars[old_index] = char

    return Font(max_width=max_width, height=height, chars=chars)


def show(lines_or_font, *, cols=None, rows=None, skip=32, offset=0):
    if cols is None and rows is None:
        cols, rows = 16, 16
    cols = 256 // rows if cols is None else cols
    rows = 256 // cols if rows is None else rows
    assert rows * cols == 256, f"invalid dimensions: {cols=}, {rows=}"

    font = lines_or_font if isinstance(lines_or_font, Font) else load(lines_or_font)
    if font.error:
        return font.error

    if any(font.chars.get(i + offset, None) for i in range(skip)):
        skip = 0

    blank = Image.new("1", (font.max_width, font.height), 1)
    rows -= skip // cols
    dims = ((font.max_width + 1) * cols + 1, (font.height + 1) * rows + 1)
    im = Image.new("1", dims, 0)
    for i in range(skip, 256):
        x = i % cols * (font.max_width + 1) + 1
        y = ((i - skip) // cols) * (font.height + 1) + 1
        char = Image.new("1", (font.max_width, font.height), 1)
        char.paste(font.chars.get(i + offset, blank), (0, 0))
        im.paste(char, (x, y))
    return im


if __name__ == "__main__":
    from pathlib import Path
    import sys

    ok = True
    for arg in sys.argv[1:]:
        error = None
        path = Path(arg)
        out = path.with_suffix(".png")
        try:
            with open(path, encoding="utf-8") as f:
                result = show(f)
                if isinstance(result, Image.Image):
                    result.save(out)
                else:
                    error = result
        except OSError as e:
            error = e.strerror
        except Exception as e:
            error = f"{type(e).__name__}: {e}"
        if error:
            ok = False
            print(f"{sys.argv[0]}: {arg}: {error}", flush=True, file=sys.stderr)
    if not ok:
        exit(1)
