from fastapi.responses import JSONResponse
from fastapi import FastAPI, Request
import uvicorn

app = FastAPI()

@app.post('/img/get-resul')
async def getResult(request: Request):
    userByteData = await request.body()

    return JSONResponse(content={"overlayImageBase64": imgBase64})

if __name__ == '__main__':
    uvicorn.run('serverSide:app', host='localhost', reload=True, port=8080, workers=10)