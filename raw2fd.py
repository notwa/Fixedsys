#!/usr/bin/python3


def loadraw(
    raw, width=None, height=None, n=256, *, name="unknown", copyright="unknown"
):
    from fancyfd import savefancy, newfancy, Font, Char

    end = len(raw)
    if width is None:
        width = 8 if height is None else end // (n // 8 * height)
    if height is None:
        height = end // (n // 8 * width)
    charsize = width * height // 8

    f = Font(height)
    for i in range(0, end, charsize):
        c = Char(width)
        c.data[:] = raw[i : i + charsize]
        f.chars.append(c)

    fd = newfancy(name=name, copyright=copyright, height=height)
    for i in range(n):
        savefancy(f, i, fd)
    return fd.getvalue()


def raw2fd(arg):
    from pathlib import Path

    path = Path(arg)
    out = path.with_suffix(".fd")
    with open(path, "rb") as f:
        data = f.read()
    width, height = None, None
    suf = path.suffix.lower().removeprefix(".")
    if suf[0] == "f" and all(c in "0123456789" for c in suf[1:]):
        height = int(suf[1:], 10)
        out = out.with_stem(f"{out.stem}-{height}")
    else:
        width = 8
    fd = loadraw(data, width, height, name=path.stem)
    with open(out, "w", newline="\n", encoding="utf-8") as f:
        f.write(fd)


if __name__ == "__main__":
    from cli import foreacharg

    exit(0 if foreacharg(raw2fd) else 1)
