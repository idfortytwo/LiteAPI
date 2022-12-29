import abc
from typing import Tuple, Callable

from liteapi.parsing import Scope


class Middleware(abc.ABC):
    @abc.abstractmethod
    async def handle(self, scope: Scope, receive: Callable, send: Callable) -> Tuple[Scope, Callable, Callable]:
        pass