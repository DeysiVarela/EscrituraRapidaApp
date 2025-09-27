import traceback
from datetime import datetime
from typing import Any, Dict
import fitz  # PyMuPDF
from PIL import Image
import base64
from io import BytesIO

def leer_archivo(ruta_archivo: str) -> str:
    """
    Lee el contenido de un archivo de texto.

    Args:
        ruta_archivo (str): La ruta del archivo a leer.

    Returns:
        str: El contenido del archivo.

    Example:
        >>> contenido = leer_archivo("archivo.txt")
    """
    with open(ruta_archivo, "r", encoding="utf-8") as archivo:
        archivo_leido =  archivo.read()
    return archivo_leido

def escribir_archivo(ruta_archivo: str, contenido: str, modo: str = "w") -> None:
    """
    Escribe contenido en un archivo de texto.

    Args:
        ruta_archivo (str): La ruta del archivo en el que se escribirá el contenido.
        contenido (str): El contenido que se escribirá en el archivo.
        modo (str): El modo de escritura del archivo (opcional, por defecto es "w").

    Example:
        >>> escribir_archivo("archivo.txt", "Este es el contenido que se escribirá en el archivo.")
    """
    try:
        with open(ruta_archivo, modo, encoding="utf-8") as f:
            f.write(str(contenido))

    except Exception as e:
        return {"error": f"Error al escribir el archivo {e}"}


def manejo_errores(nombre_funcion: str = "", estado: int = 500,
                   estado_aparte: bool = False, error_base: Any = "",
                   usar_traceback: bool = True, ruta_archivo_errores: str = "logs_errores.txt") -> Dict[str, Any]:
    
    """
    Maneja y registra errores producidos durante la ejecución de una función/metodo.

    Args:
        nombre_funcion (str): Nombre de la función donde ocurrió el error.
        estado (int): Código de estado del error (opcional, por defecto es 500).
        estado_aparte (bool): Si es True, el estado es separado del mensaje de error (opcional, por defecto es False).
        error_base (any): Mensaje de error base (opcional).
        usar_traceback (bool): Si es True, se incluye la traza del error en el registro (opcional, por defecto es True).
        ruta_archivo_errores (str): Ruta del archivo donde se guardarán los registros de errores (opcional, por defecto es "logs_errores.txt")

    Returns:
        (dict | tuple): Un diccionario con la información del error, y opcionalmente el estado si `estado_aparte` es True.
    """
    try:
        if usar_traceback:
            error_traceback = traceback.format_exc().splitlines()[-4:-2]
            archivo_info = error_traceback[0].strip().split(",")
            archivo = archivo_info[0].replace("File", "").replace(
                '"', "").strip().replace("\\", "/")
            linea = archivo_info[1].replace(
                "line", "").strip() + f", {error_traceback[1].strip()}"
            cadena_traceback = f"Archivo: {archivo} | Linea: {linea}"
            error_traceback_formateado = f" | {cadena_traceback}"
        else:
            error_traceback_formateado = ""

        retorno: Dict[str, Any] = {"status": estado, "error": f"{error_base}{error_traceback_formateado}",
                    "funcion": nombre_funcion}
        registro_logs_errores = f"{datetime.now()} [ERROR] ({estado}): {retorno['error']} | Funcion: {nombre_funcion}\n"
        escribir_archivo(ruta_archivo_errores, registro_logs_errores, "a")
        return retorno
    except Exception as e:
        registro_logs_errores = f"{datetime.now()} [ERROR] ({estado}): {error_base} | Funcion: {nombre_funcion}\n"
        escribir_archivo(ruta_archivo_errores, registro_logs_errores, "a")
        registro_log_interno = f"{datetime.now()} [ERROR] (500): {e} | Funcion: manejo_errores\n"
        escribir_archivo(ruta_archivo_errores, registro_log_interno, "a")
        return {"status": estado, "error": f"{error_base}", "funcion": nombre_funcion}



def evaluador(texto: str, lista: bool = False) -> any:
    """
    Evalúa una cadena de texto y la convierte en una estructura de datos de Python.
    Args:
        texto (str): El texto a evaluar.
        lista (bool): Indicador de si se espera una lista en lugar de un diccionario (opcional, por defecto es False).

    Returns:
        any: La estructura de datos resultante de la evaluación del texto, puede ser una lista, diccionario
             o una estructura vacía en caso de error.
    Example:
        >>> evaluador("{'clave': 'valor'}")
        {'clave': 'valor'}
        >>> evaluador("[1, 2, 3]", lista=True)
        [1, 2, 3]
    """
    try:
        return eval(texto)
    except:
        texto = eliminador_texto(texto, lista)
    try:
        return eval(texto)
    except:
        return [] if lista else {}


def eliminador_texto(texto: str, lista: bool) -> str:
    """
    Elimina texto adicional para extraer una estructura de datos válida de Python.

    Args:
        texto (str): El texto original.
        lista (bool): Indicador de si se espera una lista en lugar de un diccionario.

    Returns:
        str: El texto modificado que contiene sólo una estructura de datos válida.

    Example:
        >>> eliminador_texto("foo = {'clave': 'valor'}", lista=False)
        "{'clave': 'valor'}"
        >>> eliminador_texto("foo = [1, 2, 3]", lista=True)
        "[1, 2, 3]"
    """
    indice1 = texto.find("{") if not lista else texto.find("[")
    indice2 = texto.rfind("}") if not lista else texto.rfind("]")
    return texto[indice1 if indice1 != -1 else 0: indice2+1 if indice2 != -1 else None]




def pdf_a_base64(ruta_pdf: str) -> list[str]:
    """
    Convierte un documento PDF en una lista de cadenas Base64,
    donde cada cadena representa una página del PDF convertida en imagen.

    Args:
        ruta_pdf (str): La ruta del archivo PDF a convertir.

    Returns:
        list[str]: Lista de cadenas en formato Base64 de cada página.

    Example:
        >>> lista_base64 = pdf_a_base64("documento.pdf")
    """
    try:
    # Abre el documento PDF
        pdf_documento = fitz.open(ruta_pdf)
        lista_base64 = []

    # Itera sobre cada página del PDF
        for num_pagina in range(len(pdf_documento)):
        # Obtiene la página
            pagina = pdf_documento.load_page(num_pagina)
        # Convierte la página a una imagen
            pixmap = pagina.get_pixmap()
            imagen = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)

        # Convierte la imagen a un objeto BytesIO
            buffer = BytesIO()
            imagen.save(buffer, format="PNG")

            # Convierte la imagen a base64
            imagen_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            imagen_base64 = f"data:image/png;base64,{imagen_base64}"
            lista_base64.append(imagen_base64)

        return lista_base64

    except Exception as error:
        manejo_errores("pdf_a_base64", error_base=str(error))
        return []
