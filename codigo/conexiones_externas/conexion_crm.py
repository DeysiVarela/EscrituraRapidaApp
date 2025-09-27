import os
import requests
import json


class ConexionCrm:
    """
    Esta clase proporciona métodos para interactuar con un servidor FHIR (Fast Healthcare Interoperability Resources) utilizando el estándar de autenticación de Azure.

    Args:
        crm_server (str): La URL del servidor FHIR. 
        TenantId (str): El identificador del inquilino de Azure.
    """

    def __init__(self,
                 crm_server=os.environ["CRM_SERVER"],
                 crm_api=os.environ["CRM_API"],
                 TenantId=os.environ["TENANT_ID_CRM"]):
        self.crm_server = crm_server
        self.crm_api = crm_api
        self.TenantId = TenantId

    def GetAzureAccessToken(self):
        """
        Obtiene un token de acceso de Azure para autenticarse en el servidor FHIR.

        Returns:
            str: El token de acceso de Azure.

        Example:
            >>> CRM = Crm()
            >>> token = CRM.GetAzureAccessToken()
        """
        # Obtieene el token de acceso a azure
        Url = f"https://login.microsoftonline.com/{self.TenantId}/oauth2/token"
        Data = {
            "grant_type": "Client_Credentials",
            "client_id": os.environ["CLIENT_ID_CRM"],
            "client_secret": os.environ["CLIENT_SECRET_CRM"],
            "resource": self.crm_server
        }
        Headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        Response = requests.request("POST", Url, headers=Headers, data=Data)
        return Response.json()["access_token"]

    def GetResource(self, ResourceType: str = "itc_projects", proyect_name: str = "") -> dict:
        """
        Obtiene recursos del servidor FHIR.

        Args:
            ResourceType (str): El tipo de recurso a consultar, p. ej., "itc_projects".
            proyect_name (str): Nombre del proyecto a buscar.\n

        Returns:
            dict: Un diccionario con los datos del recurso solicitado.

        Example:
            >>> CRM = Crm()
            >>> projects = CRM.GetResource("itc_projects", "Proyecto 1")
        """
        proyect_name = proyect_name.split("-")[0].strip()
        Url = f"{self.crm_api}/{ResourceType}?$select=itc_address,cbol_quotaadministration_base,cbol_locationurl,itc_name,cbol_urlonlinepayment,cbol_urlhowsworkgoing,cbol_paymentreferenceholder&$filter=contains(itc_name,'{proyect_name}')"
        # Limpia la url de // para evitar errores excepto los primeros del protocolo
        Url = self.crm_api + Url.removeprefix(self.crm_api).replace("//", "/")

        Headers = {
            "Authorization": f"Bearer {self.GetAzureAccessToken()}",
            "Content-Type": "application/json"
        }
        Response = requests.request("GET", Url, headers=Headers)
        try:
            DataList = Response.json()["value"]
        except:
            return {}
        DataList: list
        # Elimina todos los elementos con valores nulos
        nuevas_claves = {
            "itc_address": "direccion",
            "itc_name": "nombre_proyecto",
            "cbol_quotaadministration_base": "cuota_administracion",
            "cbol_urlmarketing": "url_logo_proyecto",
            "cbol_locationurl": "url_ubicacion_google_maps",
            "cbol_urlonlinepayment": "url_pago_online",
            "cbol_urlhowsworkgoing": "url_pagina_avance_de_obra",
            "cbol_paymentreferenceholder": "titular_referencia_pago"
        }
        nueva_data_lista = []
        for Data in DataList:
            nueva_data = {}
            for key, value in Data.items():
                if key == "cbol_urlonlinepayment" and value == None:
                    value = "https://www.constructorabolivar.com/pagos-en-linea"
                if key == "cbol_urlhowsworkgoing" and value == None:
                    value = "Actualmente no hay un avance para este proyecto, pero proximamente podras consultarlo en el siguiente enlace: https://www.constructorabolivar.com/avance-de-obra"
                if value != None and key not in ["@odata.etag", "itc_projectid", "_transactioncurrencyid_value"]:
                    nueva_data[nuevas_claves[key]] = value
            nueva_data_lista.append(nueva_data)
        return {"informacion_crm": nueva_data_lista}


conexion_crm = ConexionCrm()
# -----------------Main Call------------------#
if __name__ == '__main__':
    projects = conexion_crm.GetResource("itc_projects", "Los Linos")
    print(json.dumps(projects, indent=4))
    print(len(projects))
