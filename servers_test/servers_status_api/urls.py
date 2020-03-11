from django.urls import path, re_path
from . import views

urlpatterns = [
    re_path(r'^analice_url/(?P<url>[a-zA-Z0-9_.-/:?=#]*)/$', views.status_response),
]
