from celery import shared_task
from .models import *

# To use run save_image.delay(args)
@shared_task
def save_image(project_id):
    instance = Project.objects.get(id=project_id)
    print(instance.name)
