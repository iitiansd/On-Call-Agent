from typing import List
from fastapi import WebSocket
from fastapi.websockets import WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        print(f"self.active_connections personal=> {len(self.active_connections)}")
        # print(f"self.active_connections{self.active_connections}")
        # print(f"self.message{message}")
        
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending message: {e}")

    async def broadcast(self, message: dict):
        # print(f"self.active_connections broadcast => {self.active_connections}")
        print(f"self.active_connections{len(self.active_connections)}")
        # print(f"self.message{message}")
        for connection in self.active_connections:
            await connection.send_json(message)
