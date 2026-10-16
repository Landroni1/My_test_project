from datetime import datetime
from flask import Blueprint, request, jsonify
from .models import db, Client, Parking, ClientParking

api_bp = Blueprint("api", __name__)


@api_bp.route("/clients", methods=["GET"])
def get_clients():
    clients = Client.query.all()
    return jsonify([client.to_dict() for client in clients]), 200


@api_bp.route("/clients/<int:client_id>", methods=["GET"])
def get_client(client_id):
    # Заменяем Client.query.get(client_id) на db.session.get
    client = db.session.get(Client, client_id)
    if not client:
        return jsonify({"error": "Client not found"}), 404
    return jsonify(client.to_dict()), 200


@api_bp.route("/clients", methods=["POST"])
def create_client():
    data = request.get_json() or {}
    name = data.get("name")
    surname = data.get("surname")

    if not name or not surname:
        return jsonify({"error": 'Fields "name" and "surname" are required'}), 400

    new_client = Client(
        name=name,
        surname=surname,
        credit_card=data.get("credit_card"),
        car_number=data.get("car_number"),
    )
    db.session.add(new_client)
    db.session.commit()

    return jsonify(new_client.to_dict()), 201


@api_bp.route("/parkings", methods=["POST"])
def create_parking():
    data = request.get_json() or {}
    address = data.get("address")
    count_places = data.get("count_places")

    if not address or count_places is None:
        return (
            jsonify({"error": 'Fields "address" and "count_places" are required'}),
            400,
        )

    count_available_places = data.get("count_available_places", count_places)
    opened = data.get("opened", True)

    new_parking = Parking(
        address=address,
        opened=opened,
        count_places=count_places,
        count_available_places=count_available_places,
    )
    db.session.add(new_parking)
    db.session.commit()

    return jsonify(new_parking.to_dict()), 201


@api_bp.route("/client_parkings", methods=["POST"])
def enter_parking():
    data = request.get_json() or {}
    client_id = data.get("client_id")
    parking_id = data.get("parking_id")

    if not client_id or not parking_id:
        return (
            jsonify({"error": 'Fields "client_id" and "parking_id" are required'}),
            400,
        )

    client = db.session.get(Client, client_id)
    if not client:
        return jsonify({"error": "Client not found"}), 404

    parking = db.session.get(Parking, parking_id)
    if not parking:
        return jsonify({"error": "Parking not found"}), 404

    if not parking.opened:
        return jsonify({"error": "Parking is closed"}), 400

    if parking.count_available_places <= 0:
        return jsonify({"error": "No available parking places"}), 400

    active_parking = ClientParking.query.filter_by(
        client_id=client_id, parking_id=parking_id, time_out=None
    ).first()
    if active_parking:
        return jsonify({"error": "Client is already in this parking"}), 400

    record = ClientParking.query.filter_by(
        client_id=client_id, parking_id=parking_id
    ).first()
    current_time = datetime.now()

    if record:
        record.time_in = current_time
        record.time_out = None
    else:
        record = ClientParking(
            client_id=client_id, parking_id=parking_id, time_in=current_time
        )
        db.session.add(record)

    parking.count_available_places -= 1
    db.session.commit()

    return jsonify(record.to_dict()), 201


@api_bp.route("/client_parkings", methods=["DELETE"])
def exit_parking():
    data = request.get_json() or {}
    client_id = data.get("client_id")
    parking_id = data.get("parking_id")

    if not client_id or not parking_id:
        return (
            jsonify({"error": 'Fields "client_id" and "parking_id" are required'}),
            400,
        )

    client = db.session.get(Client, client_id)
    if not client:
        return jsonify({"error": "Client not found"}), 404

    if not client.credit_card:
        return jsonify({"error": "Client has no credit card attached for payment"}), 400

    parking = db.session.get(Parking, parking_id)
    if not parking:
        return jsonify({"error": "Parking not found"}), 404

    record = ClientParking.query.filter_by(
        client_id=client_id, parking_id=parking_id, time_out=None
    ).first()

    if not record:
        return jsonify({"error": "Client is not currently parked at this parking"}), 404

    record.time_out = datetime.now()

    if parking.count_available_places < parking.count_places:
        parking.count_available_places += 1

    db.session.commit()

    return (
        jsonify(
            {
                "message": "Successfully checked out and payment processed",
                "record": record.to_dict(),
            }
        ),
        200,
    )
