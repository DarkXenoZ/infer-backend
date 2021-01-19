# Generated by Django 3.0.4 on 2021-01-13 17:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_auto_20210113_2344'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='project',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='images', to='api.Project'),
        ),
        migrations.AlterField(
            model_name='pipeline',
            name='project',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='pipelines', to='api.Project'),
        ),
    ]