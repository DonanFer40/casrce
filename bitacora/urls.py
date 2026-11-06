from django.urls import path
from . import views

urlpatterns = [
    path("", views.bitacora_acciones, name="bitacora_acciones"),
    path("<int:id_registro>/", views.detalle_accion, name="detalle_accion"),
]
