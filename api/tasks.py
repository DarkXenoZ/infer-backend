from celery import shared_task
from .models import *

# To use run save_image.delay(args)
@shared_task
def save_image(args):
    # instance = Project.objects.all()
    pass
