from django.urls import path
from django.conf.urls import include
from rest_framework import routers
from .views.export_view import ExportViewSet
from .views.image_3d_view import Image3DViewSet
from .views.image_view import ImageViewSet
from .views.log_view import LogViewSet
from .views.pipeline_view import PipelineViewSet
from .views.predict_result_view import PredictResultViewSet
from .views.project_view import ProjectViewSet
from .views.user_view import UserViewSet
from .views.util_view import UtilViewSet

router = routers.SimpleRouter()
router.register('user', UserViewSet)
router.register('log', LogViewSet)
router.register('image', ImageViewSet)
router.register('project', ProjectViewSet)
router.register('pipeline', PipelineViewSet)
router.register('predictResult', PredictResultViewSet)
router.register('image3D', Image3DViewSet)
router.register('util', UtilViewSet, basename='util')
router.register('export', ExportViewSet)
urlpatterns = [
    path('', include(router.urls)),
]
