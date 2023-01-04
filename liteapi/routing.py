from typing import Dict, Callable, List, Type, Union

from liteapi.endpoint import Endpoint
from liteapi.middleware import PreMiddleware, PostMiddleware, Middleware


class RoutingMixin:
    _endpoints: Dict[str, Dict[str, Endpoint]]

    def __init__(self):
        self._middlewares = []

    def route(
            self,
            path: str,
            method: str = 'ANY',
            *,
            status_code: int = 200,
            content_type: str = 'application/json',
            returns: Type = None
    ):
        def decorator(func: Callable):
            endpoint = Endpoint(func, method, status_code, content_type, returns)
            for middleware in self._middlewares:
                endpoint = middleware(endpoint)

            if self._endpoints.get(path):
                self._endpoints[path].update({method: endpoint})
            else:
                self._endpoints[path] = {method: endpoint}

            return endpoint

        return decorator

    def get(self, path: str, *, status_code: int = 200, content_type: str = 'application/json', returns: Type = None):
        return self.route(path, 'GET', status_code=status_code, content_type=content_type, returns=returns)

    def post(self, path: str, *, status_code: int = 200, content_type: str = 'application/json', returns: Type = None):
        return self.route(path, 'POST', status_code=status_code, content_type=content_type, returns=returns)

    def put(self, path: str, *, status_code: int = 200, content_type: str = 'application/json', returns: Type = None):
        return self.route(path, 'PUT', status_code=status_code, content_type=content_type, returns=returns)

    def patch(self, path: str, *, status_code: int = 200, content_type: str = 'application/json', returns: Type = None):
        return self.route(path, 'PATCH', status_code=status_code, content_type=content_type, returns=returns)

    def delete(self, path: str, *, status_code: int = 200, content_type: str = 'application/json',
               returns: Type = None):
        return self.route(path, 'DELETE', status_code=status_code, content_type=content_type, returns=returns)

    def add_middleware(self, middleware: Union[PreMiddleware, PostMiddleware, Middleware]):
        print('adding middleware')
        self._middlewares.append(middleware)


class Router(RoutingMixin):
    def __init__(self, prefix: str = '', tags: List[str] = None):
        super().__init__()

        self.prefix = prefix
        self._endpoints: Dict[str, Dict[str, Endpoint]] = {}
        self._tags = tags

    @property
    def tag(self) -> List[str]:
        if self._tags is not None:
            return self._tags
        else:
            return [self.prefix.strip('/')[self.prefix.rfind('/'):]]

    @property
    def endpoints(self) -> Dict[str, Dict[str, Endpoint]]:
        return self._endpoints
