FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY friday_agent ./friday_agent

RUN useradd --create-home --uid 10001 friday
USER friday

CMD ["python", "-m", "friday_agent.livekit_agent", "start"]
