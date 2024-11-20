# from fastapi import FastAPI, WebSocket, BackgroundTasks, UploadFile, Form
# from fastapi.responses import FileResponse, HTMLResponse
# from fastapi.staticfiles import StaticFiles
# from motor.motor_asyncio import AsyncIOMotorClient
# from uuid import uuid4
# from datetime import datetime
# import os, asyncio
# from dotenv import load_dotenv
# from .services import translate_file_with_gemini  # Import the translation function

# # app.mount("/static", StaticFiles(directory="static"), name="static")


# load_dotenv()

# app = FastAPI()

# # Initialize MongoDB
# client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
# db = client["translation_service"]

# # Serve static files
# app.mount("/static", StaticFiles(directory="static"), name="static")

# @app.get("/", response_class=HTMLResponse)
# async def home():
#     return FileResponse("static/index.html")

# @app.get("/history", response_class=HTMLResponse)
# async def history_page():
#     return FileResponse("static/history.html")

# @app.post("/upload")
# async def upload_file(
#     file: UploadFile, language: str = Form(...), session_id: str = Form(...), background_tasks: BackgroundTasks = BackgroundTasks()
# ):
#     # Save file temporarily
#     file_path = f"temp/{uuid4()}_{file.filename}"
#     with open(file_path, "wb") as f:
#         f.write(await file.read())

#     # Store initial entry in MongoDB
#     entry = {
#         "sessionId": session_id,
#         "fileName": file.filename,
#         "filePath": file_path,
#         "createdAt": datetime.now(),
#         "status": "In Progress",
#         "result": None
#     }
#     await db.files.insert_one(entry)

#     # Add background translation task
#     background_tasks.add_task(perform_translation, file_path, language, session_id)

#     return {"message": "File uploaded successfully, translation in progress"}

# async def perform_translation(file_path: str, language: str, session_id: str):
#     """
#     Background task to perform file translation and update the database.
#     """
#     try:
#         translated_file_url = await translate_file_with_gemini(file_path, language)
#         # Update the database with the translated file URL and status
#         await db.files.update_one(
#             {"sessionId": session_id, "filePath": file_path},
#             {"$set": {"status": "Completed", "result": translated_file_url}}
#         )
#     except Exception as e:
#         await db.files.update_one(
#             {"sessionId": session_id, "filePath": file_path},
#             {"$set": {"status": "Failed", "error": str(e)}}
#         )

# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     try:
#         while True:
#             # This could be extended to check and send real-time updates from MongoDB
#             await websocket.send_text("Translation in progress...")
#             await asyncio.sleep(1)  # Simulating progress update
#             await websocket.send_text("Translation completed")
#             await websocket.close()
#             break
#     except Exception as e:
#         await websocket.send_text(f"Error: {str(e)}")
#         await websocket.close()


import os
import asyncio
from uuid import uuid4
from datetime import datetime

from fastapi import FastAPI, WebSocket, BackgroundTasks, UploadFile, Form, HTTPException, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import ssl
from .services import translate_file_with_gemini

load_dotenv()

# # Create a custom SSL context
# ssl_context = ssl.create_default_context()
# ssl_context.check_hostname = True
# ssl_context.verify_mode = ssl.CERT_REQUIRED

# # Initialize FastAPI app
app = FastAPI()

uri = os.getenv("MONGODB_URI")
print(uri)
# MongoDB Connection
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["translation_service"]

# Ensure temp and translated directories exist
os.makedirs("temp", exist_ok=True)
os.makedirs("translated", exist_ok=True)

# Ensure MongoDB is reachable on startup
# @app.on_event("startup")
# async def startup_db_client():
#     try:
#         # Attempt a simple ping to test the MongoDB connection
#         await client.admin.command('ping')
#         print("Successfully connected to MongoDB!")
#     except Exception as e:
#         print(f"Failed to connect to MongoDB: {e}")
#         raise HTTPException(status_code=500, detail="Database connection failed")

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)


# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home():
    return FileResponse("static/index.html")

