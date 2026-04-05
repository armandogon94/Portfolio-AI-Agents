import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.integration
class TestCrewExecution:
    def test_build_crew(self):
        """Test crew assembly without executing."""
        with patch("src.crew.LLMFactory") as MockLLM:
            MockLLM.create.return_value = MagicMock()

            with patch("src.crew.AgentFactory") as MockAgentFactory:
                mock_agents = {
                    "researcher": MagicMock(),
                    "analyst": MagicMock(),
                    "writer": MagicMock(),
                    "validator": MagicMock(),
                }
                MockAgentFactory.return_value.create_all.return_value = mock_agents

                with patch("src.crew.TaskFactory") as MockTaskFactory:
                    MockTaskFactory.return_value.create_all.return_value = [
                        MagicMock() for _ in range(4)
                    ]

                    from src.crew import build_crew

                    crew = build_crew()
                    assert crew is not None

    def test_build_crew_with_domain(self):
        """Test crew assembly with domain override."""
        with patch("src.crew.LLMFactory") as MockLLM:
            MockLLM.create.return_value = MagicMock()

            with patch("src.crew.AgentFactory") as MockAgentFactory:
                mock_agents = {
                    "researcher": MagicMock(),
                    "analyst": MagicMock(),
                    "writer": MagicMock(),
                    "validator": MagicMock(),
                }
                MockAgentFactory.return_value.create_all.return_value = mock_agents

                with patch("src.crew.TaskFactory") as MockTaskFactory:
                    MockTaskFactory.return_value.create_all.return_value = [
                        MagicMock() for _ in range(4)
                    ]

                    from src.crew import build_crew

                    crew = build_crew(domain="healthcare")
                    MockAgentFactory.assert_called_with(domain="healthcare")


@pytest.mark.integration
class TestFastAPI:
    def test_health_endpoint(self):
        """Test the /health endpoint."""
        from fastapi.testclient import TestClient
        from src.main import app

        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "llm_provider" in data
        assert "embedding_mode" in data
