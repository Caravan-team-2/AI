# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.10.12
FROM python:${PYTHON_VERSION}-slim as base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# OpenCV and YOLO optimizations for Docker
ENV OPENCV_IO_ENABLE_OPENEXR=1
ENV YOLO_VERBOSE=False
ENV TORCH_HOME=/app/cache
ENV QT_QPA_PLATFORM=offscreen
ENV YOLO_MODEL_DIR=/app/models
ENV HOME=/app
ENV EASYOCR_HOME=/app/cache

WORKDIR /app

# Install system dependencies for OCR, OpenCV, and YOLO
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       tesseract-ocr \
       tesseract-ocr-eng \
       libglib2.0-0 \
       libsm6 \
       libxext6 \
       libxrender1 \
       libgl1-mesa-glx \
       libgomp1 \
       libgtk-3-0 \
       libavcodec-dev \
       libavformat-dev \
       libswscale-dev \
       libv4l-dev \
       libxvidcore-dev \
       libx264-dev \
       libjpeg-dev \
       libpng-dev \
       libtiff-dev \
       libatlas-base-dev \
       gfortran \
       wget \
       curl \
       libfontconfig1 \
       libxfixes3 \
       libxi6 \
       libxrandr2 \
       libxss1 \
       libgconf-2-4 \
       libasound2 \
       libxtst6 \
       libpangocairo-1.0-0 \
       libatk1.0-0 \
       libcairo-gobject2 \
       libgdk-pixbuf2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Create non-privileged user
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

# Python deps
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --no-cache-dir torch==2.1.0+cpu torchvision==0.16.0+cpu -f https://download.pytorch.org/whl/torch_stable.html

RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install --no-cache-dir -r requirements.txt

# Create directories for model downloads and set permissions
RUN mkdir -p /app/models /app/cache && \
    chown -R appuser:appuser /app

# Pre-download YOLO model as root
RUN python -c "from ultralytics import YOLO; model = YOLO('yolov8n.pt'); print('Model downloaded successfully')" && \
    mv yolov8n.pt /app/models/ && \
    chown appuser:appuser /app/models/yolov8n.pt

USER appuser

COPY . .

EXPOSE 8001

CMD uvicorn 'fraud.main:app' --host=0.0.0.0 --port=8001