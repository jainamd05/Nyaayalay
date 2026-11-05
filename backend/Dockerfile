FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first so they are cached between code changes.
COPY requirements.txt pyproject.toml README.md /app/
COPY backend/requirements.txt /app/backend/requirements.txt
COPY src /app/src
RUN pip install -r requirements.txt -r backend/requirements.txt

COPY . /app

# Pre-download Chroma's embedding model into the image so the first request
# after a (cold) start does not have to fetch ~80 MB.
RUN python -c "import sys; sys.path.insert(0, 'src'); from nyayalay.retrieval import warm_up; print('records:', warm_up())"

EXPOSE 8000

# Render (and most PaaS) inject $PORT; default to 8000 locally.
CMD ["sh", "-c", "uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port ${PORT:-8000}"]
