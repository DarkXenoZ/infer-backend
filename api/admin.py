from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(Project)
admin.site.register(Log)
admin.site.register(Image)
admin.site.register(Pipeline)
admin.site.register(PredictResult)