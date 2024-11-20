# Text Translation Microservice

This project is a translation microservice built with **FastAPI**, **MongoDB Atlas**, **Gemini AI**, and **WebSockets**. It enables users to upload text files, select a target language, and receive the translated content as a downloadable file. The project includes real-time updates on the status of each translation session, displaying stages like file upload, translation in progress, and completion.

## Features

- **File Upload**: Upload `.txt` files for translation.
- **Language Translation**: Specify a target language for translation using the Gemini AI API.
- **Real-Time Status Updates**: Receive live updates on translation progress, including file upload, translation in progress, and completion, through WebSocket notifications.
- **Download Translated File**: Download the translated file once processing is complete.
- **Session Management**: Track each session with file names, statuses, download links, and other metadata stored in MongoDB.
- **Environment Configuration**: Secure API keys and connection strings with environment variables.

## Project Structure

```
TEXT-TRANSLATION-MICROSERVICE/
│
├── app/
│   ├── static/            # Static files for HTML/CSS templates
│       ├── history.html   # HTML template for translation history
│       ├── index.html     # HTML template for the main page
│       ├── style.css      # CSS styling
│   ├── uploads/           # Directory to store uploaded files
│   ├── database.py        # MongoDB Atlas connection and schema definitions
│   ├── main.py            # Main FastAPI application and routing 
│   ├── models.py          # Models for MongoDB document schemas
│   └── services.py        # Core translation services and API calls to Gemini AI 
│
├── myenv/                 # Virtual environment (not included in version control)
├── temp/                  # Temporary files directory
├── .env                   # Environment variables for API keys and MongoDB connection(not included in vc)
├── .gitignore             # Ignore list for files and directories
├── README.md              # Project documentation
└── requirements.txt       # Python dependencies
```

## Getting Started

### Prerequisites

- **Python 3.8+**
- **FastAPI** and **MongoDB Atlas** account
- **Gemini AI** account for translation API access
- **Virtual Environment**: Recommended to isolate dependencies

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/text-translation-microservice.git
   cd text-translation-microservice
   ```

2. **Create a Virtual Environment**
   ```bash
   python3 -m venv myenv
   source myenv/bin/activate  # On macOS/Linux
   myenv\Scripts\activate     # On Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**

   Create a `.env` file in the project root directory with the following keys:

   ```plaintext
   GEMINI_API_KEY=<your_gemini_api_key>
   MONGODB_URI=<your_mongodb_atlas_connection_string>
   ```

### Running the Application

1. **Start FastAPI Server**
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Access the Application**
   Open a browser and navigate to `http://127.0.0.1:8000`.

### API Endpoints

- **`POST /upload`**: Upload a `.txt` file and specify the target language.
- **`GET /download/{file_name}`**: Download the translated file by providing the file ID.
- **`GET /history/{session_id}`**: View all uploaded files and their statuses, with download links.
- **`/ws/`**: WebSocket endpoint for real-time status updates on translation progress.

### Real-Time Translation Status

This project includes real-time status updates using WebSockets, with notifications at each stage of the translation process:
- **File Uploaded**: Confirmation when the file is successfully uploaded.
- **Translation In Progress**: Status update when translation begins.
- **Translation Completed**: Notification when translation is completed and the file is ready for download.

Users can view these updates live in the user interface.

### Example Usage

1. Navigate to the main page and upload a `.txt` file.
2. Choose a target language for translation.
3. As the file is processed, observe real-time updates on its status.
4. When the translation is complete, download the file through the provided link.

### File Status Tracking

Each uploaded file has metadata stored in MongoDB Atlas, including:
- **File Name**
- **Upload Date**
- **Translation Status** (Pending, In Progress, Completed)
- **Download Link** (available once translation is complete)

### Project Dependencies

All required dependencies are listed in `requirements.txt`. Some key packages include:
- **fastapi**: For creating the REST API and WebSocket endpoints
- **motor**: MongoDB asynchronous driver
- **requests**: To make HTTP requests to the Gemini AI API
- **dotenv**: For environment variable management

### Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/YourFeature`).
3. Commit your changes (`git commit -am 'Add new feature'`).
4. Push to the branch (`git push origin feature/YourFeature`).
5. Open a Pull Request.

### Troubleshooting

- Ensure that **MongoDB Atlas** connection is active and accessible.
- Verify the **Gemini API Key** in your `.env` file.
- Make sure all required Python packages are installed in your virtual environment.

### License

This project is licensed under the MIT License.
