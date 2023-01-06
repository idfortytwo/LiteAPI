from examples.main import app
from liteapi import Router
from liteapi.responses import HTMLResponse, JSONResponse, PlainResponse

implicit = Router('/implicit')
explicit = Router('/explicit')


@implicit.get('/hello1', content_type='text/html')
def hello_html():
    return '<h1>hello in HTML</h1>'


@implicit.patch('/hello2', content_type='application/json')
def hello_json():
    return {'text': 'hello in JSON'}, 201


@implicit.delete('/hello3', content_type='text/plain', status_code=202)
def hello_text():
    return 'hello in plaintext'


@explicit.get('/hello1')
def hello_html():
    return HTMLResponse('<h1>hello in HTML</h1>')


@explicit.patch('/hello2')
def hello_json():
    return JSONResponse({'text': 'hello in JSON'}, 201)


@explicit.delete('/hello3', status_code=202)
def hello_text():
    return PlainResponse('hello in plaintext', 202)


app.add_router(implicit)
app.add_router(explicit)
