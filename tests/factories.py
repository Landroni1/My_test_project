import factory
from factory import fuzzy
from parking_app.models import db, Client, Parking


class ClientFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Client
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'commit'

    name = factory.Faker('first_name')
    surname = factory.Faker('last_name')
    credit_card = fuzzy.FuzzyChoice([None, '1234-5678-9012-3456', '9876-5432-1098-7654'])
    car_number = factory.Faker('bothify', text='?###??##')


class ParkingFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Parking
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'commit'

    address = factory.Faker('address')
    opened = factory.Faker('boolean')
    count_places = factory.Faker('random_int', min=10, max=100)
    count_available_places = factory.LazyAttribute(lambda obj: obj.count_places)