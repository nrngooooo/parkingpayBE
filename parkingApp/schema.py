from django.db import transaction
import traceback
from django.db.models import Q
import graphene
from .models import *
from django.core.files.storage import default_storage
from graphene_django import DjangoObjectType
from graphene import Mutation
import logging
logger = logging.getLogger("main")
from datetime import datetime

class CarType(DjangoObjectType):
    class Meta:
        model = Car

class ParkingSessionType(DjangoObjectType):
    class Meta:
        model = ParkingSession

class CreateParkingSession(graphene.Mutation):
    class Arguments:
        car_plate = graphene.String(required=True)
        entry_photo = graphene.String(required=False)  # The entry photo as a base64 or URL

    session = graphene.Field(ParkingSessionType)

    def mutate(self, info, car_plate, entry_photo=None):
        # Create or get car by license plate number
        car, created = Car.objects.get_or_create(car_plate=car_plate)
        
        # If there's an entry photo, save it
        if entry_photo:
            # Save the entry photo
            # For simplicity, assuming the photo is base64, you'll need to handle base64 decoding
            file_name = f"car_photos/entry/{car_plate}_entry.jpg"
            photo = default_storage.save(file_name, entry_photo)

            # Save the entry photo to the car object
            car.entry_photo = photo
            car.save()

        # Create a new ParkingSession
        session = ParkingSession.objects.create(
            car=car,
            entry_time=datetime.now(),
            exit_time=None,  # Exit time will be set later
            duration=None,   # Duration will be calculated later
        )

        return CreateParkingSession(session=session)

class Mutation(graphene.ObjectType):
    create_parking_session = CreateParkingSession.Field()

class Query(graphene.ObjectType):
    all_sessions = graphene.List(ParkingSessionType)

    def resolve_all_sessions(self, info):
        return ParkingSession.objects.all()
    
class AtomicSchema(graphene.Schema):
    def execute(self, *args, **kwargs):
        with transaction.atomic():
            result = super().execute(*args, **kwargs)
            if result.errors:
                transaction.set_rollback(True)
                logger.error(
                    f"GQL Error Traceback: {result.errors}",
                    extra={"details": traceback.format_exc()},
                )
            return result

schema = AtomicSchema(query=Query, mutation=Mutation)
