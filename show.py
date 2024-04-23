from PIL import Image


def show(lines):
    chars = []
    x, y = 0, 0
    rows = 14
    cols = 16
    max_width = 0
    width, height, ascent, pointsize = -1, -1, -1, -1
    charset = -1
    i = -1

    for line in filter(bool, map(str.strip, lines)):
        if line.startswith("#"):
            continue
        elif line.startswith("0") or line.startswith("1"):
            error = lambda s: f"{s}: {line}"
            if width < 0 or height < 0 or i < 0:
                return error("unexpected data")
            if x >= width or y >= height:
                return error("too much data")
            pix = chars[-1].load()
            for x, c in enumerate(line):
                if c not in "01":
                    return error("expected binary")
                pix[x, y] = 1 if c != "0" else 0
            y += 1
            continue

        k, _, v = line.partition(" ")
        v = int(v) if v and all(c in "0123456789" for c in v) else v
        error = lambda s: f"{s}: {k}={v}"
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
            case ["charset", charset]:
                pass
            case ["char", i]:
                if height < 0:
                    return error("unexpected property")
                if not isinstance(i, int):
                    return error("invalid integer")
                if i > 255:
                    return error("value out of range")
                if i < 32 and width:
                    rows = 16
            case ["width", width]:
                if height < 0 or i < 0:
                    return error("unexpected property")
                if not isinstance(width, int):
                    return error("invalid integer")
                if width > 255:
                    return error("value out of range")
                max_width = max(max_width, width)
                char = Image.new("1", (width, height), 1)
                chars.append(char)
                x, y = 0, 0
            case _:
                return error("unknown property")

    im = Image.new("1", ((max_width + 1) * cols + 1, (height + 1) * rows + 1), 0)
    skip = 16 - rows
    for i in range(16 * skip, 256):
        x = i % 16 * (max_width + 1) + 1
        y = (i // 16 - skip) * (height + 1) + 1
        char = Image.new("1", (max_width, height), 1)
        char.paste(chars[i], (0, 0))
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
            print(f"{sys.argv[0]}: {arg}: {error}", flush=True, file=sys.stderr)
    if not ok:
        exit(1)
