from typing import List
import motor.motor_asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from mongodb import Mongo, chat_collection
import json
app = FastAPI()
templates = Jinja2Templates(directory="templates")

def helper(data) -> dict:
    id_value = str(data['_id'])
    old_key = "_id"
    data.pop(old_key)
    new_dict = {'id': id_value} 
    data = {**new_dict, **data}
    
    return data

db = Mongo(chat_collection, helper)


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()

# class Message(BaseModel):
#     username: str
#     message: str

@app.get("/{username}")
async def get(request: Request, username: str,response_class=HTMLResponse):
    chat = await db.get(limit=20, offset=0, query={})
    print(chat)
    client_host = str(request.url)
    host = str(client_host.rsplit('/',1)[0])
    if host == 'http://127.0.0.1:8000':
        host = host.replace("http://","") 
    else:
        host = host.replace("https://","") 

    return templates.TemplateResponse("index.html", {"request": request, "username": username, 'chat': chat['data'], 'host': host})


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            data = json.loads(data)
            # add data to mongodb
            await db.add(data)
            # await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"{client_id}: {data['message']}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")