# Gunakan image Python ringan dan stabil
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy dan install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Salin seluruh isi proyek ke dalam container
COPY . .

# Cloud Run mengharuskan aplikasi mendengarkan pada port 8080
ENV PORT 8080

# Jalankan FastAPI dengan Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]