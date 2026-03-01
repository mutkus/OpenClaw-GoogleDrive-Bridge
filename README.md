# OpenClaw-GoogleDrive-Bridge
A lightweight FastAPI bridge that lets an OpenClaw agent securely read and write notes/scripts to your personal Google Drive using OAuth 2.0 (drive.file scope). Designed for self‑hosted AI assistants that need structured, file‑based memory in Drive.
This project is a small **FastAPI bridge** that lets an **OpenClaw agent** read and write notes/scripts to your **personal Google Drive** using OAuth 2.0.

# Blog Link: 
https://www.mutkus.com/nedir/ai/openclawi-kisisel-google-driveiniza-baglamak/ 

The goal:

> Give your agent commands like "save this note to Drive", "write this script and store it in Drive", "open yesterday's note and summarize it".

## Features

- `POST /files` – create or update a file under a specific Drive folder
- `GET /files` – list files under that folder (optionally filter by name)
- `GET /files/{id}` – fetch file content
- Auth:
  - Uses a **Desktop OAuth client** + `token.json` (your Google account)
  - Scope: `https://www.googleapis.com/auth/drive.file` (only files created/opened by this app)

## Repo structure

```text
OpenClaw-GoogleDrive-Bridge/
  ├── main.py             # FastAPI app + Drive integration
  ├── requirements.txt    # Python dependencies
  ├── README.md           # (this file)
  └── .gitignore          # ignore venv and secrets
```

> Important: keep `credentials.json` and `token.json` **out of Git**.

## Setup

### 1) Clone & install

```bash
git clone https://github.com/<your-user>/OpenClaw-GoogleDrive-Bridge.git
cd OpenClaw-GoogleDrive-Bridge

python3 -m venv .venv
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -r requirements.txt
```

### 2) Enable Google Drive API & create OAuth client

In Google Cloud Console:

1. Create/select a project.
2. Enable **Google Drive API**.
3. Configure **OAuth consent screen** (External, add your Gmail as test user).
4. Create **OAuth client ID** (Application type: **Desktop app**).
5. Download the JSON and save it next to your code as `credentials.json`.

### 3) Generate `token.json`

On a trusted local machine:

1. Put `credentials.json` and `get_token.py` in the same folder.
2. Run:

```bash
python3 get_token.py
```

3. A browser window will open; log in with the Google account you want to use.
4. After granting permission, a `token.json` file is created.
5. Copy both files to your server:

```bash
scp credentials.json token.json user@server:/path/to/OpenClaw-GoogleDrive-Bridge/
```

### 4) Configure folder ID

Create a folder in Google Drive (e.g. "OpenClaw Files") and copy its ID from the URL:

```python
OPENCLAW_GOOGLEDRIVE_FOLDER_ID = "YOUR_DRIVE_FOLDER_ID"
```

Update this constant in `main.py`.

### 5) Run the server

```bash
cd OpenClaw-GoogleDrive-Bridge
./.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
```

You can now open `http://<server-ip>:8000/docs` to try the API.

## API examples

### Create or update a file

```bash
curl -X POST "http://localhost:8000/files" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-note.txt",
    "content": "Hello from OpenClaw-GoogleDrive-Bridge!",
    "mimeType": "text/plain",
    "overwrite": true
  }'
```

### List files

```bash
curl "http://localhost:8000/files"
```

### Get file content

```bash
curl "http://localhost:8000/files/<file_id>"
```

## .gitignore

Make sure your `.gitignore` includes at least:

```gitignore
.venv/
__pycache__/
credentials.json
token.json
service-account.json
*.pyc
```

## License

Use any license you prefer (MIT is a good default).
