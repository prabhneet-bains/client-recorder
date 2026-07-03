# Physio Scribe Web Recorder

This repository now includes a browser-based recording frontend and a lightweight Flask proxy backend so you can host the recorder for free and stream audio to your GPU server.

## What it contains

- `client_recorder.py` — existing Python CLI recorder.
- `app.py` — Flask app that serves the frontend and proxies chunk uploads and finalization requests.
- `static/index.html` — polished web UI.
- `static/style.css` — modern dark theme.
- `static/app.js` — browser recorder logic.
- `requirements.txt` — dependencies for the Flask app.

## Local run

1. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

2. Start the app:

```bash
python app.py
```

3. Open `http://127.0.0.1:5000` in your browser.

## Free hosting

### Option 1: Render.com

1. Create a free account at https://render.com.
2. Connect your repository.
3. Create a new Web Service.
4. Set the build and start commands:

```bash
pip install -r requirements.txt
python app.py
```

5. Add environment variables:

- `BACKEND_URL` — your GPU server public URL, e.g. `https://impulse-perfume-afterlife.ngrok-free.dev`
- `API_KEY` — your existing API key.

6. Deploy.

### Option 2: Railway.app

Railway also supports free Python web services and works the same way.

## How it works

- The browser records audio using the microphone.
- Each 30-second chunk is uploaded automatically through `/append_chunk`.
- Once finished, press `Finalize notes` and the app requests `/finalize_session`.
- The Flask backend proxies these requests to your configured `BACKEND_URL` with the API key.

## Notes

- If your backend does not support cross-origin requests, this proxy backend avoids CORS issues.
- You can still use `client_recorder.py` as a command-line client if you prefer.

## Quick command

```bash
python app.py
```
