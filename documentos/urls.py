
from django.urls import path
from documentos.views import emitir_reporte_academico
from documentos.views.constancias import emitir_constancia_estudios
from documentos.views import verificar_documento, descargar_documento
from . import views


app_name = "documentos"


urlpatterns = [

    # Verificación pública
    path("verificar/<uuid:identificador>/",views.verificar_documento,name="verificar_documento",),
    # Emisión de reporte académico
    path("reportes/academico/emitir/<int:id_estudiante>/",views.emitir_reporte_academico,name="emitir_reporte_academico",),
    # Descarga de documento
    path("descargar/<uuid:identificador>/",views.descargar_documento,name="descargar_documento",),
    path("reportes/academico/emitir/<int:id_estudiante>/", emitir_reporte_academico, name="emitir_reporte_academico"), 
    path("constancias/estudios/emitir/<int:id_estudiante>/", emitir_constancia_estudios, name="emitir_constancia_estudios"),
    path("verificar/<uuid:identificador>/", verificar_documento, name="verificar_documento"),
    path("descargar/<uuid:identificador>/", descargar_documento, name="descargar_documento"),

]
