# from fastapi import FastAPI, WebSocket

# app = FastAPI()


# @app.websocket("/ws/simple")
# async def simple_ws(websocket: WebSocket):
#     await websocket.accept()
#     await websocket.send_text("Hello!")
#     await websocket.close()


# if __name__ == "__main__":
#     import uvicorn

#     uvicorn.run(app, host="127.0.0.1", port=8000)
