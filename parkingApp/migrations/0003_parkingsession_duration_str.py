# Generated by Django 5.1.2 on 2024-12-23 13:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parkingApp', '0002_remove_car_cropped_plate_photo_alter_car_car_plate'),
    ]

    operations = [
        migrations.AddField(
            model_name='parkingsession',
            name='duration_str',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
