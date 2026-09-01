# Voice Credit Mapping Prototype - Voice Interaction v2

This is the original React + FastAPI credit-mapping prototype upgraded with two-way voice interaction.

## Features

- React frontend
- FastAPI backend
- REST API
- Controller / Service / Repository architecture
- Logging
- Course mapping prototype
- Speech-to-Text
- Text-to-Speech
- Continuous conversation mode
- Multi-turn confirmation (`Yes` / `No`)
- Conversation history
- Browser `localStorage` session ID
- Text input fallback
- Future integration point for Hermes / a local LLM

## Example conversation

1. Click **Start Conversation**.
2. Say: `Map Database Systems`.
3. The assistant says it found DB201 and asks whether to add the suggested mapping.
4. Say: `Yes`.
5. The mapping is created and the assistant reads the result aloud.

You can also say:

- `Map MATH101`
- `Map Programming Fundamentals`
- `List courses`
- `Show mappings`
- `Help`
- `Yes`
- `No`

## Run backend in VS Code

Open a terminal in the project directory:

```powershell
cd backend
```

Use your existing Python 3.11 virtual environment, or create one if needed.

Install dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Start FastAPI:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Backend:

```text
http://127.0.0.1:8000
```

Swagger API documentation:

```text
http://127.0.0.1:8000/docs
```

## Run frontend

Open a second terminal:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Open:

```text
http://localhost:5173
```

Use Microsoft Edge or Google Chrome and allow microphone access.

## Architecture

```text
Microphone
   ↓
Browser Speech-to-Text
   ↓
React Frontend
   ↓
POST /api/voice-command
   ↓
FastAPI Controller
   ↓
MappingService + Conversation State
   ↓
Repository
   ↓
Mapping Result
   ↓
React Frontend
   ↓
Browser Text-to-Speech
   ↓
Speaker
```

## Where to add Hermes / Local LLM later

The current intent recognition is in:

```text
backend/app/service.py
```

Specifically:

```python
interpret_voice_command()
```

At the moment this method uses simple rules. Later it can call Hermes / a local LLM and receive structured output such as:

```json
{
  "action": "create_mapping",
  "course_code": "DB201",
  "requires_confirmation": true
}
```

The rest of the API / Service / Repository architecture can remain largely unchanged.

## Deployment

`frontend/src/api.js` supports:

```text
VITE_API_BASE_URL
```

For local development it automatically falls back to:

```text
http://127.0.0.1:8000
```

For a deployed frontend, set `VITE_API_BASE_URL` to the public FastAPI backend URL.
