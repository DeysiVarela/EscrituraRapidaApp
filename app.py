from dash_board_module import create_dash_board_module, Configuration
from bot_service_module import create_bot_service_module, ConfiguracionBotService
from ngrok_module.ngrok import run_ngrok

from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
import os
from dotenv import load_dotenv
from codigo.funciones_auxiliares import manejo_errores

from codigo.procesos_internos.modelo import modelo_procesos
load_dotenv('.env')
app = Flask(__name__)
CORS(app)

configuration = Configuration()
configuration.atajos = []
configuration.nombre_aplicacion = "Bolivar IA Comercial"
create_dash_board_module(app, configuration)

configuracion_bot_services = ConfiguracionBotService(modelo_procesos.proceso_recepcion_mensajes)
create_bot_service_module(app, configuracion_bot_services)


if __name__ == "__main__":
    port = 5060
    run_ngrok(port, True, os.environ["NGROK_URL"])
    app.run(debug=True, port=port, threaded=True)

    # from codigo.procesos_internos.bot_comercial import bot_comercial,modelos_ia
    # from codigo.conexiones_externas.bot_services import bot_services
    # from codigo.procesos_internos.gestor_usuario import gestor_usuario

    # chat = []
    # datos_usuario = {}
    # while True:
    #     mensaje = input("Mensaje: ")
    #     cuerpo = {
    #         "mensajero": "bot_services",
    #         "mensaje": mensaje,
    #         "id_usuario": "123"
    #     }

    #     respuesta_mapeada = bot_services.recibir_datos(cuerpo)
    #     if respuesta_mapeada["status"] != 200:
    #         codigo_estado = respuesta_mapeada.pop("status")

    #     id_usuario = respuesta_mapeada["datos"]["id_usuario"]

    #     respuesta_conversacion = gestor_usuario.escribir_usuario(
    #             id_usuario, 
    #             respuesta_mapeada["datos"])
        
    #     if respuesta_conversacion["status"] != 200:
    #         codigo_estado = respuesta_conversacion.pop("status")

    #     respuesta_bot = bot_comercial.llamar(respuesta_mapeada["datos"]["historial_conversacion"],
    #                                         respuesta_mapeada["datos"]["datos_usuario"],
    #                                         id_usuario)
        
    #     if "status" in respuesta_bot and respuesta_bot["status"] == 400:
    #         print("Respuesta Bot: ", respuesta_bot["datos"]["registro_asistente"]["content"])
    #         continue

    #     if "status" in respuesta_bot and respuesta_bot["status"] == 200:
    #         for registro_funcion in respuesta_bot["datos"]["respuestas_funciones"]:
    #                 chat.append(registro_funcion)

    #         for registro_funcion in respuesta_bot["datos"]["respuestas_funciones"]:
    #             respuesta_conversacion = gestor_usuario.actualizar_conversacion(
    #                 id_usuario, 
    #                 registro_funcion
    #             )

    #     respuesta_conversacion = gestor_usuario.actualizar_conversacion(
    #         id_usuario, 
    #         respuesta_bot["datos"]["registro_asistente"]
    #     )

    #     print("Respuesta Bot: ", respuesta_bot["datos"]["registro_asistente"]["content"])
    #     if respuesta_bot["datos"]["escalar"]["activo"]:
    #          print(f"====SE ESCALA LA CONVERSACIÓN {respuesta_bot['datos']['escalar']['contexto']}====")

    #     if "terminar" in respuesta_bot["datos"] and respuesta_bot["datos"]["terminar"]:
    #         print(f"====FINALIZA CONVERSACIÓN====")

            

