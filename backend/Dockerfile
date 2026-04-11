FROM python:3.11-slim

WORKDIR /app

# System deps needed by scipy/numpy/matplotlib
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libgomp1 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Data directories — mount volumes over these in production
RUN mkdir -p cache/ahba_data cache/neurosynth_data cache/chroma_db cache/demo sessions

EXPOSE 8000

# Single worker: session store and correlation map store are in-process memory.
# For multi-worker deployments, replace with Redis session store + S3 map storage.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
