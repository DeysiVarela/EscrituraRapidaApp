from enum import Enum

class ColaEscalamiento(int, Enum):
    BOT_COPILOT_STUDIO = 1,
    BOT_IA_INTERMEDIA = 2

class Canal(str,Enum):
    WHATSAPP = "whatsapp",
    FACEBOOK = "facebook",
    INSTAGRAM = "instagram",
    WEB = "web"

class TipoCliente(str,Enum):
    LEAD = "lead",
    CONTACTO = "contacto"

class TipoUsuario(str,Enum):
    LEAD = 1,
    CONTACTO = 2,
    SIN_IDENTIFICAR = 3,
    NUEVO_LEAD = 4

class CamposUsuario(str,Enum):
    ID_ASESOR_CONFIANZA = "id_asesor_confianza",
    PERFILAR_CLIENTE = "perfilar_cliente",
    DESCALIFICADO = "descalificado",
    NEGOCIO_VALIDADO_EQUIPO_SAC_POSTVENTA = "negocio_valido_equipo_sac_postventa",
    TIPO_CLIENTE = "tipo_cliente",
    ID_CLIENTE = "id_cliente",
    DOCUMENTO_IDENTIFICACION = "documento",
    TIEMPO_COMPRA = "tiempo_compra",
    INGRESOS_MENSUALES = "ingresos_mensuales",
    ACTIVIDAD_ECONOMICA = "actividad_economica",
    EMAIL_CLIENTE = "email_cliente",
    ES_NACIONAL = "es_nacional",
    EXISTE_EN_BASE_DATOS = "existe_en_base_datos",
    PROYECTO_INTERES = "proyecto_interes",
    CELULAR = "celular_cliente",
    ES_NUEVO_LEAD = "es_nuevo_lead",
    CANAL = "canal",
    ID_USUARIO_DIRECT_LINE = "id_usuario_direct_line",
    ID_COLA = "id_cola",
    ID_CONVERSACION = "id_conversacion",
    SAC_POSTVENTA = "sac_postventa",
    NOMBRE_COMPLETO = "nombre_completo",
    ESCALAR = "escalar",
    BUSCAR_PROYECTOS = "buscar_proyectos",
    NOMBRE = "nombre",
    APELLIDO = "apellido",
    TIPO_DOCUMENTO_IDENTIFICACION = "tipo_documento_identificacion",
    HACER_PREGUNTA_PERFILACION = "hacer_pregunta_perfilacion"
    PRIMER_NOMBRE = "primer_nombre",
    TERRITORIO = "territorio",
    ESCALAR_AUTOMATICAMENTE = "escalar_automaticamente",
    HORA_INICIO_SEMANA = "hora_inicio_semana",
    HORA_FIN_SEMANA = "hora_fin_semana",
    HORA_INICIO_SABADO = "hora_inicio_sabado",
    HORA_FIN_SABADO = "hora_fin_sabado",
    HORA_INICIO_DOMINGO = "hora_inicio_domingo",
    HORA_FIN_DOMINGO = "hora_fin_domingo",
    DIAS_NO_HABILES = "dias_no_habiles",
    FUERA_HORARIO = "fuera_horario",
    FECHA_CONTACTAR = "fecha_contactar",
    HORA_CONTACTAR = "hora_contactar",
    CONTACTO_AGENDADO = "contacto_agendado"
        

class ActividadEconomica(Enum):
    AMA_DE_CASA = 100000000
    EMPLEADO = 100000001
    ESTUDIANTE = 100000002
    INDEPENDIENTE = 100000003
    PENSIONADO = 100000004
    SOCIO_RENTISTA = 100000006
    RELIGIOSO = 100000007
    SERVIDOR_PUBLICO = 100000008

    @property
    def nombre_legible(self):
        nombres = {
            self.AMA_DE_CASA: "Ama de casa",
            self.EMPLEADO: "Empleado",
            self.ESTUDIANTE: "Estudiante",
            self.INDEPENDIENTE: "Independiente",
            self.PENSIONADO: "Pensionado",
            self.SOCIO_RENTISTA: "Socio o rentista de capital",
            self.RELIGIOSO: "Religioso",
            self.SERVIDOR_PUBLICO: "Servidor público"
        }
        return nombres.get(self, self.name)

class TipoDocumento(Enum):
    NIT = 100000000
    CEDULA_CIUDADANIA = 100000001
    TARJETA_IDENTIDAD = 100000004
    NUIP = 100000005
    CEDULA_EXTRANJERIA = 100000006
    VISA = 100000002
    LIBRETA_MILITAR = 100000007
    PASAPORTE = 100000008
    REGISTRO_CIVIL = 100000010

    @property
    def nombre_legible(self):
        nombres = {
            self.NIT: "NIT",
            self.CEDULA_CIUDADANIA: "Cédula de ciudadanía",
            self.TARJETA_IDENTIDAD: "Tarjeta de identidad",
            self.NUIP: "NUIP",
            self.CEDULA_EXTRANJERIA: "Cédula de extranjería",
            self.VISA: "Visa",
            self.LIBRETA_MILITAR: "Libreta militar",
            self.PASAPORTE: "Pasaporte",
            self.REGISTRO_CIVIL: "Registro civil"
        }
        return nombres.get(self, self.name)
    
class TiempoCompra(Enum):
    DE_0_A_30_DIAS = 700320003
    DE_31_A_60_DIAS = 700320002
    DE_61_A_90_DIAS = 700320001
    MAS_DE_91_DIAS = 700320000

    @property
    def nombre_legible(self):
        nombres = {
            self.MAS_DE_91_DIAS: "Más de 91 días",
            self.DE_61_A_90_DIAS: "Desde 61 a 90 días",
            self.DE_31_A_60_DIAS: "Desde 31 a 60 días",
            self.DE_0_A_30_DIAS: "Desde 0 a 30 días",
        }
        return nombres.get(self, self.name)