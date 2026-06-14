import os
import re
from typing import Dict, Any, Optional, Tuple, List
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
        "https://hbp-100.vercel.app",
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
    use_privacy: bool = True

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

PHONE_KEYWORDS = ['phone', 'mobile', 'call', 'contact', 'number', 'whatsapp', 'nearby', 'tel', 'cell', 'dial', 'reach', 'text', 'message', 'msg']
OTP_KEYWORDS = ['otp', 'verification', 'login', 'code', 'sms', 'auth', '2fa', 'one-time', 'passcode', 'verify']

def has_context_keyword(text: str, keywords: list) -> bool:
    text_lower = text.lower()
    for keyword in keywords:
        if re.search(rf'\b{keyword}\b', text_lower):
            return True
    return False

def is_likely_phone(word: str, full_context: str) -> Tuple[bool, float]:
    cleaned = re.sub(r'[^0-9]', '', word)
    if 10 <= len(cleaned) <= 15:
        if has_context_keyword(full_context, PHONE_KEYWORDS):
            return True, 0.85
        return False, 0
    return False, 0

def is_likely_otp(word: str, full_context: str) -> Tuple[bool, float]:
    if re.match(r'^\d{6}$', word):
        if has_context_keyword(full_context, OTP_KEYWORDS):
            return True, 0.90
        return False, 0
    return False, 0

def is_likely_ssn(word: str, full_context: str) -> Tuple[bool, float]:
    if re.match(r'^\d{3}-\d{2}-\d{4}$', word):
        return True, 0.95
    
    if word.count('-') > 2:
        return False, 0
    
    cleaned = re.sub(r'[^0-9]', '', word)
    if len(cleaned) == 9:
        if has_context_keyword(full_context, ['ssn', 'social security', 'tax id', 'federal id']):
            return True, 0.80
        return False, 0
    return False, 0

class RequestCounters:
    def __init__(self):
        self.year = 1
        self.month = 1
        self.day = 1
        self.email = 1
        self.phone = 1
        self.otp = 1
        self.ssn = 1

def get_email_placeholder(counters):
    placeholder = f"[EMAIL_{counters.email}]"
    counters.email += 1
    return placeholder

def get_phone_placeholder(counters):
    placeholder = f"[PHONE_{counters.phone}]"
    counters.phone += 1
    return placeholder

def get_otp_placeholder(counters):
    placeholder = f"[OTP_{counters.otp}]"
    counters.otp += 1
    return placeholder

def get_ssn_placeholder(counters):
    placeholder = f"[SSN_{counters.ssn}]"
    counters.ssn += 1
    return placeholder

def get_year_placeholder(counters):
    placeholder = f"[YEAR_{counters.year}]"
    counters.year += 1
    return placeholder

def get_month_placeholder(counters):
    placeholder = f"[MONTH_{counters.month}]"
    counters.month += 1
    return placeholder

def get_day_placeholder(counters):
    placeholder = f"[DAY_{counters.day}]"
    counters.day += 1
    return placeholder

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
    if re.match(r'^[\w\.-]+@[\w\.-]+\.[a-z]{2,}$', word, re.IGNORECASE):
        return True, 0.95
    
    parts = word.split('@')
    if len(parts) != 2:
        return False, 0
    domain_part = parts[1].split('.')[0] if '.' in parts[1] else parts[1]
    for known in COMMON_DOMAINS:
        if fuzz.ratio(domain_part.lower(), known) > threshold:
            return True, 0.75
    return False, 0

def is_ssn_fuzzy(word: str, full_context: str) -> Tuple[bool, float]:
    if re.match(r'^\d{3}-\d{2}-\d{4}$', word):
        return True, 0.95
    
    if word.count('-') > 2:
        return False, 0
    
    cleaned = re.sub(r'[^0-9]', '', word)
    if len(cleaned) == 9:
        if has_context_keyword(full_context, ['ssn', 'social security', 'tax id', 'federal id']):
            return True, 0.80
        return False, 0
    return False, 0

def is_phone_fuzzy(word: str, full_context: str) -> Tuple[bool, float]:
    cleaned = re.sub(r'[^0-9]', '', word)
    if 10 <= len(cleaned) <= 15:
        if has_context_keyword(full_context, PHONE_KEYWORDS):
            return True, 0.85
        return False, 0
    return False, 0

def is_otp_fuzzy(word: str, full_context: str) -> Tuple[bool, float]:
    if re.match(r'^\d{6}$', word):
        if has_context_keyword(full_context, OTP_KEYWORDS):
            return True, 0.90
        return False, 0
    return False, 0

def extract_fuzzy_entities(text: str, counters, detected_values: set) -> list:
    entities = []
    detected_values = detected_values or set()
    
    patterns = [
        (r'\b[\w\.-]+@[\w\.-]+\.[a-z]{2,}\b', 'EMAIL', is_email_fuzzy, get_email_placeholder),
        (r'\b\d{3}-\d{2}-\d{4}\b', 'SSN', is_ssn_fuzzy, get_ssn_placeholder),
        (r'\+?\d{1,3}[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{3,4}', 'PHONE', is_phone_fuzzy, get_phone_placeholder),
        (r'\b\d{6}\b', 'OTP', is_otp_fuzzy, get_otp_placeholder),
    ]
    
    for pattern, ptype, checker, placeholder_func in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            word = match.group(0)
            if word in detected_values:
                continue
            is_match, conf = checker(word, text)
            if is_match:
                placeholder = placeholder_func(counters)
                entities.append({
                    'type': ptype,
                    'value': word,
                    'confidence': conf,
                    'placeholder': placeholder
                })
                detected_values.add(word)
    
    return entities

