from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload

# OAuth tabanlı kullanıcı kimliği ile Drive erişimi
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
CREDENTIALS_FILE = "credentials.json"   # OAuth client
TOKEN_FILE = "token.json"               # Kullanıcı token'ı

OPENCLAW_GOOGLEDRIVE_FOLDER_ID = "YOUR_DRIVE_FOLDER_ID"


def get_drive_service():
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise RuntimeError("Geçersiz veya yenilenemeyen Drive kimlik bilgileri")
    service = build("drive", "v3", credentials=creds)
    return service


app = FastAPI(title="OpenClaw Google Drive Bridge (OAuth)")


class FileCreateRequest(BaseModel):
    name: str
    content: str
    mimeType: Optional[str] = "text/plain"
    overwrite: Optional[bool] = True


class FileInfo(BaseModel):
    id: str
    name: str


class FileListResponse(BaseModel):
    files: List[FileInfo]


class FileContentResponse(BaseModel):
    id: str
    name: str
    mimeType: str
    content: str


def find_file_in_folder_by_name(service, name: str) -> Optional[dict]:
    query = (
        f"'{OPENCLAW_GOOGLEDRIVE_FOLDER_ID}' in parents and "
        f"name = '{name.replace("'", "\\'")}' and "
        "trashed = false"
    )
    results = service.files().list(
        q=query,
        fields="files(id, name)",
        spaces="drive",
    ).execute()
    files = results.get("files", [])
    return files[0] if files else None


@app.post("/files", response_model=FileContentResponse)
def create_or_update_file(req: FileCreateRequest):
    try:
        service = get_drive_service()

        existing = None
        if req.overwrite:
            existing = find_file_in_folder_by_name(service, req.name)

        data = req.content.encode("utf-8")
        media = MediaInMemoryUpload(data, mimetype=req.mimeType, resumable=False)

        file_metadata = {
            "name": req.name,
            "parents": [OPENCLAW_GOOGLEDRIVE_FOLDER_ID],
        }

        if existing and req.overwrite:
            file_id = existing["id"]
            file = service.files().update(
                fileId=file_id,
                media_body=media,
            ).execute()
        else:
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields="id, name, mimeType, parents",
            ).execute()

        file_id = file["id"]
        downloaded = service.files().get_media(fileId=file_id).execute()

        return FileContentResponse(
            id=file_id,
            name=file["name"],
            mimeType=file.get("mimeType", req.mimeType),
            content=downloaded.decode("utf-8", errors="ignore"),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/files", response_model=FileListResponse)
def list_files(name_contains: Optional[str] = None):
    try:
        service = get_drive_service()

        q = f"'{OPENCLAW_GOOGLEDRIVE_FOLDER_ID}' in parents and trashed = false"
        if name_contains:
            q += f" and name contains '{name_contains.replace("'", "\\'")}'"

        results = service.files().list(
            q=q,
            fields="files(id, name)",
            spaces="drive",
        ).execute()
        files = results.get("files", [])

        return FileListResponse(
            files=[FileInfo(id=f["id"], name=f["name"]) for f in files]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/files/{file_id}", response_model=FileContentResponse)
def get_file(file_id: str):
    try:
        service = get_drive_service()

        file = service.files().get(fileId=file_id, fields="id, name, mimeType, parents").execute()

        parents = file.get("parents", [])
        if OPENCLAW_GOOGLEDRIVE_FOLDER_ID not in parents:
            raise HTTPException(status_code=403, detail="Bu klasöre erişim yok")

        data = service.files().get_media(fileId=file_id).execute()
        content = data.decode("utf-8", errors="ignore")

        return FileContentResponse(
            id=file["id"],
            name=file["name"],
            mimeType=file.get("mimeType", "text/plain"),
            content=content,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
