# Generated by Django 3.0.4 on 2021-01-10 09:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_auto_20210110_0038'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dicom',
            name='data',
            field=models.FileField(upload_to='dicom/'),
        ),
    ]