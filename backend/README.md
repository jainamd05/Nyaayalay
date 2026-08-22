# Nyayalay API

FastAPI layer between the React frontend and the Nyayalay core engine.

## Run

From the repository root:

```powershell
pip install -r requirements.txt
pip install -r backend/requirements.txt
uvicorn app.main:app --app-dir backend --reload
```

API:
- `GET /api/health`
- `POST /api/analysis`

Swagger:
- `http://127.0.0.1:8000/docs`
