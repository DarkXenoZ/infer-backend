# Generated by Django 3.1 on 2021-02-07 09:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0012_auto_20210207_1555'),
    ]

    operations = [
        migrations.AlterField(
            model_name='predictresult',
            name='predicted_class',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
