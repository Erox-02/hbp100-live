```markdown
# 🐦 hbp100 — Hummingbird Precision 100

**322KB. 0.77ms. 100% precision. Faster than you blink.**
---

## What is hbp100?

A privacy firewall for LLM prompts. Detects PII, masks it, sends only placeholders to the LLM, then restores responses — so the API never sees real data.

**322KB. 0.77ms. 100% precision. Runs on your phone.**

---

## Install

```bash
pip install hbp100
```

---

Use

```python
from hbp100 import sanitize

# Email masking
result = sanitize("My email is john@gmail.com")
print(result.text)      # "My email is [EMAIL_1]"
print(result.metadata)  # {'[EMAIL_1]': 'john@gmail.com'}

# Context-aware: zodiac keeps year
result = sanitize("What's my zodiac for 1990?")
print(result.text)      # "What's my zodiac for 1990?"

# Context-aware: birth masks year
result = sanitize("I was born in 1990")
print(result.text)      # "I was born in [YEAR_ONLY_1]"
```

---

Numbers

Metric Value
Package size 322KB
Inference 0.77ms
Precision 100%
F1 Score 84%
PII types 40+

---

How It Works

```
Input → ML Detector (75KB) → Reasoner (context-aware) → Masker → Safe Text → LLM → Restore
```

1. Detector (Pridel) — 75KB LightGBM model finds PII
2. Reasoner — Decides MASK vs KEEP (zodiac keeps year, birth masks it)
3. Masker — Replaces values with placeholders
4. Restoration — Puts original values back in LLM response

---

Why hbp100?

 Microsoft Presidio hbp100
Size 70MB 322KB
Precision 85-90% 100%
Latency 10-50ms 0.77ms
Context-aware ❌ ✅
Edge-ready ❌ ✅
Offline ❌ ✅

---

Run the Demo

```bash
git clone https://github.com/Erox-02/hbp100-prot
cd hbp100-prot/backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# New terminal
cd ../frontend
pnpm install && npnm run dev
```

Open http://localhost:5173

---

License

MIT — use it, fork it, improve it.

---

pip install hbp100

Faster than you blink. 🔥

```
