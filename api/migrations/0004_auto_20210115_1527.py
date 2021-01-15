# Generated by Django 3.0.4 on 2021-01-15 08:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_auto_20210114_0026'),
    ]

    operations = [
        migrations.AddField(
            model_name='result',
            name='note',
            field=models.CharField(blank=True, max_length=300),
        ),
        migrations.AlterUniqueTogether(
            name='image',
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name='image',
            name='name',
        ),
    ]
