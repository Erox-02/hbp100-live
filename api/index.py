import os
import re
from typing import Dict, Any, Optional, Tuple
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from hbp100 import sanitize
from rapidfuzz import fuzz
from openai import OpenAI
from prompt import SYSTEM_PROMPT  

app = FastAPI(
    title="hbp100 Privacy Firewall API",
    description="Ultra-light privacy firewall for LLM prompts",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://hbp-100.vercel.app",
        "https://hbp100.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
groq_client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
) if GROQ_API_KEY else None

class ChatRequest(BaseModel):
    prompt: str
    use_real_llm: bool = False

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

ZODIAC_KEYWORDS = [
    'zodiac', 'horoscope', 'star sign', 'astrological sign',
    'sun sign', 'moon sign', 'rising sign', 'birth chart', 'what is my sign'
]

BIRTH_KEYWORDS = ['bd', 'birthday', 'born', 'birth', 'dob', 'date of birth']

CALENDAR_KEYWORDS = [
    'convert', 'calendar', 'hijri', 'bengali', 'hebrew', 'nepali',
    'julian', 'shaka', 'gregorian', 'islamic', 'chinese', 'ethiopian', 'coptic'
]

_year_counter = 1
_month_counter = 1
_day_counter = 1

def get_year_placeholder():
    global _year_counter
    placeholder = f"[YEAR_{_year_counter}]"
    _year_counter += 1
    return placeholder

def get_month_placeholder():
    global _month_counter
    placeholder = f"[MONTH_{_month_counter}]"
    _month_counter += 1
    return placeholder

def get_day_placeholder():
    global _day_counter
    placeholder = f"[DAY_{_day_counter}]"
    _day_counter += 1
    return placeholder

def reset_counters():
    global _year_counter, _month_counter, _day_counter
    _year_counter = 1
    _month_counter = 1
    _day_counter = 1

def detect_context(text: str) -> str:
    text_lower = text.lower()
    
    if any(kw in text_lower for kw in ZODIAC_KEYWORDS):
        return "ZODIAC"
    elif any(kw in text_lower for kw in CALENDAR_KEYWORDS):
        return "CALENDAR"
    elif any(kw in text_lower for kw in BIRTH_KEYWORDS):
        return "BIRTHDAY"
    else:
        return "UNKNOWN"

def extract_date_components(text: str) -> Dict[str, Any]:
    result = {'day': None, 'month': None, 'year': None, 'full_match': None}
    
    if re.search(r'\b\d{3}-\d{2}-\d{4}\b', text):
        return result
    if re.search(r'\b\d{4}-\d{4}-\d{4}\b', text):
        return result
    if re.search(r'\b\d{3}-\d{3}-\d{4}\b', text):
        return result
    
    match = re.search(r'(\d{1,2})(?:st|nd|rd|th)?\s+(\w+)\s+(\d{4})', text, re.IGNORECASE)
    if match:
        result['day'] = match.group(1)
        result['month'] = match.group(2)
        result['year'] = match.group(3)
        result['full_match'] = match.group(0)
        return result
    
    match = re.search(r'(\w+)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})', text, re.IGNORECASE)
    if match:
        result['month'] = match.group(1)
        result['day'] = match.group(2)
        result['year'] = match.group(3)
        result['full_match'] = match.group(0)
        return result
    
    match = re.search(r'(\d{4})[,.]?\s+(\w+)\s+(\d{1,2})(?:st|nd|rd|th)?', text, re.IGNORECASE)
    if match:
        result['year'] = match.group(1)
        result['month'] = match.group(2)
        result['day'] = match.group(3)
        result['full_match'] = match.group(0)
        return result
    
    year_match = re.search(r'\b(19|20)\d{2}\b', text)
    if year_match and not re.search(r'\d{4}-\d{4}', text):
        result['year'] = year_match.group(0)
        result['full_match'] = result['year']
    
    return result

def should_mask_date_component(component: str, context: str) -> bool:
    if context == "ZODIAC":
        return component == "YEAR"
    elif context == "BIRTHDAY":
        return True
    elif context == "CALENDAR":
        return False
    else:
        return component == "YEAR"

COMMON_DOMAINS = ['gmail', 'yahoo', 'hotmail', 'outlook', 'protonmail', 'aol', 'icloud', 'mail']

def is_email_fuzzy(word: str, threshold: int = 85) -> Tuple[bool, float]:
    if '@' not in word:
        return False, 0
    if re.match(r'[\w\.-]+@[\w\.-]+\.[a-z]{2,}', word, re.IGNORECASE):
        return True, 0.95
    parts = word.split('@')
    if len(parts) != 2:
        return False, 0
    domain_part = parts[1].split('.')[0] if '.' in parts[1] else parts[1]
    for known in COMMON_DOMAINS:
        if fuzz.ratio(domain_part.lower(), known) > threshold:
            return True, 0.75
    return False, 0

