from django.db import models

class Car(models.Model):
    car_plate = models.CharField(max_length=7, unique=True, null=True, blank=True)  # License plate number
    entry_photo = models.ImageField(upload_to='car_photos/entry/', null=True, blank=True)  # Entry photo
    is_employee_car = models.BooleanField(default=False)  # Whether the car belongs to an employee
    def __str__(self):
        return self.car_plate

class PaymentMethod(models.Model):
    method_name = models.CharField(max_length=50)  # Payment method name
    qr = models.ImageField(upload_to='payment_qrs/', null=True, blank=True)  # QR code for payment
    logo = models.ImageField(upload_to='payment_logos/', null=True, blank=True)  # Payment method logo

    def __str__(self):
        return self.method_name
    
class ParkingSession(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE)  # Related car
    entry_time = models.DateTimeField(auto_now_add=True)  # Entry time
    paid_status = models.BooleanField(default=False)  # Payment status
    exit_time = models.DateTimeField(null=True, blank=True)  # Exit time
    exit_photo = models.ImageField(upload_to='car_photos/exit/', null=True, blank=True)  # Exit photo

    def __str__(self):
        return f"Session {self.id} - {self.car.car_plate}"

class Employee(models.Model):
    name = models.CharField(max_length=100)  # Employee's name
    car = models.OneToOneField(Car, on_delete=models.SET_NULL, null=True, blank=True)  # Assigned car
    position = models.CharField(max_length=50, null=True, blank=True)  # Employee's position
    department = models.CharField(max_length=100, null=True, blank=True)  # Employee's department

    def __str__(self):
        return self.name
    
class Tariff(models.Model):
    free_duration = models.IntegerField(default=30)  # Free parking duration (in minutes)
    hourly_rate = models.DecimalField(max_digits=6, decimal_places=2)  # Hourly rate after free duration

    def __str__(self):
        return f"Tariff {self.id}: {self.hourly_rate} per hour"
    
class Payment(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, default=1)  # Related car
    parking_session = models.ForeignKey(ParkingSession, on_delete=models.CASCADE)  # Related parking session
    amount = models.DecimalField(max_digits=8, decimal_places=2)  # Payment amount
    payment_time = models.DateTimeField(auto_now_add=True)  # Payment timestamp
    duration = models.IntegerField(null=True, blank=True)  # Parking duration in minutes
    status = models.CharField(max_length=20, default='pending')  # Payment status
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True)  # Payment method
    is_within_free_period = models.BooleanField(default=False)  # Free period flag
    is_employee_vehicle = models.BooleanField(default=False)  # Employee vehicle flag

    def __str__(self):
        return f"Payment {self.id} - {self.amount}"

class Admin(models.Model):
    username = models.CharField(max_length=50, unique=True)  # Admin username
    password_hash = models.TextField()  # Password hash
    full_name = models.CharField(max_length=100, null=True, blank=True)  # Admin's full name
    email = models.EmailField(unique=True, null=True, blank=True)  # Admin email
    last_login = models.DateTimeField(null=True, blank=True)  # Last login timestamp

    def __str__(self):
        return self.username

class Kiosk(models.Model):
    location = models.CharField(max_length=100)  # Kiosk location
    last_maintenance = models.DateTimeField(null=True, blank=True)  # Last maintenance timestamp
    status = models.CharField(max_length=20, default='active')  # Kiosk status
    managed_by = models.ForeignKey(Admin, on_delete=models.SET_NULL, null=True, blank=True)  # Associated admin

    def __str__(self):
        return f"Kiosk {self.id} at {self.location}"