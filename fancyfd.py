from dataclasses import dataclass, field
from io import StringIO


@dataclass
class Char:
    width: int = 0
    data: list[int] = field(default_factory=list)


@dataclass
class Font:
    height: int = 0
    chars: list[Char] = field(default_factory=list)


def newfancy(*, name, copyright, height, charset=255):
    header = StringIO()
    printer = lambda *args, **kwargs: print(*args, file=header, **kwargs)
    printer("# .fd font description")
    printer()
    printer("facename", name)
    printer("copyright", copyright)
    printer()
    printer("height", height)
    printer("#", "ascent", height)
    printer("#", "pointsize", height)
    printer()
    printer("#", "italic", "no")
    printer("#", "underline", "no")
    printer("#", "strikeout", "no")
    printer("#", "weight", "400")
    printer()
    printer("charset", charset)
    printer()
    return header


def savefancy(f, i, printer, *, single=False, chars1=" █", chars2=" ▀▄█"):
    charset = chars1 if single else chars2
    c = f.chars[i]
    w, h = c.width, f.height

    if not callable(printer):
        fd = printer
        printer = lambda *args, **kwargs: print(*args, file=fd, **kwargs)

    printer(f"new {w:d}")

    def writeout(rows):
        assert rows in (1, 2), f"{rows=}"
        c = "." if rows == 1 else ":"
        s = c + "".join(charset[b] for b in buf).rstrip(" ")
        printer(s)

    if w != 0:
        buf = [0] * w
        start_x, start_y = 0, 0
        for j in range(w):
            if any(c.data[k] & 1 << (w - j - 1) for k in range(h)):
                break
            start_x += 1
        for j in range(h):
            if c.data[j]:
                break
            start_y += 1
        if 0 < start_x < w or 0 < start_y < h:
            printer(f"at {start_x:d} {start_y:d}")
        final_y = h
        for j in reversed(range(h)):
            if c.data[j]:
                break
            final_y -= 1
        odd = True
        for j in range(start_y, final_y):
            # printer(f"# {c.data[j]:0{w}b}")
            odd = not odd
            v = c.data[j] << start_x
            m = 1 << (w - 1)
            for k in range(w):
                if v & m:
                    buf[k] |= (odd and not single) + 1
                v = v << 1
            if odd or single:
                writeout(1 if single else 2)
                buf[:] = [0] * w
        if not odd and not single:
            writeout(1)
        del buf
    printer(f"push {i:d}")
    printer()
