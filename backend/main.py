import os
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from hbp100 import sanitize

# Initialize FastAPI app
app = FastAPI(
    title="hbp100 Privacy Firewall API",
    description="Ultra-light privacy firewall for LLM prompts",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    prompt: str


class ChatResponse(BaseModel):
    original_prompt: str
    masked_prompt: str
    metadata: Dict[str, Any]
    llm_response_masked: Optional[str] = None
    llm_response_restored: Optional[str] = None
    has_pii: bool


def restore_placeholders(text: str, metadata: Dict[str, Any]) -> str:
    """Restore placeholders with original values."""
    if not text or not metadata:
        return text
    
    restored_text = text
    for placeholder, original_value in metadata.items():
        restored_text = restored_text.replace(placeholder, original_value)
    
    return restored_text


@app.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Process prompt through hbp100 privacy pipeline with mock AI response."""
    try:
        # Step 1: Sanitize with hbp100
        result = sanitize(request.prompt)
        
        # Step 2: Generate mock LLM response
        if result.has_pii:
            mock_response = f"I received your message. Detected and masked sensitive information. Here's what I see: {result.text}"
        else:
            mock_response = f"Your message is clean. Here's what you said: {result.text}"
        
        # Step 3: Restore placeholders for user display
        restored_response = restore_placeholders(mock_response, result.metadata)
        
        return ChatResponse(
            original_prompt=request.prompt,
            masked_prompt=result.text,
            metadata=result.metadata,
            llm_response_masked=mock_response,
            llm_response_restored=restored_response,
            has_pii=result.has_pii
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "hbp100 Privacy Firewall"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
