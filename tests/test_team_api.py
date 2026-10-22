"""Agent Team persistence, routing, orchestration and token boundary."""
import asyncio

from fastapi import FastAPI
from fastapi.testclient import TestClient

from friday_agent import team_api


def test_store_and_cooperation(tmp_path):
    store = team_api.TeamStore(str(tmp_path / "team.sqlite"))
    assert len(store.agents()) == 6
    thread = store.create_thread("Plan a secure React app")
    calls = []

    async def fake_model(system, prompt):
        calls.append(system)
        return "Proposed steps; not executed."

    engine = team_api.TeamEngine(store, fake_model)
    response = asyncio.run(engine.run(
        thread["id"], "Build a secure React app", ["engineer", "security"]
    ))
    assert response["agents_used"] == ["engineer", "security"]
    assert [message["speaker"] for message in response["messages"]] == [
        "user", "agent", "agent", "coordinator"
    ]
    assert len(calls) == 3
    assert store.messages(thread["id"])[-1]["content"] == "Proposed steps; not executed."


def test_auth_and_validation(tmp_path, monkeypatch):
    monkeypatch.setenv("FRIDAY_TEAM_DB", str(tmp_path / "api.sqlite"))
    monkeypatch.setenv("FRIDAY_TEAM_API_TOKEN", "unit-test-secret")
    team_api.get_store.cache_clear()
    team_api.get_engine.cache_clear()
    app = FastAPI()
    app.include_router(team_api.router)
    client = TestClient(app)
    assert client.get("/api/team/agents").status_code == 401
    assert client.get("/api/team/threads").status_code == 401
    headers = {"Authorization": "Bearer unit-test-secret"}
    assert len(client.get("/api/team/agents", headers=headers).json()) == 6
    created = client.post(
        "/api/team/threads", headers=headers, json={"title": "My team"}
    )
    assert created.status_code == 201
    invalid = client.post(
        "/api/team/threads/" + created.json()["id"] + "/messages",
        headers=headers,
        json={"content": "Hello", "agent_ids": ["made-up"]},
    )
    assert invalid.status_code == 422
    assert client.get("/api/team/threads/missing", headers=headers).status_code == 404
    team_api.get_store.cache_clear()
    team_api.get_engine.cache_clear()


def test_missing_token_disabled(monkeypatch):
    monkeypatch.delenv("FRIDAY_TEAM_API_TOKEN", raising=False)
    app = FastAPI()
    app.include_router(team_api.router)
    assert TestClient(app).get("/api/team/agents").status_code == 503
