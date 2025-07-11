from django.urls import path
from .views import UploadProfilePictureView

urlpatterns = [
    path('update-picture/', UploadProfilePictureView.as_view(), name='upload-profile-picture'),
]