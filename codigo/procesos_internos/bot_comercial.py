from http import HTTPStatus
import threading
from typing import Any, Dict, Optional, cast
from codigo.conexiones_externas.modelos_ia import modelos_ia
from codigo.conexiones_externas.web_scraping import web_scraping
from codigo.procesos_internos.funciones_negocio import funciones_negocio
from codigo.procesos_internos.procesar_mensajes import procesar_mensajes
from codigo.conexiones_externas.dataverse_service import dataverse_service
from codigo.variables import PROMPTS
from codigo.funciones_auxiliares import manejo_errores, leer_archivo
from codigo.procesos_internos.gestor_usuario import gestor_usuario

from datetime import datetime
import json
import pytz
from random import random

from models.enums import CamposUsuario, ColaEscalamiento, TipoCliente


class BotComercial():
    def __init__(self):
        # NOTE: Cada vez que se agrege una funcion al json, se debe agregar a mepeo_funciones        
        self.funciones = self.obtener_funciones_general()
        self.funciones_actualizacion_datos = self.obtener_funciones_perfilacion()

        self.mensaje_bot_pva = "Para poder ayudarte mejor, por favor elige una de las opciones que verás en el siguiente menú: (En otro mensaje será mandado el menú)"
        self.mensaje_escalar = "Tu conversación será transferida a un asesor"
        self.mensaje_whatsapp_bogota = "Te ayudarán con tus dudas en: "

    def llamar(
            self, 
            historial: list[Dict[str,str]], 
            datos_usuario: Dict[CamposUsuario, Any], 
            id_usuario: str
        ):
        try:
            revisar_datos_respuesta = procesar_mensajes.revisar_datos_mensaje(
                historial, 
                self.funciones_actualizacion_datos, 
                id_usuario, 
                datos_usuario
            )
            if revisar_datos_respuesta["status"] != 200:
                return revisar_datos_respuesta
            
            datos_usuario = cast(Dict[CamposUsuario, Any], revisar_datos_respuesta["datos"]["datos_usuario"])
            errores = revisar_datos_respuesta["datos"]["errores"]

            if (errores): 
                tipo_usuario = funciones_negocio.obtener_tipo_usuario(datos_usuario)
                datos_faltantes = funciones_negocio.devolver_datos_faltantes(tipo_usuario, datos_usuario)
                respuesta_cliente = procesar_mensajes.mensaje_final(
                    historial, 
                    {"message": errores}, 
                    datos_usuario, 
                    datos_faltantes
                )

                return self.armar_respuesta(
                    respuesta_cliente, 
                    datos_usuario.get(CamposUsuario.ID_CONVERSACION)
                )
            
            fuera_horario = datos_usuario.get(CamposUsuario.FUERA_HORARIO)
            contacto_agendado = datos_usuario.get(CamposUsuario.CONTACTO_AGENDADO)
            if(fuera_horario and contacto_agendado):
                return self.terminar_conversacion(
                    "Te contactaremos en la fecha y hora agendada, procederé a cerrar la conversación",
                    historial,
                    datos_usuario.get(CamposUsuario.ID_CONVERSACION),
                )

            resultado_proyectos = web_scraping.consultar_nombres_proyectos()
            proyectos_cali: Optional[list[str]] = None
            proyectos_bogota: Optional[list[str]] = None
            if resultado_proyectos.status == HTTPStatus.OK:
                proyectos_cali = resultado_proyectos.datos["proyectos_cali"]
                proyectos_bogota = resultado_proyectos.datos["proyectos_bogota"]
            
            ciudades = web_scraping.consultar_ciudades()
            respuesta_intencion_usuario = procesar_mensajes.revisar_intencion_usuario(
                historial, 
                proyectos_cali, 
                proyectos_bogota, 
                ciudades
            )
            if respuesta_intencion_usuario["status"] == 400:
                codigo_estado = respuesta_intencion_usuario.pop("status")
                datos = {
                    "registro_asistente": respuesta_intencion_usuario.get("message","Ocurrió un error, por favor vuelve a escribir"),
                }
                return {"status": codigo_estado, "datos": datos}
            elif respuesta_intencion_usuario["status"] != 200:
                return respuesta_intencion_usuario

            intencion = respuesta_intencion_usuario["datos"]["intencion"]

            accion_a_ejecutar = ""
            prompt_fuera_horario = ""
            accion = ""
            prompt_preguntas_frecuentes = ""
            es_proyectos_bogota = intencion == "ProyectosBogota"
            respuesta_bot = datos_usuario.get("respuesta_bot")
            es_sac_postventa = intencion == "SACPostventa" or intencion == "SACPostventaEscalar" or (respuesta_bot and (respuesta_bot["intencion_usuario"] == "SACPostventaEscalar" or respuesta_bot["intencion_usuario"] == "SACPostventa"))
            debe_escalar = intencion == "Asesor" or intencion == "SACPostventaEscalar" or datos_usuario.get(CamposUsuario.ESCALAR,False)
            falta_consultar_cliente = datos_usuario.get(CamposUsuario.ID_CLIENTE,"") == "" and not datos_usuario.get(CamposUsuario.ES_NUEVO_LEAD,False)
            es_preguntas_frecuentes = intencion == "PreguntasFrecuentes"
            accion_escalar = ""
            prompt_sac_postventa = PROMPTS["bot_comercial"]["sac_postventa"]
            prompt_preguntas_frecuentes = PROMPTS["bot_comercial"]["respuestas_predeterminadas_preguntas"]                
            datos_faltantes = []
            prompt_escalar = PROMPTS["bot_comercial"]["escalar"]

            tz = pytz.timezone('America/Bogota') 
            fecha = datetime.now(tz)
            fecha_actual = fecha.strftime('%Y-%m-%d %H:%M:%S')
            
            tipos_vivienda = web_scraping.get_json_tipo_vivienda()
            nombres_funcion = [d['nombre_funcion'] for d in self.funciones]
            
            if(es_proyectos_bogota):
                url_whatsapp_bogota = dataverse_service.obtener_whatsapp_bogota()
                return self.terminar_conversacion(
                    self.mensaje_whatsapp_bogota + url_whatsapp_bogota, 
                    historial,
                    datos_usuario.get(CamposUsuario.ID_CONVERSACION),
                )

            sectores = web_scraping.consultar_sectores(19)
            prompt_proyectos = PROMPTS["bot_comercial"]["proyectos"].format(
                proyectos_cali,
                proyectos_bogota,
                ciudades,
                sectores, 
                tipos_vivienda
            )

            if(intencion == "SACPostventaEscalar"
                or intencion == "Asesor" 
                or (CamposUsuario.ESCALAR in datos_usuario 
                    and datos_usuario[CamposUsuario.ESCALAR])
            ):
                datos_usuario[CamposUsuario.ESCALAR] = True

            if(intencion == "BotPVA"):
                return self.escalar_conversacion_directamente(
                    self.mensaje_bot_pva, 
                    historial,
                    datos_usuario.get(CamposUsuario.ID_CONVERSACION),
                    cola=ColaEscalamiento.BOT_COPILOT_STUDIO
                )
            
            if (falta_consultar_cliente):
                datos_faltantes = ["documento"]
                if datos_usuario.get(CamposUsuario.ES_NACIONAL) == None:
                    datos_faltantes.append("territorio")
                
                if(es_sac_postventa or debe_escalar):
                    accion_a_ejecutar = f"Para ampliar la información y poder brindarle una mejor atención, es necesario que nos confirme su número de identicación"
                    respuesta_cliente = procesar_mensajes.mensaje_final(
                        historial, 
                        {"message": accion_a_ejecutar}, 
                        datos_usuario, 
                        datos_faltantes
                    )

                    return self.armar_respuesta(
                        respuesta_cliente, 
                        datos_usuario.get(CamposUsuario.ID_CONVERSACION)
                    )

                else:
                    if "territorio" in datos_faltantes:
                        accion_a_ejecutar = f"No es obligatorio el número de identificación para resolver la duda, responde y solicita el número de identificación del cliente. Si el cliente no te quiere responder ese dato, preguntale si se encuentra en Colombia"
                    else:
                        accion_a_ejecutar = (
                            "Si en los dos mensajes anteriores no has solicitado el número de identificación, "
                            "hazlo nuevamente. De lo contrario, responde la duda del cliente. "
                            "Si ya resolviste la inquietud vuelve a solicitarle su número de identificación."
                        )

            if(es_sac_postventa):
                datos_usuario.get("respuesta_bot",{})["intencion_usuario"] = intencion
                datos_usuario[CamposUsuario.SAC_POSTVENTA] = True
                escalar_postventa = self.validar_escalar_postventa_directamente(datos_usuario)
                if escalar_postventa:
                    return self.escalar_conversacion_directamente(
                        self.mensaje_bot_pva, 
                        historial,
                        datos_usuario.get(CamposUsuario.ID_CONVERSACION),
                        cola=ColaEscalamiento.BOT_COPILOT_STUDIO
                    )
            else:
                datos_usuario[CamposUsuario.SAC_POSTVENTA] = False

            if(debe_escalar):
                datos_usuario[CamposUsuario.ESCALAR] = True
                accion_escalar = "Solicita los <datos-perfilacion> faltantes y escala la conversación"

            ################################################################################

            tipo_usuario = funciones_negocio.obtener_tipo_usuario(datos_usuario)

            if (CamposUsuario.EXISTE_EN_BASE_DATOS in datos_usuario):
                datos_faltantes = funciones_negocio.devolver_datos_faltantes(tipo_usuario, datos_usuario)
                if len(datos_faltantes) > 1:
                    accion_a_ejecutar += ""
                elif(len(datos_faltantes) == 1):
                    accion_a_ejecutar += ""

                if(len(datos_faltantes) <=2):
                    prompt_fuera_horario = PROMPTS["bot_comercial"]["fuera_horario"].format(fecha_actual)
                    if(CamposUsuario.ESCALAR in datos_usuario 
                        and datos_usuario[CamposUsuario.ESCALAR]):
                        accion_a_ejecutar+= "debes escalar la conversación, valida la sección <escalamiento-conversacion>"
                    else: 
                        accion_a_ejecutar+= "preguntar al cliente si desea hablar con un asesor"
                        # accion = "Quiero hablar con un asesor"

            if((datos_faltantes and datos_faltantes[0] != CamposUsuario.PROYECTO_INTERES)
            #    and ("proyecto" not in intencion.lower())
                and (es_sac_postventa or es_preguntas_frecuentes)
            ):
                prompt_proyectos = ""

            ################################################################################

            prompt_consultar_informacion_usuario = PROMPTS["bot_comercial"]["consultar_informacion_usuario"].format(
                accion_escalar,
                datos_faltantes,
                prompt_fuera_horario,
            )

            prompt = PROMPTS["bot_comercial"]["comportamiento_general"].format(
                fecha_actual,
                accion_a_ejecutar,
                prompt_escalar,
                datos_usuario,
                prompt_proyectos,
                prompt_consultar_informacion_usuario, 
                prompt_sac_postventa,
                prompt_preguntas_frecuentes,
                nombres_funcion
            )
                
            if random() < 0.1 and len(historial) > 5:
                prompt += f"\n{PROMPTS['bot_comercial']['alagar_usuario']}"

            chat = []
            chat = modelos_ia.llm.append_system_chat(chat, prompt)
            if(accion_a_ejecutar != ""):
                modelos_ia.llm.append_system_chat(chat, f"En este momento debes: {accion_a_ejecutar}")

            chat.extend(historial)
            mensaje_intencion = ""
            
            if("mensaje_intencion" in respuesta_intencion_usuario["datos"]):
                if isinstance( respuesta_intencion_usuario["datos"]["mensaje_intencion"], str):
                    mensaje_intencion = respuesta_intencion_usuario["datos"]["mensaje_intencion"]
                else:
                    mensaje_intencion = respuesta_intencion_usuario["datos"]["mensaje_intencion"][0]

            if isinstance(chat[-1]["content"], list): 
                chat[-1]["content"][0]["text"] += f"\n{mensaje_intencion}\n{accion}"
            else:
                chat[-1]["content"] += f"\n{mensaje_intencion}\n{accion}"

            gestor_usuario.actualizar_datos_usuario(id_usuario, datos_usuario)

            respuesta_modelo = modelos_ia.llm.llamar(chat, self.funciones, True, id_usuario)
            if respuesta_modelo["status"] == 400:
                codigo_estado = respuesta_modelo.pop("status")
                datos = {
                    "registro_asistente": respuesta_modelo.get("message", "Ocurrió un error, por favor vuelve a escribir"),
                }
                return {"status": codigo_estado, "datos": datos}
            elif respuesta_modelo["status"] != 200:
                return respuesta_modelo
            
            resultado_datos_usuario =  gestor_usuario.leer_usuario(datos_usuario[CamposUsuario.ID_USUARIO_DIRECT_LINE])
            if resultado_datos_usuario["status"]!= 200:
                return {"status": HTTPStatus.INTERNAL_SERVER_ERROR, "datos": {}}
            
            datos_usuario = resultado_datos_usuario["datos"]["datos_usuario"]

            tipo_usuario = funciones_negocio.obtener_tipo_usuario(datos_usuario)
            datos_faltantes = funciones_negocio.devolver_datos_faltantes(tipo_usuario, datos_usuario)
            if(datos_usuario.get(CamposUsuario.ES_NUEVO_LEAD) 
               and not datos_usuario.get(CamposUsuario.ID_CLIENTE)):
                self.crear_lead(datos_usuario)
            elif(len(datos_faltantes) == 0 
                 and not datos_usuario.get(CamposUsuario.FUERA_HORARIO)
                 and not respuesta_modelo.get("datos_escalar",{}).get("activo")
                 and not respuesta_modelo.get("datos_escalar",{}).get("terminar_conversacion")):
                if(datos_usuario.get(CamposUsuario.ESCALAR_AUTOMATICAMENTE)
                   or (not datos_usuario.get(CamposUsuario.ESCALAR_AUTOMATICAMENTE) and len(historial) >= 8)):
                    resp = self.escalar_disponibilidad_agente(datos_usuario, historial)
                    if resp["status"] == HTTPStatus.OK:
                        return resp
                    elif resp["status"] == HTTPStatus.NOT_FOUND and resp.get("datos"):
                        datos_usuario[CamposUsuario.FUERA_HORARIO] = True
                        respuesta_modelo["message"] = resp["datos"]

            respuesta_cliente = procesar_mensajes.mensaje_final(
                chat, 
                respuesta_modelo, 
                datos_usuario, 
                datos_faltantes
            )
            if respuesta_cliente["status"] == 400:
                codigo_estado = respuesta_cliente.pop("status")
                datos = {
                    "registro_asistente": respuesta_cliente.get("message","Ocurrió un error, por favor vuelve a escribir"),
                }
                return {"status": codigo_estado, "datos": datos}
            elif respuesta_cliente["status"] != 200:
                return respuesta_cliente

            registro_asistente = modelos_ia.llm.append_assistant_chat(
                [], respuesta_cliente["datos"]["mensaje"])[0]
            
            if ("funciones_log" in respuesta_modelo 
                and len(respuesta_modelo["funciones_log"]) > 0):
                threading.Thread(target=lambda:dataverse_service.agregar_log_funcion_conversacion(
                    datos_usuario[CamposUsuario.ID_CONVERSACION],
                    respuesta_modelo["funciones_log"])
                ).start()

            datos = {
                "url_audio": "",
                "registro_asistente": registro_asistente,
                "escalar": respuesta_modelo["datos_escalar"],
                "respuestas_funciones": respuesta_modelo.get("respuestas_funciones", []),
                "terminar": respuesta_modelo["datos_escalar"].get("terminar_conversacion",False)
            }
            return {"status": 200, "datos": datos}
        except Exception as e:
            return manejo_errores(self.llamar.__qualname__, 500, error_base=e)
    
    

    def validar_escalar_postventa_directamente(self, datos_usuario):
        return datos_usuario.get(CamposUsuario.TIPO_CLIENTE) == TipoCliente.CONTACTO and datos_usuario.get(CamposUsuario.NEGOCIO_VALIDADO_EQUIPO_SAC_POSTVENTA)

    def escalar_conversacion_directamente(
            self, 
            mensaje: str, 
            historial,
            id_conversacion: str,
            cola: ColaEscalamiento = None, 
            id_cola: str = None
        ) -> Dict[str, Any]:
        
        respuesta_cliente = procesar_mensajes.mensaje_final(
            historial, 
            {"message": mensaje}, 
            {}, 
            [],
            False
        )

        respuesta = self.armar_respuesta(
            respuesta_cliente, 
            id_conversacion
        )

        if respuesta["status"] != 200:
            return respuesta
        
        if cola:
            escalar_conversacion = procesar_mensajes.escalar_conversacion_directamente(cola_escalamiento=cola)
        else:
            escalar_conversacion = procesar_mensajes.escalar_conversacion_directamente(id_cola=id_cola)

        datos = {
            "url_audio": "",
            "registro_asistente": respuesta["datos"]["registro_asistente"],
            "escalar": escalar_conversacion["datos"],
            "respuestas_funciones": []
        }
        return {"status": 200, "datos": datos}
    
    def terminar_conversacion(
            self, 
            mensaje, 
            historial,
            id_conversacion
        ):
        
        respuesta_cliente = procesar_mensajes.mensaje_final(
            historial, 
            {"message": mensaje}, 
            {}, 
            [],
            False
        )

        respuesta = self.armar_respuesta(
            respuesta_cliente, 
            id_conversacion
        )

        if respuesta["status"] != 200:
            return respuesta

        datos = {
            "url_audio": "",
            "registro_asistente": respuesta["datos"]["registro_asistente"],
            "escalar": {"activo": False},
            "respuestas_funciones": [],
            "terminar": True
        }
        return {"status": 200, "datos": datos}

    def crear_lead(self, datos_usuario: Dict[CamposUsuario, Any]):
        if(datos_usuario.get(CamposUsuario.ID_CLIENTE)):
            return
        
        nombre = datos_usuario.get(CamposUsuario.NOMBRE)
        apellido = datos_usuario.get(CamposUsuario.APELLIDO)
        email = datos_usuario.get(CamposUsuario.EMAIL_CLIENTE)
        celular = datos_usuario.get(CamposUsuario.CELULAR)
        if (nombre and apellido and (celular or email)):
            documento = datos_usuario.get(CamposUsuario.DOCUMENTO_IDENTIFICACION)
            canal = datos_usuario.get(CamposUsuario.CANAL)
            id_conversacion = datos_usuario.get(CamposUsuario.ID_CONVERSACION)
            id_usuario_direct_line = datos_usuario.get(CamposUsuario.ID_USUARIO_DIRECT_LINE)
            dataverse_service.crear_lead(nombre, 
                                         apellido, 
                                         canal, 
                                         id_conversacion, 
                                         id_usuario_direct_line, 
                                         False, 
                                         celular, 
                                         email, 
                                         numero_identificacion=documento)

    def escalar_disponibilidad_agente(
            self, 
            datos_usuario: Dict[CamposUsuario, Any], 
            historial
        ) -> Dict[str,Any]:
        respuesta_escalar = dataverse_service.disponibilidad_agente(
            datos_usuario.get(CamposUsuario.ID_USUARIO_DIRECT_LINE), 
            1 if datos_usuario.get(CamposUsuario.TIPO_CLIENTE) == TipoCliente.LEAD and datos_usuario.get(CamposUsuario.PROYECTO_INTERES, "") != "N/A" else 0, 
            False
        )
        if(respuesta_escalar.status == HTTPStatus.OK):
            data = respuesta_escalar.datos
            if(CamposUsuario.FUERA_HORARIO in data and data[CamposUsuario.FUERA_HORARIO]):
                return {"status": HTTPStatus.NOT_FOUND, "datos": data["mensaje"]}
            else:
                id_conversacion = datos_usuario[CamposUsuario.ID_CONVERSACION]
                respuesta = self.escalar_conversacion_directamente(
                    self.mensaje_escalar,
                    historial,
                    id_conversacion,
                    id_cola=data["id_cola"])
                return respuesta

        return {"status": HTTPStatus.INTERNAL_SERVER_ERROR}

    def obtener_funciones_general(self):
        funciones = json.loads(leer_archivo(
            "assets/funciones_general.json"))
        mapeo_funciones = {
            "consultar_proyectos": web_scraping.consultar_proyectos,
            "consultar_macro_proyectos": web_scraping.consultar_macro_proyectos,
            "informacion_sobre_proyecto_por_nombre": web_scraping.informacion_sobre_proyecto_por_nombre,
            "informacion_sobre_proyecto": web_scraping.informacion_sobre_proyecto,
            "disponibilidad_agente": dataverse_service.disponibilidad_agente,
            "consultar_proyectos_crm": dataverse_service.consultar_proyectos_crm,
            "obtener_whatsapp_bogota": dataverse_service.obtener_whatsapp_bogota,
            "crear_log_preguntas_no_atendidas": dataverse_service.crear_log_preguntas_no_atendidas,
            "consultar_informacion_sala_venta": web_scraping.consultar_informacion_sala_venta
        }
        for funcion in funciones:
            nombre_funcion = funcion["nombre_funcion"]
            if nombre_funcion in mapeo_funciones:
                funcion["objeto_funcion"] = mapeo_funciones[nombre_funcion]

        return funciones
    
    def obtener_funciones_perfilacion(self):
        funciones = json.loads(leer_archivo(
            "assets/funciones_perfilacion.json"))
        mapeo_funciones = {
            "consultar_proyectos_crm": dataverse_service.consultar_proyectos_crm
        }
        for funcion in funciones:
            nombre_funcion = funcion["nombre_funcion"]
            if nombre_funcion in mapeo_funciones:
                funcion["objeto_funcion"] = mapeo_funciones[nombre_funcion]

        return funciones

    def armar_respuesta(self, respuesta_modelo: Dict[str, Any], id_conversacion: str) -> Dict[str,Any]:
        
        if respuesta_modelo["status"] == 400:
            codigo_estado = respuesta_modelo.pop("status")
            datos = {
                "registro_asistente": respuesta_modelo.get("message","Ocurrió un error, por favor vuelve a escribir"),
            }
            return {"status": codigo_estado, "datos": datos}
        elif respuesta_modelo["status"] != 200:
            return respuesta_modelo

        registro_asistente = modelos_ia.llm.append_assistant_chat(
                        [], respuesta_modelo["datos"]["mensaje"])[0]
                    
        if ("funciones_log" in respuesta_modelo 
            and len(respuesta_modelo["funciones_log"]) > 0):
            threading.Thread(target=lambda:dataverse_service.agregar_log_funcion_conversacion(
                id_conversacion,
                respuesta_modelo["funciones_log"])
            ).start()

        datos:Dict[str, Any] = {
            "registro_asistente": registro_asistente,
            "escalar": respuesta_modelo.get("datos_escalar",{"activo": False}),
            "respuestas_funciones": respuesta_modelo.get("respuestas_funciones", []),
            "terminar": respuesta_modelo.get("datos_escalar",{}).get("terminar_conversacion",False)
        }

        return {"status": 200, "datos": datos}

bot_comercial = BotComercial()
