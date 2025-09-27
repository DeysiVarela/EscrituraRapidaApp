import os
import re
import threading
from typing import Dict, List
import requests
import random
import time
import json
from copy import deepcopy

from codigo.procesos_internos.gestor_usuario import gestor_usuario
from codigo.variables import LISTA_MENSAJES, PROMPTS
from codigo.funciones_auxiliares import eliminador_texto, evaluador, manejo_errores
from models.enums import CamposUsuario


class ModelosIa():
    """
    ModelosIa es una clase que encapsula diferentes modelos de inteligencia artificial,
    específicamente GPT, Whisper y SpeechAzure. Estos modelos se pueden usar paraD distintas
    tareas como generación de texto, transcripción del habla y síntesis de voz.

    Atributos:
        llm (GPT): Instancia del modelo GPT para generación de texto.
        asr (Whisper): Instancia del modelo Whisper para transcripción de audio.
        tts (SpeechAzure): Instancia del modelo SpeechAzure para síntesis de voz.
    """

    def __init__(self):
        self.llm = GPT()
        self.asr = Whisper()
        self.tts = OpenAITts()


class OpenAITts:
    def __init__(self):
        self.url = os.environ["OPENAI_TTS_URL"]
        self.api_key = os.environ["OPENAI_TTS_APY_KEY"]
        self.nombre = os.environ["OPENAI_TTS_NOMBRE"]
        self.version_api = os.environ["OPENAI_TTS_VERSION_API"]
        self.instruccion = "Habla en un tono alegre y positivo."

    def llamar(self, mensaje: str = "", ruta_audio_salida: str = "", voz: str = "nova") -> dict:
        """
        Genera un archivo de audio usando el servicio TTS de OpenAI y lo guarda en la ruta especificada.
        Args:
            mensaje (str): El mensaje de texto a convertir en audio.
            ruta_audio_salida (str): La ruta donde se guardará el archivo de audio generado.
            voz (str): El nombre de la voz a utilizar para la síntesis de voz. Por defecto es 'nova'.
            NOTA: Las voces disponibles son:
                - Femeninas: nova, shimmer, alloy
                - Masculinas: echo, onyx, fable

        Returns:
            dict: Un diccionario con el estado de la solicitud y el mensaje de respuesta.
                  - Si la generación de audio es exitosa, retorna {'status': 200, 'message': 'Audio generado correctamente'}.
                  - En caso de error, retorna un diccionario con el detalle del error.
        """
        try:
            url = f"{self.url}/openai/deployments/{self.nombre}/audio/speech?api-version={self.version_api}"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            cuerpo = {
                "input": mensaje,
                "instructions": self.instruccion,
                "voice": voz
            }
            intento = 0
            maximo_intentos = 4
            while True:
                try:
                    respuesta_tts = requests.post(
                        url, headers=headers, data=json.dumps(cuerpo))
                    if respuesta_tts.status_code == 200:
                        with open(ruta_audio_salida, "wb") as file:
                            file.write(respuesta_tts.content)
                        return {"status": 200, "message": "Audio generado correctamente"}
                    elif intento < maximo_intentos and respuesta_tts.status_code == 429:
                        intento += 1
                        time.sleep(60)
                        continue
                    else:
                        return manejo_errores(self.llamar.__qualname__, respuesta_tts.status_code,
                                              error_base="se llegaron al maximo de intentos y usos de whisper",
                                              usar_traceback=False)
                except Exception as e:
                    return manejo_errores(self.llamar.__qualname__, 500, error_base=e)
        except Exception as e:
            return manejo_errores(self.llamar.__qualname__, 500, error_base=e)


class SpeechAzure():
    def __init__(self):
        self.api_key = os.environ["SPEECH_KEY_AZURE"]
        self.service_region = "eastus2"
        self.voces = {
            "fe": {
                "es": "es-MX-DaliaNeural",
                "en": "en-US-MonicaNeural"
            }
        }

    def llamar(self, mensaje: str = "", ruta_audio_salida: str = "", voz: str = "es", genero="fe") -> dict:
        """
        Implementación placeholder para la función llamar_rest utilizando Python y la biblioteca requests.
        Realiza una solicitud POST a Azure Cognitive Services para la síntesis de voz.

        Args:
            None

        Returns:
            dict: Un diccionario con el estado de la solicitud y el mensaje de respuesta.
                    En caso de éxito, el mensaje indica que el audio se generó correctamente.
                    En caso de error, el mensaje contiene el detalle del error.
        """
        try:
            url = f"https://{self.service_region}.tts.speech.microsoft.com/cognitiveservices/v1"
            headers = {
                "Ocp-Apim-Subscription-Key": self.api_key,
                "Content-Type": "application/ssml+xml",
                "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3",
                "User-Agent": "curl"
            }
            data = f"""
            <speak version='1.0' xml:lang='en-US'>
                <voice xml:lang='en-US' xml:gender='Female' name='{self.voces[genero][voz]}'>
                    {mensaje}
                </voice>
            </speak>
            """
            response = requests.post(url, headers=headers, data=data)

            if response.status_code == 200:
                with open(ruta_audio_salida, "wb") as file:
                    file.write(response.content)
                return {"status": 200, "message": "Audio generado correctamente"}
            else:
                return manejo_errores(self.llamar.__qualname__, response, response.status_code,
                                      error_base=response.text, usar_traceback=False)
        except Exception as e:
            return manejo_errores(self.llamar.__qualname__, 500, error_base=e)


class Whisper():
    def __init__(self):
        self.api_key = os.environ["WHISPER_OPEN_AI_API_KEY_AZURE"]
        self.url = os.environ["WHISPER_URL"]
        self.nombre = os.environ["WHISPER_NAME"]
        self.version_api = "2024-06-01"

    def llamar(self, audio, audio_en_binario: bool = False, extencion: str = "mp3") -> dict:
        """
        Transcribe audio utilizando el modelo Whisper de OpenAI.

        Args:
            audio (str/bytes): La ruta del archivo de audio o el contenido binario del audio.
            audio_en_binario (bool): Indicador de si el audio se proporciona en binario.
                                      Si es False, se asume que 'audio' es una ruta de archivo.
            extencion (str): La extencion del archivo
        Returns:
            dict: Un diccionario con el estado de la solicitud y el mensaje de respuesta.
                  En caso de éxito, el mensaje contiene la transcripción del audio.
                  En caso de error, el mensaje contiene el detalle del error.

        Ejemplo de uso:
            >>> whisper = Whisper()
            >>> respuesta = whisper.llamar("ruta/al/audio.mp3")
            >>> respuesta = whisper.llamar(contenido_audio_binario, audio_en_binario=True)
        """
        try:
            url = f"{self.url}/openai/deployments/{self.nombre}/audio/transcriptions?api-version={self.version_api}"
            headers = {
                "api-key": self.api_key,
            }
            if audio_en_binario:
                archivo_audio_content = audio
                # name = uuid.uuid4()
                # with open(f"{name}.{extencion}","wb") as file:
                #     file.write(audio)
                # with open(f"{name}.{extencion}","rb") as file:
                #     archivo_audio_content = file.read()

            else:
                with open(audio, "rb") as archivo_audio:
                    archivo_audio_content = archivo_audio.read()
            files = {
                "file": (f"audio.{extencion}", archivo_audio_content),
            }
            intento = 0
            maximo_intentos = 5
            while True:
                try:
                    respuesta_whisper = requests.post(
                        url, headers=headers, files=files)
                    if respuesta_whisper.status_code == 200:
                        respuesta = {"status": 200, "message": respuesta_whisper.json()[
                            "text"]}
                        return respuesta
                    elif intento < maximo_intentos and respuesta_whisper.status_code == 429:
                        intento += 1
                        time.sleep(70)
                        continue
                    else:
                        return manejo_errores(self.llamar.__qualname__, respuesta_whisper.status_code,
                                              error_base="se llegaron al maximo de intentos y usos de whisper",
                                              usar_traceback=False)
                except Exception as e:
                    return manejo_errores(self.llamar.__qualname__, 500, error_base=e)
        except Exception as e:
            return manejo_errores(self.llamar.__qualname__, 500, error_base=e)


