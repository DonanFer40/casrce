from django.urls import path
from gestion_institucional import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [    

    path('pre_reg_personal/', views.pre_reg_personal, name="pre_reg_personal"),
    path('datos_perfiles/', views.datos_perfiles, name="datos_perfiles"),
    path('per_reg_asig/', views.per_reg_asig, name="per_reg_asig"),
    path('vis_per_asig/', views.vis_per_asig, name="vis_per_asig"),
    path('bus_per_asig/', views.bus_per_asig, name="bus_per_asig"),
    path('act_per_asig/', views.act_per_asig, name="act_per_asig"),
    path('info_per_asig/', views.info_per_asig, name="info_per_asig"),
    path('agr_per_asig/', views.agr_per_asig, name="agr_per_asig"),
    path('act_per_reg/', views.act_per_reg, name="act_per_reg"),
    path('per_dis_asi/', views.per_dis_asi, name="per_dis_asi"),
    path('per_reg/', views.per_reg, name="per_reg"),
    path('eli_var_sec/', views.eli_var_sec, name="eli_var_sec"),

    path('tray_reg_acad/', views.tray_reg_acad, name="tray_reg_acad"),

    path('pnfs_disp/', views.pnfs_disp, name="pnfs_disp"),
    path('pnfs_reg/', views.pnfs_reg, name="pnfs_reg"),
    path('datos_pnf/', views.datos_pnf, name="datos_pnf"),
    path('act_pnf/', views.act_pnf, name="act_pnf"),
    path('reg_pnf/', views.reg_pnf, name="reg_pnf"),
    path('nombre_pnf/', views.nombre_pnf, name="nombre_pnf"),
    path('codigo_pnf/', views.codigo_pnf, name="codigo_pnf"),
    path('ver_pnf/', views.ver_pnf, name="ver_pnf"),

    path('nombre_materia/', views.nombre_materia, name="nombre_materia"),
    path('codigo_materia/', views.codigo_materia, name="codigo_materia"),
    path('mat_lista/', views.mat_lista, name="mat_lista"),
    path('mat_datos/', views.mat_datos, name="mat_datos"),
    path('mat_guardar/', views.mat_guardar, name="mat_guardar"),
    path('reg_mat/', views.reg_mat, name="reg_mat"),

    path('tract_selec_mat/', views.tract_selec_mat, name="tract_selec_mat"),
    path('pnf_selec_mat/', views.pnf_selec_mat, name="pnf_selec_mat"),

    path('reg_calendario/', views.reg_calendario, name="reg_calendario"),
    path('per_acad_reg/', views.per_acad_reg, name="per_acad_reg"),
    path('periodos_lista/', views.periodos_lista, name="periodos_lista"),
    path('calendarios_lista/', views.calendarios_lista, name="calendarios_lista"),
    path('calendario_datos/', views.calendario_datos, name="calendario_datos"),
    path('calendario_guardar/', views.calendario_guardar, name="calendario_guardar"),
    path('vis_cal_reg/', views.vis_cal_reg, name="vis_cal_reg"),
    path('opc_reg_cal/', views.opc_reg_cal, name="opc_reg_cal"),

    path('auts_reg/', views.auts_reg, name="auts_reg"),
    path('datos_aut/', views.datos_aut, name="datos_aut"),
    path('act_datos_aut/', views.act_datos_aut, name="act_datos_aut"),
    path('cargo_asig_aut/', views.cargo_asig_aut, name="cargo_asig_aut"),
    path('val_ci_aut/', views.val_ci_aut, name="val_ci_aut"),
    path('cargo_user/', views.cargo_user, name="cargo_user"),
    path('val_resolucion/', views.val_resolucion, name="val_resolucion"),
    path('vist_auts/', views.vist_auts, name="vist_auts"),
    path('reg_auts/', views.reg_auts, name="reg_auts"),

    path('aulas_reg/', views.aulas_reg, name="aulas_reg"),
    path('datos_aula/', views.datos_aula, name="datos_aula"),
    path('act_aula_acad/', views.act_aula_acad, name="act_aula_acad"),
    path('reg_aula/', views.reg_aula, name="reg_aula"),
    path('val_aula/', views.val_aula, name="val_aula"),

    path('sec_reg/', views.sec_reg, name="sec_reg"),
    path('datos_sec/', views.datos_sec, name="datos_sec"),
    path('guardar_act_sec/', views.guardar_act_sec, name="guardar_act_sec"),
    path('reg_sec/', views.reg_sec, name="reg_sec"),
    path('val_sec/', views.val_sec, name="val_sec"),

    path('docs_reg/', views.docs_reg, name="docs_reg"),
    path('mats_reg/', views.mats_reg, name="mats_reg"),
    path('asig_mat_doc/', views.asig_mat_doc, name="asig_mat_doc"),
    path('busc_mat/', views.busc_mat, name="busc_mat"),
    path('act_asig/', views.act_asig, name="act_asig"),
    path('pnf_per_acad/', views.pnf_per_acad, name="pnf_per_acad"),

    path('mat_asig/', views.mat_asig, name="mat_asig"),
    path('mats_desact/', views.mats_desact, name="mats_desact"),
    path('asig_desact/', views.asig_desact, name="asig_desact"),
    path('tray_mat_asg/', views.tray_mat_asg, name="tray_mat_asg"),
    path('obt_pnfs_coord/', views.obt_pnfs_coord, name="obt_pnfs_coord"),

    path('tray_reg/', views.tray_reg, name="tray_reg"),

    path('obt_pnfs_asignado/', views.obt_pnfs_asignado, name="obt_pnfs_asignado"),
    path('obt_pre_inscrt/', views.obt_pre_inscrt, name="obt_pre_inscrt"),
    path('obt_data_est/', views.obt_data_est, name="obt_data_est"),
    path('inscr_est/', views.inscr_est, name="inscr_est"),
    path('perf_asig_coord/', views.perf_asig_coord, name="perf_asig_coord"),
    path('rech_inscr_est/', views.rech_inscr_est, name="rech_inscr_est"),

    path('pl_reg_coord_pnf/', views.pl_reg_coord_pnf, name="pl_reg_coord_pnf"),
    path('vis_pl_env/', views.vis_pl_env, name="vis_pl_env"),
    path('datos_pl_reg_coord_pnf/', views.datos_pl_reg_coord_pnf, name="datos_pl_reg_coord_pnf"),
    path('camb_est_pl/', views.camb_est_pl, name="camb_est_pl"),

]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )