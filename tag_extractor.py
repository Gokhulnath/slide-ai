#!/usr/bin/env python3
"""
Tag Extractor API - FastAPI application that extracts tags from user prompts using PydanticAI and OpenAI
and integrates with Google Slides API to insert tags into presentations
"""

from fastapi import FastAPI, HTTPException
from pydantic_ai import Agent
from pydantic import BaseModel, Field
from typing import List
import uuid
import uvicorn
import os
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json

# Load environment variables from .env.local file (or .env as fallback)
load_dotenv('.env.local')  # Try .env.local first
load_dotenv()  # Fallback to .env if .env.local doesn't exist


# Pydantic models for API request/response
class TagExtractionRequest(BaseModel):
    """Request model for tag extraction"""
    prompt: str = Field(..., description="The user prompt to extract tags from", min_length=1)


class TagExtractionResponse(BaseModel):
    """Response model containing extracted tags"""
    tags: List[str] = Field(..., description="List of extracted tags")
    prompt: str = Field(..., description="The original prompt that was processed")


class SlideInsertRequest(BaseModel):
    """Request model for inserting tags into Google Slides"""
    prompt: str = Field(..., description="The user prompt to extract tags from", min_length=1)
    slide_id: str = Field(..., description="Google Slides presentation ID")


class SlideInsertResponse(BaseModel):
    """Response model for slide insertion"""
    tags: List[str] = Field(..., description="List of extracted tags that were inserted")
    prompt: str = Field(..., description="The original prompt that was processed")
    slide_id: str = Field(..., description="Google Slides presentation ID")
    page_id: str = Field(..., description="The slide page ID where tags were inserted")
    success: bool = Field(..., description="Whether the insertion was successful")


class TagsResponse(BaseModel):
    """Internal response model for PydanticAI agent"""
    tags: List[str]


# Create the agent with OpenAI
agent = Agent(
    'openai:gpt-4o-mini',
    system_prompt='Extract relevant tags from the user prompt. Return a list of concise, meaningful tags that categorize or describe the main topics, themes, or keywords in the prompt.',
    output_type=TagsResponse,
)

# Initialize FastAPI app
app = FastAPI(
    title="Tag Extractor API",
    description="API for extracting tags from user prompts using PydanticAI and OpenAI, with Google Slides integration",
    version="1.0.0"
)


