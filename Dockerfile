# استخدام Python 3.11 كصورة أساسية
FROM python:3.11-slim AS base

# بيئة ثابتة
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    APP_HOME=/app

WORKDIR $APP_HOME

# مستخدم غير جذر
RUN useradd --create-home --home-dir $APP_HOME appuser

COPY requirements.txt .

# تثبيت المتطلبات
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# أنشئ مجلد instance وأعطه للمستخدم غير الجذر
RUN mkdir -p $APP_HOME/instance && chown -R appuser:appuser $APP_HOME

EXPOSE 5000

USER appuser

# تشغيل التطبيق باستخدام Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "--timeout", "120", "app:app"]
