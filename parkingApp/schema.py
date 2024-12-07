from django.db import transaction
import traceback
from django.db.models import Q
import graphene
from parkingApp.models import *
from graphene_django import DjangoObjectType
from graphene import Mutation
import logging
logger = logging.getLogger("main")
from .utils import process_image  # Import the above utility function

class CarType(DjangoObjectType):
    class Meta:
        model = Car

class ParkingSessionType(DjangoObjectType):
    class Meta:
        model = ParkingSession

class VehicleEntryMutation(graphene.Mutation):
    class Arguments:
        photo = graphene.String(required=True)  # Base64 encoded image

    car = graphene.Field(CarType)
    parking_session = graphene.Field(ParkingSessionType)

    def mutate(self, info, photo):
        from django.core.files.base import ContentFile
        import base64

        try:
            # Decode the base64 image
            format, imgstr = photo.split('data:image/jpeg;base64,')
            ext = format.split('/')[-1]
            photo_file = ContentFile(base64.b64decode(imgstr), name=f"entry.{ext}")
            print("Image decoded successfully.")

            # Process the image
            try:
                car_plate, cropped_plate_photo = process_image(photo_file)
            except Exception as e:
                print(f"Image processing failed: {e}")
                raise Exception("Image processing failed. Please check the image.")

            print(f"Car Plate: {car_plate}")

            # Save or update car in the database
            car, created = Car.objects.get_or_create(car_plate=car_plate)
            car.entry_photo.save(f"entry_photo.{ext}", photo_file, save=False)
            car.cropped_plate_photo.save("cropped_plate.jpg", cropped_plate_photo, save=False)
            car.save()
            print("Car saved successfully.")

            # Create a parking session
            session = ParkingSession.objects.create(car=car)
            print("Parking session created successfully.")

            return VehicleEntryMutation(car=car, parking_session=session)

        except Exception as e:
            print(f"Mutation failed: {e}")
            raise e

class Mutation(graphene.ObjectType):
    vehicle_entry = VehicleEntryMutation.Field()

class Query(graphene.ObjectType):
    parking_sessions = graphene.List(ParkingSessionType)

    def resolve_parking_sessions(self, info):
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
