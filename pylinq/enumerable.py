from typing import (
    TypeVar, Generic, Iterable,
    Iterator, Callable, Optional,
    List, Set, Dict,
    Any, Union, Sequence,
    Sized
)
from collections import deque
from itertools import chain, islice
from functools import reduce

T = TypeVar('T')
R = TypeVar('R')


class _IEnumerableProps(Generic[T]):
    def __init__(self, iterable: Union[Iterable[T], Sequence[T]]) -> None:
        self._iterable = (
            list(iterable) if isinstance(iterable, (list, tuple))
            else iterable
        )
        self._iterator: Optional[Iterator[T]] = None

    def __iter__(self) -> Iterator[T]:
        if isinstance(self._iterable, Iterator):
            return self._iterable
        return iter(self._iterable)

    def __next__(self) -> T:
        if self._iterator is None:
            self._iterator = iter(self)
        return next(self._iterator)


class IEnumerable(_IEnumerableProps[T]):
    def __getitem__(
        self,
        index: Union[int, slice]
    ) -> Union[T, 'IEnumerable[T]']:
        if isinstance(self._iterable, (list, tuple)):
            result = self._iterable[index]
            if isinstance(index, int):
                return result
            return IEnumerable[T](list(result))

        if isinstance(index, int):
            if index < 0:
                return self.to_list()[index]
            return next(islice(
                self._iterable,
                index,
                index + 1
            ))

        return IEnumerable(islice(
            self._iterable,
            index.start,
            index.stop,
            index.step
        ))

    def __len__(self) -> int:
        if isinstance(self._iterable, Sized):
            return len(self._iterable)

        return sum(1 for _ in self)

    def __bool__(self) -> bool:
        try:
            next(iter(self))
            return True
        except StopIteration:
            return False

    def __contains__(self, item: T) -> bool:
        return any(x == item for x in self)

    def __add__(self, other: Iterable[T]) -> 'IEnumerable[T]':
        return IEnumerable(chain(self, other))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, _IEnumerableProps):
            return NotImplemented
        return all(a == b for a, b in zip(self, other))

    def where(self, predicate: Callable[[T], bool]) -> 'IEnumerable[T]':
        if isinstance(self._iterable, (list, tuple)):
            return IEnumerable([item for item in self._iterable if predicate(item)])
        return IEnumerable(item for item in self._iterable if predicate(item))

    def select(self, selector: Callable[[T], R]) -> 'IEnumerable[R]':
        if isinstance(self._iterable, (list, tuple)):
            return IEnumerable([selector(item) for item in self._iterable])
        return IEnumerable(selector(item) for item in self._iterable)

    def select_many(self, selector: Callable[[T], Iterable[R]]) -> 'IEnumerable[R]':
        if isinstance(self._iterable, (list, tuple)):
            return IEnumerable([item for sublist in (selector(x) for x in self._iterable) for item in sublist])
        return IEnumerable(chain.from_iterable(selector(item) for item in self._iterable))

    def first(self, predicate: Optional[Callable[[T], bool]] = None) -> T:
        if predicate is None:
            return next(iter(self))
        return next(item for item in self if predicate(item))

    def first_or_default(self, default: T, predicate: Optional[Callable[[T], bool]] = None) -> T:
        try:
            return self.first(predicate)
        except StopIteration:
            return default

    def last(self, predicate: Optional[Callable[[T], bool]] = None) -> T:
        if isinstance(self._iterable, (list, tuple)):
            filtered = [x for x in self._iterable if predicate(
                x)] if predicate else self._iterable
            if not filtered:
                raise StopIteration("Sequence contains no elements")
            return filtered[-1]

        if predicate is not None:
            filtered = self.where(predicate)
        else:
            filtered = self

        try:
            return deque(filtered, maxlen=1)[0]
        except IndexError:
            raise StopIteration("Sequence contains no elements")

    def take(self, count: int) -> 'IEnumerable[T]':
        if isinstance(self._iterable, (list, tuple)):
            return IEnumerable(self._iterable[:count])
        return IEnumerable(islice(self._iterable, count))

    def skip(self, count: int) -> 'IEnumerable[T]':
        if isinstance(self._iterable, (list, tuple)):
            return IEnumerable(self._iterable[count:])
        return IEnumerable(islice(self._iterable, count, None))

    def order_by(
        self,
        key_selector: Callable[[T], Any] = lambda x: x
    ) -> 'IEnumerable[T]':
        return IEnumerable(sorted(self, key=key_selector))

    def order_by_descending(
        self,
        key_selector: Callable[[T], Any] = lambda x: x
    ) -> 'IEnumerable[T]':
        return IEnumerable(
            sorted(self, key=key_selector, reverse=True)
        )

    def group_by(self, key_selector: Callable[[T], R]) -> 'IEnumerable[tuple[R, "IEnumerable[T]"]]':
        groups: Dict[R, List[T]] = {}
        for item in self:
            key = key_selector(item)
            if key not in groups:
                groups[key] = []
            groups[key].append(item)
        return IEnumerable(
            (key, IEnumerable(group))
            for key, group in groups.items()
        )

    def distinct(self) -> 'IEnumerable[T]':
        return IEnumerable(dict.fromkeys(self))

    def count(self, predicate: Optional[Callable[[T], bool]] = None) -> int:
        if predicate is None:
            return len(self)
        return sum(1 for item in self if predicate(item))

    def any(self, predicate: Optional[Callable[[T], bool]] = None) -> bool:
        if predicate is None:
            return bool(self)
        return any(predicate(item) for item in self)

    def all(self, predicate: Callable[[T], bool]) -> bool:
        return all(predicate(item) for item in self)

    def aggregate(self, func: Callable[[T, T], T], seed: Optional[T] = None) -> T:
        if seed is None:
            return reduce(func, self)
        return reduce(func, self, seed)

    def to_list(self) -> List[T]:
        return list(self._iterable) if isinstance(self._iterable, (list, tuple)) else list(self)

    def to_set(self) -> Set[T]:
        return set(self)



