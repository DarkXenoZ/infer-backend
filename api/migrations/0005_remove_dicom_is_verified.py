# Generated by Django 3.0.4 on 2021-01-09 17:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_auto_20210110_0019'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dicom',
            name='is_verified',
        ),
    ]