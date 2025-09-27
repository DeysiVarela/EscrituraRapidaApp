from http import HTTPStatus
from typing import Any, Dict
import requests
from bs4 import BeautifulSoup
import re
from codigo.conexiones_externas.bot_copilot import bot_copilot
from codigo.conexiones_externas.conexion_crm import conexion_crm
from codigo.conexiones_externas.dataverse_service import dataverse_service
from codigo.funciones_auxiliares import manejo_errores
from models.resultado_operacion import ResultadoOperacion


class WebScraping:
    def __init__(self):
        self.url_proyectos = "https://www.constructorabolivar.com/api/proyectos2/{}/{}/{}?_format=json"
        self.url_macro_proyectos = "https://www.constructorabolivar.com/api/macroproyectos/{}/{}?_format=json"
        self.url_ciudades = "https://www.constructorabolivar.com/api/ciudad/all?_format=json"
        self.url_sectores = "https://www.constructorabolivar.com/api/sector/{}/all?_format=json"
        self.url_base = "https://www.constructorabolivar.com"
        self.url_sala_venta = "https://constructorabolivar.com/api/sedes?_format=json"
        self.estado_proyecto_validos = ["Lanzamiento", "Últimas unidades", "En venta"]
        self.id_ciudad_cali = "19"
        self.id_ciudad_armenia = "170"
    
    def eliminar_repetidos(self, lista: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return list(map(dict, set(tuple(sorted(d.items())) for d in lista)))

    def consultar_proyectos(
            self, 
            id_ciudad: str = "all", 
            id_sector: str = "all", 
            id_tipo_vivienda: str = "all"
        ) -> Dict[str, Any]:
        try:
            if "" == id_ciudad:
                id_ciudad = "all"
            if "" == id_sector:
                id_sector = "all"
            if "" == id_tipo_vivienda:
                id_tipo_vivienda = "all"

            #Condicion si es diferente la ciudad de cali y sus alrededores & Armenia
            if id_ciudad != self.id_ciudad_cali and id_ciudad != self.id_ciudad_armenia  and id_ciudad != 'all':
                result = dataverse_service.obtener_whatsapp_bogota()
                return result

            consulta = requests.get(self.url_proyectos.format(
                id_ciudad, id_sector, id_tipo_vivienda), verify=False)
            
            return self.limpiar_proyectos(consulta.json())
        except Exception as e:
            return {"data": f"no se pudo acceder a la información de los proyectos porque {e}"}

    def informacion_sobre_proyecto_por_nombre(self, nombre_proyecto: str) -> dict:
        try:            
            consulta = requests.get(self.url_proyectos.format(
                "all", "all", "all"), verify=False)
            proyectos = self.limpiar_proyectos(consulta.json(), con_id=True)
            nuevos_proyectos = []
            for proyecto in proyectos:
                if nombre_proyecto.lower() in proyecto["title"].lower():
                    id_ciudad = proyecto["id_ciudad"]
                    estado = proyecto["field_estados"]
                    if id_ciudad == self.id_ciudad_cali or id_ciudad == self.id_ciudad_armenia:
                        if estado in self.estado_proyecto_validos:
                            nuevos_proyectos.append(proyecto)
                        else:
                            nuevos_proyectos.append({"title": proyecto["title"], "Nota": f"Este proyecto se encuentra {estado}, recomiendale un proyecto similar al cliente"})    
                    else:
                        nuevos_proyectos.append({"title": proyecto["title"], "Nota": "este proyecto no pertenece a la ciudad de cali o sus alrededores ni a Armenia"})
 
            return nuevos_proyectos
        except Exception as e:
            return {"data": f"no se pudo acceder a la información de los proyectos porque {e}"}

    def limpiar_proyectos(self, datos, con_id: bool = False) -> Dict[str, Any]:
        try:
            llaves_usadas = ["title", 
                             "body", 
                             "field_tipo_de_vivienda",
                             "field_descripcion_destacada_1",
                             "field_descripcion_destacada_2", 
                             "field_descripcion_destacada_3",
                             "field_descripcion_destacada_4", 
                             "field_macroproyecto",
                             "field_clasificacion_de_proyecto", 
                             "field_ciudad",
                             "field_precio",
                             "field_precio_smmlv",
                             "field_alcobas",
                             "field_alcobas_maximas",
                             "field_area_minima",
                             "field_precio_smmlv",
                             "field_precio",
                             "field_estados"
                             ]
            if con_id:
                llaves_usadas += ["id_ciudad"]
                             

            proyectos = []
            for proyecto in datos:
                proyecto_limpio = {llave: proyecto[llave]
                                   for llave in llaves_usadas}
                proyecto_limpio["url_proyecto"] = self.url_base + proyecto["view_node"]
                proyectos.append(proyecto_limpio)
            return proyectos
        except Exception:
            return {"data": "no se pudo acceder a la información de los proyectos"}

    def consultar_macro_proyectos(self, id_ciudad: str = "all", id_sector: str = "all") -> dict:
        try:
            if "" == id_ciudad:
                id_ciudad = "all"
            if "" == id_sector:
                id_sector = "all"

            #Condicion si es diferente la ciudad de cali y sus alrededores & Armenia
            if id_ciudad != self.id_ciudad_cali and id_ciudad != self.id_ciudad_armenia  and id_ciudad != 'all':
                result = dataverse_service.obtener_whatsapp_bogota()
                return result

            consulta = requests.get(
                self.url_macro_proyectos.format(id_ciudad, id_sector), verify=False)
            
            return self.limpiar_macro_proyectos(consulta.json())
             
        except Exception as e:
            return {"data": "no se pudo acceder a la información de los macroproyectos"}

    def limpiar_macro_proyectos(self, datos) -> dict:
        try:
            llaves_usadas = ["title", "body", "field_ciudad", "id_ciudad", "field_precio",
                             "field_sector", "id_sector", "field_imagen_destacada", "view_node",
                             "field_tipo_de_vivienda", "id_tipo_vivienda", "field_subsidio_de_vivienda",
                             "field_area_minima", "field_precio_maximo", "field_proyectos",
                             "field_descripcion_tarjetas"]

            macro_proyectos = []
            for macro_proyecto in datos:
                macro_proyecto_limpio = {
                    llave: macro_proyecto[llave] for llave in llaves_usadas}
                macro_proyectos.append(macro_proyecto_limpio)
            return macro_proyectos
        except Exception:
            return {"data": "no se pudo acceder a la información de los macroproyectos"}

    def consultar_ciudades(self) -> Dict[str, str]:
        try:
            consulta = requests.get(self.url_ciudades, verify=False)
            return self.limpiar_ciudades(consulta.json())
        except Exception:
            return {"data": "no se pudo acceder a la información de las ciudades"}

    def limpiar_ciudades(self, datos) -> dict:
        try:
            llaves_usadas = ["name", "tid"]
            ciudades = []
            for ciudad in datos:
                ciudad_limpia = {llave: ciudad[llave]
                                 for llave in llaves_usadas}
                ciudades.append(ciudad_limpia)
            return self.eliminar_repetidos(ciudades)
        except Exception:
            return {"data": "no se pudo acceder a la información de las ciudades"}

    def consultar_sectores(self, id_ciudad: str) -> dict:
        try:
            consulta = requests.get(
                self.url_sectores.format(id_ciudad), verify=False)
            if not consulta.ok:
                return {"data": "no se pudo acceder a la información de los sectores"}
            return self.limpiar_sectores(consulta.json())
        except Exception:
            return {"data": "no se pudo acceder a la información de los sectores"}

    def limpiar_sectores(self, datos) -> dict:
        try:
            llaves_usadas = ["name", "tid"]
            sectores = []
            for sector in datos:
                sector_limpio = {llave: sector[llave]
                                 for llave in llaves_usadas}
                sectores.append(sector_limpio)
            return self.eliminar_repetidos(sectores)
        except Exception:
            return {"data": "no se pudo acceder a la información de los sectores"}

    def get_json_tipo_vivienda(self) -> Dict[str,str]:
        return {"1": "Apartamentos", "260": "Mixto", "31621": "Locales", "2": "Casas"}

    def informacion_sobre_proyecto(self, url_proyecto: str) -> Dict[str,Any]:
        try:
            if "http" not in url_proyecto:
                url_proyecto = self.url_base + url_proyecto
            if self.url_base not in url_proyecto:
                return {"data": "la url proporcionada no pertenece a la página de constructora bolívar, vuelve a busar la url del proyecto usando el nombre del proyecto"}
            consulta = requests.get(
                url_proyecto.replace("\\", ""), verify=False)
            data = self.limpiador_informacion_sobre_proyecto(consulta.content)
            data.update(conexion_crm.GetResource("itc_projects", data.get(
                "titulo", "asndijasichadshfkjhdjjasdklfjawdojfkaedjfkpadsjf")))
            
            return data
        except Exception:
            return {"data": "no se pudo acceder a la información del proyecto"}

    def limpiador_informacion_sobre_proyecto(self, html) -> Dict[str,Any]:
        try:
            respuesta: Dict[str, Any] = {
                "video": None,
                "galeria": None,
                "vista-360-links": None,
                "folleto": None
            }
            soup = BeautifulSoup(html, 'html.parser')
            try:
                url_video = self.eliminador_caracteres(
                        str(soup.find("div", class_="modal fade clsModalGallery", id="modal-video")))

                if url_video != "None" and len(url_video) > 0: 
                    respuesta["video"] =  f"</RECURSO-VIDEO>{url_video}</RECURSO-VIDEO>"
            except:
                pass
            try:
                respuesta["titulo"] = self.eliminador_caracteres(
                    str(soup.find("h1", class_="title-section-single").text))
            except:
                pass
            try:
                modal_galeria = soup.find(
                    "div", 
                    class_="modal fade clsModalGallery", 
                    id="modal-galeria"
                )
                if modal_galeria:
                    multi_main = modal_galeria.find("div", class_="multi-main")
                    if multi_main:
                        imagenes = multi_main.find_all("img")
                        if imagenes:
                            resultado = []
                            for img in imagenes:
                                src = img.get('src')
                                alt = img.get('alt', 'Imagen')
                                recurso = f"<RECURSO-IMAGEN>{src} ; {alt}</RECURSO-IMAGEN>"
                                resultado.append(recurso)
                            respuesta["galeria"] = resultado

                imagenes = modal_galeria = soup.find_all(
                    "img", class_="img-fluid slider-pro-img")
                if imagenes:
                    resultado = []
                    for img in imagenes:
                        src = img.get('src')
                        alt = img.get('alt', 'Imagen')
                        recurso = f"<RECURSO-IMAGEN>{src} ; {alt}</RECURSO-IMAGEN>"
                        resultado.append(recurso)
                    if respuesta["galeria"]:
                        respuesta["galeria"].extend(resultado)
                    else:
                        respuesta["galeria"] = resultado
            except:
                pass

            try:
                modal_video = soup.find(
                    "div", class_="modal fade clsModalGallery", id="modal-video").find("iframe")
                modal_video = modal_video["src"]

                if modal_video != "None"  and len(modal_video) > 0:
                    respuesta["video"] = f"<RECURSO-VIDEO>{str(modal_video)}</RECURSO-VIDEO>" 
            except:
                pass

            try:
                vista_360_links = []
                contenedor = self.eliminador_caracteres(
                    str(soup.find("div", class_="cont-slide-recorridos")))
                
                if(contenedor):
                    contenedorHTML = BeautifulSoup(contenedor, "html.parser")

                    for iframe in contenedorHTML.find("div"):

                        src = iframe.find("iframe").get("src")
                        if src:
                            vista_360_links.append(f"<LINK-VISTA-360>{src}</LINK-VISTA-360>")

                respuesta["vista-360-links"] = vista_360_links if len(vista_360_links) > 0 else []
            except:
                pass        

            try:
                folleto_url: list[str] = []

                contenedor = self.eliminador_caracteres(
                    str(soup.find("div", class_="cont-shared")))
                
                if(contenedor):
                    contenedorHTML = BeautifulSoup(contenedor, "html.parser")

                    for link in contenedorHTML.find_all("a", href=True, class_='btn-download'):
                        href = link["href"]
                        if href:
                            folleto_url.append(f"<RECURSO-PDF>{href}</RECURSO-PDF>")
                            break

                respuesta["folleto"] = folleto_url[0] if len(folleto_url)  > 0 else None
            except:
                pass

            nueva_respuesta: Dict[str, Any] = {}
            for key, value in respuesta.items():
                if value == "None" or not value:
                    nueva_respuesta[key] = "No se encontró información sobre este campo"
                else:
                    nueva_respuesta[key] = value
            
            return nueva_respuesta
        except Exception:
            return {"data": "no se pudo acceder a la información del proyecto"}

    def eliminador_caracteres(self, texto: str) -> str:
        caracteres = ["\\t", "\\r", "\\n", "\t", "\r", "\n"]
        for caracter in caracteres:
            texto = texto.replace(caracter, "")
        texto = re.sub(r'<!--.*?-->', '', texto, flags=re.DOTALL)
        return texto

    def informacion_sobre_temas_de_interes(self, pregunta_simplificada: str) -> str:
        try:
            datos = bot_copilot.llamar(pregunta_simplificada)
            return datos
        except Exception:
            return "no se pudo acceder a la información del tema de interés"

    def consultar_informacion_sala_venta(self) -> Dict[str,Any]:
        try:
            consulta = requests.get(
                self.url_sala_venta, verify=False)
            return self.limpiar_informacion_sala_venta(consulta.json())
        except Exception as e:
            return {"mensaje": "No se puedo acceder a la informacion de la sala de venta"}
        
    def limpiar_informacion_sala_venta(self, datos) -> Dict[str, Any] :
        try:
            llaves_usadas = ["city", "sector", "name", "address", "phone","email", "schedule"]
            salas_ventas = []
            for sala_venta in datos:
                sala_venta_limpio = {llave: sala_venta[llave]
                                 for llave in llaves_usadas}
                salas_ventas.append(sala_venta_limpio)
            return self.eliminar_repetidos(salas_ventas)
        except Exception as e:
            return {"data": "no se pudo acceder a la información de los puntos de venta"}
        
    def consultar_nombres_proyectos(self) -> ResultadoOperacion:
        try:
            respuesta = requests.get(self.url_proyectos.format("all", "all", "all"), verify=False)
            proyectos = respuesta.json()
            proyectos_cali: list[str] = []
            proyectos_bogota: list[str] = []
            for proyecto in proyectos:
                id_ciudad = proyecto.get('id_ciudad')
                titulo = proyecto.get('title', '').strip()
                ciudad = proyecto.get('field_ciudad', '').strip()
                estado = proyecto.get('field_estados', '').strip()
                if id_ciudad == self.id_ciudad_cali or id_ciudad == self.id_ciudad_armenia:
                    proyectos_cali.append(f"{titulo}, ciudad: {ciudad}, estado:{estado}")
                else:
                    proyectos_bogota.append(f"{titulo}, ciudad: {ciudad}, estado:{estado}")

            datos = {
                "proyectos_cali": proyectos_cali,
                "proyectos_bogota": proyectos_bogota,
            }
            return ResultadoOperacion.exitoso(datos)
        except Exception as e:
            manejo_errores(self.consultar_nombres_proyectos.__qualname__, 500, error_base=e)
            return ResultadoOperacion.error(HTTPStatus.INTERNAL_SERVER_ERROR, e)
        
    def obtener_datos_respuesta_peticion(self, datos, llaves):
        try:
            items = []
            for item in datos:
                item_limpio = {llave: item[llave]
                                   for llave in llaves}
                items.append(item_limpio)
            return items
        except Exception as e:
            return {"data": "no se pudo acceder a la información solicitada"}

web_scraping = WebScraping()
if __name__ == "__main__":
    pass
