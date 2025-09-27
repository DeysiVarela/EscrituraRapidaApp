from botbuilder.core import ActivityHandler, MessageFactory, TurnContext
from botbuilder.schema import ChannelAccount, Attachment
import json
from bs4 import BeautifulSoup, Comment
import time

from .utils import parseador_de_mensajes


class BasicBot(ActivityHandler):
    """
    Inicializa el BasicBot.

    Args:
        ruta_consulta (str): La ruta para donde se generan los mensajes del bot
    """

    def __init__(self, funcion_proyecto):
        self.funcion_consulta = funcion_proyecto

    async def on_message_activity(self, turn_context: TurnContext):
        """
        Maneja los mensajes entrantes de los usuarios y responde en consecuencia.
        Args:
            turn_context (TurnContext): El objeto de contexto para este turno.

        Returns:
            Activity: La respuesta del bot al mensaje del usuario.
        """
        cuerpo = {
            "mensajero": "bot_services",
            "mensaje": turn_context.activity.text,
            "id_usuario": turn_context.activity.channel_data["fromUserId"],
            "archivos": eval(turn_context.activity.channel_data.get("amsMetadata", "[]")),

        }

        if(cuerpo["id_usuario"] == "System"):
            return 
        
        respuesta_consulta = self.funcion_consulta(cuerpo)
        if (respuesta_consulta[1] == 400 and
            isinstance(respuesta_consulta[0], dict) and
            isinstance(respuesta_consulta[0].get("datos"), dict) and
            respuesta_consulta[0]["datos"].get("registro_asistente")):
            try:
                respuesta = await self.generar_actividad_mensaje(respuesta_consulta[0]["datos"]["registro_asistente"])
                return await turn_context.send_activity(respuesta)
            except Exception as e:
                respuesta_consulta[1] = 410
        
        if respuesta_consulta[1] != 200:
            respuesta = await self.generar_actividad_mensaje("Estoy teniendo problemas en este momento")
            return await turn_context.send_activity(respuesta)

        datos_consulta = respuesta_consulta[0]

        if datos_consulta["escalar"]["activo"]:
            return await self.escalar(turn_context, datos_consulta)

        lista_mensajes = parseador_de_mensajes(
            datos_consulta["registro_asistente"]["content"])


        espera_archivos = 2
        espera_texto = 1
        espera_defecto = 5
        contador_archivos = 0
        for mensaje in lista_mensajes:
            if mensaje[0] == "text":
                respuesta = await self.generar_actividad_mensaje(mensaje[1])
                if contador_archivos == 1:
                    time.sleep(espera_defecto)
                else:
                    time.sleep(contador_archivos*2 + espera_texto)
                contador_archivos = 0
            elif mensaje[0] == "application/pdf":
                nuevo_mensaje = f"BOT-PDF-URL: {mensaje[1]}"
                respuesta = await self.generar_actividad_mensaje(nuevo_mensaje)
                time.sleep(espera_archivos)
                contador_archivos += 1
            elif "video" in mensaje[0]:
                nuevo_mensaje = f"BOT-VIDEO-URL: {mensaje[1]}"
                respuesta = await self.generar_actividad_mensaje(nuevo_mensaje)
                if contador_archivos == 1:
                    time.sleep(espera_defecto)
                else:
                    time.sleep(contador_archivos*2 + espera_texto)
                contador_archivos = 0
            elif "image" in mensaje[0]:
                if len(mensaje) == 2:
                    respuesta = await self.generar_actividad_archivo(
                        mensaje[1], mensaje[0])
                else:
                    respuesta = await self.generar_actividad_archivo(
                        mensaje[1], mensaje[0], mensaje[2])
                contador_archivos += 1
                time.sleep(espera_archivos)
            else:
                pass
            await turn_context.send_activity(respuesta)

        terminar = datos_consulta.get("terminar",False)
        if (terminar):
            actividad_cierre = await self.generar_actividad_cierre_conversacion()
            respuesta = await turn_context.send_activity(actividad_cierre)

    async def escalar(self, turn_context: TurnContext, datos: dict):
        cuerpo = {
            "type": "Escalate",
            "context": datos["escalar"]["contexto"]
        }
        cuerpo_cadena = json.dumps(cuerpo)
        Actividad = MessageFactory.text("Se escaló desde el bot comercial")
        if not isinstance(Actividad.channel_data, dict):
            Actividad.channel_data = {"tags": cuerpo_cadena}
        else:
            Actividad.channel_data["tags"] = cuerpo_cadena

        mensaje_respuesta = await self.generar_actividad_mensaje(datos["registro_asistente"]["content"])
        return await turn_context.send_activities([mensaje_respuesta, Actividad])

    async def generar_actividad_cierre_conversacion(self):
        cuerpo = {
            "type": "EndConversation",
            "context": {}
        }
        cuerpo_cadena = json.dumps(cuerpo)
        actividad = MessageFactory.text("Se cierra la conversación")
        if not isinstance(actividad.channel_data, dict):
            actividad.channel_data = {"tags": cuerpo_cadena}
        else:
            actividad.channel_data["tags"] = cuerpo_cadena

        return actividad

    async def generar_actividad_mensaje(self, mensaje):
        actividad = MessageFactory.text(mensaje)
        if not isinstance(actividad.channel_data, dict):
            actividad.channel_data = {"deliveryMode": "bridged"}
        else:
            actividad.channel_data["deliveryMode"] = "bridged"

        return actividad

    async def generar_actividad_archivo(self, url, contenttype, texto_alternativo=None):
        file = Attachment(
            content_type=contenttype,
            content_url=url,
            name=url.split("/")[-1],
        )
        mensaje = f"BOT-ARCHIVO-URL: {url}"
        if texto_alternativo:
            mensaje += f" ; {texto_alternativo}"

        actividad = MessageFactory.attachment(file, mensaje)
        if not isinstance(actividad.channel_data, dict):
            actividad.channel_data = {"deliveryMode": "bridged"}
        else:
            actividad.channel_data["deliveryMode"] = "bridged"

        return actividad
