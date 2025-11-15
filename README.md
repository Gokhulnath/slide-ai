# Tag Extractor API

A FastAPI application that extracts tags from user prompts using PydanticAI and OpenAI, and integrates with Google Slides API to insert tags into presentations.

## Installation

1. Create and activate a virtual environment (recommended):

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env.local` file in the project root and add your API keys:

```bash
# Create .env.local file
cat > .env.local << EOF
OPENAI_API_KEY=your-openai-api-key-here
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json
EOF
```

Or manually create a `.env.local` file with:

```
OPENAI_API_KEY=your-openai-api-key-here
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json
```

**Note:** The `.env.local` and `.env` files are already in `.gitignore` to keep your API keys secure. The application will load from `.env.local` first, then fall back to `.env` if needed.

### Google Slides API Setup

**Quick Setup:** Run the interactive setup script:

```bash
python setup_google_credentials.py
```

**Or follow the detailed guide:** See [SETUP_GOOGLE_API.md](SETUP_GOOGLE_API.md) for step-by-step instructions.

To use the Google Slides integration, you need to set up Google API credentials. There are two methods:

#### Method 1: Service Account (Recommended)

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Slides API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Slides API"
   - Click "Enable"
4. Create a Service Account:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Fill in the details and create the service account
   - Click on the created service account
   - Go to "Keys" tab > "Add Key" > "Create new key"
   - Choose JSON format and download the key file
5. Share your Google Slides presentation with the service account email (found in the JSON file)
6. Set the environment variable:
   - Option A: Set `GOOGLE_APPLICATION_CREDENTIALS` to the path of the JSON file
   - Option B: Set `GOOGLE_SERVICE_ACCOUNT_JSON` to the JSON content as a string

#### Method 2: OAuth2 Credentials

1. Follow steps 1-3 from Method 1
2. Create OAuth2 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Configure the consent screen if prompted
   - Choose "Desktop app" as the application type
   - Download the credentials JSON
3. Use the OAuth2 flow to get refresh tokens and set `GOOGLE_CREDENTIALS_JSON` environment variable with the credentials JSON content

**Getting the Slide ID:**

- Open your Google Slides presentation
- The Slide ID is in the URL: `https://docs.google.com/presentation/d/{SLIDE_ID}/edit`

## Running the API

Start the FastAPI server:

```bash
python tag_extractor.py
```

Or use uvicorn directly:

```bash
uvicorn tag_extractor:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

### GET `/`

Root endpoint with API information.

### GET `/health`

Health check endpoint.

### POST `/extract-tags`

Extract tags from a user prompt.

**Request Body:**

```json
{
  "prompt": "Create a presentation about machine learning and artificial intelligence"
}
```

**Response:**

```json
{
  "tags": [
    "machine learning",
    "artificial intelligence",
    "presentation",
    "technology"
  ],
  "prompt": "Create a presentation about machine learning and artificial intelligence"
}
```

### POST `/insert-tags-to-slide`

Extract tags from a user prompt and create a new slide with the tags inserted.

**Request Body:**

```json
{
  "prompt": "Create a presentation about machine learning and artificial intelligence",
  "slide_id": "1a2b3c4d5e6f7g8h9i0j"
}
```

**Response:**

```json
{
  "tags": [
    "machine learning",
    "artificial intelligence",
    "presentation",
    "technology"
  ],
  "prompt": "Create a presentation about machine learning and artificial intelligence",
  "slide_id": "1a2b3c4d5e6f7g8h9i0j",
  "page_id": "g1234567890",
  "success": true
}
```

**Note:** A new slide will be created in the presentation each time this endpoint is called. The tags will be inserted as a formatted text box on the newly created slide.

## API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Example Usage

### Using curl:

```bash
curl -X POST "http://localhost:8000/extract-tags" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a presentation about machine learning and artificial intelligence"}'
```

### Using Python requests:

```python
import requests

response = requests.post(
    "http://localhost:8000/extract-tags",
    json={"prompt": "Create a presentation about machine learning and artificial intelligence"}
)
print(response.json())
```

### Using JavaScript fetch:

```javascript
fetch("http://localhost:8000/extract-tags", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    prompt:
      "Create a presentation about machine learning and artificial intelligence",
  }),
})
  .then((response) => response.json())
  .then((data) => console.log(data));
```

### Inserting Tags into Google Slides:

```bash
curl -X POST "http://localhost:8000/insert-tags-to-slide" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a presentation about machine learning and artificial intelligence",
    "slide_id": "1a2b3c4d5e6f7g8h9i0j"
  }'
```

```python
import requests

response = requests.post(
    "http://localhost:8000/insert-tags-to-slide",
    json={
        "prompt": "Create a presentation about machine learning and artificial intelligence",
        "slide_id": "1a2b3c4d5e6f7g8h9i0j"
    }
)
print(response.json())
```