class GPT():
    def __init__(self):
        self.api_key = os.environ["GPT_OPEN_AI_API_KEY_AZURE"]
        self.url = os.environ["GPT_URL"]
        self.headers = {"api-key": self.api_key,
                        "Content-Type": "application/json"}
        self.cuerpo_consulta = {
            "temperature": 0.5,
            "top_p": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "tool_choice": "auto",
            "stop": None
        }

    def append_user_chat(self, chat: list, data) -> list:
        """
        Agrega un mensaje de usuario al chat.

        Args:
            chat (list): La conversación existente.
            data (str): El mensaje del usuario.

        Returns:
            list: El chat actualizado con el mensaje de usuario.

        Example:
            >>> chat = []
            >>> chat = append_user_chat(chat, "Hola, ¿puedes ayudarme?")
        """
        chat.append({"role": "user", "content": data})
        return chat

    def append_user_image_chat(self, chat: list, user_message: str, images64: list) -> list:
        """
        Agrega un mensaje de usuario al chat junto con imágenes en base64.

        Args:
            chat (list): La conversación existente.
            user_message (str): El mensaje del usuario.
            images64 (list): Lista de imágenes en base64.

        Returns:
            list: El chat actualizado con el mensaje de usuario y las imágenes.

        Example:
            >>> chat = []
            >>> chat = append_user_image_chat(chat, "Hola, ¿puedes ayudarme?", ["imagen64"])
        """
        content = [
            {
                "type": "text",
                        "text": user_message
            }
        ]
        for image64 in images64:
            content.append({"type": "image_url",
                            "image_url": {
                                "url": image64
                            }})
        chat.append({"role": "user", "content": content})
        return chat

    def append_assistant_chat(self, chat: List[Dict[str, str]], data: str) -> list[Dict[str,str]]:
        """
        Agrega un mensaje del asistente al chat.

        Args:
            chat (list): La conversación existente.
            data (str): El mensaje del asistente.

        Returns:
            list: El chat actualizado con el mensaje del asistente.

        Example:
            >>> chat = []
            >>> chat = append_assistant_chat(chat, "Claro, estoy aquí para ayudarte.")
        """
        chat.append({"role": "assistant", "content": data})
        return chat

    def append_system_chat(self, chat: List[Dict[str, str]], data: str) -> List[Dict[str, str]]:
        """
        Agrega un mensaje del sistema al chat.

        Args:
            chat (list): La conversación existente.
            data (str): El mensaje del sistema.

        Returns:
            list: El chat actualizado con el mensaje del sistema.

        Example:
            >>> chat = []
            >>> chat = append_system_chat(chat, "Eres un ayudante.")
        """
        chat.append({"role": "system", "content": data})
        return chat

    def mapear_a_nuevo_formato(self, json_original):
        nuevo_formato = []

        for funcion in json_original:
            nueva_funcion = {
                "type": "function",
                "function": {
                    "name": funcion["nombre_funcion"],
                    "description": funcion["descripcion"],
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }

            for nombre_argumento, detalles_argumento in funcion["argumentos"].items():
                nueva_funcion["function"]["parameters"]["properties"][nombre_argumento] = {
                    "type": detalles_argumento["tipo"],
                    "description": detalles_argumento["descripcion"]
                }
                if detalles_argumento["es_obligatorio"]:
                    nueva_funcion["function"]["parameters"]["required"].append(
                        nombre_argumento)

            nuevo_formato.append(nueva_funcion)

        return nuevo_formato

    def llamar(self, chat: list, funciones: list = [], validar_mensaje = False, id_usuario: str = None, temperature = None):
        """
        Genera una respuesta utilizando el modelo GPT de OpenAI y funciones.

        Args:
            chat (list): La conversación con mensajes de usuario, asistente y sistema.
            funciones (list): Las funciones que se pueden llamar en formato (Opcional)
                [{"nombre_funcion" : "suma", "objeto_funcion": "objeto_funcion", "descripcion": "","argumentos":{}}]

        Returns:
            str: La respuesta generada por el modelo.

        Example:
            >>> chat = [{"role": "user", "content": "Cuéntame sobre la diabetes."}]
            >>> funciones = [{"nombre_funcion" : "suma", "objeto_funcion": "objeto_funcion", "descripcion": "","argumentos":{}}]
            >>> response = GPT.llamar(chat)
            >>> response = GPT.llamar(chat,funciones)
        """
        try:
            funciones_a_persistir = [
                "buscar_clientes_por_numero_identificacion",
                "disponibilidad_agente"
            ]
            guardar_respuesta_funcion_log = [
                "buscar_clientes_por_numero_identificacion",
                "disponibilidad_agente",
                "actualizar_territorio",
                "actualizar_datos_lead",
                "actualizar_datos_contacto"
            ]
            funciones_log = []
            datos_usuario = {}
            datos_escalar = {"activo":False}
            intentos = 0
            maximos_intentos = 3
            funciones_gpt = self.mapear_a_nuevo_formato(
                funciones) if funciones != [] else []
            diccionario_funciones = {funcion['nombre_funcion']: funcion['objeto_funcion']
                                     for funcion in funciones}

            while intentos < maximos_intentos:
                intentos += 1
                cuerpo_consulta = deepcopy(self.cuerpo_consulta)
                if temperature:
                    cuerpo_consulta["temperature"] = temperature
                cuerpo_consulta.update(
                    {"messages": chat, "tools": funciones_gpt})
                respaldo_chat = deepcopy(chat)
                debe_procesar_respuesta = True
                es_primer_llamado = True

                while debe_procesar_respuesta or es_primer_llamado:
                    respuesta = requests.post(
                        self.url, headers=self.headers, json=cuerpo_consulta)
                    es_primer_llamado = False

                    json_respuesta = respuesta.text
                    json_respuesta = respuesta.json()
                    if respuesta.status_code != 200:
                        manejo_errores(self.llamar.__qualname__,
                                       respuesta.status_code,
                                       False,
                                       json_respuesta["error"]["message"],
                                       False)
                        if json_respuesta["error"]["code"] == "context_length_exceeded":
                            return {"status": 400, "message": random.choice(LISTA_MENSAJES['MAXIMO_CONTENIDO'])}

                        elif (json_respuesta["error"]["code"] == "BadRequest" and
                              json_respuesta["error"]["message"] == "Too many images in request. Max is 50."):
                            return {"status": 400, "message": random.choice(LISTA_MENSAJES['MAXIMO_IMAGENES'])}

                        elif json_respuesta["error"]["code"] == "429":
                            time.sleep(70)
                            chat = deepcopy(respaldo_chat)
                            continue

                        elif json_respuesta["error"]["code"] == "content_filter":
                            return {"status": 400, "message": random.choice(LISTA_MENSAJES['CONTENIDO_FILTRADO'])}
                        else:
                            return {"status": 400, "message": random.choice(LISTA_MENSAJES['ERROR'])}
                        

                    funciones_necesarias = json_respuesta['choices'][0]['message'].get(
                        'tool_calls', [])

                    if funciones_necesarias != []:
                        chat.append(json_respuesta['choices'][0]['message'])

                        for funcion in funciones_necesarias:
                            nombre_funcion = funcion["function"]["name"]
                            id_funcion = funcion["id"]
                            if nombre_funcion in diccionario_funciones.keys():                                
                                argumentos_funcion = eval(
                                    funcion["function"]["arguments"])
                                respuesta_funcion = diccionario_funciones[nombre_funcion](
                                    **argumentos_funcion)
                                chat.append({
                                    "tool_call_id": id_funcion,
                                    "role": "tool",
                                    "name": nombre_funcion,
                                    "content": str(respuesta_funcion),
                                })

                                funciones_log.append({
                                    "function": nombre_funcion,
                                    "parameters": json.dumps(argumentos_funcion),
                                    "response": str(respuesta_funcion) if nombre_funcion in guardar_respuesta_funcion_log else None
                                })

                            else:
                                chat.append({
                                    "tool_call_id": id_funcion,
                                    "role": "tool",
                                    "name": nombre_funcion,
                                    "content": "No existe esta función. No inventes funciones.",
                                })

                        try:
                            if(id_usuario):
                                respuesta_usuario = gestor_usuario.leer_usuario(id_usuario)
                                if respuesta_usuario["status"] == 200:
                                    datos_usuario = respuesta_usuario["datos"]["datos_usuario"]
                                    datos_limpios = {
                                        k: v.replace('\xa0', ' ') if isinstance(v, str) else v
                                        for k, v in datos_usuario.items()
                                    }

                                    json_datos = json.dumps(datos_limpios, ensure_ascii=False)

                                    fin_tag = chat[0]["content"].find("</datos-cliente>")
                                    if fin_tag != -1:
                                        # Buscar hacia atrás el <datos-cliente> más cercano antes del cierre
                                        inicio_tag = chat[0]["content"].rfind("<datos-cliente>", 0, fin_tag)
                                        
                                        if inicio_tag != -1:
                                            bloque = chat[0]["content"][inicio_tag + 15: fin_tag]
                                            chat[0]["content"] = chat[0]["content"].replace(bloque,json_datos)
                        except:
                            pass
                                        
                        cuerpo_consulta.update({"messages": chat})                    
                    else:
                        debe_procesar_respuesta = False

                    # TODO: Hacer que el bot valide por si solo los links, y en caso de que no valide validarlo nosotros
                    if funciones_necesarias == [] and validar_mensaje: 
                        mensaje = json_respuesta['choices'][0]['message']['content']
                        links_validos = self.validar_links(mensaje)
                        if links_validos["status"] != 200:
                            debe_procesar_respuesta = True
                            self.append_system_chat(chat, "no es válido la URL que enviaste en el último mensaje")

                        no_debe_esperar = self.no_debe_esperar_mensajes(mensaje)
                        if no_debe_esperar["status"] != 200:
                            debe_procesar_respuesta = True
                            self.append_system_chat(chat, "Solo puedes enviar 1 mensaje, no puedes indicarle al usuario que debe esperar")

                        respuesta_escalar = self.escalar_conversacion(mensaje, id_usuario=id_usuario)
                        if respuesta_escalar["status"] != 200:
                            debe_procesar_respuesta = True
                            self.append_system_chat(chat, respuesta_escalar.get("datos",{}).get("error","error validando si se debe escalar"))
                            continue
                        
                        if respuesta_escalar["datos"]["activo"]:
                            id_cola = datos_usuario.get(CamposUsuario.ID_COLA, None)
                            if id_cola == None:
                                debe_procesar_respuesta = True
                                self.append_system_chat(chat, "Debes ejecutar la función disponibilidad_agente")
                            else: 
                                datos_escalar = respuesta_escalar["datos"]
                        else:
                            datos_escalar = respuesta_escalar["datos"]

                    respuestas_funciones = []
                    if len(chat) > len(respaldo_chat):
                        for elemento in chat[(len(respaldo_chat)):]:
                            if "name" in elemento and elemento["name"] in funciones_a_persistir:
                                respuestas_funciones.append({
                                    "role": "system",
                                    "fuction": elemento["name"],
                                    "content": elemento["content"]
                                })

                salida_gpt = {
                    "status": 200, 
                    "message": json_respuesta['choices'][0]['message']['content'] ,
                    "respuestas_funciones": respuestas_funciones,
                    "funciones_log": funciones_log,
                    "datos_escalar": datos_escalar
                    }
                return salida_gpt
            salida_gpt = {
                "status": 400, 
                "message": random.choice(LISTA_MENSAJES['ERROR']),
                "respuestas_funciones": []
                }
            return salida_gpt
        except Exception as e:
            return manejo_errores(self.llamar.__qualname__, 500, error_base=e)

    def manejar_chat(self, system_message: str = "", user_history: list = [], user_message: str = "", image: str = None) -> dict:
        """
        Maneja un chat que puede incluir un mensaje del sistema, un historial de mensajes del usuario,
        un nuevo mensaje del usuario y opcionalmente una imagen.
        Args:
            system_message (str): El mensaje del sistema.
            user_history (list, opcional): El historial de mensajes del usuario.
            user_message (str, opcional): El nuevo mensaje del usuario.
            image (str, opcional): La imagen en base64.

        Returns:
            dict: El diccionario con la respuesta o el error

        Example:
            >>> respuesta = manejar_chat("Eres un ayudante.", [], "Cuanto es 2 mas 2?")
            >>> respuesta = manejar_chat("Eres un ayudante.", ["Hola, ¿puedes ayudarme?"], "¿Cómo puedo hacer un depósito?")
            >>> respuesta = manejar_chat("Eres un ayudante.", ["Hola, ¿puedes ayudarme?"], "Que hay en la imagen?", image="imagen_base64")
            >>> print(respuesta)
        Out
            `{"status": 200, "message": respuesta}`
            `{"status": 500, "erro": error}`
        """
        try:
            chat = []
            chat = self.append_system_chat(chat, system_message)
            chat.extend(user_history)

            if image:
                chat = self.append_user_image_chat(chat, user_message, [image])
            else:
                chat = self.append_user_chat(chat, str(user_message))

            respuesta = self.llamar(chat)
            if respuesta["status"] == 200:
                respuesta = respuesta["message"]
            else:
                respuesta = random.choice(LISTA_MENSAJES['ERROR'])
            return {"status": 200, "message": respuesta}
        except Exception as e:
            return manejo_errores(self.manejar_chat.__qualname__, 500, error_base=e)

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

    def escalar_conversacion(self, mensaje_asistente: str, id_cola: str = "", id_usuario: str = "") -> dict:
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

            datos_escalar = {"activo": False,
                             "contexto": {"BLVTeam": ""},
                             "terminar_conversacion": False}
            
            if len(respuesta_validacion) > 0 and respuesta_validacion[0] == "Terminar":
                terminar = True
                respuesta_validacion[0] = ""
            elif len(respuesta_validacion) > 0  and respuesta_validacion[0]:
                activo = True
            elif len(respuesta_validacion) > 1 and respuesta_validacion[1] and id_cola:
                activo = True
                respuesta_validacion[0] = id_cola
            elif len(respuesta_validacion) > 1 and respuesta_validacion[1] and id_usuario:
                respuesta_usuario = gestor_usuario.leer_usuario(id_usuario)
                if respuesta_usuario["status"] != 200:
                    datos_escalar["error"] = "Error consultado los datos del usuario"
                    return {"status": 400, "datos": datos_escalar}
                
                datos_usuario = respuesta_usuario["datos"]["datos_usuario"]
                id_cola = datos_usuario.get(CamposUsuario.ID_COLA)
                if not id_cola:
                    datos_escalar["error"] = "No se conoce el ID de la cola a la cual se debe escalar, utiliza disponibilidad_agente"
                    return {"status": 400, "datos": datos_escalar}
                
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

modelos_ia = ModelosIa()
