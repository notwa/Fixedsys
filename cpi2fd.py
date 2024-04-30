#!/usr/bin/python3

_print_copyright = False


def warn(*args):
    print(end="\033[7;31;107m")
    print(*args, end="\033[m\n")


def convert_cpi(f, name, *, width=8, height=None):
    from fancyfd import savefancy, newfancy, Font, Char

    font, fd = None, None
    copyright = "Copyright (c) Microsoft Corporation"  # TODO: do something smarter.

    reader = lambda n: sum(x << (i * 8) for i, x in enumerate(f.read(n)))
    char, short, long = (lambda: reader(1)), (lambda: reader(2)), (lambda: reader(4))
    segoff = lambda x: (x >> 16 << 4) + (x & 0xFFFF)

    id8 = f.read(8)
    assert id8 in (b"\xFFFONT   ", b"\xFFFONT.NT"), f"wrong file format: {id8}"
    pad = f.read(8)

    nt = id8 == b"\xFFFONT.NT"

    pnum = short()
    assert pnum == 1, "only 1 pointer is supported"
    ptyp = char()
    assert ptyp == 1, "only pointer-type 1 is supported"
    fih_offset = long()

    if fih_offset != 0x17:
        warn(f"unusual seek (FIH) to ${fih_offset:04X} from ${f.tell():04X}")
        f.seek(fih_offset)

    num_codepages = short()

    printers = (
        b"4201    ",
        b"4208    ",
        b"5202    ",
        b"1050    ",
        b"EPS     ",
        b"PPDS    ",
    )

    def read_screen_font():
        nonlocal font, fd, width, height

        height = char()
        width = char()
        if width == 0xAA and height == 0xAA:
            warn("skipping invalid font")
            return "break"
        yaspect = char()
        xaspect = char()
        num_chars = short()
        if width != 8:
            warn("unusual dimensions:", f"{width}x{height}")
        if yaspect != 0:
            warn("unusual Y aspect ratio:", yaspect)
        if xaspect != 0:
            warn("unusual X aspect ratio:", xaspect)
        if num_chars not in (256, 512):
            warn("unusual character count:", num_chars)

        width_bytes = (width + 7) // 8  # TODO: what's this called, stride?
        char_size = width_bytes * height
        bitmap_size = num_chars * char_size

        if font is None:
            fd = newfancy(name=name, copyright=copyright, height=height)
            font = Font(height)

        if bitmap_size == 0:
            warn("skipping empty font")
            return "continue"

        for k in range(num_chars):
            _char = Char(width)
            _char.data = [reader(width_bytes) for _ in range(height)]
            font.chars.append(_char)

    def read_printer_font():
        nonlocal font, fd, width, height

        ref = f.tell()
        printer_type = short()
        escape_length = short()
        # (ref + 4)

        if printer_type == 1:  # 2 escape sequences
            sequence_1 = f.read(char())
            sequence_2 = f.read(char())
            if device_name == b"4201    " and sequence_1 == b"\033I\000\0336":
                pass
            else:
                print(f"{codepage=} {sequence_1=}")
            if device_name == b"4201    " and sequence_2 == b"\033I\004\0336":
                pass
            else:
                print(f"{codepage=} {sequence_2=}")
            if escape_length != f.tell() - (ref + 4):
                warn("invalid escape length")
                return "break"

        elif printer_type == 2:  # 1 escape sequences
            sequence_1 = f.read(escape_length)
            if (
                device_name == b"4208    "
                and sequence_1 == b"\x1bI\x0e\x1bI\x07\x1bI\x06\x00\x1b6"
            ):
                pass
            else:
                print(f"{codepage=} {sequence_1=}")
            # codepage is at sequence_1[7:9] in big-endian
            # 5202 format: b"\033T" + long:length + f.read(length)

        bitmap_size = ref + size - f.tell()
        if bitmap_size == 0:
            return "continue"  # bitmap is stored on the printer itself

        ref = f.tell()

        # am i doing this right?
        width = 11
        height = 8

        if font is None:
            fd = newfancy(name=name, copyright=copyright, height=height)
            font = Font(height)
            font.chars = [None] * 256  # TODO: fix this hack.

        while f.tell() < ref + bitmap_size:
            # c = bytes((k,)).decode("CP" + str(codepage), errors="replace")
            cmd = char()

            assert cmd in (0x00, 0x1B), f"unsupported command: ${cmd:02X}"
            if cmd == 0x00:
                continue  # NOP

            # cmd must be 0x1B.

            subcmd = char()
            assert subcmd in (
                0x36,
                0x3D,
                0x49,
            ), f"unsupported subcommand: ${subcmd:02X}"
            if subcmd == 0x49:
                idk = char()  # doesn't matter
                continue
            elif subcmd == 0x36:
                continue  # idk

            # subcmd must be 0x3D.

            length = short()
            if length == 0:
                continue

            kind = char()
            assert kind in (0x14, 0x15), f"unsupported kind: ${kind:02X}"
            if length == 1:
                continue

            index = char()  # into the charmap, i think?
            if length == 2:
                continue

            if kind == 0x15:
                # these are transposed glyphs with their bytes interleaved.
                # TODO: dump these too!
                f.read(length - 2)
                for more in range((length - 2) // 0x30):
                    pass  # print("found big glyph for", index + more)
                continue

            # kind must be 0x14.

            k = index
            ref14 = f.tell() - 2
            while f.tell() - ref14 < length:
                # chartypes:
                # $00 => normal character
                # $01 => box-drawing character, also including "█▄▌▐▀"
                # $02 => character like "░▒▓"
                # $20 => character like "­" (soft hyphen)
                # $40 => character like "­" (soft hyphen)
                # $80 => character like ",;_gjpqy °±²µ·¸Çßç÷ýÿΓΘΣΦΩαδεπστφ‗ⁿ∙√∞∩≈≡≤≥⌠⌡■"
                chartype = char()  # see commented elifs above
                unknown = char()  # the display width?
                # assert chartype != 0 or unknown != 0, f"early out at {k}"

                _char = Char(width, [0] * height)
                for x in range(width):  # printer fonts are stored transposed
                    col = reader(1)
                    for y in range(height):
                        if col & 1 << (height - 1 - y):
                            _char.data[y] |= 1 << (width - 1 - x)
                font.chars[k] = _char
                k += 1

        if bitmap_size != f.tell() - ref:
            warn(
                f"invalid bitmap length, wanted ${bitmap_size:04X} but read ${f.tell() - ref:04X} (read {k} chars)"
            )
            if font is not None:
                font = None
                fd.close()
            return "break"

    furthest = 0  # needed to find copyright text when file is non-contiguous
    for i in range(num_codepages):
        if f.peek(4)[:4] == b"IBM ":
            warn("detected copyright text, stopping")
            break

        start = f.tell() if nt else 0
        cpeh_size = short()
        assert cpeh_size in (
            0x1A,
            0x1C,
            0x20,
        ), f"unsupported CPEH size ${cpeh_size:04X} at ${f.tell() - 2:04X}"
        next_cpeh_offset = long()
        device_type = short()
        assert device_type in (1, 2), "unknown device type"
        device_name = f.read(8)
        if cpeh_size == 0x20:
            assert device_name == b"VIDEO   ", "weird"
        if device_name in printers:
            device_type = 2
        codepage = short()
        reserved = f.read(6)
        cpih_offset = long() if cpeh_size >= 0x1C else short()
        if cpeh_size == 0x20:
            long()

        no_segoff = device_name == b"VIDEO   "

        if cpih_offset > 0xFFFF and not no_segoff:
            cpih_offset = segoff(cpih_offset)
        if cpih_offset + start != f.tell():
            if device_type != 2:
                warn(
                    f"unusual seek (CPIH) to ${cpih_offset + start:04X} from ${f.tell():04X}"
                )
            if cpih_offset + start < f.tell():
                warn("preventing backwards seek")
            else:
                f.seek(cpih_offset + start)

        version = short()
        assert version in (0, 1), "unsupported CPIH version"  # 2 is DRFONT
        num_fonts = short()
        size = short()  # FIXME: use this? might fix the russian fonts?
        if num_fonts == 0:
            warn("suspiciously zero number of fonts")

        if device_type == 2:
            if num_fonts != 1:
                warn(f"{num_fonts=}")
            num_fonts = 1

        for j in range(num_fonts):
            desire = read_screen_font() if device_type == 1 else read_printer_font()
            if desire == "break":
                break
            elif desire == "continue":
                continue

            if font is not None:
                for ci in range(len(font.chars)):
                    if font.chars[ci] is not None:  # TODO: fix this hack.
                        savefancy(font, ci, fd)
                yield f"{width}x{height}${codepage}", fd.getvalue()
                font = None
                fd.close()

        furthest = max(furthest, f.tell())
        adjusted = next_cpeh_offset if no_segoff else segoff(next_cpeh_offset)
        if i + 1 == num_codepages:
            if next_cpeh_offset not in (0, 0xFFFFFFFF, f.tell()):
                warn(f"final offset should be 0 or -1, not ${next_cpeh_offset:08X}")
        elif adjusted + start != f.tell():
            if device_type != 2:
                warn(
                    f"unusual seek (next CPEH) to ${adjusted + start:04X} from ${f.tell():04X} ({i+1}/{num_codepages})"
                )
            if adjusted + start < f.tell() and device_type != 2:
                warn("preventing backwards seek")
            else:
                f.seek(adjusted + start)

    if _print_copyright:
        if f.tell() != furthest:
            warn(f"seeking to ${furthest:04X} for copyright text")
            f.seek(furthest)
        print("<copyright>")
        copyright = f.read()
        print(copyright.decode("ascii", errors="replace").replace("\r", "").strip())
        if len(copyright) > 0x150:
            warn("copyright was more than 336 bytes in length")
        print("</copyright>")


def cpi2fd(arg):
    from pathlib import Path

    path = Path(arg)
    out = path.with_suffix(".fd")
    if _print_copyright:
        print()
    print("processing", path)
    results = {}
    with open(path, "rb") as f:
        for info, result in convert_cpi(f, path.stem.upper()):
            info = str(info)
            if info in results:
                warn("unusual duplicate info")
            while info in results:
                info += "-"
            results[str(info)] = result
    for info, result in results.items():
        out_cp = out.with_stem(out.stem + "-" + info)
        with open(out_cp, "w", newline="\n", encoding="utf-8") as f:
            f.write(result)


if __name__ == "__main__":
    from cli import foreacharg

    exit(0 if foreacharg(cpi2fd) else 1)
