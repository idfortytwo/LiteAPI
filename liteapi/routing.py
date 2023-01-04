from typing import Dict, Callable, List, Type

from liteapi.endpoint import Endpoint


class RoutingMixin:
    _endpoints: Dict[str, Dict[str, Endpoint]]

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
            if self._endpoints.get(path):
                self._endpoints[path].update({method: endpoint})
            else:
                self._endpoints[path] = {method: endpoint}
            return func

        return decorator

    def get(self, path: str, *, status_code: int = 200, content_type: str = 'application/json', returns: Type = None):
        return self.route(path, 'GET', status_code=status_code, content_type=content_type, returns=returns)

    def post(self, path: str, *, status_code: int = 200, content_type: str = 'application/json', returns: Type = None):
        return self.route(path, 'POST', status_code=status_code, content_type=content_type, returns=returns)

    def put(self, path: str, *, status_code: int = 200, content_type: str = 'application/json', returns: Type = None):
        return self.route(path, 'PUT', status_code=status_code, content_type=content_type, returns=returns)

    def patch(self, path: str, *, status_code: int = 200, content_type: str = 'application/json', returns: Type = None):
        return self.route(path, 'PATCH', status_code=status_code, content_type=content_type, returns=returns)

    def delete(self, path: str, *, status_code: int = 200, content_type: str = 'application/json', returns: Type = None):
        return self.route(path, 'DELETE', status_code=status_code, content_type=content_type, returns=returns)


class Router(RoutingMixin):
    def __init__(self, prefix: str = '', tags: List[str] = None):
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
