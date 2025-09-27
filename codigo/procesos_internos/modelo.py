import time
import traceback
import os
import jwt

from codigo.procesos_internos.gestor_usuario import gestor_usuario
from codigo.conexiones_externas.bot_services import bot_services
from codigo.procesos_internos.bot_comercial import bot_comercial
from codigo.funciones_auxiliares import manejo_errores


class ModeloProcesos():
    def __init__(self):
        self.clave_token = os.environ["CLAVE_TOKEN"]

    def validar_token(self, token: str) -> dict:
        """
        Valida el token JWT proporcionado.

        Args:
            token (str): el token JWT que necesita ser validado.

        Returns:
            dict: Un diccionario con el estado de la operación.
                  En caso de éxito, el diccionario contiene 'status' igual a 200.
                  En caso de error, el diccionario contiene el mensaje de error apropiado.
        """
        try:
            token_decodificado = jwt.decode(
                token, self.clave_token, algorithms='HS256')
            if 'exp' not in token_decodificado or token_decodificado['exp'] < time.time():
                return manejo_errores(self.validar_token.__qualname__, 401, "Token expirado o inexistente")
            return {"status": 200}
        except Exception as e:
            return manejo_errores(self.validar_token.__qualname__, 500, error_base= e)

    def proceso_recepcion_mensajes(self, datos):
        try:
            respuesta_mapeada = bot_services.recibir_datos(datos)

            if respuesta_mapeada["status"] != 200:
                codigo_estado = respuesta_mapeada.pop("status")
                return respuesta_mapeada, codigo_estado
            id_usuario = respuesta_mapeada["datos"]["id_usuario"]
            respuesta_conversacion = gestor_usuario.escribir_usuario(
                id_usuario, respuesta_mapeada["datos"])

            if respuesta_conversacion["status"] != 200:
                codigo_estado = respuesta_conversacion.pop("status")
                return respuesta_conversacion, codigo_estado
            
            respuesta_imagenes = gestor_usuario.contar_imagnes(id_usuario)
            if respuesta_imagenes["status"] != 200:
                codigo_estado = respuesta_imagenes.pop("status")
                return respuesta_imagenes, codigo_estado
            
            if respuesta_imagenes["datos"]["cantidad_total_imagenes"] > 50:
                # TODO: Crear la funcion que convierte a texto las imagenes
                pass
            respuesta_bot = bot_comercial.llamar(respuesta_mapeada["datos"]["historial_conversacion"],
                                                     respuesta_mapeada["datos"]["datos_usuario"], respuesta_mapeada["datos"]["id_usuario"])
            
            if respuesta_bot["status"] != 200:
                codigo_estado = respuesta_bot.pop("status")
                return respuesta_bot, codigo_estado

            for registro_funcion in respuesta_bot["datos"]["respuestas_funciones"]:
                respuesta_conversacion = gestor_usuario.actualizar_conversacion(
                respuesta_mapeada["datos"]["id_usuario"], registro_funcion)

            respuesta_conversacion = gestor_usuario.actualizar_conversacion(
                respuesta_mapeada["datos"]["id_usuario"], respuesta_bot["datos"]["registro_asistente"])
            return respuesta_bot["datos"], 200
        except Exception as e:
            return manejo_errores(self.proceso_recepcion_mensajes.__qualname__, 500,True, error_base=e)


modelo_procesos = ModeloProcesos()
