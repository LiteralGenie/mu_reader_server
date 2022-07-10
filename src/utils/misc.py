from typing import TypeVar


CALL_LOG = dict()


def limit(calls: int, period: float = 1, scope=""):
    """
    Decorator for rate limiting function calls
    """

    import functools, time

    CALL_LOG.setdefault(scope, [])

    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            history = CALL_LOG[scope]
            now = time.time()

            while True:
                if len(history) == 0:
                    break

                elapsed = now - history[0]
                if elapsed > period:
                    history.pop(0)
                else:
                    break

            if len(history) >= calls:
                oldest = history[0]
                elapsed = now - oldest
                rem = period - elapsed
                if rem >= 0:
                    time.sleep(rem)
                    history.pop(0)

            result = f(*args, **kwargs)
            history.append(time.time())
            return result

        return wrapper

    return decorator


T = TypeVar("T")


def upsert(cls: T, key: dict, data: dict | None = None) -> T:
    data = data or dict()

    obj = cls.get(**key)
    if obj is None:
        obj = cls(**key, **data)
    else:
        obj.set(**data)
    return obj