def replace_first_occurrence(text: str, old: str, new: str) -> str:
    idx = text.find(old)
    if idx == -1:
        return text
    return text[:idx] + new + text[idx + len(old):]

def preprocess_with_fuzzy(text: str) -> str:
    return text

def call_llm(masked_prompt: str, metadata: Dict[str, Any]) -> str:
    if not GROQ_API_KEY or not groq_client:
        return "LLM not configured. Add GROQ_API_KEY to environment."
    
    if metadata:
        allowed_text = ", ".join(metadata.keys())
    else:
        allowed_text = "No placeholders are allowed in the response."
    
    user_message = f"""Allowed placeholders you can use in your response:
{allowed_text}

User message:
{masked_prompt}"""
    
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0,
            max_tokens=200,
        )
        return completion.choices[0].message.content or ""
    except Exception as e:
        return f"LLM error: {str(e)}"

def get_mock_response(final_masked_prompt: str) -> str:
    return f"MOCK MODE: This is what the LLM would receive:\n\n{final_masked_prompt}"

def validate_placeholders(response: str, metadata: Dict[str, Any], is_mock: bool = False) -> str:
    if is_mock:
        return response
    
    pattern = r'\[(?:EMAIL|PHONE|OTP|SSN|YEAR|MONTH|DAY)_[0-9]+\]'
    placeholders = re.findall(pattern, response)
    for ph in placeholders:
        if ph not in metadata:
            return f"[ERROR: Hallucinated placeholder {ph} detected. The LLM invented a placeholder that wasn't in the allowed list: {list(metadata.keys())}]"
    return response

class MockResult:
    def __init__(self, text, metadata, has_pii):
        self.text = text
        self.metadata = metadata
        self.has_pii = has_pii

@app.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        counters = RequestCounters()
        
        original_prompt = request.prompt
        cleaned_prompt = preprocess_with_fuzzy(original_prompt)
        
        context = detect_context(cleaned_prompt)
        date_info = extract_date_components(cleaned_prompt)
        
        masked_prompt = cleaned_prompt
        metadata = {}
        detected_values = set()
        
        if date_info['full_match']:
            masked_date_parts = []
            original_date = date_info['full_match']
            
            if date_info['day']:
                if should_mask_date_component("DAY", context):
                    placeholder = get_day_placeholder(counters)
                    masked_date_parts.append(placeholder)
                    metadata[placeholder] = date_info['day']
                    detected_values.add(date_info['day'])
                else:
                    masked_date_parts.append(date_info['day'])
            
            if date_info['month']:
                if should_mask_date_component("MONTH", context):
                    placeholder = get_month_placeholder(counters)
                    masked_date_parts.append(placeholder)
                    metadata[placeholder] = date_info['month']
                    detected_values.add(date_info['month'])
                else:
                    masked_date_parts.append(date_info['month'])
            
            if date_info['year']:
                if should_mask_date_component("YEAR", context):
                    placeholder = get_year_placeholder(counters)
                    masked_date_parts.append(placeholder)
                    metadata[placeholder] = date_info['year']
                    detected_values.add(date_info['year'])
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
        
        fuzzy_entities = extract_fuzzy_entities(cleaned_prompt, counters, detected_values)
        
        for entity in fuzzy_entities:
            placeholder = entity['placeholder']
            masked_prompt = replace_first_occurrence(masked_prompt, entity['value'], placeholder)
            metadata[placeholder] = entity['value']
            detected_values.add(entity['value'])
        
        if request.use_privacy:
            result = sanitize(masked_prompt)
            result.metadata.update(metadata)
            masked_prompt = result.text
        else:
            result = MockResult(
                text=masked_prompt,
                metadata=metadata,
                has_pii=False
            )
        
        final_masked_prompt = masked_prompt
        llm_response_masked = None
        llm_response_restored = None
        
        if request.use_real_llm:
            llm_response_masked = call_llm(final_masked_prompt, result.metadata)
            llm_response_masked = validate_placeholders(llm_response_masked, result.metadata, is_mock=False)
            llm_response_restored = restore_placeholders(llm_response_masked, result.metadata)
        else:
            llm_response_masked = get_mock_response(final_masked_prompt)
            llm_response_restored = llm_response_masked
        
        return ChatResponse(
            original_prompt=original_prompt,
            masked_prompt=final_masked_prompt if request.use_privacy else "",
            metadata=result.metadata,
            llm_response_masked=llm_response_masked,
            llm_response_restored=llm_response_restored,
            has_pii=result.has_pii or len(fuzzy_entities) > 0 or len(metadata) > 0
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "hbp100 Privacy Firewall"}

@app.get("/warmup")
async def warmup():
    return {"status": "warm"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
