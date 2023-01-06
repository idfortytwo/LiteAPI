from examples.main import app
from liteapi import Router
from liteapi.middleware import PostMiddleware, PreMiddleware
from liteapi.requests import Request
from liteapi.responses import PlainResponse


class PathLogger(PreMiddleware):
    async def preprocess(self, request: Request):
        print(f'path: {request.scope.path}')
        return request


class AddCORS(PostMiddleware):
    async def postprocess(self, response):
        response.add_header('Access-Control-Allow-Origin', '*')
        return response


class MagicGuard(PreMiddleware):
    def __init__(self, magic_code: str):
        self.magic_code = magic_code

    async def preprocess(self, request: Request):
        if request.scope.headers.get('magic_code', None) != self.magic_code:
            return PlainResponse('You shall not pass!', 401)
        return request


log_path = PathLogger()
cors = AddCORS()
guard = MagicGuard('123')

logged_router = Router('/logged')
logged_router.add_middleware(log_path)
app.add_middleware(cors)


@logged_router.get('/{pos_input}')
def cors_and_logged(pos_input: str):
    return f'Received: {pos_input}'


@guard
@app.get('/magic')
def enter_with_magic():
    return 'Passage granted'
