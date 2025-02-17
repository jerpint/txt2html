> Note: This is a fork of https://no-gravity.github.io/html_editor/

# txt2html

This is an experimental UI for LLMs.

It can only respond with html, which gets rendered in real-time to the user.

The backend is a simple FastAPI app that uses gpt-4o-mini.

## Usage

1. Clone the repo
2. Install dependencies: `pip install -r requirements.txt`
2. Run the backend:  `uv run python app.py`
3. Open `index.html` in your browser

> You need to set the `OPENAI_API_KEY` environment variable.