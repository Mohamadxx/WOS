from django.urls import path
from . import views


urlpatterns = [
    path("", views.index, name="index"),
    path("author/<slug:slug>", views.author_details, name="author-details" ),
    
]
