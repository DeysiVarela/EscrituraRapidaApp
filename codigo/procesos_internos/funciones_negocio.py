import re
from typing import Any, Dict
import uuid
from models.enums import CamposUsuario, TipoCliente, TipoUsuario

class FuncionesNegocio:
    def __init__(self):
        self.datos_perfilar_lead = [
            CamposUsuario.TERRITORIO,
            CamposUsuario.ACTIVIDAD_ECONOMICA,
            CamposUsuario.PROYECTO_INTERES,
            CamposUsuario.INGRESOS_MENSUALES,
            CamposUsuario.EMAIL_CLIENTE,
            CamposUsuario.TIEMPO_COMPRA]
        
        self.datos_perfilar_contacto = [
            CamposUsuario.TERRITORIO,
            CamposUsuario.INGRESOS_MENSUALES,
            CamposUsuario.EMAIL_CLIENTE,
            CamposUsuario.CELULAR
        ]

        self.datos_crear_lead = [
            CamposUsuario.TERRITORIO,
            CamposUsuario.NOMBRE,
            CamposUsuario.APELLIDO,
            CamposUsuario.EMAIL_CLIENTE,
            CamposUsuario.DOCUMENTO_IDENTIFICACION,
            CamposUsuario.TIPO_DOCUMENTO_IDENTIFICACION,
            CamposUsuario.CELULAR,
            CamposUsuario.ACTIVIDAD_ECONOMICA,
            CamposUsuario.PROYECTO_INTERES,
            CamposUsuario.INGRESOS_MENSUALES,
            CamposUsuario.TIEMPO_COMPRA
        ]

    def obtener_datos_perfilacion(self, datos_usuario: Dict[CamposUsuario, Any]):
        datos: list[CamposUsuario]  = []

        if CamposUsuario.EXISTE_EN_BASE_DATOS in datos_usuario and datos_usuario[CamposUsuario.EXISTE_EN_BASE_DATOS] == False: 
            for dato in self.datos_crear_lead:
                datos.append(dato)
        
        elif datos_usuario.get(CamposUsuario.TIPO_CLIENTE) == TipoCliente.LEAD:
            for dato in self.datos_perfilar_lead:
                datos.append(dato)
        
        elif datos_usuario.get(CamposUsuario.TIPO_CLIENTE) == TipoCliente.CONTACTO:
            for dato in self.datos_perfilar_contacto:
                datos.append(dato)
        else:
            datos.append(CamposUsuario.TERRITORIO)
            datos.append(CamposUsuario.DOCUMENTO_IDENTIFICACION)

        nombre_datos = [campo.value for campo in datos]
        return nombre_datos
    
    def obtener_tipo_usuario(self, datos_usuario: Dict[CamposUsuario, Any]) -> TipoUsuario:
        if (datos_usuario.get(CamposUsuario.ES_NUEVO_LEAD)): 
            return TipoUsuario.NUEVO_LEAD
        
        elif datos_usuario.get(CamposUsuario.TIPO_CLIENTE) == TipoCliente.LEAD:
            return TipoUsuario.LEAD
        
        elif datos_usuario.get(CamposUsuario.TIPO_CLIENTE) == TipoCliente.CONTACTO:
            return TipoUsuario.CONTACTO
        else:
            return TipoUsuario.SIN_IDENTIFICAR
        
    def devolver_datos_faltantes(
            self, 
            tipo_usuario: TipoUsuario,
            datos_usuario: Dict[CamposUsuario, Any]
        ) -> list[str]:
        datos_faltantes: list[CamposUsuario] = []
        
        if tipo_usuario == TipoUsuario.NUEVO_LEAD: 
            for dato in self.datos_crear_lead:
                if dato not in datos_usuario or datos_usuario[dato] == None or datos_usuario[dato] == "":
                    datos_faltantes.append(dato)
        
        elif tipo_usuario == TipoUsuario.LEAD:
            for dato in self.datos_perfilar_lead:
                if dato not in datos_usuario or datos_usuario[dato] == None or datos_usuario[dato] == "":
                    datos_faltantes.append(dato)
        
        elif tipo_usuario == TipoUsuario.CONTACTO:
            for dato in self.datos_perfilar_contacto:
                if dato not in datos_usuario or datos_usuario[dato] == None:
                    datos_faltantes.append(dato)

        elif tipo_usuario == TipoUsuario.SIN_IDENTIFICAR:
            datos_faltantes.append(CamposUsuario.DOCUMENTO_IDENTIFICACION)
            datos_faltantes.append(CamposUsuario.TERRITORIO)

        if (CamposUsuario.TERRITORIO in datos_faltantes 
            and datos_usuario.get(CamposUsuario.ES_NACIONAL) != None):
            datos_faltantes.remove(CamposUsuario.TERRITORIO)

        nombres_datos_faltantes:list[str] = [campo.value for campo in datos_faltantes]
        return nombres_datos_faltantes

    def es_guid_valido(self, valor: str) -> bool:
        try:
            uuid_obj = uuid.UUID(valor)
            return str(uuid_obj) == valor.lower()
        except ValueError:
            return False

funciones_negocio = FuncionesNegocio()

if __name__ == "__main__":
    pass