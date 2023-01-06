from abc import ABC, abstractmethod
from typing import Union

from liteapi.endpoint import Endpoint
from liteapi.requests import Request
from liteapi.responses import Response


class PreMiddleware(ABC):
    def __call__(self, endpoint: Endpoint):
        endpoint.preprocessors.append(self.preprocess)
        return endpoint

    @abstractmethod
    async def preprocess(self, request: Request) -> Union[Request, Response]:
        pass


class PostMiddleware(ABC):
    def __call__(self, endpoint: Endpoint):
        endpoint.postprocessors.append(self.postprocess)
        return endpoint

    @abstractmethod
    async def postprocess(self, response: Response) -> Response:
        pass
