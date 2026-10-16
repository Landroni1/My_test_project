import factory

from parking_app.models import Client, Parking
from tests.factories import ClientFactory, ParkingFactory


def test_create_client_with_factory(client, db):
    initial_count = db.session.query(Client).count()

    client_data = factory.build(dict, FACTORY_CLASS=ClientFactory)
    if not client_data.get("credit_card"):
        client_data["credit_card"] = "4444-5555-6666-7777"

    response = client.post("/clients", json=client_data)
    assert response.status_code == 201

    data = response.get_json()
    assert "id" in data
    assert data["id"] is not None
    assert data["name"] == client_data["name"]
    assert data["surname"] == client_data["surname"]

    assert db.session.query(Client).count() == initial_count + 1

    created_client = db.session.get(Client, data["id"])
    assert created_client is not None
    assert created_client.car_number == client_data["car_number"]


def test_create_parking_with_factory(client, db):
    initial_count = db.session.query(Parking).count()

    parking_data = factory.build(dict, FACTORY_CLASS=ParkingFactory)

    response = client.post("/parkings", json=parking_data)
    assert response.status_code == 201

    data = response.get_json()
    assert "id" in data
    assert data["id"] is not None
    assert data["address"] == parking_data["address"]
    assert data["count_places"] == parking_data["count_places"]

    assert db.session.query(Parking).count() == initial_count + 1

    created_parking = db.session.get(Parking, data["id"])
    assert created_parking is not None
    assert created_parking.address == parking_data["address"]


def test_factories_direct_creation(db):
    initial_clients = db.session.query(Client).count()
    initial_parkings = db.session.query(Parking).count()

    new_client = ClientFactory()
    new_parking = ParkingFactory()

    assert new_client.id is not None
    assert new_parking.id is not None

    assert new_parking.count_available_places == new_parking.count_places

    assert db.session.query(Client).count() == initial_clients + 1
    assert db.session.query(Parking).count() == initial_parkings + 1
