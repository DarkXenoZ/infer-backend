from django.urls import path
from django.contrib import admin
from rest_framework.authtoken.views import obtain_auth_token
from django.conf.urls import include

urlpatterns = [
    path('api/', include('api.urls')),
    path('auth/', obtain_auth_token),
    path('admin/', admin.site.urls),
]