def get_google_slides_service():
    """
    Authenticate and return a Google Slides API service object.
    
    Supports two authentication methods:
    1. Service Account (GOOGLE_APPLICATION_CREDENTIALS or GOOGLE_SERVICE_ACCOUNT_JSON)
    2. OAuth2 credentials (GOOGLE_CREDENTIALS_JSON)
    
    Returns:
        Google Slides API service object
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Method 1: Service Account (recommended for server-to-server)
        service_account_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        service_account_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
        
        if service_account_path and os.path.exists(service_account_path):
            creds = service_account.Credentials.from_service_account_file(
                service_account_path,
                scopes=['https://www.googleapis.com/auth/presentations']
            )
        elif service_account_json:
            service_account_info = json.loads(service_account_json)
            creds = service_account.Credentials.from_service_account_info(
                service_account_info,
                scopes=['https://www.googleapis.com/auth/presentations']
            )
        else:
            # Method 2: OAuth2 credentials
            credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
            if credentials_json:
                creds_info = json.loads(credentials_json)
                creds = Credentials.from_authorized_user_info(
                    creds_info,
                    scopes=['https://www.googleapis.com/auth/presentations']
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Google API credentials not configured. Please set GOOGLE_APPLICATION_CREDENTIALS, GOOGLE_SERVICE_ACCOUNT_JSON, or GOOGLE_CREDENTIALS_JSON"
                )
        
        service = build('slides', 'v1', credentials=creds)
        return service
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to authenticate with Google Slides API: {str(e)}"
        )


async def insert_tags_into_slide(slide_id: str, tags: List[str]) -> str:
    """
    Create a new slide and insert tags into it.
    
    Args:
        slide_id: The Google Slides presentation ID
        tags: List of tags to insert
        
    Returns:
        The page_id of the newly created slide
        
    Raises:
        HTTPException: If slide creation or insertion fails
    """
    try:
        service = get_google_slides_service()
        
        # Get presentation information
        presentation = service.presentations().get(presentationId=slide_id).execute()
        
        # Step 1: Create a new slide first
        new_slide_id = f'slide_{uuid.uuid4().hex[:8]}'
        create_slide_request = {
            'createSlide': {
                'objectId': new_slide_id,
                'insertionIndex': len(presentation.get('slides', [])),  # Add at the end
                'slideLayoutReference': {
                    'predefinedLayout': 'BLANK'
                }
            }
        }
        
        # Create the slide
        create_response = service.presentations().batchUpdate(
            presentationId=slide_id,
            body={'requests': [create_slide_request]}
        ).execute()
        
        # Get the actual page ID from the response
        create_slide_response = create_response.get('replies', [])[0].get('createSlide', {})
        actual_page_id = create_slide_response.get('objectId', new_slide_id)
        
        # Step 2: Get slide dimensions for positioning
        presentation = service.presentations().get(presentationId=slide_id).execute()
        page_size = presentation.get('pageSize', {})
        width_dict = page_size.get('width', {'magnitude': 720, 'unit': 'PT'})
        # Extract width magnitude (handle both dict and direct value)
        if isinstance(width_dict, dict):
            width_magnitude = width_dict.get('magnitude', 720)
        else:
            width_magnitude = width_dict
        
        # Step 3: Prepare requests to add tags as heading
        requests = []
        
        # Format tags as heading text
        if not tags:
            tags_text = "No tags"
        else:
            tags_text = " • ".join(tags)
        
        # Calculate position (centered at top, like a title/heading)
        box_width = 650
        box_height = 100
        x_position = (width_magnitude - box_width) / 2
        y_position = 50  # Near the top for heading
        
        # Generate unique object ID for the heading text box
        heading_id = f'heading_{uuid.uuid4().hex[:8]}'
        
        # Create text box for heading with initial text
        create_shape_request = {
            'createShape': {
                'objectId': heading_id,
                'shapeType': 'TEXT_BOX',
                'elementProperties': {
                    'pageObjectId': actual_page_id,
                    'size': {
                        'height': {'magnitude': box_height, 'unit': 'PT'},
                        'width': {'magnitude': box_width, 'unit': 'PT'}
                    },
                    'transform': {
                        'scaleX': 1,
                        'scaleY': 1,
                        'translateX': x_position,
                        'translateY': y_position,
                        'unit': 'PT'
                    }
                }
            }
        }
        requests.append(create_shape_request)
        
        # Insert heading text (TEXT_BOX starts empty, so we insert at index 0)
        insert_text_request = {
            'insertText': {
                'objectId': heading_id,
                'text': tags_text,
                'insertionIndex': 0
            }
        }
        requests.append(insert_text_request)
        
        # Style as heading (large, bold, centered)
        style_text_request = {
            'updateTextStyle': {
                'objectId': heading_id,
                'style': {
                    'fontSize': {'magnitude': 28, 'unit': 'PT'},  # Large heading size
                    'bold': True,
                    'foregroundColor': {
                        'opaqueColor': {
                            'rgbColor': {
                                'red': 0.0,
                                'green': 0.0,
                                'blue': 0.0
                            }
                        }
                    }
                },
                'textRange': {
                    'type': 'ALL'
                },
                'fields': 'fontSize,bold,foregroundColor'
            }
        }
        requests.append(style_text_request)
        
        # Center align the text
        paragraph_style_request = {
            'updateParagraphStyle': {
                'objectId': heading_id,
                'style': {
                    'alignment': 'CENTER',
                    'spacingMode': 'NEVER_COLLAPSE',
                    'lineSpacing': 115  # 115% line spacing
                },
                'textRange': {
                    'type': 'ALL'
                },
                'fields': 'alignment,spacingMode,lineSpacing'
            }
        }
        requests.append(paragraph_style_request)
        
        # Execute batch update to add tags
        body = {'requests': requests}
        try:
            response = service.presentations().batchUpdate(
                presentationId=slide_id,
                body=body
            ).execute()
            
            # Check for errors in response
            if 'replies' in response:
                for i, reply in enumerate(response.get('replies', [])):
                    if 'error' in reply:
                        raise HTTPException(
                            status_code=500,
                            detail=f"Error in batch update request {i}: {reply['error']}"
                        )
                    # Verify shape was created
                    if i == 0 and 'createShape' in reply:
                        created_shape_id = reply['createShape'].get('objectId')
                        if created_shape_id != heading_id:
                            # Log warning but continue
                            pass
        except HttpError as batch_error:
            # Re-raise HttpError to be handled by outer exception handler
            raise batch_error
        
        return actual_page_id
        
    except HttpError as e:
        error_details = json.loads(e.content.decode('utf-8'))
        error_message = error_details.get('error', {}).get('message', str(e))
        status_code = e.resp.status
        
        # Provide helpful messages for common errors
        if status_code == 403:
            # Try to get the service account email for better error message
            try:
                # Get credentials from the service that was already created
                creds = service._http.credentials
                if hasattr(creds, 'service_account_email'):
                    service_email = creds.service_account_email
                    error_message = (
                        f"Permission denied (403). The service account '{service_email}' "
                        f"does not have access to this presentation. "
                        f"Please share your Google Slides presentation with this email address "
                        f"and give it Editor permissions. Original error: {error_message}"
                    )
                else:
                    error_message = (
                        f"Permission denied (403). Please ensure you've shared your Google Slides "
                        f"presentation with the service account email and given it Editor permissions. "
                        f"Original error: {error_message}"
                    )
            except Exception:
                error_message = (
                    f"Permission denied (403). Please ensure you've shared your Google Slides "
                    f"presentation with the service account email and given it Editor permissions. "
                    f"Original error: {error_message}"
                )
        elif status_code == 404:
            error_message = (
                f"Presentation not found (404). Please check that the slide_id is correct. "
                f"Original error: {error_message}"
            )
        
        raise HTTPException(
            status_code=status_code,
            detail=f"Google Slides API error: {error_message}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to insert tags into slide: {str(e)}"
        )


async def extract_tags(prompt: str) -> List[str]:
    """
    Extract tags from a user prompt.
    
    Args:
        prompt: The user's input prompt
        
    Returns:
        List of extracted tags
    """
    result = await agent.run(prompt)
    return result.output.tags


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Tag Extractor API",
        "version": "1.0.0",
        "endpoints": {
            "extract_tags": "/extract-tags (POST)",
            "insert_tags_to_slide": "/insert-tags-to-slide (POST)",
            "health": "/health (GET)",
            "check_google_auth": "/check-google-auth (GET)"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/check-google-auth")
async def check_google_auth():
    """
    Check Google Slides API authentication and return service account email.
    Useful for troubleshooting permission issues.
    """
    try:
        service = get_google_slides_service()
        creds = service._http.credentials
        
        if hasattr(creds, 'service_account_email'):
            service_email = creds.service_account_email
            return {
                "status": "authenticated",
                "service_account_email": service_email,
                "message": f"Service account email: {service_email}. Make sure to share your Google Slides presentation with this email address."
            }
        else:
            return {
                "status": "authenticated",
                "message": "Using OAuth2 credentials. Make sure the account has access to the presentation."
            }
    except HTTPException as e:
        return {
            "status": "error",
            "detail": e.detail
        }
    except Exception as e:
        return {
            "status": "error",
            "detail": f"Failed to check authentication: {str(e)}"
        }


@app.post("/extract-tags", response_model=TagExtractionResponse)
async def extract_tags_endpoint(request: TagExtractionRequest):
    """
    Extract tags from a user prompt.
    
    Args:
        request: TagExtractionRequest containing the prompt
        
    Returns:
        TagExtractionResponse with extracted tags
        
    Raises:
        HTTPException: If tag extraction fails
    """
    try:
        tags = await extract_tags(request.prompt)
        return TagExtractionResponse(
            tags=tags,
            prompt=request.prompt
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error extracting tags: {str(e)}"
        )


@app.post("/insert-tags-to-slide", response_model=SlideInsertResponse)
async def insert_tags_to_slide_endpoint(request: SlideInsertRequest):
    """
    Extract tags from a user prompt and create a new slide with the tags inserted.
    
    Args:
        request: SlideInsertRequest containing the prompt and slide_id
        
    Returns:
        SlideInsertResponse with insertion details
        
    Raises:
        HTTPException: If tag extraction or slide creation/insertion fails
    """
    try:
        # Extract tags from prompt
        tags = await extract_tags(request.prompt)
        
        # Create a new slide and insert tags into it
        page_id = await insert_tags_into_slide(
            slide_id=request.slide_id,
            tags=tags
        )
        
        return SlideInsertResponse(
            tags=tags,
            prompt=request.prompt,
            slide_id=request.slide_id,
            page_id=page_id,
            success=True
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)

