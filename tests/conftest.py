from datetime import datetime, timedelta
import pytest
from parking_app import create_app
from parking_app.models import db as _db, Client, Parking, ClientParking


class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


@pytest.fixture
def app():
    _app = create_app(TestConfig)

    with _app.app_context():
        _db.create_all()

        test_client = Client(
            name='Тест',
            surname='Тестов',
            credit_card='1111-2222-3333-4444',
            car_number='А001АА77'
        )
        _db.session.add(test_client)

        test_parking = Parking(
            address='г. Москва, ул. Тестовая, д. 1',
            opened=True,
            count_places=10,
            count_available_places=10
        )
        _db.session.add(test_parking)
        _db.session.commit()

        time_in = datetime.now() - timedelta(hours=2)
        time_out = datetime.now() - timedelta(hours=1)
        test_log = ClientParking(
            client_id=test_client.id,
            parking_id=test_parking.id,
            time_in=time_in,
            time_out=time_out
        )
        _db.session.add(test_log)
        _db.session.commit()

        yield _app

        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    """Тестовый клиент Flask для выполнения HTTP-запросов."""
    return app.test_client()


@pytest.fixture
def db(app):
    """Сессия базы данных для проверки изменений внутри тестов."""
    return _db