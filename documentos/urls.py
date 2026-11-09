
from django.urls import path
from documentos.views.constancias import (
    emitir_constancia_estudios,
    emitir_constancia_estudios_actual,
    emitir_constancia_inscripcion,
    emitir_constancia_inscripcion_actual,
)
from documentos.views.horarios import emitir_horario_personal
from documentos.views.reportes_estadisticos import emitir_reporte_estadistico
from documentos.views.verificar_documentos import (
    descargar_documento,
    emitir_reporte_academico,
    emitir_reporte_academico_actual,
    verificar_documento,
)


app_name = "documentos"


urlpatterns = [
    path("verificar/<uuid:identificador>/", verificar_documento, name="verificar_documento"),
    path("descargar/<uuid:identificador>/", descargar_documento, name="descargar_documento"),
    path("reportes/academico/emitir/<int:id_estudiante>/", emitir_reporte_academico, name="emitir_reporte_academico"),
    path("reportes/academico/emitir-actual/", emitir_reporte_academico_actual, name="emitir_reporte_academico_actual"),
    path("constancias/estudios/emitir/<int:id_estudiante>/", emitir_constancia_estudios, name="emitir_constancia_estudios"),
    path("constancias/estudios/emitir-actual/", emitir_constancia_estudios_actual, name="emitir_constancia_estudios_actual"),
    path("constancias/inscripcion/emitir/<int:id_estudiante>/", emitir_constancia_inscripcion, name="emitir_constancia_inscripcion"),
    path("constancias/inscripcion/emitir-actual/", emitir_constancia_inscripcion_actual, name="emitir_constancia_inscripcion_actual"),
    path("horarios/emitir/", emitir_horario_personal, name="emitir_horario_personal"),
    path("reportes/estadisticos/emitir/", emitir_reporte_estadistico, name="emitir_reporte_estadistico"),
]
