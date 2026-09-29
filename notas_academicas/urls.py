from django.urls import path
from notas_academicas import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('mat_asig_doc/', views.mat_asig_doc, name="mat_asig_doc"),
    path('datos_unid_reg/', views.datos_unid_reg, name="datos_unid_reg"),
    path('todos_pnfs_asig_doc/', views.todos_pnfs_asig_doc, name="todos_pnfs_asig_doc"),
    path('reg_pl_act/', views.reg_pl_act, name="reg_pl_act"),
    path('fech_cal_mat/', views.fech_cal_mat, name="fech_cal_mat"),
    path('fech_reg_mat/', views.fech_reg_mat, name="fech_reg_mat"),
    path('tray_mat_asig/', views.tray_mat_asig, name="tray_mat_asig"),

    path('doc_selec/', views.doc_selec, name="doc_selec"),
    path('perf_asig/', views.perf_asig, name="perf_asig"),
    path('doc_reg/', views.doc_reg, name="doc_reg"),

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
    path('tray_not_reg/', views.tray_not_reg, name="tray_not_reg"),

    path('nucl_reg_not/', views.nucl_reg_not, name="nucl_reg_not"),
    path('pnf_reg_not/', views.pnf_reg_not, name="pnf_reg_not"),
    path('doc_reg_not/', views.doc_reg_not, name="doc_reg_not"),

    path('nucl_mod_not/', views.nucl_mod_not, name="nucl_mod_not"),
    path('pnf_mod_not/', views.pnf_mod_not, name="pnf_mod_not"),
    path('doc_mod_not/', views.doc_mod_not, name="doc_mod_not"),
    path('tray_mod_not/', views.tray_mod_not, name="tray_mod_not"),
    path('reg_nota_acad/', views.reg_nota_acad, name="reg_nota_acad"),

    path('vis_not_acad/', views.vis_not_acad, name="vis_not_acad"),
    path('mat_reg_not/', views.mat_reg_not, name="mat_reg_not"),
    path('perd_reg_not/', views.perd_reg_not, name="perd_reg_not"),
    path('fech_reg_not/', views.fech_reg_not, name="fech_reg_not"),
    path('calf_reg_not/', views.calf_reg_not, name="calf_reg_not"),
    path('vis_doc_not/', views.vis_doc_not, name="vis_doc_not"),
    
    path('vis_nucl_not/', views.vis_nucl_not, name="vis_nucl_not"),
    path('vis_pnf_not/', views.vis_pnf_not, name="vis_pnf_not"),

    path('mod_mat_not/', views.mod_mat_not, name="mod_mat_not"),
    path('mod_per_not/', views.mod_per_not, name="mod_per_not"),
    path('mod_calf_not/', views.mod_calf_not, name="mod_calf_not"),
    path('mod_not_acad/', views.mod_not_acad, name="mod_not_acad"),

    path('nucl_est_asig/', views.nucl_est_asig, name="nucl_est_asig"),
    path('pnfs_est_asig/', views.pnfs_est_asig, name="pnfs_est_asig"),
    path('mat_est_vist/', views.mat_est_vist, name="mat_est_vist"),
    path('planif_acad_est/', views.planif_acad_est, name="planif_acad_est"),
    path('calif_est_reg/', views.calif_est_reg, name="calif_est_reg"),
    path('tray_est_curs/', views.tray_est_curs, name="tray_est_curs"),
    path('perid_acad_mat/', views.perid_acad_mat, name="perid_acad_mat"),

    path('info_acad_est/', views.info_acad_est, name="info_acad_est"),

    path('tray_mat_est/', views.tray_mat_est, name="tray_mat_est"),
    path('mat_present_est/', views.mat_present_est, name="mat_present_est"),
    path('mat_vis_est/', views.mat_vis_est, name="mat_vis_est"),
    
    path('tray_est_planif/', views.tray_est_planif, name="tray_est_planif"),
    path('mat_est_planif/', views.mat_est_planif, name="mat_est_planif"),
    path('per_aca_planif/', views.per_aca_planif, name="per_aca_planif"),
    path('planif_est_vis/', views.planif_est_vis, name="planif_est_vis"),
    path('planif_est_reg/', views.planif_est_reg, name="planif_est_reg"),

    path('calc_prom_est/', views.calc_prom_est, name="calc_prom_est"),
    path('act_prom_rep/', views.act_prom_rep, name="act_prom_rep"),
    path('mod_cant_pla/', views.mod_cant_pla, name="mod_cant_pla"),
    path('vis_cant_planif/', views.vis_cant_planif, name="vis_cant_planif"),
    
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

    path('pnfs_rem_not_acad/', views.pnfs_rem_not_acad, name="pnfs_rem_not_acad"),
    path('doc_rem_not_acad/', views.doc_rem_not_acad, name="doc_rem_not_acad"),
    path('tray_rem_not/', views.tray_rem_not, name="tray_rem_not"),
    path('mat_rem_not/', views.mat_rem_not, name="mat_rem_not"),
    path('perid_rem_not/', views.perid_rem_not, name="perid_rem_not"),
    path('cant_est_rem/', views.cant_est_rem, name="cant_est_rem"),
    path('rem_calif_mod/', views.rem_calif_mod, name="rem_calif_mod"),
    path('rem_camb_not/', views.rem_camb_not, name="rem_camb_not"),
    path('rem_not_acad/', views.rem_not_acad, name="rem_not_acad"),
]