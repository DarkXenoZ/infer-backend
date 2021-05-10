from django.urls import path
from django.conf.urls import include
from rest_framework import routers
from .views import *

router = routers.SimpleRouter()
router.register('user', UserViewSet)
router.register('log', LogViewSet)
router.register('image', ImageViewSet)
router.register('project', ProjectViewSet)
router.register('pipeline', PipelineViewSet)
router.register('predictResult', PredictResultViewSet)
router.register('image3D', Image3DViewSet)
router.register('util',UtilViewSet)
urlpatterns = [
    path('', include(router.urls)),
]
