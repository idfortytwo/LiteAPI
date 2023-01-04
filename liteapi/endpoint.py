import inspect
from dataclasses import dataclass, field
from inspect import signature, Signature
from typing import Callable, List, Type

from liteapi.requests import Request
from liteapi.responses import response_factory, Response


@dataclass
class Endpoint:
    func: Callable
    http_method: str
    status_code: int
    content_type: str
    returns: Type = None
    tags: List[str] = None
    signature: Signature = field(init=False, repr=False)

    preprocessors: List[Callable] = field(init=False, repr=False)
    postprocessors: List[Callable] = field(init=False, repr=False)

    def __post_init__(self):
        self.signature = signature(self.func)

        self.preprocessors = []
        self.postprocessors = []

    async def handle(self, request: Request) -> Response:
        for preprocessor in self.preprocessors:
            request = await preprocessor(request)
            if isinstance(request, Response):
                return request

        response = await self._process(**request.args)

        for postprocessor in self.postprocessors:
            response = await postprocessor(response)
        return response

    async def _process(self, *args, **kwargs) -> Response:
        if inspect.iscoroutinefunction(self.func):
            result = await self.func(*args, **kwargs)
        else:
            result = self.func(*args, **kwargs)

        match result:
            case Response():
                response = result
            case data, int(code):
                response = response_factory(data, code, self.content_type)
            case data:
                response = response_factory(data, self.status_code, self.content_type)

        return response


not_found = Endpoint(lambda: 'No such endpoint', 'GET', 404, 'application/json')