@app.get("/history", response_class=HTMLResponse)
async def history_page():
    return FileResponse("static/history.html")

@app.get("/fetch-history")
async def fetch_history(session_id: str):
    # Retrieve translation history for the specific session
    history = await db.files.find({"sessionId": session_id}).to_list(length=100)
    
    # Convert MongoDB documents to a JSON serializable format
    formatted_history = []
    for item in history:
        formatted_item = {
            "fileName": item.get("fileName"),
            "status": item.get("status"),
            "createdAt": item.get("createdAt").isoformat() if item.get("createdAt") else None,
            "filePath": item.get("result")  # This will be the download link
        }
        formatted_history.append(formatted_item)
    
    return JSONResponse(formatted_history)

@app.post("/upload")
async def upload_file(
    file: UploadFile, 
    language: str = Form(...), 
    session_id: str = Form(...), 
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    # Validate file type
    if not file.filename.lower().endswith('.txt'):
        raise HTTPException(status_code=400, detail="Only .txt files are allowed")

    # Save file temporarily
    file_path = f"temp/{uuid4()}_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Store initial entry in MongoDB
    entry = {
        "sessionId": session_id,
        "fileName": file.filename,
        "filePath": file_path,
        "createdAt": datetime.now(),
        "status": "Received",
        "result": None
    }
    await db.files.insert_one(entry)

    # Add background translation task
    background_tasks.add_task(perform_translation, file_path, language, session_id)
    
    return {"message": "File uploaded successfully, translation in progress"}

async def perform_translation(file_path: str, language: str, session_id: str):
    """
    Background task to perform file translation and update the database.
    """
    try:
        # Update status to translating
        await db.files.update_one(
            {"sessionId": session_id, "filePath": file_path},
            {"$set": {"status": "Translating"}}
        )

        # Perform translation
        translated_content = await translate_file_with_gemini(file_path, language)

        # Create translated file
        original_filename = os.path.basename(file_path)
        translated_filename = f"translated/{os.path.splitext(original_filename)[0]}_translated.txt"
        with open(translated_filename, "w") as f:
            f.write(translated_content)

        # Update the database with the translated file path and status
        await db.files.update_one(
            {"sessionId": session_id, "filePath": file_path},
            {"$set": {
                "status": "Completed", 
                "result": translated_filename
            }}
        )
    except Exception as e:
        # Update database with error status
        await db.files.update_one(
            {"sessionId": session_id, "filePath": file_path},
            {"$set": {
                "status": "Failed", 
                "error": str(e)
            }}
        )

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        # Send status updates
        await websocket.send_text("Connection established")
        await websocket.send_text("Waiting for file upload")
        
        while True:
            # This could be extended to fetch real-time updates from MongoDB
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        await websocket.close()
    except Exception as e:
        await websocket.send_text(f"Error: {str(e)}")
        await websocket.close()



# from pymongo.mongo_client import MongoClient
# from pymongo.server_api import ServerApi

# # uri = "mongodb+srv://mohtasimhossain:<db_password>@cluster0.51p8c.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# # Create a new client and connect to the server
# client = MongoClient(uri, server_api=ServerApi('1'))

# # Send a ping to confirm a successful connection
# try:
#     client.admin.command('ping')
#     print("Pinged your deployment. You successfully connected to MongoDB!")
# except Exception as e:
#     print(e)


# async def save_session_history(session_id: str, file_entry: FileEntry):
#     session_history = {
#         "session_id": session_id,
#         "created_at": datetime.utcnow(),
#         "files_processed": [file_entry.dict()]
#     }

#     # Insert session history into MongoDB (await the insertion)
#     result = await db.session_history.insert_one(session_history)
    
#     # Return the result of the insert operation, which includes the _id field
#     return result


# # Update the translation status of a file in the session history
# async def update_translation_status(session_id: str, translated_file_path: str):
#     history_collection.update_one(
#         {"session_id": session_id, "files_processed.file_path": translated_file_path},
#         {"$set": {"files_processed.$.result": "Completed"}}
#     )
