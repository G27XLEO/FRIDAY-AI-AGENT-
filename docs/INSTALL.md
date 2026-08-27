# FRIDAY Installation Guide

This guide covers the supported development environments. The FRIDAY core is a Python/LiveKit worker; a client may run on another platform and connect through LiveKit.

## Prerequisites

- Git
- Python 3.12 recommended
- Network access
- LiveKit project credentials
- Groq API key
- ElevenLabs API key
- Docker for container deployment

## Linux

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip

git clone https://github.com/G27XLEO/FRIDAY-AI-AGENT-.git
cd FRIDAY-AI-AGENT-
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
nano .env
python -m friday_agent.livekit_agent dev
```

## Ubuntu / WSL2

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip

git clone https://github.com/G27XLEO/FRIDAY-AI-AGENT-.git
cd FRIDAY-AI-AGENT-
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Then start the worker:

```bash
python -m friday_agent.livekit_agent dev
```

## macOS

Using Homebrew:

```bash
brew install git python@3.12

git clone https://github.com/G27XLEO/FRIDAY-AI-AGENT-.git
cd FRIDAY-AI-AGENT-
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python -m friday_agent.livekit_agent dev
```

## Windows PowerShell

```powershell
winget install --id Git.Git -e
winget install --id Python.Python.3.12 -e

git clone https://github.com/G27XLEO/FRIDAY-AI-AGENT-.git
Set-Location FRIDAY-AI-AGENT-
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m friday_agent.livekit_agent dev
```

If PowerShell blocks activation, use:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## Android / Termux

```bash
pkg update -y
pkg upgrade -y
pkg install -y git python clang make pkg-config

git clone https://github.com/G27XLEO/FRIDAY-AI-AGENT-.git
cd FRIDAY-AI-AGENT-
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Run the MCP server locally:

```bash
python -m friday_agent.mcp_server
```

Run the LiveKit worker locally when all native dependencies are available:

```bash
python -m friday_agent.livekit_agent dev
```

For devices where a binary dependency cannot build under Termux, keep Termux as the operator/development terminal and run the worker in Docker or on a Linux server.

## Docker (recommended production path)

```bash
git clone https://github.com/G27XLEO/FRIDAY-AI-AGENT-.git
cd FRIDAY-AI-AGENT-
cp .env.example .env
# Fill .env with secrets locally or inject them through your deployment platform.
docker build --pull -t friday-ai-agent .
docker run --rm --env-file .env friday-ai-agent
```

## Start MCP + worker together

Linux/macOS/WSL2/Termux:

```bash
chmod +x scripts/run_background.sh
./scripts/run_background.sh
```

## Verify installation

```bash
python -m unittest discover -v
python -m compileall friday_agent tests
git diff --check
```

## Environment

Never commit `.env`. Use `.env.example` as the safe template and configure production values through a secret manager or GitHub Actions Secrets.

Required variables:

```text
LIVEKIT_URL
LIVEKIT_API_KEY
LIVEKIT_API_SECRET
GROQ_API_KEY
ELEVENLABS_API_KEY
```

Optional model/voice variables are documented in `.env.example`.

## Client platforms

Web, Android, iOS, and desktop clients can be built separately around the LiveKit connection. This repository provides the reusable FRIDAY worker and MCP runtime rather than pretending to be a native application for every client OS.
