from django.urls import path
from django.conf.urls import include
from rest_framework import routers
from .views import *

router = routers.SimpleRouter()
router.register('user', UserViewSet)
router.register('log', LogViewSet)
router.register('dicom', DicomViewSet)
router.register('project', ProjectViewSet)
router.register('pipeline', PipelineViewSet)


urlpatterns = [
    path('', include(router.urls)),
]
