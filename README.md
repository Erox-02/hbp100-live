
```markdown
#  hbp100 Demo — Pield Privacy Firewall

**See hbp100 in action. The LLM never sees your secrets.**

---

## Live Demo (Video)

[![Demo Video]


---

## Run Locally

```bash
git clone https://github.com/Erox-02/hbp100-demo
cd hbp100-demo

# Backend
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Frontend (new terminal)
cd frontend
pnpm install
pnpm run dev
Open http://localhost:5173

What You'll See
Step	What happens
1	Type a prompt with PII
2	hbp100 masks it → placeholders
3	Metadata vault stores mapping
4	LLM responds (mock) with placeholders
5	Restored response shows real data
The API never sees your data. The vault lives only in RAM.

Tech Stack
Layer	Tech
Backend	FastAPI + hbp100
Frontend	React + Tailwind + Vite
LLM	Mock (OpenRouter/DeepSeek ready)
Why This Matters
Most privacy tools:

Send your data to the cloud (ironic)

Are too heavy for edge devices

Destroy context (mask everything)

hbp100 fixes all three.

Related
hbp100 engine — PyPI package

Demo video — Full walkthrough

License
MIT
