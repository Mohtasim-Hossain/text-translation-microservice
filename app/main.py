
import os, shutil, uuid, asyncio
from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect, Form, BackgroundTasks, Request, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
from dotenv import load_dotenv
from models import FileEntry, SessionHistory  # Assuming models.py is in the same directory
from database import startup_db, history_collection, db
from services import translate_file
from bson import ObjectId
import json



load_dotenv()
app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


# WebSocket clients to push real-time updates
clients = []

@app.on_event("startup")
async def on_startup():
    await startup_db()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        clients.remove(websocket)

# Utility function to send status updates via WebSocket
async def send_status_update(message: str):
    for client in clients:
        try:
            await client.send_text(message)
        except Exception as e:
            print(f"Error sending WebSocket message: {e}")
            clients.remove(client)



# Render the main HTML page
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return FileResponse("static/index.html")
    # return templates.TemplateResponse("index.html", {"request": request})



UPLOADS_DIR = "uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)  # Ensure uploads directory exists




@app.post("/upload")
async def upload_file(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...), 
    language: str = Form(...), 
    session_id: str = Form(...)
):
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are allowed")

    # Generate a unique file path to avoid collisions
    file_path = os.path.join(UPLOADS_DIR, f"{uuid.uuid4()}_{file.filename}")

    # Save the uploaded file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
     # Send WebSocket update when translation starts

    await send_status_update(f"File {file.filename} uploaded. Translation starting...")

    # Add background task to translate the file
    background_tasks.add_task(translate_file, file.filename, file_path, language, session_id)
    
    # Immediate response indicating file is uploaded and processing has started
    return {
        "message": "File uploaded successfully. Translation is in progress.",
        "file_path": file_path,
        "session_id": session_id
    }




@app.get("/download/{file_name}")
async def download_file(file_name: str):
    file_path = os.path.join(UPLOADS_DIR, file_name)  # Make sure the path is correct
    # file_path = os.path.join(UPLOADS_DIR, f"{uuid.uuid4()}_{file.filename}")
    
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type='application/octet-stream', headers={"Content-Disposition": f"attachment; filename={file_name}"})
    else:
        return JSONResponse(content={"message": "File not found"}, status_code=404)






# Custom JSON encoder to handle datetime and ObjectId
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)
    



# Serve history.html for a specific session
@app.get("/history/{session_id}", response_class=HTMLResponse)
async def view_history_page(session_id: str):
    # This serves the history.html file directly
    return FileResponse("static/history.html")




@app.get("/history_page/{session_id}")
async def get_session_history(session_id: str):
    try:
        session_data = await history_collection.find_one({"session_id": session_id})
        if not session_data:
            return JSONResponse(content={
                "session_id": session_id,
                "created_at": datetime.utcnow().isoformat(),
                "files_processed": []
            })
        
        # Convert the MongoDB document to a dictionary and serialize it
        session_dict = {
            "session_id": session_data["session_id"],
            "created_at": session_data.get("created_at", datetime.utcnow()).isoformat(),
            "files_processed": []
        }
        
        # Process files_processed array
        for file in session_data.get("files_processed", []):
            processed_file = {
                "file_name": file.get("file_name", ""),
                "file_path": file.get("file_path", ""),
                "processed_at": file.get("processed_at", datetime.utcnow()).isoformat(),
                "status": file.get("status", "UNKNOWN"),
                "result": file.get("result", None),
                "link": file.get("link", None),
            }
            session_dict["files_processed"].append(processed_file)
        
        return JSONResponse(content=session_dict)
    except Exception as e:
        print(f"Error processing history: {str(e)}")  # Add logging for debugging
        raise HTTPException(status_code=500, detail=str(e))





