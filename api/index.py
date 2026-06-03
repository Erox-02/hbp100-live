import os
import re
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from hbp100 import sanitize
import requests
from rapidfuzz import fuzz

app = FastAPI(
    title="hbp100 Privacy Firewall API",
    description="Ultra-light privacy firewall for LLM prompts",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "https://hbp-100.vercel.app"],
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

# ============================================================
# FUZZY MATCHING & TYPO PROTECTION
# ============================================================

COMMON_DOMAINS = ['gmail', 'yahoo', 'hotmail', 'outlook', 'protonmail', 'aol', 'icloud', 'mail']

def is_email_fuzzy(word: str, threshold: int = 85) -> tuple:
    """Check if word is an email (exact or fuzzy with typos)"""
    # Must contain @
    if '@' not in word:
        return False, 0
    
    # Exact email pattern match
    if re.match(r'[\w\.-]+@[\w\.-]+\.[a-z]{2,}', word, re.IGNORECASE):
        return True, 0.95
    
    # Extract domain part
    parts = word.split('@')
    if len(parts) != 2:
        return False, 0
    
    domain_part = parts[1].split('.')[0] if '.' in parts[1] else parts[1]
    
    for known in COMMON_DOMAINS:
        if fuzz.ratio(domain_part.lower(), known) > threshold:
            return True, 0.75
    
    return False, 0

def is_ssn_fuzzy(word: str) -> tuple:
    """Check if word is SSN (exact, partial, or with spaces/dots)"""
    # Exact SSN: XXX-XX-XXXX
    if re.match(r'\d{3}-\d{2}-\d{4}', word):
        return True, 0.95
    
    # Partial SSN (missing last digit(s))
    if re.match(r'\d{3}-\d{2}-\d{3,4}', word):
        return True, 0.70
    
    # SSN with spaces or dots instead of dashes
    cleaned = re.sub(r'[^0-9]', '', word)
    if len(cleaned) == 9:
        return True, 0.85
    
    # 9 consecutive digits (no separators)
    if re.match(r'\b\d{9}\b', word):
        return True, 0.80
    
    return False, 0

def is_phone_fuzzy(word: str) -> tuple:
    """Check if word is a phone number (supports various formats)"""
    # Standard phone pattern with country code
    if re.match(r'\+?\d{1,3}[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{3,4}', word):
        return True, 0.90
    
    # 10-digit number (no separators)
    if re.match(r'\b\d{10}\b', word):
        return True, 0.85
    
    # 10-digit with spaces/dots/dashes
    cleaned = re.sub(r'[^0-9]', '', word)
    if len(cleaned) == 10:
        return True, 0.85
    
    return False, 0

def is_otp_fuzzy(word: str) -> tuple:
    """Check if word is an OTP (6 digits)"""
    if re.match(r'\b\d{6}\b', word):
        return True, 0.95
    return False, 0

def preprocess_with_fuzzy(text: str) -> str:
    """Apply fuzzy matching to catch typos before sanitization"""
    words = text.split()
    corrected_words = []
    
    for word in words:
        # Check if it's an email with typo
        is_email, conf = is_email_fuzzy(word)
        if is_email and conf < 0.9:
            # Try to suggest correction for common domain typos
            if '@' in word:
                parts = word.split('@')
                if len(parts) == 2:
                    domain_part = parts[1].split('.')[0] if '.' in parts[1] else parts[1]
                    for known in COMMON_DOMAINS:
                        if fuzz.ratio(domain_part.lower(), known) > 85:
                            corrected_domain = known + (parts[1][len(domain_part):] if len(parts[1]) > len(domain_part) else '.com')
                            corrected = parts[0] + '@' + corrected_domain
                            corrected_words.append(corrected)
                            break
                    else:
                        corrected_words.append(word)
                else:
                    corrected_words.append(word)
            else:
                corrected_words.append(word)
        else:
            corrected_words.append(word)
    
    return ' '.join(corrected_words)

def extract_fuzzy_entities(text: str) -> list:
    """Extract entities with confidence scores (for metadata)"""
    entities = []
    words = re.findall(r'\S+', text)
    
    for word in words:
        is_email, conf = is_email_fuzzy(word)
        if is_email:
            entities.append({'type': 'EMAIL', 'value': word, 'confidence': conf})
            continue
        
        is_ssn, conf = is_ssn_fuzzy(word)
        if is_ssn:
            entities.append({'type': 'SSN', 'value': word, 'confidence': conf})
            continue
        
        is_phone, conf = is_phone_fuzzy(word)
        if is_phone:
            entities.append({'type': 'PHONE', 'value': word, 'confidence': conf})
            continue
        
        is_otp, conf = is_otp_fuzzy(word)
        if is_otp:
            entities.append({'type': 'OTP', 'value': word, 'confidence': conf})
            continue
    
    return entities

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
        # Step 0: Preprocess with fuzzy matching (typo correction)
        cleaned_prompt = preprocess_with_fuzzy(request.prompt)
        
        # Step 1: Sanitize with hbp100
        result = sanitize(cleaned_prompt)
        
        # Step 2: If no PII found but fuzzy entities exist, add them to metadata
        fuzzy_entities = extract_fuzzy_entities(cleaned_prompt)
        if fuzzy_entities and not result.has_pii:
            # Merge fuzzy entities into metadata
            for entity in fuzzy_entities:
                placeholder = f"{entity['type']}_FUZZY_{entity['confidence']}"
                result.metadata[placeholder] = entity['value']
        
        # Step 3: Call LLM
        llm_response_masked = call_llm(result.text)
        
        # Step 4: Restore placeholders
        restored_response = restore_placeholders(llm_response_masked, result.metadata)
        
        return ChatResponse(
            original_prompt=request.prompt,
            masked_prompt=result.text,
            metadata=result.metadata,
            llm_response_masked=llm_response_masked,
            llm_response_restored=restored_response,
            has_pii=result.has_pii or len(fuzzy_entities) > 0
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "hbp100 Privacy Firewall"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
