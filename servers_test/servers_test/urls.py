from django.contrib import admin
from django.urls import path, include
from servers_status_api import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('', include('servers_status_api.urls')),
]
