# Google Slides API Setup Guide

This guide will help you set up Google Slides API credentials for the Tag Extractor API.

## Quick Setup (Service Account - Recommended)

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top
3. Click "New Project"
4. Enter a project name (e.g., "slide-ai-project")
5. Click "Create"

### Step 2: Enable Google Slides API

1. In the Google Cloud Console, go to **APIs & Services** > **Library**
2. Search for "Google Slides API"
3. Click on "Google Slides API"
4. Click the **Enable** button

### Step 3: Create a Service Account

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **Service Account**
3. Enter a name (e.g., "slide-ai-service")
4. Click **Create and Continue**
5. Skip the optional steps and click **Done**

### Step 4: Create and Download Service Account Key

1. Click on the service account you just created
2. Go to the **Keys** tab
3. Click **Add Key** > **Create new key**
4. Select **JSON** format
5. Click **Create** - this will download a JSON file (e.g., `your-project-xxxxx.json`)

### Step 5: Share Your Google Slides Presentation

1. Open the downloaded JSON file
2. Find the `client_email` field (it looks like: `your-service-account@your-project.iam.gserviceaccount.com`)
3. Open your Google Slides presentation
4. Click the **Share** button
5. Paste the service account email address
6. Give it **Editor** permissions
7. Click **Send** (you can uncheck "Notify people" if you want)

### Step 6: Configure Your Environment

You have two options:

#### Option A: Using File Path (Recommended)

1. Move the downloaded JSON file to your project directory (or keep it somewhere safe)
2. Create or edit `.env.local` file in your project root:

```bash
OPENAI_API_KEY=your-openai-api-key-here
GOOGLE_APPLICATION_CREDENTIALS=/full/path/to/your-service-account-key.json
```

**Example on macOS/Linux:**
```bash
GOOGLE_APPLICATION_CREDENTIALS=/Users/gokhulnath/Desktop/slide ai/service-account-key.json
```

**Example on Windows:**
```bash
GOOGLE_APPLICATION_CREDENTIALS=C:\Users\YourName\Desktop\slide ai\service-account-key.json
```

#### Option B: Using JSON Content as String

1. Open the downloaded JSON file
2. Copy the entire JSON content
3. Create or edit `.env.local` file:

```bash
OPENAI_API_KEY=your-openai-api-key-here
GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account","project_id":"...","private_key_id":"...","private_key":"...","client_email":"...","client_id":"...","auth_uri":"...","token_uri":"...","auth_provider_x509_cert_url":"...","client_x509_cert_url":"..."}'
```

**Note:** Make sure to escape quotes properly if using this method.

### Step 7: Verify Setup

1. Restart your FastAPI server
2. Test the endpoint:

```bash
curl -X POST "http://localhost:8000/insert-tags-to-slide" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Test prompt for machine learning",
    "slide_id": "your-slide-id-here"
  }'
```

## Getting Your Slide ID

1. Open your Google Slides presentation in a web browser
2. Look at the URL: `https://docs.google.com/presentation/d/{SLIDE_ID}/edit`
3. Copy the `SLIDE_ID` part (the long string between `/d/` and `/edit`)

## Troubleshooting

### Error: "Google API credentials not configured"
- Make sure your `.env.local` file exists in the project root
- Check that the environment variable name is correct
- Verify the file path is absolute and correct
- Restart your server after making changes

### Error: "Permission denied" or "Insufficient permissions"
- Make sure you shared the Google Slides presentation with the service account email
- Verify the service account has Editor permissions
- Check that the Google Slides API is enabled in your Google Cloud project

### Error: "File not found"
- Verify the path in `GOOGLE_APPLICATION_CREDENTIALS` is correct
- Use absolute paths (full path from root)
- Make sure the JSON file exists at that location

## Security Notes

- **Never commit** your service account JSON file to git
- The `.env.local` file is already in `.gitignore`
- Keep your service account key secure
- Only share presentations that need to be modified

