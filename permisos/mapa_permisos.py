"""
Mapa central de permisos de CASRCE.

Los nombres deben coincidir con los valores que devuelve Cuenta.obtener_rol_principal
o con los roles guardados por inicio_sesion.views.autenticacion.obtener_roles.
Los permisos se validan contra los modelos en base de datos; la sesión no es la
fuente de autoridad.
"""

ROLES = {
    "DIRECTOR": "Director General",
    "CONTROL": "Control de Estudio",
    "COORDINADOR": "Coordinador PNF",
    "DOCENTE": "Docente",
    "ESTUDIANTE": "Estudiante",
}

ROLES_ADMINISTRATIVOS = frozenset({
    ROLES["DIRECTOR"], ROLES["CONTROL"], ROLES["COORDINADOR"]
})
ROL_DIRECTOR = frozenset({ROLES["DIRECTOR"]})
ROLES_PERSONAL = ROLES_ADMINISTRATIVOS | {ROLES["DOCENTE"]}
TODOS_LOS_ROLES = ROLES_PERSONAL | {ROLES["ESTUDIANTE"]}

# Permisos por módulo. Si una vista no está listada aquí, se aplica el grupo
# predeterminado del módulo configurado en DEFAULT_MODULE_ROLES.
DEFAULT_MODULE_ROLES = {
    "inicio_sesion": TODOS_LOS_ROLES,
    "gestion_institucional": ROLES_PERSONAL,
    "notas_academicas": TODOS_LOS_ROLES,
    "documentos": TODOS_LOS_ROLES,
    "bitacora": ROLES_ADMINISTRATIVOS,
}

