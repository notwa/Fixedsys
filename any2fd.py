#!/usr/bin/python3


def any2fd(arg):
    from asm2fd import asm2fd
    from cpi2fd import cpi2fd
    from raw2fd import raw2fd
    from dewinfont import fnt2fd

    from pathlib import Path

    suf = Path(arg).suffix.lower()
    if suf == ".asm":
        return asm2fd(arg)
    elif suf == ".cpi":
        return cpi2fd(arg)
    elif suf == ".fon" or suf == ".fnt":
        return fnt2fd(arg, fancy=True)
    else:
        return raw2fd(arg)


if __name__ == "__main__":
    from cli import foreacharg

    exit(0 if foreacharg(any2fd) else 1)
