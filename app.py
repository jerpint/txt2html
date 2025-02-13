from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import html

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active WebSocket connections
active_connections = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            # Process the message (you can add your HTML generation logic here)
            response_html = f"<div class='message'>{html.escape(data)}</div>"

            # Send response back to client
            await websocket.send_text(response_html)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        active_connections.remove(websocket)

# Mount static files after the WebSocket route
app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)