from abc import ABC, abstractmethod

from liteapi.parsing import Request
from liteapi.responses import Response


class RequestMiddleware(ABC):
    @abstractmethod
    async def handle(self, request: Request) -> Request:
        pass


class ResponseMiddleware(ABC):
    @abstractmethod
    async def handle(self, response: Response) -> Response:
        pass