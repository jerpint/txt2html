import os
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import json
import dotenv

from litellm import completion

dotenv.load_dotenv()

deployed_env = os.getenv("DEPLOYED_ENV", False) == "true" # Check if we're in production

SYSTEM_PROMPT = """
You are answering questions to a user using html.
You will respond using valid html code.
Your code gets rendered in real time to a user.
It should be helpful and contain the answer to their question.
You might also be given the previous history of the conversation, consider it in your response.
Do not include any other text than the html. Do not add ```html or ``` when responding.
Change the layout and style of the html to be more appealing.
Ignore the html styling on the first message as its just an example.
You have about half a page-width to work with.
Don't be afraid to be creative.
The html will be directly rendered to the user.
Include any css in the html directly.
"""

model = "openai/gpt-4o-mini"

if model.startswith("openai/"):
    assert os.getenv("OPENAI_API_KEY"), "OPENAI_API_KEY is not set"

def get_response(message, raw_html):
    response = completion(
        model=model,
        messages=[
            {"content": SYSTEM_PROMPT, "role": "system"},
            {"content": raw_html,"role": "assistant"},
            {"content": message,"role": "user"},
        ],
        stream=True,
    )
    return response

app = FastAPI()

# Set allowed origins based on the environment, by default we're in development
if deployed_env:
    allowed_origins = [
        "https://www.jerpint.io",
    ]
else:
    allowed_origins = [
        "http://localhost:4000",
    ]

print(f"Allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "CONNECT"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Upgrade",
        "Connection",
        "Sec-WebSocket-Key",
        "Sec-WebSocket-Version",
        "Sec-WebSocket-Extensions",
        "Sec-WebSocket-Protocol"
    ],
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
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=not deployed_env)
