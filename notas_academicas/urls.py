from django.urls import path
from notas_academicas import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('mat_asig_doc/', views.mat_asig_doc, name="mat_asig_doc"),
    path('perd_acad_reg/', views.perd_acad_reg, name="perd_acad_reg"),
    path('cant_und_reg/', views.cant_und_reg, name="cant_und_reg"),
    path('reg_pl_act/', views.reg_pl_act, name="reg_pl_act"),
    path('fech_cal_mat/', views.fech_cal_mat, name="fech_cal_mat"),
    path('fech_reg_mat/', views.fech_reg_mat, name="fech_reg_mat"),

    path('vis_plan_est/', views.vis_plan_est, name="vis_plan_est"),
    path('env_pla/', views.env_pla, name="env_pla"),
    path('pl_reg/', views.pl_reg, name="pl_reg"),
    path('datos_pl_reg/', views.datos_pl_reg, name="datos_pl_reg"),
    path('act_pl_reg/', views.act_pl_reg, name="act_pl_reg"),

    path('nucl_asig_doc/', views.nucl_asig_doc, name="nucl_asig_doc"),
    path('pnfs_asig_doc/', views.pnfs_asig_doc, name="pnfs_asig_doc"),
    path('mat_not_acad/', views.mat_not_acad, name="mat_not_acad"),
    path('per_not_acad/', views.per_not_acad, name="per_not_acad"),
    path('est_not_acad/', views.est_not_acad, name="est_not_acad"),
    path('cant_det_pla/', views.cant_det_pla, name="cant_det_pla"),

    path('reg_nota_acad/', views.reg_nota_acad, name="reg_nota_acad"),

    path('vis_not_acad/', views.vis_not_acad, name="vis_not_acad"),
    path('mat_reg_not/', views.mat_reg_not, name="mat_reg_not"),
    path('perd_reg_not/', views.perd_reg_not, name="perd_reg_not"),
    path('fech_reg_not/', views.fech_reg_not, name="fech_reg_not"),
    path('calf_reg_not/', views.calf_reg_not, name="calf_reg_not"),

    path('mod_mat_not/', views.mod_mat_not, name="mod_mat_not"),
    path('mod_per_not/', views.mod_per_not, name="mod_per_not"),
    path('mod_calf_not/', views.mod_calf_not, name="mod_calf_not"),
    path('mod_not_acad/', views.mod_not_acad, name="mod_not_acad"),

    path('nucleos_est_asig/', views.nucleos_est_asig, name="nucleos_est_asig"),
    path('pnfs_est_asig/', views.pnfs_est_asig, name="pnfs_est_asig"),
    path('mate_tray_est/', views.mate_tray_est, name="mate_tray_est"),
    path('plan_act_est/', views.plan_act_est, name="plan_act_est"),
    path('eval_reg_est/', views.eval_reg_est, name="eval_reg_est"),

    path('info_acad_est/', views.info_acad_est, name="info_acad_est"),

    path('calc_prom_est/', views.calc_prom_est, name="calc_prom_est"),
    path('act_prom_rep/', views.act_prom_rep, name="act_prom_rep"),
    
    path('act_tray_est/', views.act_tray_est, name="act_tray_est"),

    path('reg_eval_rep/', views.reg_eval_rep, name="reg_eval_rep"),
    path('mat_rep_not/', views.mat_rep_not, name="mat_rep_not"),

    path('dato_eval_rep/', views.dato_eval_rep, name="dato_eval_rep"),
    path('vis_eval_rep/', views.vis_eval_rep, name="vis_eval_rep"),

    path('mat_reg_eval/', views.mat_reg_eval, name="mat_reg_eval"),
    path('eval_reg_rep/', views.eval_reg_rep, name="eval_reg_rep"),
    path('mod_eval_rep/', views.mod_eval_rep, name="mod_eval_rep"),

    path('eval_mat_rep/', views.eval_mat_rep, name="eval_mat_rep"),
    path('est_rep_not/', views.est_rep_not, name="est_rep_not"),
    path('reg_rep_not/', views.reg_rep_not, name="reg_rep_not"),
   
    path('vis_rep_not/', views.vis_rep_not, name="vis_rep_not"),
    path('mat_vis_not/', views.mat_vis_not, name="mat_vis_not"),
    path('fech_reg_rep/', views.fech_reg_rep, name="fech_reg_rep"),
    path('reg_est_rep/', views.reg_est_rep, name="reg_est_rep"),

    path('mod_mat_rep_reg/', views.mod_mat_rep_reg, name="mod_mat_rep_reg"),
    path('mod_not_rep_reg/', views.mod_not_rep_reg, name="mod_not_rep_reg"),
    path('mod_rep_reg/', views.mod_rep_reg, name="mod_rep_reg"),
]