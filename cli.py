import sys


def default_handler(name, argument, error):
    print(name, argument, error, sep=": ", flush=True, file=sys.stderr)


def foreach(args, callback, *, program_name=None, error_handler=default_handler):
    if program_name is None:
        program_name = sys.argv[0] if sys.argv else "unknown"

    ok = True
    for arg in args:
        error = None
        try:
            error = callback(arg)
        except OSError as e:
            error = e.strerror
        except Exception as e:
            error = f"{type(e).__name__}: {e}"
        if error is not None:
            error_handler(program_name, arg, error)
            ok = False
    return ok


def foreacharg(callback):
    return foreach(sys.argv[1:], callback)
