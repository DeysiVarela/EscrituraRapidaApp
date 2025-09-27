from enum import Enum
import os
from codigo.variables import PROMPTS
from codigo.funciones_auxiliares import eliminador_texto, evaluador, manejo_errores
from codigo.conexiones_externas.modelos_ia import modelos_ia
from codigo.procesos_internos.gestor_usuario import gestor_usuario

import re

import threading
import requests
from copy import deepcopy

from models.enums import CamposUsuario, ColaEscalamiento

class RespuestaMensajes:
    def __init__(self):
        pass

    def sac_postventa(self, id_usuario_direct_line):
        respuesta_usuario = gestor_usuario.leer_usuario(id_usuario_direct_line)
        if respuesta_usuario["status"] != 200:
            return "error consultando datos del usuario"
                
        datos_usuario = respuesta_usuario["datos"]["datos_usuario"]

        if (datos_usuario.get(CamposUsuario.ID_CLIENTE, "") == "" and not datos_usuario.get(CamposUsuario.ES_NUEVO_LEAD, False)):
            return "Se requiere conocer si el cliente existe en la base de datos para responder"
        
        return PROMPTS["bot_comercial"]["sac_postventa"]       


respuesta_mensajes = RespuestaMensajes()    