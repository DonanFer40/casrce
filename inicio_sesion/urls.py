from django.urls import path
from inicio_sesion import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('foro/', views.foro, name="foro"),
    path('', views.foro, name='inicio_publico'),
    path('inicio_sesion/', views.autenticacion, name="inicio_sesion"),
    path('panel_usuario/', views.panel_usuario, name="panel_usuario"),
    path('panel_registro/', views.panel_registro, name="panel_registro"),
    path('cerrar_sesion/', views.cerrar_sesion, name="cerrar_sesion"),

    path('comp_registro/', views.comp_registro, name="comp_registro"),
    path('datos_usr_admin/', views.datos_usr_admin, name="datos_usr_admin"),
    path('validar_ci_auxiliar/', views.validar_ci_auxiliar, name="validar_ci_auxiliar"),
    path('validar_cod_opsu/', views.validar_cod_opsu, name="validar_cod_opsu"),
 
    path('validar_ci_usr/', views.validar_ci_usr, name="validar_ci_usr"),
    path('validar_email/', views.validar_email, name="validar_email"),
    path('panel_registro/', views.panel_registro, name="panel_registro"),
    path('val_usuario/', views.val_usuario, name="val_usuario"),
    path('val_password/', views.val_password, name="val_password"),
    path('registro_est/', views.registro_est, name="registro_est"),
    path('confirmar_reg/', views.confirmar_reg, name="confirmar_reg"),
    path('guardar_cred/', views.guardar_cred, name="guardar_cred"),
    path('pnfs_cursar/', views.pnfs_cursar, name="pnfs_cursar"),

    path('bus_usr/', views.bus_usr, name="bus_usr"),
    path('comp_usr/', views.comp_usr, name="comp_usr"),
    path('env_cod_usr/', views.env_cod_usr, name="env_cod_usr"),
    path('comp_cod_usr/', views.comp_cod_usr, name="comp_cod_usr"),
    path('val_cod/', views.val_cod, name="val_cod"),
    path('reenv_cod_btn/', views.reenv_cod_btn, name="reenv_cod_btn"),
    path('env_cod_ver/', views.env_cod_ver, name="env_cod_ver"),
    path('panel_rec_cred/', views.panel_rec_cred, name="panel_rec_cred"),
    path('rec_cont/', views.rec_cont, name="rec_cont"),
    path('rec_usr/', views.rec_usr, name="rec_usr"),
    path('exist_cod/', views.exist_cod, name="exist_cod"),
    path('corr_reg/', views.corr_reg, name="corr_reg"),

    #FORO
    path('Historia/', views.Historia, name="Historia"),
    path('mision_vision/', views.mision_vision, name="mision_vision"),
    path('pst/', views.pst, name="pst"),
    path('psc/', views.psc, name="psc"),
    path('trayectoria/', views.trayectoria, name="trayectoria"),
    path('carreras_impartidas/', views.carreras_impartidas, name="carreras_impartidas"),
    path('Planificacion_Docente/', views.Planificacion_Docente, name="Planificacion_Docente"),
    path('noticias-por-nucleo/', views.noticias_por_nucleo, name="noticias_por_nucleo"),

    path('barra_lateral/', views.barra_lateral, name="barra_lateral"),

    path('reporte_estudiantes_pdf/', views.reporte_estudiantes_pdf, name='reporte_estudiantes_pdf'),
    path('reportes_control_estudio/', views.reportes_control_estudio, name='reportes_control_estudio'),
    path('reporte_academico_pdf/', views.reporte_academico_pdf, name='reporte_academico_pdf'),
    path('reporte_inscripciones_pdf/', views.reporte_inscripciones_pdf, name='reporte_inscripciones_pdf'),

    # NOTICIAS - DIRECTOR GENERAL
    path('noticias/', views.visualizar_noticias, name='visualizar_noticias'),
    path('noticias/registrar/', views.registrar_noticia, name="registrar_noticia"),
    path('noticias/modificar/<int:id_noticia>/', views.modificar_noticia, name="modificar_noticia"),
    path('noticias/desactivar/<int:id_noticia>/', views.desactivar_noticia, name="desactivar_noticia"),
    path('noticias/activar/<int:id_noticia>/', views.activar_noticia, name="activar_noticia"),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )