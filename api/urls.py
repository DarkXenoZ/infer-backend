from django.urls import path
from django.conf.urls import include
from rest_framework import routers
import .views

router = routers.SimpleRouter()
router.register('user', views.UserViewSet)
router.register('log', views.LogViewSet)
router.register('image', views.ImageViewSet)
router.register('project', views.ProjectViewSet)
router.register('pipeline', views.PipelineViewSet)
router.register('predictResult', views.PredictResultViewSet)
router.register('image3D', views.Image3DViewSet)
router.register('util', views. UtilViewSet, basename='util')
router.register('export', views.ExportViewSet)
urlpatterns = [
    path('', include(router.urls)),
]
