from typing import (
    Any, Dict, Generator, Iterable, Iterator, Optional, Sequence, Tuple,
    TypeVar
)

from django.urls import reverse

_T = TypeVar


def lastloop(iterable: Iterable[_T]) -> Generator[Tuple[_T, bool], None, None]:
    """Pass through all values from the given iterable. Report is this is the
    last iteration or not (more values to come).

    >>> for val, last in lastloop('abc'):
    ...     (val, last)
    ('a', False)
    ('b', False)
    ('c', True)

    """
    it: Iterator = iter(iterable)
    try:
        last = next(it)
    except StopIteration:
        # to avoid raising Stop Iteration by `for` loop if Itterable is empty
        return None
    for val in it:
        yield last, False
        last = val
    # Report about the last loop
    yield last, True


def reverse_next(
        viewname: str,
        next_url: str,
        urlconf: Optional[str] = None,
        args: Optional[Sequence[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        current_app: Optional[str] = None) -> str:
    """An extention for django's reverse function. Append 'next=' parameter to
    given url.
    """
    return (
        reverse(viewname, urlconf, args, kwargs, current_app)
        + '?next=' + next_url
    )
