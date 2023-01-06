from examples.main import app
from liteapi import Router

first_router = Router('/first')
second_router = Router()


@app.get('/hello')
def hello_from_root():
    return 'hello from /hello'


@first_router.get('/hello')
def hello_from_first():
    return 'hello from /first/hello'


@second_router.get('/hello')
def hello_from_second():
    return 'hello from /second/hello'


app.add_router(first_router)
app.add_router(second_router, prefix='/second')