def is_ssn_fuzzy(word: str) -> Tuple[bool, float]:
    if re.match(r'^\d{3}-\d{2}-\d{4}$', word):
        return True, 0.95
    if re.match(r'^\d{3}-\d{2}-\d{3,4}$', word):
        return True, 0.70
    if word.count('-') > 2:
        return False, 0
    cleaned = re.sub(r'[^0-9]', '', word)
    if len(cleaned) == 9 and word.count('-') <= 2:
        return True, 0.80
    if re.match(r'^\d{9}$', word):
        return True, 0.85
    return False, 0

def is_phone_fuzzy(word: str) -> Tuple[bool, float]:
    if re.match(r'\+?\d{1,3}[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{3,4}', word):
        return True, 0.90
    if re.match(r'\b\d{10}\b', word):
        return True, 0.85
    cleaned = re.sub(r'[^0-9]', '', word)
    if len(cleaned) == 10:
        return True, 0.85
    return False, 0

def is_otp_fuzzy(word: str) -> Tuple[bool, float]:
    if re.match(r'\b\d{6}\b', word):
        return True, 0.95
    return False, 0

def preprocess_with_fuzzy(text: str) -> str:
    words = text.split()
    corrected_words = []
    for word in words:
        is_email, conf = is_email_fuzzy(word)
        if is_email and conf < 0.9 and '@' in word:
            parts = word.split('@')
            if len(parts) == 2:
                domain_part = parts[1].split('.')[0] if '.' in parts[1] else parts[1]
                for known in COMMON_DOMAINS:
                    if fuzz.ratio(domain_part.lower(), known) > 85:
                        corrected_domain = known + (parts[1][len(domain_part):] if len(parts[1]) > len(domain_part) else '.com')
                        corrected_words.append(parts[0] + '@' + corrected_domain)
                        break
                else:
                    corrected_words.append(word)
            else:
                corrected_words.append(word)
        else:
            corrected_words.append(word)
    return ' '.join(corrected_words)

def extract_fuzzy_entities(text: str) -> list:
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
    if not GROQ_API_KEY or not groq_client:
        return "LLM not configured. Add GROQ_API_KEY to environment."
    
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": masked_prompt}
            ],
            temperature=0.5,
            max_tokens=300,
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"LLM error: {str(e)}"

def get_mock_response(result, masked_prompt: str) -> str:
    if result.has_pii:
        return f"[MOCK] I received your message. Detected and masked sensitive information. Here's what I see: {masked_prompt}"
    else:
        return f"[MOCK] Your message is clean. Here's what you said: {masked_prompt}"

@app.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        reset_counters()
        
        original_prompt = request.prompt
        cleaned_prompt = preprocess_with_fuzzy(original_prompt)
        
        context = detect_context(cleaned_prompt)
        date_info = extract_date_components(cleaned_prompt)
        
        masked_prompt = cleaned_prompt
        metadata = {}
        
        if date_info['full_match']:
            masked_date_parts = []
            original_date = date_info['full_match']
            
            if date_info['day']:
                if should_mask_date_component("DAY", context):
                    placeholder = get_day_placeholder()
                    masked_date_parts.append(placeholder)
                    metadata[placeholder] = date_info['day']
                else:
                    masked_date_parts.append(date_info['day'])
            
            if date_info['month']:
                if should_mask_date_component("MONTH", context):
                    placeholder = get_month_placeholder()
                    masked_date_parts.append(placeholder)
                    metadata[placeholder] = date_info['month']
                else:
                    masked_date_parts.append(date_info['month'])
            
            if date_info['year']:
                if should_mask_date_component("YEAR", context):
                    placeholder = get_year_placeholder()
                    masked_date_parts.append(placeholder)
                    metadata[placeholder] = date_info['year']
                else:
                    masked_date_parts.append(date_info['year'])
            
            if len(masked_date_parts) == 3:
                if date_info['full_match'].find(date_info['year'] if date_info['year'] else '') < date_info['full_match'].find(date_info['day'] if date_info['day'] else ''):
                    masked_date = f"{masked_date_parts[0]} {masked_date_parts[1]} {masked_date_parts[2]}"
                else:
                    masked_date = f"{masked_date_parts[1]} {masked_date_parts[0]} {masked_date_parts[2]}"
            elif len(masked_date_parts) == 1:
                masked_date = masked_date_parts[0]
            else:
                masked_date = original_date
            
            masked_prompt = masked_prompt.replace(original_date, masked_date)
        
        result = sanitize(masked_prompt)
        result.metadata.update(metadata)
        
        fuzzy_entities = extract_fuzzy_entities(cleaned_prompt)
        if fuzzy_entities and not result.has_pii:
            for entity in fuzzy_entities:
                placeholder = f"{entity['type']}_FUZZY_{entity['confidence']}"
                result.metadata[placeholder] = entity['value']
        
        if request.use_real_llm:
            llm_response_masked = call_llm(result.text)
        else:
            llm_response_masked = get_mock_response(result, result.text)
        
        restored_response = restore_placeholders(llm_response_masked, result.metadata)
        
        return ChatResponse(
            original_prompt=original_prompt,
            masked_prompt=result.text,
            metadata=result.metadata,
            llm_response_masked=llm_response_masked,
            llm_response_restored=restored_response,
            has_pii=result.has_pii or len(fuzzy_entities) > 0 or len(metadata) > 0
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "hbp100 Privacy Firewall"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
