from django.contrib import admin
from .models import *

admin.site.register(Car)
admin.site.register(Payment)
admin.site.register(PaymentMethod)
admin.site.register(ParkingSession)
admin.site.register(Employee)
admin.site.register(Kiosk)
admin.site.register(Tariff)
admin.site.register(Admin)

