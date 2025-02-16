from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import json
import dotenv

from litellm import completion

dotenv.load_dotenv()

SYSTEM_PROMPT = """
You are answering questions to a user using html.
You will respond using valid html code.
Your code gets rendered in real time to a user.
It should be helpful and contain the answer to their question.
You might also be given the previous history of the conversation, consider it in your response.
Do not include any other text than the html. Do not add ```html or ``` when responding.
Don't be afraid to be creative.
Add easter eggs from time to time.
The html will be directly rendered to the user.
Include any css in the html directly.
"""

def get_response(message, raw_html):
    response = completion(
        model="openai/gpt-4o-mini",
        messages=[
            {"content": SYSTEM_PROMPT, "role": "system"},
            {"content": raw_html,"role": "assistant"},
            {"content": message,"role": "user"},
        ],
        stream=True,
    )
    return response

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

            # Parse the JSON payload
            payload = json.loads(data)
            message = payload['message']
            raw_html = payload['html']
            history = payload.get('history', [])  # Get conversation history

            messages = [
                {"content": SYSTEM_PROMPT, "role": "system"},
                *history,
                {"content": raw_html, "role": "assistant"},
                {"content": message, "role": "user"},
            ]

            # Get response using the message, raw HTML, and history
            response = completion(
                model="openai/gpt-4o-mini",
                messages=messages,
                stream=True,
            )

            # Send response back to client
            for chunk in response:
                if chunk.choices[0].delta.content:
                    await websocket.send_text(chunk.choices[0].delta.content)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        active_connections.remove(websocket)

# Mount static files after the WebSocket route
app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)