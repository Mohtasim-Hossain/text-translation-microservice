from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId

class FileEntry(BaseModel):
    data: str
    file_name: str
    file_path: str
    processed_at: datetime
    result: str
    status: str

class SessionHistory(BaseModel):
    session_id: str = Field(...)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    files_processed: list[FileEntry] = []
