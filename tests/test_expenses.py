import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from main import app, get_session


@pytest.fixture
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass= StaticPool)
    SQLModel.metadata.create_all(engine)

    def override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override 
    yield TestClient(app)
    app.dependency_overrides.clear()

def add(client, **fields):
    body = {"title": "Lunch", "amount":250, "category": "Food", **fields}
    return client.post("/expenses", json=body)

def test_create_expense(client):
    res=add(client)
    assert res.status_code == 201
    assert res.json()["id"] == 1

def test_negative_amount_rejected(client):
    assert add(client, amount = -5).status_code == 422

def test_missing_expense_returns_404(client):
    assert client.get("/expenses/999").status_code == 404

def test_update_keeps_original_date(client):
    add(client, spent_on = "2026-10-01")
    res = client.put("/expenses/1", json={"title": "Lunch", "amount": 300, "category":"food"})
    assert res.json()["amount"] == 300
    assert res.json()["spent_on"] == "2026-10-01"

def test_delete_expense(client):
    add(client)
    assert client.delete("/expenses/1").status_code == 204
    assert client.get("/expenses/1").status_code == 404

def test_summary_totals(client):
    add(client, amount = 100)
    add(client, amount = 50.5)
    add(client, category="bills", amount = 900)
    assert client.get("/expenses/summary").json() == {"Food": 150.5, "bills": 900.0}




      