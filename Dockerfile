FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY friday_agent ./friday_agent
CMD ["python", "-m", "friday_agent.livekit_agent", "start"]