# Restricciones puntuales por nombre de URL (reverse name).
# Estas reglas prevalecen sobre el permiso predeterminado del módulo.
URL_PERMISSIONS = {
    # Gestión de personal, estructura institucional y configuración general.
    "pre_reg_personal": ROL_DIRECTOR,
    "per_reg_asig": ROL_DIRECTOR,
    "vis_per_asig": ROL_DIRECTOR,
    "bus_per_asig": ROL_DIRECTOR,
    "act_per_asig": ROL_DIRECTOR,
    "info_per_asig": ROL_DIRECTOR,
    "agr_per_asig": ROL_DIRECTOR,
    "act_per_reg": ROL_DIRECTOR,
    "per_dis_asi": ROL_DIRECTOR,
    "per_reg": ROL_DIRECTOR,
    "eli_var_sec": ROL_DIRECTOR,
    "pnfs_disp": ROL_DIRECTOR,
    "pnfs_reg": ROL_DIRECTOR,
    "datos_pnf": ROL_DIRECTOR,
    "act_pnf": ROL_DIRECTOR,
    "reg_pnf": ROL_DIRECTOR,
    "nombre_pnf": ROL_DIRECTOR,
    "codigo_pnf": ROL_DIRECTOR,
    "ver_pnf": ROL_DIRECTOR,
    "reg_calendario": ROL_DIRECTOR,
    "per_acad_reg": ROL_DIRECTOR,
    "periodos_lista": ROL_DIRECTOR,
    "calendarios_lista": ROL_DIRECTOR,
    "calendario_datos": ROL_DIRECTOR,
    "calendario_guardar": ROL_DIRECTOR,
    "vis_cal_reg": ROL_DIRECTOR,
    "opc_reg_cal": ROL_DIRECTOR,
    "auts_reg": ROL_DIRECTOR,
    "datos_aut": ROL_DIRECTOR,
    "act_datos_aut": ROL_DIRECTOR,
    "cargo_asig_aut": ROL_DIRECTOR,
    "val_ci_aut": ROL_DIRECTOR,
    "cargo_user": ROL_DIRECTOR,
    "val_resolucion": ROL_DIRECTOR,
    "vist_auts": ROL_DIRECTOR,
    "reg_auts": ROL_DIRECTOR,
    "aulas_reg": ROL_DIRECTOR,
    "visualizar_aulas": ROL_DIRECTOR,
    "datos_aula": ROL_DIRECTOR,
    "act_aula_acad": ROL_DIRECTOR,
    "reg_aula": ROL_DIRECTOR,
    "val_aula": ROL_DIRECTOR,
    "sec_reg": ROL_DIRECTOR,
    "datos_sec": ROL_DIRECTOR,
    "guardar_act_sec": ROL_DIRECTOR,
    "reg_sec": ROL_DIRECTOR,
    "val_sec": ROL_DIRECTOR,
    "registrar_horario": {ROLES["COORDINADOR"]},
    "trayecto_hor": {ROLES["COORDINADOR"]},
    "aulas_hor": {ROLES["COORDINADOR"]},
    "periodo_academico_hor": {ROLES["COORDINADOR"]},
    "asig_mat_reg": {ROLES["COORDINADOR"]},
    "horario_existente": {ROLES["COORDINADOR"]},
    "reg_hor": {ROLES["COORDINADOR"]},
    "horario_estudiante": {ROLES["ESTUDIANTE"]},

    # Acciones de coordinación/control de estudio.
    "obt_pre_inscrt": ROLES_ADMINISTRATIVOS,
    "obt_data_est": ROLES_ADMINISTRATIVOS,
    "inscr_est": ROLES_ADMINISTRATIVOS,
    "perf_asig_coord": ROLES_ADMINISTRATIVOS,
    "rech_inscr_est": ROLES_ADMINISTRATIVOS,
    "pl_reg_coord_pnf": {ROLES["COORDINADOR"], ROLES["DIRECTOR"]},
    "vis_pl_env": {ROLES["COORDINADOR"], ROLES["DIRECTOR"], ROLES["CONTROL"]},
    "datos_pl_reg_coord_pnf": {ROLES["COORDINADOR"], ROLES["DIRECTOR"], ROLES["CONTROL"]},
    "camb_est_pl": {ROLES["COORDINADOR"], ROLES["DIRECTOR"], ROLES["CONTROL"]},

    # La bitácora es información administrativa.
    "bitacora_acciones": ROLES_ADMINISTRATIVOS,
    "detalle_accion": ROLES_ADMINISTRATIVOS,
    "reportes_control_estudio": TODOS_LOS_ROLES,
}

# Endpoints públicos o de autenticación que nunca deben bloquearse por rol.
PUBLIC_URL_NAMES = frozenset({
    "inicio_publico", "foro", "inicio_sesion", "panel_registro", "cerrar_sesion",
    "comp_registro", "validar_ci_auxiliar", "validar_cod_opsu",
    "validar_ci_usr", "validar_email", "val_usuario", "val_password",
    "registro_est", "verificar_codigo_registro", "reenviar_codigo_registro",
    "confirmar_reg", "guardar_cred", "pnfs_cursar",
    "verificar_codigo_personal", "reenviar_codigo_personal",
    "bus_usr", "comp_usr", "env_cod_usr", "comp_cod_usr", "val_cod",
    "reenv_cod_btn", "env_cod_ver", "panel_rec_cred", "rec_cont",
    "rec_usr", "exist_cod", "corr_reg", "Historia", "mision_vision",
    "pst", "psc", "trayectoria", "carreras_impartidas",
    "Planificacion_Docente", "noticias_por_nucleo",
    "verificar_documento",
    "iniciar_acceso_admin", "verificar_codigo_correo_admin",
    "verificar_totp_admin", "reenviar_codigo_admin", "cancelar_acceso_admin",
    "configurar_totp_admin", "confirmar_totp_admin", "acceso_admin",
})

# Enlaces con identificador firmado/aleatorio y validación propia de acceso.
PUBLIC_OR_TOKEN_URL_NAMES = frozenset({
    "verificar_documento", "descargar_documento",
})
