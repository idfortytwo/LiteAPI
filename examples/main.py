import os
from typing import List, Optional, Dict

from pydantic import BaseModel

from liteapi import App, Router, RequestMiddleware, ResponseMiddleware

app = App()


@app.get('/positional_and_query/{pos1}/{pos2}')
def positional_and_query(
        pos1: str,
        pos2: int,
        query1: float,
        query2: str):
    return {
        'first positional': pos1,
        'second positional': pos2,
        'first query': query1,
        'second query': query2
    }


class TestModel(BaseModel):
    some_string: str
    some_float: float
    optional_str: str = 'default value'
    numbers: List[int]


@app.post('/json_to_pydantic')
def json_to_pydantic(value: TestModel):
    return {
        'test_model': value.dict()
    }


class RequiredModel(BaseModel):
    required_field: str
    optional_field: Optional[str] = 'optional field'


@app.post('/validate_input', content_type='text/plain')
def validate_input(
    required_param: str,
    required_model: RequiredModel,
    optional_param: str = 'optional value'
):
    print(required_param)
    print(required_model)
    print(optional_param)

    return 'ok'


@app.post('/upload', content_type='text/plain')
async def files_and_form_data(
        filename1: str,
        filename2: str,
        file1: bytes,
        file2: bytes
):
    os.makedirs('downloaded', exist_ok=True)

    if file1:
        with open(f'downloaded/{filename1}.png', 'wb') as f1:
            f1.write(file1)
    if file2:
        with open(f'downloaded/{filename2}.png', 'wb') as f2:
            f2.write(file2)

    return f'saved files: {[f1.name, f2.name]}'


@app.get('/download', content_type='image/png')
async def download_image(image_name: str = 'a'):
    with open(f'downloaded/{image_name}.png', 'rb') as f:
        resp = []
        while chunk := f.read(1024):
            resp.append(chunk)
        return resp


model_router = Router('/models')


@model_router.get('/model-output', content_type='application/json')
def single_model() -> TestModel:
    return TestModel(some_string='some_string', some_float=3.14, numbers=[1, 2, 3])


@model_router.get('/list-output', content_type='application/json', returns=List[TestModel])
def model_list() -> List[TestModel]:
    return [
        TestModel(some_string='some_string', some_float=3.14, numbers=[1, 2, 3]),
        TestModel(some_string='some_string', some_float=6.28, numbers=[2, 4, 6])
    ]


@model_router.get('/mixed-output', content_type='application/json')
def mixed_model_dict() -> Dict:
    return {
        'models': [
            TestModel(some_string='some_string', some_float=3.14, numbers=[1, 2, 3]),
            TestModel(some_string='some_string', some_float=6.28, numbers=[2, 4, 6])
        ],
        'count': 2
    }


html_router = Router('/html')
json_router = Router('/json')
text_router = Router()


@html_router.get('/hello1', content_type='text/html')
def hello_html():
    return '<h1>hello in HTML</h1>', 201


@json_router.patch('/hello2', content_type='application/json')
def hello_json():
    return {'text': 'hello in JSON'}, 202


@text_router.delete('/hello3', content_type='text/plain')
def hello_text():
    return 'hello in plaintext', 203


app.add_router(html_router)
app.add_router(json_router)
app.add_router(text_router, prefix='/plaintext')
app.add_router(model_router)


class LogPath(RequestMiddleware):
    async def handle(self, request):
        print(f'path: {request.path}')
        return request


class AddCORS(ResponseMiddleware):
    async def handle(self, response):
        response.add_header('Access-Control-Allow-Origin', '*')
        return response


app.add_middleware(LogPath())
app.add_middleware(AddCORS())
