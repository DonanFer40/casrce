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
ROLES_PERSONAL = ROLES_ADMINISTRATIVOS | {ROLES["DOCENTE"]}
TODOS_LOS_ROLES = ROLES_PERSONAL | {ROLES["ESTUDIANTE"]}

# Permisos por módulo. Si una vista no está listada aquí, se aplica el grupo
# predeterminado del módulo configurado en DEFAULT_MODULE_ROLES.
DEFAULT_MODULE_ROLES = {
    "gestion_institucional": ROLES_PERSONAL,
    "notas_academicas": TODOS_LOS_ROLES,
    "bitacora": ROLES_ADMINISTRATIVOS,
}

# Restricciones puntuales por nombre de URL (reverse name).
# Estas reglas prevalecen sobre el permiso predeterminado del módulo.
URL_PERMISSIONS = {
    # Gestión de personal, estructura institucional y configuración general.
    "pre_reg_personal": ROLES_ADMINISTRATIVOS,
    "per_reg_asig": ROLES_ADMINISTRATIVOS,
    "vis_per_asig": ROLES_ADMINISTRATIVOS,
    "bus_per_asig": ROLES_ADMINISTRATIVOS,
    "act_per_asig": ROLES_ADMINISTRATIVOS,
    "info_per_asig": ROLES_ADMINISTRATIVOS,
    "agr_per_asig": ROLES_ADMINISTRATIVOS,
    "act_per_reg": ROLES_ADMINISTRATIVOS,
    "per_dis_asi": ROLES_ADMINISTRATIVOS,
    "per_reg": ROLES_ADMINISTRATIVOS,
    "eli_var_sec": ROLES_ADMINISTRATIVOS,
    "pnfs_disp": ROLES_ADMINISTRATIVOS,
    "pnfs_reg": ROLES_ADMINISTRATIVOS,
    "datos_pnf": ROLES_ADMINISTRATIVOS,
    "act_pnf": ROLES_ADMINISTRATIVOS,
    "reg_pnf": ROLES_ADMINISTRATIVOS,
    "nombre_pnf": ROLES_ADMINISTRATIVOS,
    "codigo_pnf": ROLES_ADMINISTRATIVOS,
    "ver_pnf": ROLES_ADMINISTRATIVOS,
    "reg_calendario": ROLES_ADMINISTRATIVOS,
    "per_acad_reg": ROLES_ADMINISTRATIVOS,
    "periodos_lista": ROLES_ADMINISTRATIVOS,
    "calendarios_lista": ROLES_ADMINISTRATIVOS,
    "calendario_datos": ROLES_ADMINISTRATIVOS,
    "calendario_guardar": ROLES_ADMINISTRATIVOS,
    "vis_cal_reg": ROLES_ADMINISTRATIVOS,
    "opc_reg_cal": ROLES_ADMINISTRATIVOS,
    "auts_reg": ROLES_ADMINISTRATIVOS,
    "datos_aut": ROLES_ADMINISTRATIVOS,
    "act_datos_aut": ROLES_ADMINISTRATIVOS,
    "cargo_asig_aut": ROLES_ADMINISTRATIVOS,
    "val_ci_aut": ROLES_ADMINISTRATIVOS,
    "cargo_user": ROLES_ADMINISTRATIVOS,
    "val_resolucion": ROLES_ADMINISTRATIVOS,
    "vist_auts": ROLES_ADMINISTRATIVOS,
    "reg_auts": ROLES_ADMINISTRATIVOS,
    "aulas_reg": ROLES_ADMINISTRATIVOS,
    "datos_aula": ROLES_ADMINISTRATIVOS,
    "act_aula_acad": ROLES_ADMINISTRATIVOS,
    "reg_aula": ROLES_ADMINISTRATIVOS,
    "val_aula": ROLES_ADMINISTRATIVOS,
    "sec_reg": ROLES_ADMINISTRATIVOS,
    "datos_sec": ROLES_ADMINISTRATIVOS,
    "guardar_act_sec": ROLES_ADMINISTRATIVOS,
    "reg_sec": ROLES_ADMINISTRATIVOS,
    "val_sec": ROLES_ADMINISTRATIVOS,

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
}

# Endpoints públicos o de autenticación que nunca deben bloquearse por rol.
PUBLIC_URL_NAMES = frozenset({
    "inicio_publico", "foro", "inicio_sesion", "cerrar_sesion",
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
