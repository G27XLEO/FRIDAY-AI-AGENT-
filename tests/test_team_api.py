"""Unit tests discovered by the existing Docker/CI unittest command."""
import asyncio
import os
import tempfile
import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from friday_agent import team_api


class AgentTeamTests(unittest.TestCase):
    def test_store_routing_and_collaboration(self):
        with tempfile.TemporaryDirectory() as directory:
            store = team_api.TeamStore(os.path.join(directory, "team.sqlite"))
            self.assertEqual(len(store.agents()), 6)
            thread = store.create_thread("Plan a secure React app")
            calls = []

            async def fake_model(system, prompt):
                calls.append((system, prompt))
                return "Proposed steps; not executed."

            engine = team_api.TeamEngine(store, fake_model)
            response = asyncio.run(engine.run(
                thread["id"], "Build a secure React app", ["engineer", "security"]
            ))
            self.assertEqual(response["agents_used"], ["engineer", "security"])
            self.assertEqual(
                [message["speaker"] for message in response["messages"]],
                ["user", "agent", "agent", "coordinator"],
            )
            self.assertEqual(len(calls), 3)
            self.assertEqual(
                store.messages(thread["id"])[-1]["content"],
                "Proposed steps; not executed.",
            )

    def test_api_auth_and_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {
                "FRIDAY_TEAM_DB": os.path.join(directory, "api.sqlite"),
                "FRIDAY_TEAM_API_TOKEN": "unit-test-secret",
            }):
                team_api.get_store.cache_clear()
                team_api.get_engine.cache_clear()
                try:
                    app = FastAPI()
                    app.include_router(team_api.router)
                    client = TestClient(app)
                    self.assertEqual(client.get("/api/team/agents").status_code, 401)
                    self.assertEqual(client.get("/api/team/threads").status_code, 401)
                    headers = {"Authorization": "Bearer unit-test-secret"}
                    self.assertEqual(
                        len(client.get("/api/team/agents", headers=headers).json()), 6
                    )
                    created = client.post(
                        "/api/team/threads", headers=headers,
                        json={"title": "My team"},
                    )
                    self.assertEqual(created.status_code, 201)
                    invalid = client.post(
                        "/api/team/threads/" + created.json()["id"] + "/messages",
                        headers=headers,
                        json={"content": "Hello", "agent_ids": ["made-up"]},
                    )
                    self.assertEqual(invalid.status_code, 422)
                    self.assertEqual(
                        client.get("/api/team/threads/missing",
                                   headers=headers).status_code, 404
                    )
                finally:
                    team_api.get_engine.cache_clear()
                    team_api.get_store.cache_clear()

    def test_missing_token_disables_private_endpoints(self):
        with patch.dict(os.environ, {}, clear=True):
            app = FastAPI()
            app.include_router(team_api.router)
            self.assertEqual(
                TestClient(app).get("/api/team/agents").status_code, 503
            )


if __name__ == "__main__":
    unittest.main()
