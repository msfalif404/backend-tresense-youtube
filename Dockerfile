# Menggunakan image python resmi
FROM python:3.9-slim

# Menetapkan direktori kerja
WORKDIR /app

# Menyalin file requirements.txt ke dalam image
COPY requirements.txt .

# Menginstal dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Menambahkan uvicorn sebagai dependency
RUN pip install uvicorn

# Menyalin semua file aplikasi
COPY . .

# Menentukan variabel lingkungan untuk PORT
ENV PORT=8080

# Menjalankan aplikasi menggunakan uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
