from datetime import datetime
from http import HTTPStatus
import json
import os
from typing import Any, Dict, Optional, cast

import pytz
from codigo.conexiones_externas.dataverse_service import dataverse_service
from codigo.variables import PROMPTS
from codigo.funciones_auxiliares import eliminador_texto, evaluador, manejo_errores
from codigo.conexiones_externas.modelos_ia import modelos_ia
from codigo.procesos_internos.gestor_usuario import gestor_usuario
from codigo.procesos_internos.funciones_negocio import funciones_negocio

import re

import threading
import requests

from models.enums import CamposUsuario, ColaEscalamiento, TipoCliente, TipoUsuario
from models.resultado_operacion import ResultadoOperacion

class ProcesarMensajes:
    def __init__(self):
        self.id_cola_bot_ia_intermedia = os.environ["COLA_BOT_IA_INTERMEDIA"]
        self.id_cola_bot_copilot_studio = os.environ["COLA_BOT_COPILOT_STUDIO"]
        self.saludo = "Es obligatorio incluir el saludo y las políticas de protección de datos, según lo indicado en la sección <saludo>. La respuesta a lo preguntado por el cliente debe incluirse después de este mensaje estándar de saludo y protección de datos."
        self.saludo_ejemplo = "<saludo>Mensaje: ¡Hola{}! Soy el agente IA Constructora Bolívar y fui creado para ser tu asesor virtual en temas de inversión de tu próxima vivienda. Cuéntame tus dudas para darte una rápida respuesta y ponerte en contacto con un agente comercial 💚 Queremos informarte que tus datos personales serán tratados de acuerdo con nuestra política de protección de datos. Puedes consultarla en el siguiente enlace: https://www.constructorabolivar.com/politicas-de-calidad-y-privacidad Al continuar con esta conversación, entendemos que aceptas los términos establecidos en nuestra política.</saludo>"

    def revisar_intencion_usuario(
            self, 
            historial: list[Dict[str,str]], 
            proyectos_cali: Optional[list[str]], 
            proyectos_bogota: Optional[list[str]], 
            ciudades
        ) -> Dict[str, Any]:

        try:
            chat = [item for item in historial if 'tool_call_id' not in item and 'annotations' not in item]

            mensajes = self.transformar_conversacion(chat)
            prompt_intervencion = PROMPTS["revision_mensajes"]["revisar_intencion_usuario"].format(
                mensajes, 
                proyectos_cali, 
                proyectos_bogota, 
                ciudades
            )
            chat_prompt = modelos_ia.llm.append_system_chat([], prompt_intervencion)
            respuesta_modelo = modelos_ia.llm.llamar(chat_prompt,temperature=0.0)
            if respuesta_modelo["status"] != 200:
                return respuesta_modelo

            datos = {
                "mensaje_intencion": "",
                "intencion": ""
            }

            intencion = evaluador(eliminador_texto(
                respuesta_modelo["message"], True))
            if isinstance(intencion, list):
                intencion = intencion[0]
            if not intencion:
                return {"status": 200, "datos": datos}

            mensajes_por_intencion = {
                "Terminar": "\nQuiero hablar con un asesor",
                "Asesor": "\nQuiero hablar con un asesor, pideme mis datos si no los tienes completos ya",
                "Otro": ""
            }
            mensaje_intencion = mensajes_por_intencion.get(intencion, "")

            datos["mensaje_intencion"] = mensaje_intencion,
            datos["intencion"] = intencion
            return {"status": 200, "datos": datos}
        except Exception as e:
            return manejo_errores(self.revisar_intencion_usuario.__qualname__, 500, error_base=e)

    def revisar_datos_mensaje(
            self, 
            historial: list[Dict[str,str]], 
            funciones, 
            id_usuario: str, 
            datos_usuario: Dict[CamposUsuario, Any]
        ) -> Dict[str,Any]:

        try:
            chat:list[Dict[str,str]] = []
            historial = [item for item in historial if 'tool_call_id' not in item and 'annotations' not in item]
            if len(historial) >= 3:
                chat.append(historial[-3])
                chat.append(historial[-2])
                chat.append(historial[-1])
            elif len(historial) == 2:
                chat.append(historial[-2])
                chat.append(historial[-1])
            elif len(historial) == 1:
                chat.append(historial[-1])
            else:
                return manejo_errores(self.revisar_datos_mensaje.__qualname__, 400, error_base="historial_vacio", usar_traceback=False)

            mensajes = self.transformar_conversacion(chat)
            esta_fuera_horario = datos_usuario.get(CamposUsuario.FUERA_HORARIO, False)

            tipo_usuario = funciones_negocio.obtener_tipo_usuario(datos_usuario)
            prompt_ejemplo = self.obtener_prompt_perfilacion(tipo_usuario, esta_fuera_horario)

            prompt_intervencion = PROMPTS["revision_mensajes"]["revisar_datos_entregados"].format(prompt_ejemplo, mensajes)
            chat_prompt = modelos_ia.llm.append_system_chat([], prompt_intervencion)
            respuesta_modelo = modelos_ia.llm.llamar(chat_prompt,funciones,False,id_usuario,0.0)
            if respuesta_modelo["status"] != 200:
                return respuesta_modelo

            match = re.search(r"```json\s*(\{.*?\})\s*```", respuesta_modelo["message"], re.DOTALL)
            datos:Dict[str,Any] = {}
            if match:
                bloque_json = match.group(1)
                try:
                    datos = json.loads(bloque_json)
                except Exception as e:
                    print("Error al parsear JSON:", e)
            else:
                try:
                    datos = json.loads(respuesta_modelo["message"])
                except Exception as e:
                    print("Error al parsear JSON:", e)

            errores = ""
            resultado_gestion_usuario = None
            if esta_fuera_horario:
                resultado_gestion_usuario = self.gestionar_fuera_horario(datos_usuario, datos)
            elif any(value is not None for value in datos.values()):
                if tipo_usuario == TipoUsuario.NUEVO_LEAD:
                    resultado_gestion_usuario = self.gestionar_nuevo_lead(datos_usuario, datos)
                elif tipo_usuario == TipoUsuario.LEAD:
                    resultado_gestion_usuario = self.gestionar_lead(datos_usuario, datos)
                elif tipo_usuario == TipoUsuario.CONTACTO:
                    resultado_gestion_usuario = self.gestionar_contacto(datos_usuario, datos)
                else:
                    self.identificacion_clientes(datos_usuario, datos)

            if resultado_gestion_usuario:
                if resultado_gestion_usuario.status != HTTPStatus.OK:
                    errores = resultado_gestion_usuario.error
                                    
                respuesta_usuario = gestor_usuario.leer_usuario(id_usuario)
                if respuesta_usuario["status"] != 200:
                    return respuesta_usuario
                
                datos_usuario = respuesta_usuario["datos"]["datos_usuario"]
            
            datos = {
                "datos_usuario": datos_usuario,
                "errores": errores
            }
            return {"status": 200, "datos": datos}
        except Exception as e:
            return manejo_errores(self.revisar_datos_mensaje.__qualname__, 500, error_base=e)

    def mensaje_final(
            self, 
            historial: list[Dict[str,str]], 
            respuesta_modelo: Dict[str,Any], 
            datos_usuario: Dict[CamposUsuario, Any], 
            datos_faltantes: list[str],
            aplicar_logica_datos: bool = True
        ) -> Dict[str,Any]:

        try:
            mensaje:str = respuesta_modelo["message"]
            chat: list[Dict[str,str]] = []
            historial = [item for item in historial if 'tool_call_id' not in item and 'annotations' not in item]
            chat.extend(historial)
            chat.append({    
                'role': "assistant-revision",
                'content': mensaje
            })
            print(mensaje)

            debe_saludar = len(historial) < 4
            regla_basada_datos_usuario = ""
            regla_basada_datos_faltantes = ""
            nombre = datos_usuario.get(CamposUsuario.PRIMER_NOMBRE, datos_usuario.get(CamposUsuario.NOMBRE))
            
            if(respuesta_modelo.get("datos_escalar",{}).get("activo")):
                prompt = "Debes decir que vas a transferir la conversación con un asesor de forma entusiasta, amable, con emojis. No debes saludar, solo indicar que vas a realizar la transferencia"
                
            elif(respuesta_modelo.get("datos_escalar",{}).get("terminar_conversacion") or not aplicar_logica_datos):
                mensajes = self.transformar_conversacion(chat)
                prompt = PROMPTS["revision_mensajes"]["revisar_salida_terminar"].format(
                    self.saludo + self.saludo_ejemplo.format(f" {nombre}" if nombre else "") if debe_saludar else "",
                    mensajes
                )
            else:
                if nombre:
                    regla_basada_datos_usuario += f"Debes utilizar el nombre del cliente cada 2 mensajes. el nombre es {nombre}"

                if (len(datos_faltantes) > 0):
                    if(CamposUsuario.TERRITORIO in datos_faltantes and not CamposUsuario.DOCUMENTO_IDENTIFICACION in datos_faltantes):
                        regla_basada_datos_faltantes =  "Debes preguntar en este momento por el territorio sobre cualquier otra pregunta"
                    else:
                        if(CamposUsuario.NOMBRE in datos_faltantes):
                            regla_basada_datos_faltantes += "Se debe priorizar preguntar primero el nombre y después de apellido"
                        else: 
                            regla_basada_datos_faltantes = (f"Debes solicitar el dato {datos_faltantes[0]}")
                else:
                    regla_basada_datos_faltantes = (f"Debes preguntarle al cliente si desea que transfieras la conversación a un asesor, si en el mensaje a revisar no se menciona nada de transferencia")

                fuera_horario = datos_usuario.get(CamposUsuario.FUERA_HORARIO)
                mensajes = self.transformar_conversacion(chat)
                prompt = PROMPTS["revision_mensajes"]["revisar_salida"].format(
                    regla_basada_datos_usuario,
                    regla_basada_datos_faltantes,
                    self.saludo if debe_saludar else "",
                    datos_faltantes,
                    self.saludo_ejemplo.format(f" {nombre}" if nombre else "") if debe_saludar else "",
                    self.obtener_prompt_fuera_horario(datos_usuario[CamposUsuario.ES_NACIONAL]) if fuera_horario else "",
                    mensajes
                )

            chat_prompt = modelos_ia.llm.append_system_chat([], prompt)
            respuesta_modelo = modelos_ia.llm.llamar(chat_prompt,temperature=0.1)
            if respuesta_modelo["status"] != 200:
                return respuesta_modelo

            datos = {
                "mensaje": respuesta_modelo["message"]
            }
            return {"status": 200, "datos": datos}
        except Exception as e:
            return manejo_errores(self.mensaje_final.__qualname__, 500, error_base=e)

    def transformar_conversacion(self, conversacion: list[Dict[str,str]]):
        conversacion_transformada:list[str] = []
        for mensaje in conversacion:
            if mensaje["role"] == "user":
                conversacion_transformada.append(f"Usuario: {mensaje['content']}")
            elif mensaje["role"] == "assistant":
                conversacion_transformada.append(f"Asesor: {mensaje['content']}")
            elif mensaje["role"] == "assistant-revision":
                conversacion_transformada.append(f"Respuesta a revisar: {mensaje['content']}")
        return "\n".join(conversacion_transformada)

    def validar_links(self, texto: str) -> dict:
        """
        Valida un link entregado

        Args:
            texto (str): El texto que contiene las URLs o enlaces a validar.

        Returns:
            dict: status con el codigo, 200 si todos los links son validos, 500 si no

        """
        def es_valido(link: str) -> bool:
            """
            Valida un link entregado

            Args:
                link (str): El enlace para validar

            Returns:
                bool: `True` si el link si es valido, `False` si no lo es

            """
            try:
                if "http" not in link:
                    link = "http://" + link
                link = link.replace(").", "").replace("'", "").replace(
                    '"', "").replace(">", "").replace("<", "").rstrip(".")
                if "youtu" in link:
                    respuesta = requests.get(link, verify=False)
                    if "og:title" in respuesta.text or "embeddedPlayerOverlayVideoDetailsExpandedRenderer" in respuesta.text:
                        pass
                    else:
                        return False
                else:
                    respuesta = requests.get(link, verify=False)
                    if not respuesta.ok:
                        return False
            except Exception as e:
                return False
            return True
        try:
            exprecion_url = r'(https?://[^\s()<>]+(?:\([^\s()<>]*\))?|(www\.[^\s()<>]+(?:\([^\s()<>]*\))?)|[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?)'
            urls_crudas = re.findall(exprecion_url, texto)
            links = [url[0] if isinstance(
                url, tuple) else url for url in urls_crudas]

            if links == []:
                return {"status": 200}

            resultados = []
            threads = []

            for link in links:
                thread = threading.Thread(
                    target=lambda l: resultados.append(es_valido(l)), args=(link,))
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            if not all(resultados):
                return {"status": 500}
            return {"status": 200}
        except Exception as e:
            return manejo_errores(self.validar_links.__qualname__, 500, error_base=e, usar_traceback=False)

    def no_debe_esperar_mensajes(self, mensaje_asistente: str) -> dict:
        """
        Evalúa si se debe esperar a más mensajes basándose en la respuesta del asistente.

        Args:
            mensaje_asistente (str): El mensaje proporcionado por el asistente para evaluar.

        Returns:
            dict: Un diccionario que contiene el status de la evaluación:
                - 200 si no se debe esperar más mensajes.
                - 500 si se debe esperar más mensajes o si ocurre un error.

        """
        prompt_espera = PROMPTS["revision_mensajes"]["debe_esperar_mensajes"]
        respuesta_modelo = modelos_ia.llm.manejar_chat(
            prompt_espera, user_message=mensaje_asistente)
        if respuesta_modelo["status"] != 200:
            return respuesta_modelo

        if "yes" in respuesta_modelo["message"].strip().lower():
            return {"status": 500}
        else:
            return {"status": 200}

    def escalar_conversacion(
            self, 
            mensaje_asistente: str, 
            id_cola: Optional[str] = ""
        ) -> dict:
        """
        Evalúa si se debe escalar la converscion

        Args:
            mensaje_asistente (str): El mensaje proporcionado por el asistente para evaluar.

        Returns:
            dict: Un diccionario que contiene el status de la evaluación:
                - 200 si debe escalar
                - 500 si no debe
                unos datos de escalamiento

        """
        try:
            prompt_escalar = PROMPTS["revision_mensajes"]["escalar"]
            respuesta_modelo = modelos_ia.llm.manejar_chat(
                prompt_escalar, user_message=mensaje_asistente)
            if respuesta_modelo["status"] != 200:
                return respuesta_modelo

            respuesta_validacion = evaluador(eliminador_texto(
                respuesta_modelo["message"], True),True)
            
            activo = False
            terminar = False
            if len(respuesta_validacion) > 0 and respuesta_validacion[0] == "Terminar":
                terminar = True
                respuesta_validacion[0] = ""
            elif len(respuesta_validacion) > 0  and respuesta_validacion[0]:
                activo = True
            elif len(respuesta_validacion) > 1 and respuesta_validacion[1] and id_cola != "" and id_cola != None:
                activo = True
                respuesta_validacion[0] = id_cola
            elif len(respuesta_validacion) == 0:
                 respuesta_validacion = [""]

            datos_escalar = {"activo": activo,
                             "contexto": {"BLVTeam": respuesta_validacion[0]},
                             "terminar_conversacion": terminar}

            return {"status": 200, "datos": datos_escalar}
        except Exception as e:
            return manejo_errores(self.escalar_conversacion.__qualname__, 500, error_base=e, usar_traceback=False)

    def escalar_conversacion_directamente(self, cola_escalamiento: ColaEscalamiento = None, id_cola: str = None):
        if(not id_cola):
            if cola_escalamiento == ColaEscalamiento.BOT_COPILOT_STUDIO:
                id_cola = self.id_cola_bot_copilot_studio
            elif cola_escalamiento == ColaEscalamiento.BOT_IA_INTERMEDIA:
                id_cola = self.id_cola_bot_ia_intermedia

        datos_escalar = {
            "activo": True,
            "contexto": {"BLVTeam": id_cola}
        }

        return {"status": 200, "datos": datos_escalar}

    def obtener_prompt_perfilacion(
            self, 
            tipo_usuario: TipoUsuario,
            esta_fuera_horario: bool
        ) -> str:
        if esta_fuera_horario:
            tz = pytz.timezone('America/Bogota') 
            fecha = datetime.now(tz)
            fecha_actual = fecha.strftime('%Y-%m-%d %H:%M:%S')
            dia_semana = fecha.strftime('%A')
            return PROMPTS["datos"]["fuera_horario"].replace("{fecha_actual}", fecha_actual).replace("{dia_semana}", dia_semana)
        elif tipo_usuario == TipoUsuario.NUEVO_LEAD:
            return PROMPTS["datos"]["nuevo_lead"].replace("{catalogos}", PROMPTS["bot_comercial"]["catalogos"])
        elif tipo_usuario == TipoUsuario.LEAD:
            return PROMPTS["datos"]["lead"].replace("{catalogos}", PROMPTS["bot_comercial"]["catalogos"])
        elif tipo_usuario == TipoUsuario.CONTACTO:
            return PROMPTS["datos"]["contacto"]
        elif tipo_usuario == TipoUsuario.SIN_IDENTIFICAR:
            return PROMPTS["datos"]["identificar"]

    def identificacion_clientes(
            self, 
            datos_usuario: Dict[CamposUsuario, Any], 
            datos: Dict[str, Any]
        ):
        id_usuario_direct_line:str = datos_usuario.get(CamposUsuario.ID_USUARIO_DIRECT_LINE) 
        documento = datos.get(CamposUsuario.DOCUMENTO_IDENTIFICACION)
        if(documento):
            id_conversacion:str = datos_usuario.get(CamposUsuario.ID_CONVERSACION) 
            canal:str = datos_usuario.get(CamposUsuario.CANAL)
            dataverse_service.buscar_clientes_por_numero_identificacion(documento, id_conversacion, canal, id_usuario_direct_line)

        if(datos.get(CamposUsuario.ES_NACIONAL) != None):
            dataverse_service.actualizar_territorio(datos.get(CamposUsuario.ES_NACIONAL), id_usuario_direct_line)

    def gestionar_contacto(
            self, 
            datos_usuario: Dict[CamposUsuario, Any], 
            datos: Dict[str, Any]
        ):
        id_cliente:str = datos_usuario.get(CamposUsuario.ID_CLIENTE)
        id_usuario_direct_line:str = datos_usuario.get(CamposUsuario.ID_USUARIO_DIRECT_LINE)
        email = datos.get(CamposUsuario.EMAIL_CLIENTE)
        ingresos_mensuales = datos.get(CamposUsuario.INGRESOS_MENSUALES)
        es_nacional:Optional[bool] = cast(Optional[bool], datos.get(CamposUsuario.ES_NACIONAL))

        resultado = ResultadoOperacion.exitoso()
        resultado_territorio = ResultadoOperacion.exitoso()
        if (es_nacional != None):
            resultado_territorio = dataverse_service.actualizar_territorio(
                es_nacional, 
                id_usuario_direct_line, 
                TipoCliente.CONTACTO, 
                datos_usuario.get(CamposUsuario.ID_CLIENTE)
            )

        if(email
           or ingresos_mensuales != None):
            resultado = dataverse_service.actualizar_datos_contacto(
                id_cliente,
                id_usuario_direct_line, 
                email, 
                ingresos_mensuales
            )

        if resultado_territorio.status != HTTPStatus.OK:
            return resultado_territorio
        
        return resultado

    def gestionar_fuera_horario(
            self, 
            datos_usuario: Dict[CamposUsuario, Any], 
            datos: Dict[str, Any]
        ):
        id_usuario_direct_line:str = datos_usuario.get(CamposUsuario.ID_USUARIO_DIRECT_LINE)
        fecha = datos.get(CamposUsuario.FECHA_CONTACTAR)
        hora = datos.get(CamposUsuario.HORA_CONTACTAR)
        actualizar_datos = False
        datos_usuario_actualizados: Dict[CamposUsuario,Any] = {}
        if fecha:
            actualizar_datos = True
            datos_usuario_actualizados[CamposUsuario.FECHA_CONTACTAR] = fecha
        else:
            fecha = datos_usuario.get(CamposUsuario.FECHA_CONTACTAR)
        
        if hora:
            actualizar_datos = True
            datos_usuario_actualizados[CamposUsuario.HORA_CONTACTAR] = hora
        else:
            hora = datos_usuario.get(CamposUsuario.HORA_CONTACTAR)

        if(actualizar_datos):
            gestor_usuario.actualizar_datos_usuario(id_usuario_direct_line,datos_usuario_actualizados)

        if(not hora):
            return ResultadoOperacion.error(HTTPStatus.BAD_REQUEST, "debes indicar una hora para contactarte")
        
        if(not fecha):
            return ResultadoOperacion.error(HTTPStatus.BAD_REQUEST, "debes indicar una fecha para contactarte")

        fecha = datetime.strptime(fecha, "%Y-%m-%d").date()
        hora = datetime.strptime(hora, "%H:%M:%S").time()

        resultado = dataverse_service.actualizar_datos_para_contactar(
            id_usuario_direct_line, 
            fecha,
            hora
        )
        
        if resultado.status == HTTPStatus.OK:
            datos_usuario_actualizados[CamposUsuario.CONTACTO_AGENDADO] = True
            gestor_usuario.actualizar_datos_usuario(id_usuario_direct_line,datos_usuario_actualizados)

        return resultado

    def gestionar_lead(
            self, 
            datos_usuario: Dict[CamposUsuario, Any], 
            datos: Dict[str, Any]
        ):
        id_cliente:str = datos_usuario.get(CamposUsuario.ID_CLIENTE)
        id_usuario_direct_line:str = datos_usuario.get(CamposUsuario.ID_USUARIO_DIRECT_LINE)
        email = datos.get(CamposUsuario.EMAIL_CLIENTE)
        ingresos_mensuales = datos.get(CamposUsuario.INGRESOS_MENSUALES)
        tiempo_compra = datos.get(CamposUsuario.TIEMPO_COMPRA)
        actividad_economica = datos.get(CamposUsuario.ACTIVIDAD_ECONOMICA)
        es_nacional = datos.get(CamposUsuario.ES_NACIONAL)
        proyecto_interes = datos.get(CamposUsuario.PROYECTO_INTERES)
        
        resultado = ResultadoOperacion.exitoso()
        resultado_territorio = ResultadoOperacion.exitoso()
        if (es_nacional != None):
            resultado_territorio = dataverse_service.actualizar_territorio(
                es_nacional, 
                id_usuario_direct_line, 
                TipoCliente.LEAD, 
                id_cliente
            )
        
        if(email 
           or ingresos_mensuales != None
           or actividad_economica != None
           or proyecto_interes
           or tiempo_compra != None):
            resultado = dataverse_service.actualizar_datos_lead(
                id_cliente,
                id_usuario_direct_line, 
                email, 
                ingresos_mensuales, 
                actividad_economica,
                proyecto_interes,
                tiempo_compra
            )

        if resultado_territorio.status != HTTPStatus.OK:
            return resultado_territorio
        
        return resultado

    def gestionar_nuevo_lead(
            self, 
            datos_usuario: Dict[CamposUsuario, Any], 
            datos: Dict[str, Any]
        ):
        id_cliente = datos_usuario.get(CamposUsuario.ID_CLIENTE)
        id_usuario_direct_line:str = datos_usuario.get(CamposUsuario.ID_USUARIO_DIRECT_LINE)
        
        canal = datos_usuario.get(CamposUsuario.CANAL)
        id_conversacion = datos_usuario.get(CamposUsuario.ID_CONVERSACION)

        nombre = datos.get(CamposUsuario.NOMBRE)
        apellido = datos.get(CamposUsuario.APELLIDO)
        documento = datos_usuario.get(CamposUsuario.DOCUMENTO_IDENTIFICACION)
        celular = datos_usuario.get(CamposUsuario.CELULAR)
        email = datos.get(CamposUsuario.EMAIL_CLIENTE)

        tipo_documento = datos.get(CamposUsuario.TIPO_DOCUMENTO_IDENTIFICACION)
        ingresos_mensuales = datos.get(CamposUsuario.INGRESOS_MENSUALES)
        tiempo_compra = datos.get(CamposUsuario.TIEMPO_COMPRA)
        actividad_economica = datos.get(CamposUsuario.ACTIVIDAD_ECONOMICA)
        proyecto_interes = datos.get(CamposUsuario.PROYECTO_INTERES)
        
        es_nacional = datos.get(CamposUsuario.ES_NACIONAL)

        resultado = ResultadoOperacion.exitoso()
        resultado_territorio = ResultadoOperacion.exitoso()
        if(not id_cliente):
            if(es_nacional != None):
                resultado_territorio = dataverse_service.actualizar_territorio(
                    es_nacional, 
                    id_usuario_direct_line
                )
            
            if(nombre
               or apellido
               or email):
                resultado = dataverse_service.guardado_temporal_datos_nuevo_lead(
                    canal, 
                    id_conversacion,
                    id_usuario_direct_line, 
                    nombre,
                    apellido, 
                    celular,
                    email,
                    documento
                )
        else:
            if(es_nacional != None):
                resultado_territorio = dataverse_service.actualizar_territorio(
                    es_nacional, 
                    id_usuario_direct_line,
                    TipoCliente.LEAD,
                    id_cliente
                )

            if (tipo_documento != None
                or email
                or ingresos_mensuales != None
                or proyecto_interes != None
                or tiempo_compra != None):
                resultado = dataverse_service.actualizar_datos_nuevo_lead(
                    id_cliente,
                    id_usuario_direct_line, 
                    tipo_documento,
                    documento,
                    celular,
                    email, 
                    ingresos_mensuales, 
                    actividad_economica,
                    proyecto_interes,
                    tiempo_compra,
                )

        if resultado_territorio.status != HTTPStatus.OK:
            return resultado_territorio
        
        return resultado
    
    def obtener_prompt_fuera_horario(
            self,
            es_nacional: bool
        ) -> str:
        return PROMPTS["bot_comercial"]["fuera_horario_salida_nacional"] if es_nacional else PROMPTS["bot_comercial"]["fuera_horario_salida_internacional"]

procesar_mensajes = ProcesarMensajes()
