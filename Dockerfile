# =========================
# Builder stage
# =========================
FROM python:3.12-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt


# =========================
# Runtime stage
# =========================
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy source code
COPY . .

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# ❌ KHÔNG EXPOSE PORT CỐ ĐỊNH
# ❌ KHÔNG HEALTHCHECK PORT CỐ ĐỊNH

# =========================
# Run app (Railway compatible)
# =========================
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
