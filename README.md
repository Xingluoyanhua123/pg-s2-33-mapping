# pg-s2-33-mapping

## Voice Credit Mapping Prototype

A React + FastAPI credit-mapping prototype with two-way voice interaction.

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
- Mute and volume controls

## Example Conversation

The following examples describe the original prototype workflow.
Available commands and responses depend on the current backend configuration and course data.

1. Click **Start Conversation**.
2. Say: `Map Database Systems`.
3. The assistant identifies a course and asks for confirmation.
4. Say: `Yes`.
5. The mapping is created and the assistant reads the result aloud.

Other example commands:

- `Map MATH101`
- `Map Programming Fundamentals`
- `List courses`
- `Show mappings`
- `Help`
- `Yes`
- `No`

Prototype results are not official university credit decisions.

## Run the Backend

Open a PowerShell terminal in the project root:

```powershell
cd backend
```

If `.venv` does not already exist, create a Python 3.11 virtual environment:

```powershell
py -3.11 -m venv .venv
```

Install dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Start FastAPI:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Backend address:

http://127.0.0.1:8000

Swagger API documentation:

http://127.0.0.1:8000/docs

If the backend uses a local model or external data files, configure those dependencies before testing the relevant features.

## Run the Frontend

Open a second PowerShell terminal in the project root:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Default frontend address:

http://localhost:5173

If this port is occupied, use the address shown in the terminal.

Use Microsoft Edge or Google Chrome and allow microphone access for voice interaction.

## Architecture

The browser handles voice input and playback. The React frontend sends requests to the FastAPI backend, where the controller, service, and repository layers handle application logic and data access.

- **Frontend:** user interface, voice input, conversation history, and speech playback.
- **Controller:** receives API requests and returns responses.
- **Service:** processes commands and manages conversation state.
- **Repository:** provides access to course and mapping data.

For the current API endpoints and request formats, see the running backend's Swagger documentation.

## Model Integration

Model integration details depend on the backend version and configuration.

When running a version connected to Hermes or another local LLM, ensure the required model service is running and accessible to the backend.

## Deployment

The frontend API configuration supports this environment variable:

```text
VITE_API_BASE_URL
```

The local backend address is:

```text
http://127.0.0.1:8000
```

For a deployed frontend, set `VITE_API_BASE_URL` to the public FastAPI backend URL and configure the backend to allow requests from the frontend's origin.

Do not store passwords or secret API keys in `VITE_` variables, because they are exposed to the browser.

## Security

Do not commit:

- `.env` files containing secrets
- API keys or passwords
- Python virtual environments such as `.venv`
- `node_modules`
- Private student records or other sensitive data

Use `.gitignore` to exclude local environment files and generated dependencies.