# Opinion Search – Quick Setup

1. **Create virtual environment**  
   - Linux/macOS: `python3 -m venv venv && source venv/bin/activate`  
   - Windows: `python -m venv venv && venv\Scripts\activate`

2. **Install dependencies**  
   - `pip install -r requirements.txt`

3. **Create a `.env` file** in the project root  
   - Add: `OPENAI_API_KEY=...`  
   - Add: `BRIGHTDATA_API_KEY=...`

4. **Run the development server**  
   - `uvicorn app:app --reload`
   - OR: `python app.py`
   - OR: `uvicorn app:app --reload --host 0.0.0.0 --port 8000`

5. **Open in browser**  
   - Go to: `http://127.0.0.1:8000` (and `/docs` for API docs)
