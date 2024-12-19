from django.db import transaction
import traceback
from django.db.models import Q
import graphene
from parkingApp.models import *
from django.core.files.storage import default_storage
from graphene_django import DjangoObjectType
from graphene import Mutation
import logging
import re
import base64
from django.core.files.base import ContentFile

logger = logging.getLogger("main")

class CarType(DjangoObjectType):
    class Meta:
        model = Car

class ParkingSessionType(DjangoObjectType):
    class Meta:
        model = ParkingSession

# Input for the mutation
class CreateEntryCarInput(graphene.InputObjectType):
    car_plate = graphene.String(required=True)
    image = graphene.String(required=True)  # Assume Base64-encoded image

class CreateEntryCarMutation(graphene.Mutation):
    class Arguments:
        input = CreateEntryCarInput(required=True)

    car = graphene.Field(CarType)
    parking_session = graphene.Field(ParkingSessionType)

    def mutate(self, info, input):
        car_plate = input["car_plate"]
        image_data = input["image"]

        # Validate car_plate format
        if not re.match(r"^\d{4}[А-Я]{3}$", car_plate):
            raise ValueError("Invalid car plate format.")
        
        try:
            decoded_image = base64.b64decode(image_data)
        except (TypeError, ValueError):
            raise ValueError("Invalid Base64-encoded image.")
        
        # Save Car
        car, created = Car.objects.get_or_create(car_plate=car_plate)
        car.entry_photo.save(f"{car_plate}_entry.jpg", ContentFile(decoded_image))

        # Check for active sessions
        if ParkingSession.objects.filter(car=car, exit_time__isnull=True).exists():
            raise ValueError("This car already has an active session.")
        
        # Create Parking Session
        parking_session = ParkingSession.objects.create(car=car)

        return CreateEntryCarMutation(car=car, parking_session=parking_session)

class Mutation(graphene.ObjectType):
    create_entry_car = CreateEntryCarMutation.Field()

class Query(graphene.ObjectType):
    all_sessions = graphene.List(ParkingSessionType)

    def resolve_all_sessions(self, info):
        return ParkingSession.objects.select_related("car").all()
    
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
