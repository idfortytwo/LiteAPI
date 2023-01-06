import os

from examples.main import app
from liteapi import Router

image_router = Router('/images')


@image_router.post('/upload', content_type='text/plain')
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


@image_router.get('/download', content_type='image/png')
async def download_image(image_name: str = 'a'):
    with open(f'downloaded/{image_name}.png', 'rb') as f:
        resp = []
        while chunk := f.read(1024):
            resp.append(chunk)
        return resp


app.add_router(image_router)
