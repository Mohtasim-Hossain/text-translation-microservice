import os, asyncio
import google.generativeai as genai
from dotenv import load_dotenv
from database import db, DOWNLOADS_DIR
from datetime import datetime


# Load environment variables
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

genai.configure(api_key=GEMINI_API_KEY)

# UPLOADS_DIR = "downloads"
# os.makedirs(UPLOADS_DIR, exist_ok=True)

# Language Mapping Dictionary
LANGUAGE_MAP = {
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'zh': 'Chinese',
    'ja': 'Japanese',
    'ar': 'Arabic',
    'hi': 'Hindi',
    'pt': 'Portuguese',
    'ru': 'Russian',
    'ko': 'Korean',
    'bn': 'Bangla',
    'tr': 'Turkish',
}

async def send_status_update_(message: str):
    """
    Wrapper function to send status updates from services module
    """
    from main import send_status_update  # Local import to avoid circular dependency
    await send_status_update(message)


async def translate_file(file_name: str, file_path: str, language: str, session_id: str):
    """
    Translate file content using Gemini API, save translation in MongoDB, and generate downloadable file.

    Args:
        file_path (str): Path to the original file
        language (str): Target language code
        session_id (str): Session identifier
    """
    try:
        # Read original file content
        with open(file_path, 'r', encoding='utf-8') as file:
            original_text = file.read()
        
        # Validate language
        target_language = LANGUAGE_MAP.get(language.lower(), language.capitalize())
        
        # Prepare translation prompt
        translation_prompt = f"Translate the following text to {target_language} language:\n\n{original_text}"
        
        # Send status update that translation is starting
        await send_status_update_(f"Translation started for {os.path.basename(file_path)} to {target_language}...")

        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Generate translation
        translated_text = model.generate_content(translation_prompt)
        if translated_text and translated_text.text:
           print("translated")
        else:
            print("Some error occured")


        status = "COMPLETE"
        # Extract translated text
        if not translated_text.text:
            status = "unknown"
            raise ValueError("Translation response returned empty content.")
            
        
        # Create translated file path
        translated_file_path = os.path.join(DOWNLOADS_DIR, os.path.basename(file_path).replace(".txt", f"_{language}_translated.txt"))
        
        # Write translated content to new file
        with open(translated_file_path, 'w', encoding='utf-8') as translated_file:
            translated_file.write(translated_text.text)
       

        # Generate the download link
        download_link = f"/download/{os.path.basename(translated_file_path)}"
     
        
        # Save translated content in MongoDB
        file_entry = {
            "data": original_text,
            "file_name": file_name,
            "file_path": file_path,
            "processed_at": datetime.utcnow(),
            "result": translated_text.text,
            "status": status,
            "link": download_link
        }
        
        # Check if session already exists and update it, or create a new one
        existing_session = await db.session_history.find_one({"session_id": session_id})
        if existing_session:
            await db.session_history.update_one(
                {"session_id": session_id},
                {"$push": {"files_processed": file_entry}}
            )
        else:
            await db.session_history.insert_one({
                "session_id": session_id,
                "created_at": datetime.utcnow(),
                "files_processed": [file_entry]
            })
        
        
        
        # await send_status_update(f"Translation completed for {os.path.basename(file_path)}. You can download the translated file here: {download_link}")
        await send_status_update_(f"Translation completed: {download_link}")

    
    except Exception as e:
        # If an error occurs, notify the frontend about failure
        print(f"Translation error: {e}")
        # If an error occurs, notify the frontend about failure
        error_message = f"Translation failed for {os.path.basename(file_path)}. Error: {str(e)}"
        await send_status_update_(error_message)
        
        # Update session history in MongoDB as failed
        await db.session_history.update_one(
            {"session_id": session_id},
            {"$set": {"files_processed.$.result": "Failed", "files_processed.$.error_message": str(e)}}
        )
        raise



# Helper function to update translation status in MongoDB
async def update_translation_status(
    session_id: str, 
    translated_file_path: str = None, 
    status: str = "Completed",
    error_message: str = None
):
    """
    Update the translation status in the session history
    
    Args:
        session_id (str): Session identifier
        translated_file_path (str, optional): Path to translated file
        status (str, optional): Translation status
        error_message (str, optional): Error details if translation failed
    """
    update_data = {
        "files_processed.$.result": status
    }
    
    if translated_file_path:
        update_data["files_processed.$.translated_file_path"] = translated_file_path
    
    if error_message:
        update_data["files_processed.$.error_message"] = error_message
    
    await db.session_history.update_one(
        {"session_id": session_id},
        {"$set": update_data}
    )

# Optional: Language detection function
async def detect_language(text: str) -> str:
    """
    Detect the language of the input text
    
    Args:
        text (str): Input text to detect language
    
    Returns:
        str: Detected language code
    """
    try:
        model = genai.GenerativeModel('gemini-pro')
        prompt = f"Detect the language of the following text and return the 2-letter ISO code:\n\n{text}"
        
        response = await asyncio.to_thread(
            model.generate, 
            prompt=prompt
        )
        
        detected_language = response.get('text', '').strip().lower()
        return detected_language
    
    except Exception as e:
        print(f"Language detection error: {e}")
        return 'en'  # Default to English if detection fails
