# استخدام Python رسمي كصورة أساسية
FROM python:3.10-slim

# تعيين دليل العمل
WORKDIR /app

# نسخ ملف المتطلبات
COPY backend/requirements.txt .

# تثبيت المتطلبات
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي الملفات
COPY . .

# تشغيل كمدخل غير جذر
RUN useradd -m -u 1000 therabot
USER therabot

# تشغيل التطبيق
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]