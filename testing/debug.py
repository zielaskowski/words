import time


def debug(func):
    """Backup decorator.
    prints func name, time taken
    some vars?
    """
    import functools
    enabled = False

    @functools.wraps(func)
    def wrap(*args, **kwargs):
        ret = func(*args, **kwargs)
        if enabled:
            txt = ''
            txt += 'DEBUG:\n'
            txt += f'{func.__name__} with args, kwargs:{args[1:], kwargs}\n'
            start = time.time()
            end = time.time()
            txt += f'in {end - start} sec\n'
            txt += 'END DEBUG\n'
            with open('./testing/debug.txt', 'a') as f:
                f.writelines(txt)
        return ret

    return wrap
