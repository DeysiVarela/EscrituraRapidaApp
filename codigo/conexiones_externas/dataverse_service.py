from datetime import date, datetime, time
import os
import re
from typing import Any, Dict, Optional
import pytz
import requests
from http import HTTPStatus
from codigo.funciones_auxiliares import manejo_errores
from codigo.procesos_internos.gestor_usuario import gestor_usuario
from codigo.procesos_internos.funciones_negocio import funciones_negocio
from models.enums import ActividadEconomica, CamposUsuario, Canal, TiempoCompra, TipoCliente, TipoDocumento
from models.resultado_operacion import ResultadoOperacion

class RecidivismRequest:
    def __init__(
            self, 
            lead_id: str, 
            contact_id: str, 
            id_origen_lead: str, 
            id_media: str, 
            id_medio_digital: str
        ):
        self.lead_id = lead_id
        self.contact_id = contact_id
        self.id_origen_lead = id_origen_lead
        self.id_media = id_media
        self.id_medio_digital = id_medio_digital
        
    def to_payload(self):
        return {
            "leadId": self.lead_id,
            "contactId": self.contact_id,
            "leadSourceId": self.id_origen_lead,
            "mediaId": self.id_media,
            "digitalMediaId": self.id_medio_digital
        }

class DataverseService:
    def __init__(self):    
        self.url_base = os.environ["URL_AZURE_FUNCTION"]
        self.ambiente = os.environ["AMBIENTE"]
        self.id_origen_lead = "205a8a76-9114-f011-998a-002248e0c4b3"
        self.id_media = "b01ebf39-4896-e711-80fb-e0071b6fb0e1"
        self.id_medio_digital_facebook = "d172c443-32c1-ef11-a72e-002248e0dcab"
        self.id_medio_digital_whatsapp = "49c4d207-33c1-ef11-a72e-002248e0dcab"
        self.id_medio_digital_instagram = "235ad86d-32c1-ef11-a72e-002248e0dcab"
        self.id_medio_digital_chatweb = "d4eb6fe8-32c1-ef11-a72e-002248e0dcab"
        self.catalogo_actividad_economica = [100000000,100000001,100000002,100000003,100000004,100000006,100000007,100000008]
        self.catalogo_tiempo_compra = [700320000,700320001,700320002,700320003]
        self.catalogo_tipo_documento = [100000000,100000001,100000004,100000005,100000006,100000002,100000007,100000008,100000010]
        self.regex_email = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

        api_key = os.environ["SELF_API_KEY"]
        self.header = {
            "x-api-key": api_key
        }

    TERRITORIO_NACIONAL_CODE = 100000000
    TERRITORIO_INTERNACIONAL_CODE = 100000001

    def buscar_clientes_por_numero_identificacion(
            self, 
            numero_identificacion: str, 
            id_conversacion: str, 
            medio_digital: str, 
            id_usuario_direct_line: str
        ):
        try:
            url = f"{self.url_base}/SearchClientByDocumentNumber/{numero_identificacion}?env={self.ambiente}"
            respuesta = requests.get(url, headers=self.header)

            if respuesta.status_code == HTTPStatus.OK:
                datos = respuesta.json()
                self.asignar_cliente_conversation(
                    id_conversacion,
                    datos["entityType"],
                    datos["id"],
                    datos["fullname"],
                    datos["wasDisqualified"]
                )

                lead_id = datos["id"] if datos["entityType"] == 0 else None
                contact_id = datos["id"] if datos["entityType"] == 1 else None
                id_medio_digital = self.obtener_id_medio_digital(medio_digital)
                reincidencia = RecidivismRequest(
                    lead_id,
                    contact_id, 
                    self.id_origen_lead,
                    self.id_media,
                    id_medio_digital
                )

                respuesta_reincidencia = self.crear_reincidencia(reincidencia)
                texto_asesor_confianza = f"el id del asesor de confianza es {datos['trustedAdvisorId']} ." if datos['trustedAdvisorId'] else "no tiene asesor de confianza."
                texto_perfilar =  f"Se debe perfilar el cliente." if datos['profileAgain'] else "NO se debe perfilar al cliente."
                texto_descalificado = "Se encontraba descalificado." if datos['wasDisqualified'] else "NO se encontraba descalificado."
                texto_valido_para_bot_copilot = "Tiene un negocio válido para enrutar al equipo de SAC o Postventa" if datos['validBusinessOldBot'] else ""
                documento = datos["documentNumber"] if(datos["documentNumber"]) else None
                actividad_economica = int(datos["customerActivity"]) if(datos["customerActivity"]) else None
                proyecto_interes = datos["projectTnterestId"] if(datos["projectTnterestId"]) else None
                tiempo_compra = int(datos["purchaseTime"]) if datos["purchaseTime"] else None                                
                email_cliente = datos["email"] if datos["email"] else None
                ingresos_mensuales = int(datos["monthlyIncome"]) if datos["monthlyIncome"] else None

                primer_nombre = str(datos["fullname"]).split(" ")[0] if datos.get("fullname") else None

                datos_usuario: Dict[CamposUsuario,Any] = {
                    CamposUsuario.ID_ASESOR_CONFIANZA: datos['trustedAdvisorId'],
                    CamposUsuario.PERFILAR_CLIENTE: True if datos['profileAgain'] else False,
                    CamposUsuario.DESCALIFICADO: True if datos['wasDisqualified'] else False,
                    CamposUsuario.NEGOCIO_VALIDADO_EQUIPO_SAC_POSTVENTA: True if datos['validBusinessOldBot'] else False,
                    CamposUsuario.TIPO_CLIENTE: TipoCliente.LEAD if datos['entityType'] == 0 else TipoCliente.CONTACTO,
                    CamposUsuario.ID_CLIENTE: datos['id'],
                    CamposUsuario.DOCUMENTO_IDENTIFICACION: documento,
                    CamposUsuario.TIEMPO_COMPRA: tiempo_compra,
                    CamposUsuario.INGRESOS_MENSUALES:ingresos_mensuales, 
                    CamposUsuario.ACTIVIDAD_ECONOMICA:actividad_economica,
                    CamposUsuario.PROYECTO_INTERES: proyecto_interes,
                    CamposUsuario.EMAIL_CLIENTE: email_cliente, 
                    CamposUsuario.ES_NACIONAL: None,
                    CamposUsuario.EXISTE_EN_BASE_DATOS: True,
                    CamposUsuario.NOMBRE_COMPLETO: datos['fullname'],
                    CamposUsuario.TIPO_DOCUMENTO_IDENTIFICACION: datos["documentType"],
                    CamposUsuario.ES_NUEVO_LEAD: False,
                    CamposUsuario.PRIMER_NOMBRE: primer_nombre,
                }
                
                tipo_usuario = funciones_negocio.obtener_tipo_usuario(datos_usuario)
                datos_usuario[CamposUsuario.ESCALAR_AUTOMATICAMENTE] = (len(funciones_negocio.devolver_datos_faltantes(tipo_usuario, datos_usuario)) - 1) > 0

                if medio_digital != Canal.WHATSAPP:
                    datos_usuario[CamposUsuario.CELULAR] = datos["mobilephone"]

                gestor_usuario.actualizar_datos_usuario(id_usuario_direct_line,datos_usuario)

                respuesta_texto = f"se encontró al cliente con id {datos['id']}, su nombre es {datos['fullname']}, es de tipo {TipoCliente.LEAD if datos['entityType'] == 0 else TipoCliente.CONTACTO}. {texto_asesor_confianza} {texto_perfilar} {texto_descalificado} {respuesta_reincidencia} {texto_valido_para_bot_copilot}"
                respuesta_usuario = gestor_usuario.leer_usuario(id_usuario_direct_line)
                if respuesta_usuario["status"] != 200:
                    return respuesta_texto + ". Ejecutar la función actualizar_territorio"
                
                datos_usuario = respuesta_usuario["datos"]["datos_usuario"]
                territorio = datos_usuario.get(CamposUsuario.ES_NACIONAL)
                if(territorio != None):
                    self.actualizar_territorio(territorio, id_usuario_direct_line)
               
                return respuesta_texto
            elif respuesta.status_code == HTTPStatus.NOT_FOUND:
                datos_usuario = {
                    CamposUsuario.EXISTE_EN_BASE_DATOS: False,
                    CamposUsuario.ES_NUEVO_LEAD: True,
                    CamposUsuario.ID_CLIENTE: "",
                    CamposUsuario.TIPO_CLIENTE: "",
                    CamposUsuario.DOCUMENTO_IDENTIFICACION: numero_identificacion,
                    CamposUsuario.ESCALAR_AUTOMATICAMENTE: True
                }
                gestor_usuario.actualizar_datos_usuario(id_usuario_direct_line,datos_usuario)

                return "no se encontró el cliente en la base de datos"
            else:
                manejo_errores(
                    self.buscar_clientes_por_numero_identificacion.__qualname__, 
                    respuesta.status_code,
                    error_base=respuesta.text,
                    usar_traceback=False
                )
                return "ocurrió un error realizando la consulta"
        except Exception as e:
            manejo_errores(self.buscar_clientes_por_numero_identificacion.__qualname__, 500, error_base=e)
            return "ocurrió un error realizando la consulta"

    
    def buscar_clientes_por_celular(
            self, 
            celular: str, 
            id_conversacion: str, 
            medio_digital: str, 
            id_usuario_direct_line: str
        ):
        try:
            url = f"{self.url_base}/SearchClientByMobilephone/{celular}?env={self.ambiente}"
            respuesta = requests.get(url,headers=self.header)
            if respuesta.status_code == HTTPStatus.OK:
                datos = respuesta.json()
                self.asignar_cliente_conversation(
                    id_conversacion,
                    datos["entityType"],
                    datos["id"],
                    datos["fullname"],
                    datos["wasDisqualified"]
                )

                lead_id = datos["id"] if datos["entityType"] == 0 else None
                contact_id = datos["id"] if datos["entityType"] == 1 else None
                id_medio_digital = self.obtener_id_medio_digital(medio_digital)
                reincidencia = RecidivismRequest(
                    lead_id,
                    contact_id, 
                    self.id_origen_lead,
                    self.id_media,
                    id_medio_digital
                )

                respuesta_reincidencia = self.crear_reincidencia(reincidencia)
                texto_asesor_confianza = f"el id del asesor de confianza es {datos['trustedAdvisorId']} ." if datos['trustedAdvisorId'] else "no tiene asesor de confianza."
                texto_perfilar =  f"Se debe perfilar el cliente." if datos['profileAgain'] else "NO se debe perfilar al cliente."
                texto_descalificado = "Se encontraba descalificado." if datos['wasDisqualified'] else "NO se encontraba descalificado."
                texto_valido_para_bot_copilot = "Tiene un negocio válido para enrutar al equipo de SAC o Postventa" if datos['validBusinessOldBot'] else ""
                documento = datos["documentNumber"] if(datos["documentNumber"]) else None
                actividad_economica = int(datos["customerActivity"]) if(datos["customerActivity"]) else None
                proyecto_interes = datos["projectTnterestId"] if(datos["projectTnterestId"]) else None
                tiempo_compra = int(datos["purchaseTime"]) if datos["purchaseTime"] else None                                
                email_cliente = datos["email"] if datos["email"] else None
                ingresos_mensuales = int(datos["monthlyIncome"]) if datos["monthlyIncome"] else None
                primer_nombre = str(datos["fullname"]).split(" ")[0] if datos.get("fullname") else None

                datos_usuario:Dict[CamposUsuario,Any] = {
                    CamposUsuario.ID_ASESOR_CONFIANZA: datos['trustedAdvisorId'],
                    CamposUsuario.PERFILAR_CLIENTE: True if datos['profileAgain'] else False,
                    CamposUsuario.DESCALIFICADO: True if datos['wasDisqualified'] else False,
                    CamposUsuario.NEGOCIO_VALIDADO_EQUIPO_SAC_POSTVENTA: True if datos['validBusinessOldBot'] else False,
                    CamposUsuario.TIPO_CLIENTE: TipoCliente.LEAD if datos['entityType'] == 0 else TipoCliente.CONTACTO,
                    CamposUsuario.ID_CLIENTE: datos['id'],
                    CamposUsuario.DOCUMENTO_IDENTIFICACION: documento,
                    CamposUsuario.TIEMPO_COMPRA: tiempo_compra,
                    CamposUsuario.INGRESOS_MENSUALES:ingresos_mensuales, 
                    CamposUsuario.ACTIVIDAD_ECONOMICA:actividad_economica,
                    CamposUsuario.PROYECTO_INTERES: proyecto_interes,
                    CamposUsuario.EMAIL_CLIENTE: email_cliente, 
                    CamposUsuario.ES_NACIONAL: None,
                    CamposUsuario.EXISTE_EN_BASE_DATOS: True,
                    CamposUsuario.NOMBRE_COMPLETO: datos['fullname'],
                    CamposUsuario.TIPO_DOCUMENTO_IDENTIFICACION: datos['documentType'],
                    CamposUsuario.ES_NUEVO_LEAD: False,
                    CamposUsuario.PRIMER_NOMBRE: primer_nombre,
                }
                
                if medio_digital != Canal.WHATSAPP:
                    datos_usuario[CamposUsuario.CELULAR] = datos["mobilephone"]

                gestor_usuario.actualizar_datos_usuario(id_usuario_direct_line,datos_usuario)

                return f"se encontró al cliente con id {datos['id']}, su nombre es {datos['fullname']}, es de tipo {TipoCliente.LEAD if datos['entityType'] == 0 else TipoCliente.CONTACTO}. {texto_asesor_confianza} {texto_perfilar} {texto_descalificado} {respuesta_reincidencia} {texto_valido_para_bot_copilot}"
            elif respuesta.status_code == HTTPStatus.NOT_FOUND:
                datos_usuario = {
                    CamposUsuario.EXISTE_EN_BASE_DATOS: False,
                    CamposUsuario.ES_NUEVO_LEAD: False,
                    CamposUsuario.ID_CLIENTE: "",
                    CamposUsuario.TIPO_CLIENTE: ""
                }
                gestor_usuario.actualizar_datos_usuario(id_usuario_direct_line,datos_usuario)

                return "no se encontró el cliente en la base de datos"
            else:
                manejo_errores(
                    self.buscar_clientes_por_celular.__qualname__, 
                    respuesta.status_code,
                    error_base=respuesta.text,
                    usar_traceback=False
                )
                return "ocurrió un error realizando la consulta"
        except Exception as e:
            manejo_errores(self.buscar_clientes_por_celular.__qualname__, 500, error_base=e)
            return "ocurrió un error realizando la consulta"
    
    def actualizar_territorio(
            self, 
            esta_en_colombia: bool, 
            id_usuario_direct_line: str,
            tipo_cliente: Optional[TipoCliente] = None,
            id_cliente: Optional[str] = None):
        try:
            
            if not id_cliente:
                datos_usuario = {
                    CamposUsuario.ES_NACIONAL: esta_en_colombia
                }
                gestor_usuario.actualizar_datos_usuario(id_usuario_direct_line,datos_usuario)
                return ResultadoOperacion.exitoso()

            if tipo_cliente == TipoCliente.CONTACTO:
                url = f"{self.url_base}/Contact/UpdateTerritory?env={self.ambiente}"
            else:
                url = f"{self.url_base}/Lead/UpdateTerritory?env={self.ambiente}"

            payload:Dict[str,Any] = {
                "guid": id_cliente,
                "territory": DataverseService.TERRITORIO_NACIONAL_CODE if esta_en_colombia == True else DataverseService.TERRITORIO_INTERNACIONAL_CODE
            }
            respuesta = requests.put(url, json=payload, headers=self.header)
            
            if respuesta.status_code == HTTPStatus.NO_CONTENT:
                datos_usuario = {
                    CamposUsuario.ES_NACIONAL: esta_en_colombia
                }
                gestor_usuario.actualizar_datos_usuario(id_usuario_direct_line,datos_usuario)

                return ResultadoOperacion.exitoso()
            else:
                manejo_errores(
                    self.actualizar_territorio.__qualname__, 
                    respuesta.status_code,
                    error_base=respuesta.text,
                    usar_traceback=False
                )
                return ResultadoOperacion.error(HTTPStatus(respuesta.status_code), "ocurrió un error realizando la actualización del territorio.")
        except Exception as e:
            manejo_errores(self.actualizar_territorio.__qualname__, 500, error_base=e)
            return ResultadoOperacion.error(HTTPStatus.INTERNAL_SERVER_ERROR, "ocurrió un error realizando la actualización del territorio.")

    def crear_reincidencia(self, reincidencia: RecidivismRequest):
        try:
            url = f"{self.url_base}/RecidivismMedium?env={self.ambiente}"
            payload = reincidencia.to_payload()
            respuesta = requests.post(url, json=payload, headers=self.header)
            
            if respuesta.status_code == HTTPStatus.NO_CONTENT:
                return "se creó la reincidencia en la base de datos"
            else:
                return "ocurrió un error generando la reincidencia del cliente"
        except:
            return "ocurrió un error generando la reincidencia del cliente"
        
    
    
    def disponibilidad_agente(
            self, 
            id_usuario_direct_line: str,
            proyecto_disponible: int = 1,
            peticion_ia: bool = True
        ) -> ResultadoOperacion:
        try:
            respuesta_usuario = gestor_usuario.leer_usuario(id_usuario_direct_line)
            if respuesta_usuario["status"] != 200:
                texto = "error consultando datos del usuario"
                if(peticion_ia):
                    return texto
                else:
                    return ResultadoOperacion.error(HTTPStatus.INTERNAL_SERVER_ERROR, texto)
                
            datos_usuario = respuesta_usuario["datos"]["datos_usuario"]
            if (CamposUsuario.ID_CLIENTE not in datos_usuario or not datos_usuario[CamposUsuario.ID_CLIENTE]):
                if datos_usuario[CamposUsuario.ES_NUEVO_LEAD]:
                    texto = "Debes crear al cliente en la base de datos y perfilarlo para poder avanzar"
                else:
                    texto = "Debes solicitar el número de identificación para validar si el cliente existe en la base de datos."
                
                if(peticion_ia):
                    return texto
                else:
                    return ResultadoOperacion.error(HTTPStatus.BAD_REQUEST, texto)
            
            resultado = self.validar_perfilacion_cliente(
                                                id_usuario_direct_line,
                                                datos_usuario[CamposUsuario.TIPO_CLIENTE],
                                                datos_usuario,
                                                proyecto_disponible)
            if resultado is not None:
                if(peticion_ia):
                    return resultado
                else:
                    return ResultadoOperacion.error(HTTPStatus.BAD_REQUEST, resultado)

            id_agente = datos_usuario[CamposUsuario.ID_ASESOR_CONFIANZA]
            if id_agente != None and id_agente != "":

                url = f"{self.url_base}/AvailabilityAgent/{id_agente}?env=prd"
                respuesta = requests.get(url, headers=self.header)
            
                if respuesta.status_code == HTTPStatus.OK:
                    datos = respuesta.json()

                    if datos["isAvailable"] == True:
                        datos_usuario = {
                            CamposUsuario.ID_COLA: datos['queueId']
                        }
                        gestor_usuario.actualizar_datos_usuario(id_usuario_direct_line,datos_usuario)                
                        
                        if(peticion_ia):
                            return f"El agente está disponible. ID de la cola del agente: {datos['queueId']}. Debes escalar la conversación ya."
                        else:
                            datos = {
                                "id_cola": datos['queueId']
                            }
                            return ResultadoOperacion.exitoso(datos)
                
                elif respuesta.status_code != HTTPStatus.NOT_FOUND:
                    manejo_errores(
                        self.disponibilidad_agente.__qualname__, 
                        respuesta.status_code,
                        error_base=respuesta.text,
                        usar_traceback=False
                    )
                    return ResultadoOperacion.error(HTTPStatus(respuesta.status_code), "ocurrió un error realizando la consulta" )

            respuesta_cola = self.consultar_cola_para_enrutar(
                        datos_usuario[CamposUsuario.TIPO_CLIENTE],
                        datos_usuario[CamposUsuario.ID_CLIENTE],
                        id_usuario_direct_line,
                        datos_usuario[CamposUsuario.ES_NACIONAL],
                        datos_usuario[CamposUsuario.ID_ASESOR_CONFIANZA],
                        datos_usuario[CamposUsuario.PERFILAR_CLIENTE],
                        datos_usuario[CamposUsuario.INGRESOS_MENSUALES],
                        peticion_ia
                    )
            return respuesta_cola
            
        except Exception as e:
            manejo_errores(self.disponibilidad_agente.__qualname__, 500, error_base=e)
            return ResultadoOperacion.error(HTTPStatus.INTERNAL_SERVER_ERROR, "Ocurrió una excepción consultando la disponibilidad del agente.")
        
    
    def consultar_cola_para_enrutar(
            self, 
            tipo_cliente: TipoCliente, 
            id_cliente: str, 
            id_usuario_direct_line: str,
            es_nacional : bool,
            id_agente: str,
            perfilar: bool, 
            ingresos_mensuales: int,
            peticion_ia: bool = True
        ) -> ResultadoOperacion:
        try:
            url = f"{self.url_base}/GetQueueToRoute?env=prd"
            se_debe_perfilar = perfilar == 1
            codigo_tipo_cliente = 0 if tipo_cliente == TipoCliente.LEAD else 1

            payload = {
                "entityType": codigo_tipo_cliente,
                "id": id_cliente,
                "profileAgain": se_debe_perfilar,
                "trustedAdvisorId": id_agente,
                "monthlyIncome": ingresos_mensuales,
                "isNational": es_nacional 
            }
            respuesta = requests.post(url, json=payload, headers=self.header)
            
            if respuesta.status_code == HTTPStatus.OK:
                datos = respuesta.json()
                if datos['isAvailable']:
                    datos_usuario = {
                        CamposUsuario.ID_COLA: datos['queueId']
                    }
                    gestor_usuario.actualizar_datos_usuario(id_usuario_direct_line,datos_usuario)
                    if(peticion_ia):
                        return f"el ID de la cola a la cual se debe enrutar es {datos['queueId']}, se encuentra en horario hábil. Debes escalar la conversación ya."
                    else:
                        datos = {
                            "id_cola": datos['queueId'],
                            "fuera_horario": False
                        }
                        return ResultadoOperacion.exitoso(datos)
                else:
                    self.marcar_fuera_horario(codigo_tipo_cliente,id_cliente, datos['queueId'])
                    texto_festivos = ""
                    texto_semana = ""
                    texto_sabados = ""
                    texto_domingos = ""
                    datos_usuario: Dict[CamposUsuario, Any] = {}

                    if datos["closureDays"]:
                        fechas = [d.replace("T00:00:00","") for d in datos["closureDays"]]
                        datos_usuario[CamposUsuario.DIAS_NO_HABILES] = fechas
                        texto_festivos = f"Los siguientes días no se trabajará, por ende no se puede atender al cliente esos días: {fechas}"
                    
                    opening_hours = datos["openingHours"]
                    if(opening_hours):
                        hora_inicio = opening_hours["startTimeWeek"]
                        hora_fin = opening_hours["endTimeWeek"]
                        if hora_inicio and hora_fin:
                            texto_semana = f"lunes a viernes de {hora_inicio} hasta {hora_fin} "
                            datos_usuario[CamposUsuario.HORA_INICIO_SEMANA] = datetime.strptime(hora_inicio, "%I:%M %p").time().strftime("%H:%M:%S")
                            datos_usuario[CamposUsuario.HORA_FIN_SEMANA] = datetime.strptime(hora_fin, "%I:%M %p").time().strftime("%H:%M:%S")
                        else:
                            texto_semana = "no hay atención de lunes a viernes"
                        
                        hora_inicio = opening_hours["startTimeSaturday"]
                        hora_fin = opening_hours["endTimeSaturday"]
                        if hora_inicio and hora_fin:
                            texto_sabados = f"sábados de {hora_inicio} hasta {hora_fin}"
                            datos_usuario[CamposUsuario.HORA_INICIO_SABADO] = datetime.strptime(hora_inicio, "%I:%M %p").time().strftime("%H:%M:%S")
                            datos_usuario[CamposUsuario.HORA_FIN_SABADO] = datetime.strptime(hora_fin, "%I:%M %p").time().strftime("%H:%M:%S")
                        else: 
                            texto_sabados = "no hay atención los sábados"
                        
                        hora_inicio = opening_hours["startTimeSunday"]
                        hora_fin = opening_hours["endTimeSunday"]
                        if hora_inicio and hora_fin:
                            texto_domingos = f"domingos de {hora_inicio} hasta {hora_fin}"
                            datos_usuario[CamposUsuario.HORA_INICIO_DOMINGO] = datetime.strptime(hora_inicio, "%I:%M %p").time().strftime("%H:%M:%S")
                            datos_usuario[CamposUsuario.HORA_FIN_DOMINGO] = datetime.strptime(hora_fin, "%I:%M %p").time().strftime("%H:%M:%S")
                        else:
                            texto_domingos = "no hay atención los domingos"

                    zona_colombia = pytz.timezone("America/Bogota")
                    ahora_colombia = datetime.now(zona_colombia)

                    datos_usuario[CamposUsuario.FUERA_HORARIO] = True
                    gestor_usuario.actualizar_datos_usuario(id_usuario_direct_line,datos_usuario)
                    texto_respuesta = f"""En este momento ({ahora_colombia}) no estamos en horario hábil. El horario hábil en zona horaria Bogotá, Colombia (UTC-5) es: {texto_semana} . {texto_sabados} .{texto_domingos} .{texto_festivos}"""
                    if(peticion_ia):
                        return texto_respuesta
                    else:
                        datos: Dict[str, Any] = {
                            "id_cola": datos['queueId'],
                            "fuera_horario": True,
                            "mensaje": texto_respuesta
                        }
                        return ResultadoOperacion.exitoso(datos)
            elif HTTPStatus(respuesta.status_code) == HTTPStatus.NOT_FOUND:
                self.marcar_fuera_horario(codigo_tipo_cliente,id_cliente, None)
                return ResultadoOperacion.error(HTTPStatus(respuesta.status_code), "No se encontró la cola a la cual se debe enrutar.")
            else:
                manejo_errores(
                    self.consultar_cola_para_enrutar.__qualname__, 
                    respuesta.status_code,
                    error_base=respuesta.text,
                    usar_traceback=False
                )
                return ResultadoOperacion.error(HTTPStatus(respuesta.status_code), "ocurrió un error realizando la consulta.")
        except Exception as e:
            manejo_errores(self.consultar_cola_para_enrutar.__qualname__, 500, error_base=e)
            return ResultadoOperacion.error(HTTPStatus.INTERNAL_SERVER_ERROR, "ocurrió un error realizando la consulta.")

    def actualizar_datos_lead(self, 
                              id: str,
                              id_usuario_direct_line: str,
                              email: Optional[str] = None, 
                              ingresos_mensuales: Optional[int] = None, 
                              actividad_economica: Optional[int] = None,
                              proyecto_interes: Optional[str] = None,
                              tiempo_compra: Optional[int] = None):
        try:
            url = f"{self.url_base}/Lead/UpdateLeadData?env={self.ambiente}?env={self.ambiente}"
            payload:Dict[str,Any] = {
                "id": id,
                "email": email,
                "monthlyIncome": ingresos_mensuales,
                "customerActivity": actividad_economica,
                "projectTnterestId": proyecto_interes,
                "purchaseTime": tiempo_compra
            }

            resultado_validacion = self.validar_datos_lead(payload)
            if resultado_validacion.status != HTTPStatus.OK:
                return resultado_validacion

            payload = {
                "id": id,
                "email": email if email else None,
                "monthlyIncome": int(ingresos_mensuales) if ingresos_mensuales else None,
                "customerActivity": int(actividad_economica) if actividad_economica else None,
                "projectTnterestId": proyecto_interes if proyecto_interes and proyecto_interes != "N/A" else None,
                "purchaseTime": int(tiempo_compra) if tiempo_compra else None
            }

            self.actualizar_datos_usuario_json(
                            id_usuario_direct_line,
                            email, 
                            ingresos_mensuales, 
                            actividad_economica,
                            proyecto_interes,
                            tiempo_compra,
                            False,
            )
            
            respuesta = requests.put(url, json=payload, headers=self.header)
            if respuesta.status_code == HTTPStatus.NO_CONTENT:
                return ResultadoOperacion.exitoso()
            else:
                manejo_errores(
                    self.actualizar_datos_lead.__qualname__, 
                    respuesta.status_code,
                    error_base=respuesta.text,
                    usar_traceback=False
                )
                return ResultadoOperacion.error(HTTPStatus(respuesta.status_code), "ocurrió un error realizando la actualización.")
        except Exception as e:
            error = manejo_errores(self.actualizar_datos_lead.__qualname__, 500, error_base=e)
            return ResultadoOperacion.error(HTTPStatus.INTERNAL_SERVER_ERROR, error.get("error", "ocurrió una excepción."))
        

    def actualizar_datos_nuevo_lead(self, 
                            id: str,
                            id_usuario_direct_line: str,
                            tipo_documento:Optional[int] = None,
                            numero_identificacion: Optional[str] = None,
                            celular: Optional[str] = None,
                            email: Optional[str] = None, 
                            ingresos_mensuales: Optional[int] = None, 
                            actividad_economica: Optional[int] = None,
                            proyecto_interes: Optional[str] = None,
                            tiempo_compra: Optional[int] = None):
        try:                
            url = f"{self.url_base}/Lead/UpdateLeadData?env={self.ambiente}?env={self.ambiente}"
            payload:Dict[str,Any] = {
                "id": id,
                "documentType": tipo_documento if tipo_documento else None,
                "documentNumber": numero_identificacion if numero_identificacion else None,
                "mobilephone": celular if celular else None,
                "email": email if email else None,
                "monthlyIncome": int(ingresos_mensuales) if ingresos_mensuales else None,
                "customerActivity": int(actividad_economica) if actividad_economica else None,
                "projectTnterestId": proyecto_interes if proyecto_interes and proyecto_interes != "N/A" else None,
                "purchaseTime": int(tiempo_compra) if tiempo_compra else None
            }

            resultado_validacion = self.validar_datos_lead(payload)
            if resultado_validacion.status != HTTPStatus.OK:
                return resultado_validacion
            
            self.actualizar_datos_usuario_json(
                            id_usuario_direct_line,
                            email, 
                            ingresos_mensuales, 
                            actividad_economica,
                            proyecto_interes,
                            tiempo_compra,
                            True,
                            tipo_documento,
                            numero_identificacion,
                            celular
                            )
            
            respuesta = requests.put(url, json=payload, headers=self.header)
            if respuesta.status_code == HTTPStatus.NO_CONTENT:
                return ResultadoOperacion.exitoso()
            else:
                manejo_errores(
                    self.actualizar_datos_nuevo_lead.__qualname__, 
                    respuesta.status_code,
                    error_base=respuesta.text,
                    usar_traceback=False
                )
                return ResultadoOperacion.error(HTTPStatus(respuesta.status_code), "ocurrió un error realizando la actualización.")
        except Exception as e:
            error = manejo_errores(self.actualizar_datos_nuevo_lead.__qualname__, 500, error_base=e)
            return ResultadoOperacion.error(HTTPStatus.INTERNAL_SERVER_ERROR, error.get("error", "ocurrió una excepción."))

    def crear_lead(self, 
                   nombre: str,
                   apellido: str,
                   medio_digital,
                   id_conversacion: str,
                   id_usuario_direct_line: str,
                   perfilacion_completa: int,
                   celular: Optional[str] = None,
                   email: Optional[str] = None,
                   tipo_documento: Optional[int] = None,
                   numero_identificacion: Optional[str] = None,
                   ingresos_mensuales: Optional[int] = None, 
                   actividad_economica: Optional[int] = None,
                   proyecto_interes: str = "",
                   tiempo_compra: Optional[int] = None):
        try:
            respuesta_usuario = gestor_usuario.leer_usuario(id_usuario_direct_line)
            if respuesta_usuario["status"] != 200:
                return ResultadoOperacion.error(HTTPStatus.INTERNAL_SERVER_ERROR, "error consultando datos del usuario")
                
            datos_old = respuesta_usuario["datos"]["datos_usuario"]
            if (datos_old.get(CamposUsuario.ID_CLIENTE)):
                    return ResultadoOperacion.exitoso()

            url = f"{self.url_base}/Lead?env={self.ambiente}"

            if not nombre:
                return ResultadoOperacion.error(HTTPStatus.BAD_REQUEST, "Se debe solicitar el nombre para poder crear el lead.")
            
            if not apellido:
                return ResultadoOperacion.error(HTTPStatus.BAD_REQUEST, "Se debe solicitar el apellido para poder crear el lead.")
            
            if (not email and not celular):
                return ResultadoOperacion.error(HTTPStatus.BAD_REQUEST, "Se debe solicitar el correo o el celular para poder crear el lead.")
            
            if (numero_identificacion
                and tipo_documento
                and email
                and celular
                and ingresos_mensuales and ingresos_mensuales != 0
                and actividad_economica and actividad_economica != 0
                and proyecto_interes
                and tiempo_compra and tiempo_compra != 0
            ):
                perfilacion_completa = True
            else:
                perfilacion_completa = False

            id_medio_digital = self.obtener_id_medio_digital(medio_digital)
            payload:Dict[str,Any] = {
                "firstName": nombre,
                "lastName": apellido,
                "documentType": int(tipo_documento) if tipo_documento else None,
                "documentNumber": numero_identificacion,
                "email": email,
                "mobilephone": celular,
                "customerActivity": int(actividad_economica) if actividad_economica else None,
                "monthlyIncome": int(ingresos_mensuales) if ingresos_mensuales else None,
                "projectTnterestId": proyecto_interes,
                "purchaseTime": int(tiempo_compra) if tiempo_compra else None,
                "leadSourceId": self.id_origen_lead,
                "mediaId": self.id_media,
                "digitalMediaId": id_medio_digital,
                "isProfilingComplete": perfilacion_completa,
                "conversationId": id_conversacion
            }
            
            respuesta = requests.post(url, json=payload, headers=self.header)
            if respuesta.status_code == HTTPStatus.OK:
                datos = respuesta.json()                
                datos_usuario:Dict[CamposUsuario,Any] = {
                    CamposUsuario.PERFILAR_CLIENTE: perfilacion_completa,
                    CamposUsuario.TIPO_CLIENTE: TipoCliente.LEAD,
                    CamposUsuario.DOCUMENTO_IDENTIFICACION: numero_identificacion,
                    CamposUsuario.TIEMPO_COMPRA: int(tiempo_compra) if tiempo_compra else None,
                    CamposUsuario.INGRESOS_MENSUALES: int(ingresos_mensuales) if ingresos_mensuales else None, 
                    CamposUsuario.ACTIVIDAD_ECONOMICA:int(actividad_economica) if actividad_economica else None,
                    CamposUsuario.PROYECTO_INTERES: proyecto_interes,
                    CamposUsuario.EMAIL_CLIENTE: email, 
                    CamposUsuario.CELULAR: celular,
                    CamposUsuario.ID_CLIENTE: datos['id'],
                    CamposUsuario.TIPO_DOCUMENTO_IDENTIFICACION: int(tipo_documento) if tipo_documento else None,
                    CamposUsuario.ID_ASESOR_CONFIANZA: None,
                    CamposUsuario.NOMBRE: nombre,
                    CamposUsuario.APELLIDO: apellido,
                    CamposUsuario.ESCALAR_AUTOMATICAMENTE: True
                }
                gestor_usuario.actualizar_datos_usuario(id_usuario_direct_line,datos_usuario)
                
                territorio = datos_old.get(CamposUsuario.ES_NACIONAL)
                if(territorio != None):
                    self.actualizar_territorio(territorio, id_usuario_direct_line)

                return ResultadoOperacion.exitoso()
            else:
                manejo_errores(
                        self.crear_lead.__qualname__, 
                        respuesta.status_code,
                        error_base=respuesta.text,
                        usar_traceback=False
                    )
                return ResultadoOperacion.error(HTTPStatus(respuesta.status_code), "ocurrió un error creando el lead.")
        except Exception as e:
            manejo_errores(self.crear_lead.__qualname__, 500, error_base=e)
            return ResultadoOperacion.error(HTTPStatus.INTERNAL_SERVER_ERROR, "ocurrió una excepción creando el lead.")

    def guardado_temporal_datos_nuevo_lead(
            self, 
            medio_digital: str,
            id_conversacion: str,  
            id_usuario_direct_line: str,
            nombre: Optional[str]= "",
            apellido: Optional[str]= "",
            celular: Optional[str] = None,
            email: Optional[str] = None,
            numero_identificacion: Optional[str] = None
        ):
        try:
            respuesta_usuario = gestor_usuario.leer_usuario(id_usuario_direct_line)
            if respuesta_usuario["status"] != 200:
                return ResultadoOperacion.error(HTTPStatus.INTERNAL_SERVER_ERROR, "error consultando datos del usuario")
                
            datos_old = respuesta_usuario["datos"]["datos_usuario"]
            if (datos_old.get(CamposUsuario.ID_CLIENTE)):
                    return ResultadoOperacion.exitoso()

            if (not nombre
                or not apellido
                or (not email and not celular)):
                
                datos_usuario = {}
                if nombre:
                    datos_usuario[CamposUsuario.NOMBRE] = nombre

                if apellido:
                    datos_usuario[CamposUsuario.APELLIDO] = apellido

                if email:
                    datos_usuario[CamposUsuario.EMAIL_CLIENTE] = email

                if celular:
                    datos_usuario[CamposUsuario.CELULAR] = celular

                if numero_identificacion:
                    datos_usuario[CamposUsuario.DOCUMENTO_IDENTIFICACION] = numero_identificacion
                
                gestor_usuario.actualizar_datos_usuario(id_usuario_direct_line,datos_usuario)

                return ResultadoOperacion.exitoso()
            
            return self.crear_lead(
                nombre,
                apellido,
                medio_digital, 
                id_conversacion, 
                id_usuario_direct_line,
                False,
                celular,
                email,
                numero_identificacion=numero_identificacion
            )

        except Exception as e:
            manejo_errores(self.guardado_temporal_datos_nuevo_lead.__qualname__, 500, error_base=e)
            return ResultadoOperacion.error(HTTPStatus.INTERNAL_SERVER_ERROR, "ocurrió una excepción creando el lead.")

    
    def actualizar_datos_contacto(
            self, 
            id: str,
            id_usuario_direct_line: str,
            email: Optional[int] = None,
            ingresos_mensuales: Optional[int] = None,
            celular: str = ""
        ):
        try:
            datos_usuario: Dict[CamposUsuario, Any] = {}
            
            url = f"{self.url_base}/Contact/UpdateContactData?env={self.ambiente}"
            payload:Dict[str,Any] = {
                "id": id,
                "email": email if email else None,
                "monthlyIncome": int(ingresos_mensuales) if ingresos_mensuales else None,
                "mobilephone": celular if celular else None
            }

            ingresos_mensuales = int(ingresos_mensuales) if ingresos_mensuales else 0

            if(ingresos_mensuales is not None 
               and int(ingresos_mensuales) > 0
            ):
                datos_usuario[CamposUsuario.INGRESOS_MENSUALES] = ingresos_mensuales

            if email:
                datos_usuario[CamposUsuario.EMAIL_CLIENTE] = email

            if celular:
                datos_usuario[CamposUsuario.CELULAR] = celular

            gestor_usuario.actualizar_datos_usuario(id_usuario_direct_line, datos_usuario)
            
            respuesta = requests.put(url, json=payload, headers=self.header)
            if respuesta.status_code == HTTPStatus.NO_CONTENT:
                return ResultadoOperacion.exitoso()
            else:
                manejo_errores(
                    self.actualizar_datos_contacto.__qualname__, 
                    respuesta.status_code,
                    error_base=f"id_cliente: {id} - " + respuesta.text,
                    usar_traceback=False
                )
                ResultadoOperacion.error(HTTPStatus(respuesta.status_code), "ocurrió un error realizando la actualización.")
        except Exception as e:
            error = manejo_errores(self.actualizar_datos_contacto.__qualname__, 500, error_base=e)
            ResultadoOperacion.error(HTTPStatus.INTERNAL_SERVER_ERROR, error.get("error", "ocurrió una excepción"))

    def asignar_cliente_conversation(self, 
                                     id_conversacion: str,
                                     tipo_cliente: int,
                                     id_cliente: str,
                                     nombre_cliente: str,
                                     estaba_descalificado: bool):
        url = f"{self.url_base}/SetClientInConversation?env={self.ambiente}"
        payload:Dict[str,Any] = {
            "conversationId": id_conversacion,
            "entityType": tipo_cliente,
            "clientId": id_cliente,
            "fullname": nombre_cliente,
            "wasDisqualified": estaba_descalificado
        }
        
        respuesta = requests.post(url, json=payload, headers=self.header)
        if respuesta.status_code == HTTPStatus.NO_CONTENT:
            return ResultadoOperacion.exitoso()
        else:
            ResultadoOperacion.error(HTTPStatus(respuesta.status_code), "ocurrió un error asociando la conversación al cliente.")
    
    def obtener_whatsapp_bogota(self):
        url = f"{self.url_base}/RedirectAppWhatsapp?env={self.ambiente}"
        respuesta = requests.get(url, headers=self.header)
        if respuesta.status_code == HTTPStatus.OK:
            url = respuesta.text
            return f"La URL para contactar con Constructora Bolivar Bogotá para proyectos que no se encuentran en Cali y sus alrededores ni Armenia es {url}"
        elif respuesta.status_code == HTTPStatus.NOT_FOUND:
            return "No se encontró la información requerida."
        else:
            return "ocurrió un error realizando la consulta."

    def marcar_fuera_horario(
            self, 
            tipo_cliente: int, 
            id: str, 
            id_cola: str
        ):
        try:
            url = f"{self.url_base}/OutOfTime?env={self.ambiente}"
            payload:Dict[str,Any] = {
                "entityType": tipo_cliente,
                "Id": id,
                "queueId" : id_cola
            }
            
            respuesta = requests.post(url, json=payload, headers=self.header)
            if respuesta.status_code == HTTPStatus.NO_CONTENT:
                return "Se actualizó la información."
            else:
                return "ocurrió un error actualizando los datos."
        except:
            return "ocurrió un error actualizando los datos."
        
    def actualizar_datos_para_contactar(
            self, 
            id_usuario_direct_line: str, 
            fecha_contacto: date,
            hora_contacto: time
        ):
        try:
            respuesta_usuario = gestor_usuario.leer_usuario(id_usuario_direct_line)
            if respuesta_usuario["status"] != 200:
                return ResultadoOperacion.error(HTTPStatus.INTERNAL_SERVER_ERROR, "error consultando datos del usuario")
                
            datos_usuario = respuesta_usuario["datos"]["datos_usuario"]
            
            hora_inicio_semana = datos_usuario.get(CamposUsuario.HORA_INICIO_SEMANA)
            hora_fin_semana = datos_usuario.get(CamposUsuario.HORA_FIN_SEMANA)
            hora_inicio_sabado = datos_usuario.get(CamposUsuario.HORA_INICIO_SABADO)
            hora_fin_sabado = datos_usuario.get(CamposUsuario.HORA_FIN_SABADO)
            hora_inicio_domingo = datos_usuario.get(CamposUsuario.HORA_INICIO_DOMINGO)
            hora_fin_domingo = datos_usuario.get(CamposUsuario.HORA_FIN_DOMINGO)
            dias_no_habiles: list[str] = datos_usuario.get(CamposUsuario.DIAS_NO_HABILES)
            tz = pytz.timezone('America/Bogota') 
            fecha_completa_colombia = datetime.now(tz)
            fecha_completa_contacto = datetime.combine(fecha_contacto, hora_contacto)
            fecha_completa_contacto = tz.localize(fecha_completa_contacto)

            texto_semana = f"horario hábil: lunes a viernes de {hora_inicio_semana} a {hora_fin_semana}." if hora_fin_semana else ""
            texto_sabado = f"sábados de {hora_inicio_sabado} a {hora_fin_sabado}." if hora_inicio_sabado else ""
            texto_domingo = f"domingos de {hora_inicio_domingo} a {hora_fin_domingo}." if hora_inicio_sabado else ""
            texto_festivos = f"Los siguientes días no se trabajará, por ende no se puede atender al cliente esos días: {dias_no_habiles}" if dias_no_habiles else ""
            texto_no_habil = f"{texto_semana}{texto_sabado}{texto_domingo}{texto_festivos}"
            if (dias_no_habiles and 
                any(datetime.strptime(fecha, "%Y-%m-%d") == fecha_contacto for fecha in dias_no_habiles)):
                return ResultadoOperacion.error(HTTPStatus.BAD_REQUEST, f"el día indicado no tendremos atención, por favor selecciona otro día. {texto_no_habil}")
                    
            if fecha_completa_colombia > fecha_completa_contacto:
                return ResultadoOperacion.error(HTTPStatus.BAD_REQUEST, f"la fecha y hora elegida debe ser mayor a la fecha actual: {fecha_completa_colombia} , y encontrarse en horario hábil. {texto_no_habil}")

            if(fecha_contacto.weekday() < 5):
                if(not hora_inicio_semana or not hora_fin_semana):
                    return ResultadoOperacion.error(HTTPStatus.BAD_REQUEST, f"No tenemos atención entre semana, por favor selecciona otro día. {texto_no_habil}")
                
                time_hora_inicio_semana = datetime.strptime(hora_inicio_semana, "%H:%M:%S").time()
                time_hora_fin_semana = datetime.strptime(hora_fin_semana, "%H:%M:%S").time()
                if(hora_contacto < time_hora_inicio_semana or hora_contacto >= time_hora_fin_semana):
                    return ResultadoOperacion.error(HTTPStatus.BAD_REQUEST, f"la hora no es válida, el horario hábil entre semana es de {hora_inicio_semana} a {hora_fin_semana}, por favor selecciona un horario hábil. {texto_no_habil}")
                
            if(fecha_contacto.weekday() == 5):
                if(not hora_inicio_sabado or not hora_fin_sabado):
                    return ResultadoOperacion.error(HTTPStatus.BAD_REQUEST, f"No tenemos atención el sábado, por favor selecciona otro día. {texto_no_habil}")
                
                time_hora_inicio_sabado = datetime.strptime(hora_inicio_sabado, "%H:%M:%S").time()
                time_hora_fin_sabado = datetime.strptime(hora_fin_sabado, "%H:%M:%S").time()
                if(hora_contacto < time_hora_inicio_sabado or hora_contacto >= time_hora_fin_sabado):
                    return ResultadoOperacion.error(HTTPStatus.BAD_REQUEST, f"la hora no es válida, el horario hábil los sábados es de {hora_inicio_sabado} a {hora_fin_sabado}, por favor selecciona otro día. {texto_no_habil}")
                
            if(fecha_contacto.weekday() == 6):
                if(not hora_inicio_domingo or not hora_fin_domingo):
                    return ResultadoOperacion.error(HTTPStatus.BAD_REQUEST, f"No tenemos atención el domingo. {texto_no_habil}")
                
                time_hora_inicio_domingo = datetime.strptime(hora_inicio_domingo, "%H:%M:%S").time()
                time_hora_fin_domingo = datetime.strptime(hora_fin_domingo, "%H:%M:%S").time()
                if(hora_contacto < time_hora_inicio_domingo or hora_contacto >= time_hora_fin_domingo):
                    return ResultadoOperacion.error(HTTPStatus.BAD_REQUEST, f"la hora no es válida, el horario hábil los domingos es de {hora_inicio_domingo} a {hora_fin_domingo}. {texto_no_habil}")

            tipo_cliente = datos_usuario.get(CamposUsuario.TIPO_CLIENTE)
            id_cliente = datos_usuario.get(CamposUsuario.ID_CLIENTE)

            fecha_utc = fecha_completa_contacto.astimezone(pytz.UTC)
            fecha_utc_str = fecha_utc.isoformat().replace('+00:00', 'Z') 

            url = f"{self.url_base}/SetDataToContactClient?env={self.ambiente}"
            payload:Dict[str,Any] = {
                "entityType": 0 if tipo_cliente == TipoCliente.LEAD else 1,
                "id": id_cliente,
                "dateToContact": fecha_utc_str
            }
            
            respuesta = requests.post(url, json=payload, headers=self.header)
            if respuesta.status_code == HTTPStatus.NO_CONTENT:
                return ResultadoOperacion.exitoso()
            else:
                manejo_errores(
                    self.actualizar_datos_para_contactar.__qualname__, 
                    respuesta.status_code,
                    error_base=f"tipo_cliente: {tipo_cliente}, id_cliente: {id_cliente} - " + respuesta.text,
                    usar_traceback=False
                )
                return ResultadoOperacion.error(HTTPStatus(respuesta.status_code), "ocurrió un error actualizando los datos.")
        except Exception as e:
            manejo_errores(self.actualizar_datos_para_contactar.__qualname__, 500, error_base=e)
            return ResultadoOperacion.error(HTTPStatus.INTERNAL_SERVER_ERROR, "ocurrió una excepción actualizando los datos.")

    def consultar_proyectos_crm(
            self, 
            retornar_texto: bool = True
        ):
        try:
            url = f"{self.url_base}/Projects?env={self.ambiente}"
            respuesta = requests.get(url, headers=self.header)
            if respuesta.status_code == HTTPStatus.OK:
                datos = respuesta.json()
                if(retornar_texto):
                    texto_proyectos = "Proyectos: "
                    for proyecto in datos:
                        direccion = None
                        nombre_proyecto = None
                        if not proyecto['address'] is None:
                            direccion = proyecto['address']

                        if not proyecto['name'] is None:
                            nombre_proyecto = proyecto['name']
                        
                        texto_numero_cuotas = ""
                        if proyecto['numberPaymentInstallments']:
                            texto_numero_cuotas = f", tiempo para pagar cuota inicial: {proyecto['numberPaymentInstallments']} meses"
                        texto_proyectos = texto_proyectos + f"Nombre proyecto: {nombre_proyecto}, Id: {proyecto['id']}, Direccion: {direccion}, {texto_numero_cuotas}\n"
                    return texto_proyectos
                else:
                    return datos
            else:
                return "ocurrió un error realizando la consulta."
        except:
            return "ocurrió un error realizando la consulta."

    def crear_log_preguntas_no_atendidas(
            self, 
            asunto: str, 
            pregunta: str, 
            numero_identificacion: str = ""
        ):
        try:
            url = f"{self.url_base}/CreateLogNanAnsweredQuestions?env={self.ambiente}"
            payload = {
                "documentNumber": numero_identificacion,
                "name": asunto,
                "question": pregunta
            }
            respuesta = requests.post(url,json=payload, headers=self.header)
            if respuesta.status_code == HTTPStatus.NO_CONTENT:
                return "se creó el log de pregunta no atendida."
            else:
                return "error creando el log de pregunta no atendida."
        except:
            return "ocurrió un error creando el log de pregunta no atendida."
        
    def consultar_conversacion(
            self, 
            id_conversacion: str
        ) -> Dict[str,Any]:
        try:
            url = f"{self.url_base}/Conversation/{id_conversacion}?env=prd"
            respuesta = requests.get(url, headers=self.header)
            if respuesta.status_code == HTTPStatus.OK:
                datos = respuesta.json()
                info_conversacion = {
                    "canal": datos["channel"]
                }
                return {"status": respuesta.status_code, "datos":info_conversacion}
            else:
                manejo_errores(
                    self.consultar_conversacion.__qualname__, 
                    respuesta.status_code,
                    error_base=f"id: {id_conversacion}" + respuesta.text,
                    usar_traceback=False
                )
                return {"status": respuesta.status_code}
        except Exception as e:
            manejo_errores(self.consultar_conversacion.__qualname__, 500, error_base=e)
            return {"status": 500}        

    def obtener_id_medio_digital(self, medio_digital: str):
        match medio_digital:
            case Canal.FACEBOOK:
                return self.id_medio_digital_facebook
            case Canal.INSTAGRAM:
                return self.id_medio_digital_instagram
            case Canal.WHATSAPP:
                return self.id_medio_digital_whatsapp
            case Canal.WEB:
                return self.id_medio_digital_chatweb
            case _:
                return self.id_medio_digital_chatweb
            
    def validar_perfilacion_cliente(self,
                                    id_usuario_direct_line: str,
                                    tipo_cliente: int = -1,
                                    datos_usuario: Dict[CamposUsuario, Any] = {},
                                    proyecto_disponible: int = 1) -> Optional[str]:
        """
            Valida la información de perfilación del cliente para enrutarlo a la cola correspondiente.

            Esta función verifica que se hayan proporcionado todos los datos requeridos para la 
            clasificación del cliente como lead o contacto. Si algún dato falta, intenta obtenerlo 
            desde los datos almacenados del usuario.

            Args:
                ingresos_mensuales (float|int|str): Ingresos mensuales del cliente.
                actividad_economica (str|int): Actividad económica del cliente (solo para leads).
                proyecto_interes (str): Proyecto de interés del cliente (solo para leads).
                email_cliente (str): Correo electrónico del cliente.
                celular_cliente (str): Número de celular del cliente (solo para contactos).
                tiempo_compra (str|int): Tiempo estimado para la compra.
                id_usuario_direct_line (str): ID del usuario en Direct Line.
                tipo_cliente (int): 0 para lead, 1 para contacto.
                id_cliente (str): ID del cliente en CRM.
                es_nacional (bool|int, optional): Indica si el cliente se encuentra en Colombia.

            Returns:
                str|None: Mensaje de error si falta algún dato obligatorio, o None si todo está correcto.

            Side Effects:
                Actualiza los datos del usuario en la base de datos.
                También actualiza los datos del lead o contacto en el CRM.

            Raises:
                None
        """
                    
        usuario = datos_usuario

        if(usuario[CamposUsuario.ES_NUEVO_LEAD]):
             
            if (CamposUsuario.TIPO_DOCUMENTO_IDENTIFICACION not in usuario
                or usuario[CamposUsuario.TIPO_DOCUMENTO_IDENTIFICACION] is None 
                or usuario[CamposUsuario.TIPO_DOCUMENTO_IDENTIFICACION] == ''):
                return "Debes preguntar el tipo documento del cliente para poder consultar la cola a la cual se debe enrutar"
            
            if (CamposUsuario.DOCUMENTO_IDENTIFICACION not in usuario
                or usuario[CamposUsuario.DOCUMENTO_IDENTIFICACION] is None 
                or usuario[CamposUsuario.DOCUMENTO_IDENTIFICACION] == ''):
                return "Debes preguntar por número del documento de identificacion del cliente para poder consultar la cola a la cual se debe enrutar"
            
            if (CamposUsuario.CELULAR not in usuario
                or usuario[CamposUsuario.CELULAR] is None 
                or usuario[CamposUsuario.CELULAR] == ''):
                return  "Debes preguntar por el número de celular del cliente para poder consultar la cola a la cual se debe enrutar"


        if(CamposUsuario.ES_NACIONAL not in usuario 
           or not isinstance(usuario[CamposUsuario.ES_NACIONAL], bool)
        ):        
            return "Para poder enrutar con un asesor se debe preguntar al cliente si se encuentra en Colombia"
                    
        if (CamposUsuario.INGRESOS_MENSUALES not in usuario
            or usuario[CamposUsuario.INGRESOS_MENSUALES] is None 
            or usuario[CamposUsuario.INGRESOS_MENSUALES] == 0
        ):
            return "Debes preguntar cuáles son los ingresos mensuales para poder consultar la cola a la cual se debe enrutar"

        if(CamposUsuario.EMAIL_CLIENTE not in usuario
            or usuario[CamposUsuario.EMAIL_CLIENTE] is None 
            or usuario[CamposUsuario.EMAIL_CLIENTE] == ''
        ):
            return "Debes preguntar cuál es el correo electronico del cliente para poder consultar la cola a la cual se debe enrutar"

        if usuario[CamposUsuario.TIPO_CLIENTE] == TipoCliente.LEAD:
            if (CamposUsuario.TIEMPO_COMPRA not in usuario
                or usuario[CamposUsuario.TIEMPO_COMPRA] is None 
                or usuario[CamposUsuario.TIEMPO_COMPRA] == ''
            ):
                return "Falta conocer el código de la cantidad promedio de días en los cuales el cliente va a querer realizar el proceso de compra para poder consultar la cola a la cual se debe enrutar"

            if(CamposUsuario.ACTIVIDAD_ECONOMICA not in usuario
                or usuario[CamposUsuario.ACTIVIDAD_ECONOMICA] is None 
                or usuario[CamposUsuario.ACTIVIDAD_ECONOMICA] == ''
                or usuario[CamposUsuario.ACTIVIDAD_ECONOMICA] == -1
            ):
                return "Debes preguntar cuál es la actividad economica del cliente para poder consultar la cola a la cual se debe enrutar"

            if bool(proyecto_disponible):
                if(CamposUsuario.PROYECTO_INTERES not in usuario 
                    or usuario[CamposUsuario.PROYECTO_INTERES] is None 
                    or usuario[CamposUsuario.PROYECTO_INTERES] == ""
                ):
                    return "Falta conocer el proyecto de interes del cliente para poder consultar la cola a la cual se debe enrutar"
                
        else:
            if(CamposUsuario.CELULAR not in usuario
                or usuario[CamposUsuario.CELULAR] is None 
                or usuario[CamposUsuario.CELULAR] == ''
            ):
                return "Debes preguntar cuál es el numero de celular del cliente para poder consultar la cola a la cual se debe enrutar"

        if(usuario[CamposUsuario.ES_NUEVO_LEAD]):
            self.actualizar_datos_nuevo_lead(
                usuario[CamposUsuario.ID_CLIENTE],
                id_usuario_direct_line,
                usuario[CamposUsuario.TIPO_DOCUMENTO_IDENTIFICACION],
                usuario[CamposUsuario.DOCUMENTO_IDENTIFICACION],
                usuario[CamposUsuario.CELULAR],
                usuario[CamposUsuario.EMAIL_CLIENTE],
                usuario[CamposUsuario.INGRESOS_MENSUALES],
                usuario[CamposUsuario.ACTIVIDAD_ECONOMICA],
                usuario[CamposUsuario.PROYECTO_INTERES],
                usuario[CamposUsuario.TIEMPO_COMPRA])
        elif(tipo_cliente == TipoCliente.LEAD):
            self.actualizar_datos_lead(
                usuario[CamposUsuario.ID_CLIENTE],
                id_usuario_direct_line,
                usuario[CamposUsuario.EMAIL_CLIENTE],
                usuario[CamposUsuario.INGRESOS_MENSUALES],
                usuario[CamposUsuario.ACTIVIDAD_ECONOMICA],
                usuario[CamposUsuario.PROYECTO_INTERES],
                usuario[CamposUsuario.TIEMPO_COMPRA])
        else:
            self.actualizar_datos_contacto(
                usuario[CamposUsuario.ID_CLIENTE],
                id_usuario_direct_line,
                usuario[CamposUsuario.EMAIL_CLIENTE],
                usuario[CamposUsuario.INGRESOS_MENSUALES],
                usuario[CamposUsuario.CELULAR])

        return None
    
    def actualizar_datos_usuario_json(
            self,
            id_usuario_direct_line: str,
            email: Optional[str] = None,
            ingresos_mensuales: Optional[int] = None, 
            actividad_economica: Optional[int] = None,
            proyecto_interes: Optional[str] = None,
            tiempo_compra: Optional[int] = None,
            es_nuevo_lead:bool = False,
            tipo_documento:Optional[int] = None,
            numero_documento: Optional[str] = None,
            celular: Optional[str] = None,
            ):
        
        datos_usuario: Dict[CamposUsuario, Any] = {}

        ingresos_mensuales = int(ingresos_mensuales) if ingresos_mensuales else 0
        actividad_economica = int(actividad_economica) if actividad_economica else None
        tiempo_compra = int(tiempo_compra) if tiempo_compra else None

        if(es_nuevo_lead):
            if tipo_documento is not None and tipo_documento != '':
                datos_usuario[CamposUsuario.TIPO_DOCUMENTO_IDENTIFICACION] = tipo_documento

            if numero_documento is not None and numero_documento != '':
                datos_usuario[CamposUsuario.DOCUMENTO_IDENTIFICACION] = numero_documento

            if celular is not None and celular != '':
                datos_usuario[CamposUsuario.CELULAR] = celular

        if actividad_economica is not None and actividad_economica != '':
            datos_usuario[CamposUsuario.ACTIVIDAD_ECONOMICA] = actividad_economica

        if proyecto_interes is not None and proyecto_interes != '':
            datos_usuario[CamposUsuario.PROYECTO_INTERES] = proyecto_interes
            
        if(ingresos_mensuales is not None 
            and ingresos_mensuales != ''
            and int(ingresos_mensuales) > 0
        ):
            datos_usuario[CamposUsuario.INGRESOS_MENSUALES] = ingresos_mensuales

        if email is not None and email != '':
            datos_usuario[CamposUsuario.EMAIL_CLIENTE] = email

        if tiempo_compra is not None and tiempo_compra != '':
            datos_usuario[CamposUsuario.TIEMPO_COMPRA] = tiempo_compra

        gestor_usuario.actualizar_datos_usuario(id_usuario_direct_line, datos_usuario)
        return datos_usuario

    def agregar_log_funcion_conversacion(
            self, 
            id_conversacion: str, 
            funciones
        ):
        try:
            url = f"{self.url_base}/AddLogEventConversacion?env=prd"
            payload:Dict[str,Any] = {
                "conversationId": id_conversacion,
                "eventLogs": funciones
            }
            respuesta = requests.post(url, json=payload, headers=self.header)
            if respuesta.status_code == HTTPStatus.NO_CONTENT:
                return {"status": respuesta.status_code}
            else:
                manejo_errores(
                    self.agregar_log_funcion_conversacion.__qualname__, 
                    respuesta.status_code,
                    error_base=respuesta.text,
                    usar_traceback=False
                )
                return {"status": respuesta.status_code, "error": respuesta.text}
        except Exception as e:
            manejo_errores(self.agregar_log_funcion_conversacion.__qualname__, 500, error_base=e)
            return {"status": 500, "error": e}   

    def validar_datos_lead(self, datos: Dict[str, Any]):
        actividad = datos.get("customerActivity")
        if actividad != None:
            if(not isinstance(actividad, int)
                or actividad not in self.catalogo_actividad_economica):
                return ResultadoOperacion.error(HTTPStatus.BAD_REQUEST, f"las opciones para la actividad económica son {[tipo.nombre_legible for tipo in ActividadEconomica]}, me confirmas cuál es")
            
        tiempo_compra = datos.get("purchaseTime")
        if tiempo_compra != None:
            if (not isinstance(tiempo_compra, int)
                or tiempo_compra not in self.catalogo_tiempo_compra):
                return ResultadoOperacion.error(HTTPStatus.BAD_REQUEST, f"las opciones para el tiempo de compra son {[tipo.nombre_legible for tipo in TiempoCompra]}, me confirmas cuál es")

        email = datos.get("email")
        if email:
            if(re.match(self.regex_email, email) is None):
                return ResultadoOperacion.error(HTTPStatus.BAD_REQUEST, "el correo electrónico no tiene la forma prefijo@dominio.com")
        
        proyecto_interes = datos.get("projectTnterestId")
        if proyecto_interes:
            if(proyecto_interes != "N/A"):
                if(not funciones_negocio.es_guid_valido(str(proyecto_interes))):
                    return ResultadoOperacion.error(HTTPStatus.BAD_REQUEST, "el ID del proyecto no es válido")
                
                proyectos = self.consultar_proyectos_crm(False)
                if not (any(item.get("id") == proyecto_interes for item in proyectos)):
                    return ResultadoOperacion.error(HTTPStatus.BAD_REQUEST, "no exite un proyecto con el ID indicado")
        
        tipo_documento = datos.get("documentType")
        if tipo_documento != None:
            if(not isinstance(tipo_documento, int)
                or tipo_documento not in self.catalogo_tipo_documento):
                return ResultadoOperacion.error(HTTPStatus.BAD_REQUEST, f"las opciones para el tipo de documento son {[tipo.nombre_legible for tipo in TipoDocumento]}, me confirmas cuál es")

        return ResultadoOperacion.exitoso()

dataverse_service = DataverseService()

if __name__ == "__main__":
    pass