def test_health(client):
    assert client.get("/health").get_json() == {"status": "ok"}


def test_cors_header_for_allowed_origin(client):
    response = client.get("/api/jobs", headers={"Origin": "http://localhost:5173"})
    assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"


def test_no_cors_header_for_other_origin(client):
    response = client.get("/api/jobs", headers={"Origin": "http://evil.example"})
    assert "Access-Control-Allow-Origin" not in response.headers


def test_unknown_route_returns_json_404(client):
    response = client.get("/api/nothing-here")
    assert response.status_code == 404
    assert response.get_json() == {"error": "Not found"}
