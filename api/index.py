import os
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from hbp100 import sanitize
import requests

app = FastAPI(
    title="hbp100 Privacy Firewall API",
    description="Ultra-light privacy firewall for LLM prompts",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "https://hbp100-live.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SYSTEM_PROMPT = """You are an LLM assistant integrated with a privacy firewall. 
The user's prompt has already been sanitized — any sensitive data (emails, phones, SSNs, etc.) has been replaced with placeholders like [EMAIL_1] or [PHONE_1].

Your role:
- Respond naturally as if the placeholders are real values.
- Never ask the user to provide, confirm, or repeat any sensitive information.
- Never question why certain words are masked or why placeholders exist.
- Never request original values or clarification about masked content.
- Simply answer the user's question using the context given.

The privacy firewall handles all sensitive data. You focus only on being helpful.
Be concise, direct, and useful."""

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

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
    if not text or not metadata:
        return text
    restored_text = text
    for placeholder, original_value in metadata.items():
        restored_text = restored_text.replace(placeholder, original_value)
    return restored_text

def call_llm(masked_prompt: str) -> str:
    if not OPENROUTER_API_KEY:
        return "LLM not configured. Add OPENROUTER_API_KEY to environment."
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek/deepseek-chat:free",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": masked_prompt}
        ],
        "max_tokens": 300,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"LLM error: {response.status_code}"
    except Exception as e:
        return f"LLM error: {str(e)}"

@app.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        result = sanitize(request.prompt)
        llm_response_masked = call_llm(result.text)
        restored_response = restore_placeholders(llm_response_masked, result.metadata)
        
        return ChatResponse(
            original_prompt=request.prompt,
            masked_prompt=result.text,
            metadata=result.metadata,
            llm_response_masked=llm_response_masked,
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
