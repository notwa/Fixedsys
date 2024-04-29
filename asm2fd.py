#!/usr/bin/python3


def convert_asm(lines, name, *, width=8, height=None):
    from fancyfd import savefancy, newfancy, Font, Char

    font = None if height is None else Font(height)

    for line in filter(bool, map(str.strip, lines)):
        line = line.partition(";")[0].replace("\t", " ")
        a, _, b = line.strip().partition(" ")
        if a.strip().lower() != "db":
            continue
        glyph = b.strip().split(",")
        if font is None:
            font = Font(len(glyph))
        else:
            assert len(glyph) == font.height, "inconsistent height"
        char = Char(width)
        for y, byte in enumerate(glyph):
            assert byte.startswith("0")
            assert byte.endswith("h")
            row = int(byte.removeprefix("0").removesuffix("h"), 16)
            char.data.append(row)
        font.chars.append(char)

    copyright = "MS DOS Version 4.00 (C)Copyright 1988 Microsoft Corp"
    fd = newfancy(name=name, copyright=copyright, height=font.height)
    for i in range(len(font.chars)):
        savefancy(font, i, fd)
    return fd.getvalue()


def asm2fd(arg):
    from pathlib import Path

    path = Path(arg)
    out = path.with_suffix(".fd")
    with open(path) as f:
        result = convert_asm(f, path.stem)
    with open(out, "w", newline="\n", encoding="utf-8") as f:
        f.write(result)


if __name__ == "__main__":
    from cli import foreacharg

    exit(0 if foreacharg(asm2fd) else 1)
