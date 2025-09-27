import os
import traceback
import json
from typing import Any, Dict
from codigo.funciones_auxiliares import manejo_errores
from models.enums import CamposUsuario


class GestorUsuario:
    def __init__(self):
        self.ruta_base_usuario = f"{os.environ['RUTA_CHATS']}"+"{}.json"

    def actualizar_conversacion(self, id_usuario: str, registro: dict, extend: bool = False) -> dict:
        """
        Actializa  la conversación de un usuario en un archivo JSON.

        Args:
            id_usuario (str): El identificador único del usuario.
            registro (dict): El registro de la conversación que se añadirá.

        Returns:
            dict: Un diccionario con el estado de la operación.
            En caso de éxito, el diccionario contiene un estado 'status' igual a 200 y la conversación actualizada en 'conversacion'.
            En caso de error, el diccionario contiene el detalle del error.
        """
        try:
            ruta_usuario = self.ruta_base_usuario.format(id_usuario)

            if os.path.exists(ruta_usuario):
                respuesta = self.leer_usuario(id_usuario)

                if respuesta["status"] != 200:
                    return respuesta

                usuario = respuesta["datos"]
            else:
                usuario = {"bot_actual": "bot_ia",
                           "id_usuario": id_usuario,
                           "historial_conversacion": []}

            if extend:
                usuario["historial_conversacion"].extend(registro)    
            else:
                usuario["historial_conversacion"].append(registro)
            respuesta = self.escribir_usuario(
                id_usuario, usuario)

            if respuesta["status"] != 200:
                return respuesta

            return {"status": 200, "conversacion": usuario["historial_conversacion"]}
        except Exception as e:
            return manejo_errores(self.actualizar_conversacion.__qualname__,
                                  500, error_base=e)
        
    def cambiar_bot(self, id_usuario: str) -> dict:
        """
        Cambia el bot actual de un usuario en el archivo JSON.
        Args:
            id_usuario (str): El identificador único del usuario.

        Returns:
            dict: Un diccionario con el estado de la operación y el bot actual.
            En caso de éxito, el diccionario contiene 'status' igual a 200 y el nuevo bot en 'bot_actual'.
            En caso de error, el diccionario contiene el detalle del error.

        Ejemplo de uso:
        >>> gestor_usuario = GestorUsuario()
        >>> respuesta = gestor_usuario.cambiar_bot("id_del_usuario")
        """
        try:
            respuesta = self.leer_usuario(id_usuario)

            if respuesta["status"] != 200:
                return respuesta
            usuario = respuesta["datos"]
            if usuario["bot_actual"] == "bot_ia":
                usuario["bot_actual"] = "bot_pva"
            else:
                usuario["bot_actual"] = "bot_ia"

            respuesta = self.escribir_usuario(id_usuario, usuario)
            if respuesta["status"] != 200:
                return respuesta

            return {"status": 200, "bot_actual": usuario["bot_actual"]}

        except Exception as e:
            return manejo_errores(self.cambiar_bot.__qualname__, 500, error_base=e)
        
    def leer_usuario(self,id_usuario:str) -> Dict[Any,Any]:
        """
        Lee el archivo JSON de un usuario 

        Args:
            id_usuario (str): el identificador único del usuario.

        Returns:
            dict: Un diccionario con el estado de la operación y, si es exitoso, la conversación almacenada.
            En caso de éxito, el diccionario contiene 'status' igual a 200 y la conversación en 'datos'.
            En caso de error, el diccionario contiene el detalle del error.

        Ejemplo de uso:
        >>> gestor_usuario = GestorUsuario()
        >>> respuesta = gestor_usuario.leer_usuario("ruta/a/usuario.json")
        """
        try:
            ruta_usuario = self.ruta_base_usuario.format(id_usuario)
            with open(ruta_usuario, "r", encoding="utf-8") as archivo_usuario:
                usuario = json.load(archivo_usuario)
            return {"status": 200, "datos": usuario}
        except Exception as e:
            return manejo_errores(self.leer_usuario.__qualname__, 500, error_base=e)

    def escribir_usuario(self, id_usuario: str, usuario: dict) -> dict:
        """
        Escribe la información del usuario en un archivo JSON.

        Args:
            id_usuario (str): El identificador único del usuario.
            usuario (dict): Diccionario con la información del usuario que se desea almacenar.

        Returns:
            dict: Un diccionario con el estado de la operación.
            En caso de éxito, el diccionario contiene 'status' igual a 200 y un mensaje de confirmación en 'mensaje'.
            En caso de error, el diccionario contiene el detalle del error.

        Ejemplo de uso:
        >>> gestor_usuario = GestorUsuario()
        >>> usuario_data = {"bot_actual": "bot_ia", "historial_conversacion": [{"usuario": "Hola"}, {"bot": "Hola, ¿cómo estás?"}]}
        >>> respuesta = gestor_usuario.escribir_usuario("id_del_usuario", usuario_data)
        """
        try:
            ruta_usuario = self.ruta_base_usuario.format(id_usuario)
            with open(ruta_usuario, "w", encoding="utf-8") as archivo_usuario:
                json.dump(usuario, archivo_usuario, ensure_ascii=False, indent=4)
            return {"status": 200, "mensaje": "Usuario escrito correctamente."}
        except Exception as e:
            return manejo_errores(self.escribir_usuario.__qualname__, 500, error_base=e)
        
    def existe_usuario(self, id_usuario: str) -> dict:
        """
        Verifica si el archivo JSON del usuario existe.

        Args:
            id_usuario (str): El identificador único del usuario.

        Returns:
            dict: Un diccionario con el estado de la operación.
            En caso de éxito, el diccionario contiene 'status' igual a 200 y 'existe' igual a True o False.
            En caso de error, el diccionario contiene el detalle del error.

        Ejemplo de uso:
        >>> gestor_usuario = GestorUsuario()
        >>> respuesta = gestor_usuario.existe_usuario("id_del_usuario")
        """
        try:
            ruta_usuario = self.ruta_base_usuario.format(id_usuario)
            existe = os.path.exists(ruta_usuario)
            return {"status": 200, "existe": existe}
        except Exception as e:
            return manejo_errores(self.existe_usuario.__qualname__, 500, error_base=e)

    def crear_usuario(self, id_usuario: str) -> dict:
        """
        Crea un nuevo usuario con un historial inicial vacío.

        Args:
            id_usuario (str): El identificador único del usuario.

        Returns:
            dict: Un diccionario con el estado de la operación.
            En caso de éxito, el diccionario contiene 'status' igual a 200 y un mensaje de confirmación en 'mensaje'.
            En caso de error, el diccionario contiene el detalle del error.

        Ejemplo de uso:
        >>> gestor_usuario = GestorUsuario()
        >>> respuesta = gestor_usuario.crear_usuario("id_del_usuario")
        """
        try:
            usuario = {
                "bot_actual": "bot_ia",
                "id_usuario": id_usuario,
                "historial_conversacion": [],
                "registro_asistente": {},
                "datos_usuario":{
                    CamposUsuario.ID_USUARIO_DIRECT_LINE: None,
                    CamposUsuario.ES_NACIONAL: -1,
                    CamposUsuario.ESCALAR: False,
                    CamposUsuario.ES_NUEVO_LEAD: False,
                    CamposUsuario.BUSCAR_PROYECTOS: False,
                    CamposUsuario.ID_CONVERSACION: None,
                    CamposUsuario.CANAL: None,
                    CamposUsuario.TIPO_CLIENTE: None,
                    CamposUsuario.NEGOCIO_VALIDADO_EQUIPO_SAC_POSTVENTA: None,
                    CamposUsuario.ID_CLIENTE: None,
                    "respuesta_bot":{
                        "intencion_usuario": None
                    }
                },

            }
            respuesta = self.escribir_usuario(id_usuario, usuario)
            return respuesta
        except Exception as e:
            return manejo_errores(self.crear_usuario.__qualname__, 500, error_base=e)

    def actualizar_datos_usuario(self, id_usuario: str, registro: Dict[CamposUsuario, Any]) -> Dict[str, Any]:
        """
        Actializa  la conversación de un usuario en un archivo JSON.

        Args:
            id_usuario (str): El identificador único del usuario.
            registro (dict): El registro de la conversación que se añadirá.

        Returns:
            dict: Un diccionario con el estado de la operación.
            En caso de éxito, el diccionario contiene un estado 'status' igual a 200 y la conversación actualizada en 'conversacion'.
            En caso de error, el diccionario contiene el detalle del error.
        """
        try:
            ruta_usuario = self.ruta_base_usuario.format(id_usuario)

            if os.path.exists(ruta_usuario):
                respuesta = self.leer_usuario(id_usuario)

                if respuesta["status"] != 200:
                    return respuesta

                usuario = respuesta["datos"]
            else:
                usuario = {"bot_actual": "bot_ia",
                           "id_usuario": id_usuario,
                           "historial_conversacion": [],
                           "registro_asistente": None,
                           "datos_usuario":{}
                           }

            usuario["datos_usuario"].update(registro)
            respuesta = self.escribir_usuario(
                id_usuario, usuario)

            if respuesta["status"] != 200:
                return respuesta

            return {"status": 200}
        except Exception as e:
            return manejo_errores(self.actualizar_datos_usuario.__qualname__,
                                  500, error_base=e)
        
    def eliminar_usuario(self, id_usuario):
        try: 
            if id_usuario == "*" or id_usuario == None or id_usuario == '':
                return { "status": 400}
            
            ruta_usuario = self.ruta_base_usuario.format(id_usuario)
            if not os.path.exists(ruta_usuario):
                return { "status": 400}
        
            os.remove(ruta_usuario)
            return { "status": 200}
        
        except Exception as e:
            return manejo_errores(self.eliminar_usuario.__qualname__,
                                  500, error_base=e)

        
    def contar_imagnes(self, id_usuario: str) -> dict:
        """
        Cuenta la cantidad de imagenes en el historial de un usuario.

        Args:
            id_usuario (str): El identificador único del usuario.

        Returns:
            dict: Un diccionario con el estado de la operación.
            En caso de éxito, el diccionario contiene 'status' igual a 200 y la cantidad de imagenes en 'cantidad'.
            En caso de error, el diccionario contiene el detalle del error.
        """
        try:
            respuesta = self.leer_usuario(id_usuario)

            if respuesta["status"] != 200:
                return respuesta

            usuario = respuesta["datos"]
            cantidad_total = 0
            detalles_imagenes = []
            for i, mensaje in enumerate(usuario["historial_conversacion"]):
                if mensaje["role"] == "user":
                    if isinstance(mensaje["content"], list):
                        cantidad_imagenes = len(mensaje["content"]) - 1  # -1 porque el primer elemento es el mensaje
                        cantidad_total += cantidad_imagenes
                        detalles_imagenes.append({"mensaje_index": i, "cantidad_imagenes": cantidad_imagenes})

            return {
                "status": 200,
                "datos": {
                    "cantidad_total_imagenes": cantidad_total,
                    "imagenes_por_mensaje": detalles_imagenes
                }
            }
        except Exception as e:
            return manejo_errores(self.contar_imagnes.__qualname__, 500, error_base=e)

gestor_usuario = GestorUsuario()
