# Generated by Django 5.1.2 on 2024-12-09 07:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parkingApp', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='car',
            name='cropped_plate_photo',
        ),
        migrations.AlterField(
            model_name='car',
            name='car_plate',
            field=models.CharField(blank=True, max_length=7, null=True, unique=True),
        ),
    ]
