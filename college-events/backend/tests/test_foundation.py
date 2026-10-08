def test_health_and_documentation():
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as client:
        assert client.get("/api/health").json()["status"] == "ok"
        schema = client.get("/openapi.json").json()
        assert "/api/health" in schema["paths"]
        assert client.get("/docs").status_code == 200
