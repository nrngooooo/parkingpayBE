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

class PaymentType(DjangoObjectType):
    class Meta:
        model = Payment

class CreatePayment(graphene.Mutation):
    class Arguments:
        session_id = graphene.ID()

    payment = graphene.Field(PaymentType)

    def mutate(self, info, session_id):
        session = ParkingSession.objects.get(id=session_id)

        # Calculate duration if not already done
        if not session.duration:
            duration = (session.exit_time - session.entry_time).total_seconds() // 60
            session.duration = int(duration)
            session.save()

        # Check for Tariff
        tariff = Tariff.objects.first()
        if not tariff:
            raise Exception("No tariff configured")

        # Calculate amount based on duration and tariff
        if session.duration <= tariff.free_duration:
            amount = 0
        else:
            extra_minutes = session.duration - tariff.free_duration
            amount = ((extra_minutes // 60) + (1 if extra_minutes % 60 > 0 else 0)) * tariff.hourly_rate

        # Create the payment entry
        payment = Payment.objects.create(
            session=session,
            amount=amount,
            payment_time=session.exit_time,  # Set the payment time to the exit time
        )

        return CreatePayment(payment=payment)
class ParkingSessionType(DjangoObjectType):
    class Meta:
        model = ParkingSession
    payment = graphene.Field(PaymentType)

class CarType(DjangoObjectType):
    parking_sessions = graphene.List(ParkingSessionType)

    class Meta:
        model = Car

    def resolve_parking_sessions(self, info):
        return self.parkingsession_set.all()

class TariffType(DjangoObjectType):
    class Meta:
        model = Tariff

class PaymentMethodType(DjangoObjectType):
    class Meta:
        model = PaymentMethod

class CreatePaymentInput(graphene.InputObjectType):
    session_id = graphene.Int(required=True)
    payment_method_id = graphene.Int(required=True)

class CreatePayment(graphene.Mutation):
    class Arguments:
        input = CreatePaymentInput()

    payment = graphene.Field(PaymentType)

    def mutate(self, info, input):
        session = ParkingSession.objects.get(pk=input.session_id)
        payment_method = PaymentMethod.objects.get(pk=input.payment_method_id)

        payment = Payment.objects.create(
            session=session,
            payment_method=payment_method
        )
        return CreatePayment(payment=payment)

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
            raise ValueError("Машины дугаарын формат буруу байна. 4 оронтой тоо байх ёстой.")
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
    all_parking_sessions = graphene.List(ParkingSessionType)
    all_payments = graphene.List(PaymentType)
    all_tariffs = graphene.List(TariffType)
    all_payment_methods = graphene.List(PaymentMethodType)
    search_car_by_plate = graphene.Field(
        CarType,
        car_plate=graphene.String(required=True),
    )
    car_details = graphene.Field(
        CarType,
        car_plate=graphene.String(required=True),
    )

    def resolve_all_payments(self, info):
        return Payment.objects.all()

    def resolve_all_tariffs(self, info):
        return Tariff.objects.all()

    def resolve_all_payment_methods(self, info):
        return PaymentMethod.objects.all()
    
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
            raise ValueError("Буруу формат. Машины улсын дугаарын эхний 4 цифрийг оруулна уу.")

        car = Car.objects.filter(car_plate__startswith=car_plate).first()
        return car  # Return None if no match

class Mutation(graphene.ObjectType):
    create_entry_car = CreateEntryCarMutation.Field()
    create_payment = CreatePayment.Field()
    
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
