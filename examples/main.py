from liteapi import App

app = App()


@app.get('/ping')
def ping():
    return 'pong'
