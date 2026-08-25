FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt

COPY friday_agent ./friday_agent
COPY tests ./tests

RUN python -m compileall -q friday_agent tests \
    && useradd --create-home --uid 10001 friday \
    && chown -R friday:friday /app

USER friday

CMD ["python", "-m", "friday_agent.livekit_agent", "start"]
