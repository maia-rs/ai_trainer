from fastapi.testclient import TestClient

from app.main import app
from app.service.agente_service import AgenteService


def test_agente_chat_sucesso(monkeypatch):
    def _fake_conversar(self, mensagem: str, thread_id: str):
        return {
            "thread_id": thread_id,
            "model": "mock-model",
            "resposta": f"eco: {mensagem}",
        }

    monkeypatch.setattr(AgenteService, "conversar", _fake_conversar)

    client = TestClient(app)
    response = client.post(
        "/agente/chat",
        json={
            "mensagem": "Crie um treino para hoje",
            "thread_id": "usuario-123",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["thread_id"] == "usuario-123"
    assert payload["model"] == "mock-model"
    assert payload["resposta"] == "eco: Crie um treino para hoje"


def test_agente_chat_sem_mensagem():
    client = TestClient(app)
    response = client.post("/agente/chat", json={"thread_id": "usuario-123"})
    assert response.status_code == 422


def test_agente_chat_sem_thread_id():
    client = TestClient(app)
    response = client.post("/agente/chat", json={"mensagem": "oi"})
    assert response.status_code == 422


def test_agente_health_ok(monkeypatch):
    def _fake_health_ok():
        return (
            {
                "status": "ok",
                "provider": "groq",
                "checks": {
                    "groq_api_key": True,
                    "groq_model": "llama-3.3-70b-versatile",
                    "langsmith_enabled": True,
                    "langsmith_api_key": True,
                },
            },
            200,
        )

    monkeypatch.setattr(AgenteService, "verificar_health", staticmethod(_fake_health_ok))

    client = TestClient(app)
    response = client.get("/agente/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["provider"] == "groq"


def test_agente_health_incompleto(monkeypatch):
    def _fake_health_error():
        return (
            {
                "status": "error",
                "provider": "groq",
                "checks": {
                    "groq_api_key": False,
                    "groq_model": None,
                    "langsmith_enabled": False,
                    "langsmith_api_key": False,
                },
                "missing": ["GROQ_API_KEY", "GROQ_MODEL"],
            },
            503,
        )

    monkeypatch.setattr(AgenteService, "verificar_health", staticmethod(_fake_health_error))

    client = TestClient(app)
    response = client.get("/agente/health")

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "error"
    assert "GROQ_API_KEY" in payload["missing"]
