import os
from typing import Any, Dict
from flask import json
import requests

from codigo.funciones_auxiliares import manejo_errores
from codigo.procesos_internos.gestor_usuario import gestor_usuario
from codigo.conexiones_externas.dataverse_service import dataverse_service
from models.enums import CamposUsuario, Canal
from codigo.conexiones_externas.dataverse_service import dataverse_service

from codigo.funciones_auxiliares import manejo_errores,pdf_a_base64

class BotServices():

    def __init__(self):
        pass

    def recibir_datos(self, datos: dict) -> dict:
        """
        Recibe los datos que fueron enviados desde bot service y los mapea al formato manejado en este código.

        Args:
            datos (dict): Un diccionario que contiene la información enviada desde bot service.
        
        Returns:
            dict: Un diccionario que indica el estado de la operación y los datos mapeados.
              - "status" (int): Código de estado HTTP indicando el resultado de la operación (200 si es exitoso).
              - "datos"  (dict): Los datos recibidos mapeados al formato esperado por este código.
              - "error"  (str): El error en caso tal de existi

        """
        try:
            respuesta_usuario = gestor_usuario.existe_usuario(
                datos["id_usuario"])

            if respuesta_usuario["status"] != 200:
                return respuesta_usuario

            if not respuesta_usuario["existe"]:
                respuesta_usuario = gestor_usuario.crear_usuario(
                    datos["id_usuario"])
                if respuesta_usuario["status"] != 200:
                    return respuesta_usuario
                
            elif datos["mensaje"] and '"EventName":"omnichannelSetContext"' in datos["mensaje"]:
                gestor_usuario.eliminar_usuario(datos["id_usuario"])
                
            if datos["mensaje"] and '"EventName":"omnichannelSetContext"' in datos["mensaje"]:
                data = json.loads(datos["mensaje"])
                datos_usuario: Dict[CamposUsuario, Any] = {
                    CamposUsuario.ID_USUARIO_DIRECT_LINE: datos["id_usuario"],
                    CamposUsuario.ES_NACIONAL: None,
                    CamposUsuario.ESCALAR: False,
                    CamposUsuario.ES_NUEVO_LEAD: False,
                    CamposUsuario.BUSCAR_PROYECTOS: False,
                }
                
                if "msdyn_ConversationId" in data:
                    datos_usuario[CamposUsuario.ID_CONVERSACION] = data['msdyn_ConversationId']
                    respuesta = dataverse_service.consultar_conversacion(datos_usuario[CamposUsuario.ID_CONVERSACION])
                    if respuesta["status"] == 200:
                        datos_usuario[CamposUsuario.CANAL] = respuesta["datos"]["canal"]
                        if datos_usuario[CamposUsuario.CANAL] == Canal.WHATSAPP:
                            datos_usuario[CamposUsuario.CELULAR] = f"+{datos['id_usuario']}"
                            dataverse_service.buscar_clientes_por_celular(
                                datos_usuario[CamposUsuario.CELULAR],
                                datos_usuario[CamposUsuario.ID_CONVERSACION],
                                datos_usuario[CamposUsuario.CANAL],
                                datos_usuario[CamposUsuario.ID_USUARIO_DIRECT_LINE]
                            )
                        else:
                            datos_usuario[CamposUsuario.TIPO_CLIENTE] = None
                            datos_usuario[CamposUsuario.NEGOCIO_VALIDADO_EQUIPO_SAC_POSTVENTA] = None
                            datos_usuario[CamposUsuario.ES_NUEVO_LEAD] = False
                            datos_usuario[CamposUsuario.ID_CLIENTE] = ""
                            datos_usuario[CamposUsuario.TIPO_CLIENTE] = ""


                if "CustomChannelContext" in data:
                    custom_data = json.loads(data['CustomChannelContext'])

                gestor_usuario.actualizar_datos_usuario(datos["id_usuario"],datos_usuario)
                respuesta_usuario = gestor_usuario.actualizar_conversacion(datos["id_usuario"],custom_data["historial_conversacion"],True)
            else:
                mensaje = {
                "role": "user",
                }
                if "archivos" not in datos or datos["archivos"] == []:
                    mensaje["content"] = datos["mensaje"]
                else:
                    #Ya que cuando el usuairo envia archivos, estos llegan con una url que no les corresponde, asi que las urls se envuan por separado
                    mensaje_final,urls = datos["mensaje"].split("\nUSER-FILES-URL:")
                    urls = urls.split("\n")
                    if urls[0] == "":
                        urls = urls[1:]

                    
                    formato_archivos = [
                        {
                            "type": "text",
                            "text": mensaje_final if isinstance(mensaje_final, str) else ""
                        }
                    ]
                    formato_archivos[0]["text"] += "\nArchivos adjuntos:"
                    for index , data in enumerate(zip(datos["archivos"], urls)):
                        archivo,url = data
                        content_type = archivo["contentType"]
                        nombre_archivo = archivo["fileName"]
                        if content_type != "application/pdf":
                            formato_archivos[0]["text"] +=  f"\n{index+1}) {nombre_archivo}"
                            formato_archivos.append({"type": "image_url",
                                                    "image_url": {
                                                        "url": url
                                                    }})
                        else:
                            ruta_archivo = os.path.join("archivos_temporales", "documentos", nombre_archivo)
                            contenido_archivo = requests.get(url).content
                            with open(ruta_archivo, "wb") as f:
                                f.write(contenido_archivo)
                            imagenes_base64 = pdf_a_base64(ruta_archivo)
                            formato_archivos[0]["text"] +=  f"\n{index+1}) {nombre_archivo}"
                            for imagen in imagenes_base64:
                                formato_archivos.append({"type": "image_url",
                                                        "image_url": {
                                                            "url": imagen #Es una imagen base64
                                                        }})
                            os.remove(ruta_archivo)                        
                        mensaje["content"] = formato_archivos
                respuesta_usuario = gestor_usuario.actualizar_conversacion(datos["id_usuario"],mensaje)
                
            if respuesta_usuario["status"] != 200:
                return respuesta_usuario

            respuesta_usuario = gestor_usuario.leer_usuario(datos["id_usuario"])
            if respuesta_usuario["status"] != 200:
                return respuesta_usuario
            
            return respuesta_usuario

        except Exception as e:
            return manejo_errores(self.recibir_datos.__qualname__, 500, error_base=e)

    def enviar_mensaje(self, data):
        pass


bot_services = BotServices()
