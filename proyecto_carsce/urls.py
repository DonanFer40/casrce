"""
URL configuration for proyecto_carsce project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path, re_path
from django.conf import settings
from inicio_sesion.views.errores import pagina_no_encontrada

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('inicio_sesion.urls')),
    path('notas_academicas/', include('notas_academicas.urls')),
    path('', include('gestion_institucional.urls')),
    path('documentos/', include('documentos.urls')),
    path('bitacora/', include('bitacora.urls')),
    re_path(
        r"^(?P<ruta>.*)$",
        pagina_no_encontrada,
        name="pagina_no_encontrada",
    ),
]

handler404 = "inicio_sesion.views.errores.pagina_no_encontrada"
