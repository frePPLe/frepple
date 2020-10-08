"""
This files defines a URL for your views.
"""

from django.conf.urls import url

from .views import MyModelList
from .serializers import MyModelSerializerAPI

# Automatically add these URLs when the application is installed
autodiscover = True

urlpatterns = [
    # Model list reports, which override standard admin screens
    url(
        r"^data/my_app/my_model/$",
        MyModelList.as_view(),
        name="my_app_my_model_changelist",
    ),
    # URLs for the REST API
    url(r"^api/my_app/my_model/$", MyModelSerializerAPI.as_view()),
]
