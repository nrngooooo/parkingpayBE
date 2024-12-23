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


class ParkingSessionType(DjangoObjectType):
    class Meta:
        model = ParkingSession

class CarType(DjangoObjectType):
    parking_sessions = graphene.List(ParkingSessionType)

    class Meta:
        model = Car

    def resolve_parking_sessions(self, info):
        return self.parkingsession_set.all()
    
class PaymentType(DjangoObjectType):
    class Meta:
        model = Payment

# Input for the mutation
class CreateEntryCarInput(graphene.InputObjectType):
    car_plate = graphene.String(required=True)
    entry_photo = graphene.String(required=True)  # Assume Base64-encoded entry_photo

class CreateEntryCarMutation(graphene.Mutation):
    class Arguments:
        input = CreateEntryCarInput(required=True)

    car = graphene.Field(CarType)
    parking_session = graphene.Field(ParkingSessionType)

    def mutate(self, info, input):
        car_plate = input["car_plate"]
        entry_photo = input["entry_photo"]

        # Validate car_plate format
        if not re.match(r"^\d{4}$", car_plate):  # Only validate the first 4 digits
            raise ValueError("Invalid car plate format. Expected 4 digits.")
        try:
            decoded_image = base64.b64decode(entry_photo)
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

class Query(graphene.ObjectType):
    all_sessions = graphene.List(ParkingSessionType)

    search_car_by_plate = graphene.Field(
        CarType,
        car_plate=graphene.String(required=True),
    )
    car_details = graphene.Field(
        CarType,
        car_plate=graphene.String(required=True),
    )

    def resolve_all_sessions(self, info):
        return ParkingSession.objects.select_related("car").all()

    def resolve_car_details(self, info, car_plate):
        try:
            car = Car.objects.get(car_plate=car_plate)
            return car
        except Car.DoesNotExist:
            return None
        
    def resolve_search_car_by_plate(self, info, car_plate):
    # Validate car_plate format to ensure it's 4 digits
        if not re.match(r"^\d{4}$", car_plate):
            raise ValueError("Invalid format. Enter the first 4 digits of the car plate.")

        car = Car.objects.filter(car_plate__startswith=car_plate).first()
        return car  # Return None if no match

class Mutation(graphene.ObjectType):
    create_entry_car = CreateEntryCarMutation.Field()
    
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
