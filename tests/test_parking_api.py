from datetime import datetime

import pytest

from parking_app.models import Client, ClientParking, Parking


@pytest.mark.parametrize(
    "url",
    [
        "/clients",
        "/clients/1",
    ],
)
def test_get_methods_status_200(client, url):
    response = client.get(url)
    assert response.status_code == 200
    assert response.is_json


def test_create_client(client, db):
    payload = {
        "name": "Петр",
        "surname": "Петров",
        "credit_card": "5555-6666-7777-8888",
        "car_number": "В777ВВ99",
    }
    response = client.post("/clients", json=payload)
    assert response.status_code == 201

    data = response.get_json()
    assert data["name"] == payload["name"]
    assert data["surname"] == payload["surname"]
    assert data["credit_card"] == payload["credit_card"]
    assert data["car_number"] == payload["car_number"]

    new_client = db.session.get(Client, data["id"])
    assert new_client is not None
    assert new_client.surname == "Петров"


def test_create_parking(client, db):
    payload = {
        "address": "г. Москва, ул. Арбат, д. 5",
        "count_places": 25,
        "count_available_places": 25,
        "opened": True,
    }
    response = client.post("/parkings", json=payload)
    assert response.status_code == 201

    data = response.get_json()
    assert data["address"] == payload["address"]
    assert data["count_places"] == 25
    assert data["count_available_places"] == 25
    assert data["opened"] is True

    parking_record = db.session.get(Parking, data["id"])
    assert parking_record is not None
    assert parking_record.address == payload["address"]


@pytest.mark.parking
def test_enter_parking_success(client, db):
    parking = Parking(
        address="ул. Мира, 1", opened=True, count_places=5, count_available_places=5
    )
    test_client = Client(
        name="Алексей", surname="Смирнов", credit_card="1234", car_number="Х001ХХ"
    )
    db.session.add_all([parking, test_client])
    db.session.commit()

    initial_places = parking.count_available_places

    response = client.post(
        "/client_parkings", json={"client_id": test_client.id, "parking_id": parking.id}
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["time_in"] is not None
    assert data["time_out"] is None

    db.session.refresh(parking)
    assert parking.count_available_places == initial_places - 1


@pytest.mark.parking
def test_exit_parking_success(client, db):
    parking = Parking(
        address="ул. Тверская, 1",
        opened=True,
        count_places=10,
        count_available_places=9,
    )
    test_client = Client(
        name="Ольга",
        surname="Соколова",
        credit_card="9999-8888-7777-6666",
        car_number="М002ММ",
    )
    db.session.add_all([parking, test_client])
    db.session.commit()

    entry_time = datetime.now()
    parking_session = ClientParking(
        client_id=test_client.id,
        parking_id=parking.id,
        time_in=entry_time,
        time_out=None,
    )
    db.session.add(parking_session)
    db.session.commit()

    initial_places = parking.count_available_places

    response = client.delete(
        "/client_parkings", json={"client_id": test_client.id, "parking_id": parking.id}
    )

    assert response.status_code == 200
    db.session.refresh(parking)
    db.session.refresh(parking_session)

    assert parking.count_available_places == initial_places + 1
    assert parking_session.time_out is not None
    assert parking_session.time_out >= parking_session.time_in


@pytest.mark.parking
def test_enter_closed_parking_fails(client, db):
    """Нельзя заехать на закрытую парковку."""
    parking = Parking(
        address="ул. Закрытая, 1",
        opened=False,
        count_places=10,
        count_available_places=10,
    )
    test_client = Client(name="Иван", surname="Иванов", credit_card="1111")
    db.session.add_all([parking, test_client])
    db.session.commit()

    response = client.post(
        "/client_parkings", json={"client_id": test_client.id, "parking_id": parking.id}
    )
    assert response.status_code == 400
    assert "closed" in response.get_json()["error"]


@pytest.mark.parking
def test_enter_parking_no_places_fails(client, db):
    """Нельзя заехать, если мест нет."""
    parking = Parking(
        address="ул. Полная, 2", opened=True, count_places=5, count_available_places=0
    )
    test_client = Client(name="Иван", surname="Иванов", credit_card="1111")
    db.session.add_all([parking, test_client])
    db.session.commit()

    response = client.post(
        "/client_parkings", json={"client_id": test_client.id, "parking_id": parking.id}
    )
    assert response.status_code == 400
    assert "No available parking places" in response.get_json()["error"]


@pytest.mark.parking
def test_exit_without_credit_card_fails(client, db):
    """Нельзя оплатить и выехать без привязанной кредитной карты."""
    parking = Parking(
        address="ул. Платная, 3", opened=True, count_places=5, count_available_places=4
    )
    # Клиент без карты
    test_client = Client(name="Без", surname="Карты", credit_card=None)
    db.session.add_all([parking, test_client])
    db.session.commit()

    active_session = ClientParking(
        client_id=test_client.id, parking_id=parking.id, time_in=datetime.now()
    )
    db.session.add(active_session)
    db.session.commit()

    response = client.delete(
        "/client_parkings", json={"client_id": test_client.id, "parking_id": parking.id}
    )
    assert response.status_code == 400
    assert "credit card" in response.get_json()["error"].lower()
