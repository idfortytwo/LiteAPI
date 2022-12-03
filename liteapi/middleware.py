import abc
from typing import Tuple, Dict, Callable


class Middleware(abc.ABC):
    @abc.abstractmethod
    async def handle(self, scope, receive, send) -> Tuple[Dict, Callable, Callable]:
        pass