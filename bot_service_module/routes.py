import os
from flask import request,Response
from botbuilder.integration.aiohttp import CloudAdapter, ConfigurationBotFrameworkAuthentication
from botbuilder.schema import Activity
from bot_service_module.config import DefaultConfig
from bot_service_module.basic_bot import BasicBot

from codigo.procesos_internos.gestor_usuario import gestor_usuario
from codigo.funciones_auxiliares import manejo_errores


config = DefaultConfig()
adapter = CloudAdapter(ConfigurationBotFrameworkAuthentication(config))
API_KEY = os.environ["SELF_API_KEY"]


def init_app(bot_service_bp):
    bot = BasicBot(bot_service_bp.configuration.funcion_proyecto)

    @bot_service_bp.route("/messages", methods=["POST"])
    async def messages():
        """
        Recibe la actividad enviada por el usuario
        """
        try:
            if "application/json" in request.headers["Content-Type"]:
                body = request.json
            else:
                return Response(status=415)
            activity = Activity().deserialize(body)
            
            # Process the message
            auth_header = request.headers["Authorization"] if "Authorization" in request.headers else ""

            response = await adapter.process_activity(auth_header,activity,bot.on_turn)
            if response:
                return Response(status=response.status)
            return Response(status=200)
        except Exception as e:
            return str(e),500
        
    @bot_service_bp.route("/EndConversation", methods=["DELETE"])
    async def borrar_datos_usuario():
        api_key = request.headers.get("x-api-key")
        if api_key != API_KEY:
            return "No autorizado", 401
        
        datos = request.json

        campos_necesarios = ['id_usuario']

        datos: dict
        datos_entregados = datos.keys()
        datos_faltantes = list(
            set(campos_necesarios) - set(datos_entregados))
        
        if datos_faltantes != []:
            respuesta =  manejo_errores(f"/{request.path}", 400, True,
                                  f"Faltan los datos: {str(datos_faltantes)}", False)
            return respuesta
        
        respuesta = gestor_usuario.eliminar_usuario(datos["id_usuario"])
        if respuesta["status"] == 200:
            return "Proceso éxitoso", 200
        else: 
            return "Error realizando el borrado", 500