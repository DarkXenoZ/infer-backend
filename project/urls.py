from django.urls import path
from django.contrib import admin
from rest_framework.authtoken.views import obtain_auth_token
from django.conf.urls import include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('api/', include('api.urls')),
    path('auth/', obtain_auth_token),
    path('admin/', admin.site.urls),
]+ static(settings.MEDIA_URL, document_root= settings.MEDIA_ROOT)