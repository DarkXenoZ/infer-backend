# Generated by Django 3.1 on 2021-02-06 10:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_auto_20210206_1544'),
    ]

    operations = [
        migrations.AddField(
            model_name='queue',
            name='image',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='queue', to='api.image'),
        ),
    ]