import smtplib
from datetime import datetime
import traceback
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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
                   estado_aparte: bool = False, error_base: any = "",
                   usar_traceback: bool = True, ruta_archivo_errores: str = "gmail_module/logs_errores_gmail.txt") -> dict | tuple:
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

        if estado_aparte:
            retorno = {"error": f"{error_base}{error_traceback_formateado}",
                       "funcion": nombre_funcion}, estado
            registro_logs_errores = f"{datetime.now()} [ERROR] ({estado}): {retorno[0]['error']} | Funcion: {nombre_funcion}\n"
        else:
            retorno = {"status": estado, "error": f"{error_base}{error_traceback_formateado}",
                       "funcion": nombre_funcion}
            registro_logs_errores = f"{datetime.now()} [ERROR] ({estado}): {retorno['error']} | Funcion: {nombre_funcion}\n"
        escribir_archivo(ruta_archivo_errores, registro_logs_errores, "a")
        return retorno
    except Exception as e:
        if estado_aparte:
            return {"error": f"Error al manejar errores: {e}"}, estado
        else:
            return {"status": estado, "error": f"Error al manejar errores: {e}"}


class Gmail:
    """
    Esta clase sirve para enviar correos electrónicos por gmail.
    """
    def __init__(self):
        self.usuario = "webappsconstructorabolivar@gmail.com"
        self.contrasenia = "bnlu yvww udps zjoc "
        self.remitente = "Tester"
        self.destinatario = "webappsconstructorabolivar@gmail.com"

    def logs_peticion(self,ruta, headers: dict, body: dict,respuesta:any) -> None:
        """
        Este método recibe los headers y el body de una petición, los formatea y los envía
        como parte de un correo electrónico.
        Args:
            ruta (str): Es la ruta de la peticion
            headers (dict): Encabezados de la petición.
            body (str): Cuerpo de la petición.
            respuesta (any): La respuesta
        """
        try:
            # Formatear headers y body
            headers_formateados = "\n".join(f"{k}: {v}" for k, v in headers.items())
            body = json.dumps(body,indent=4)

            if isinstance(respuesta,dict):
                respuesta_formateada = "\n".join(f"{k}: {v}" for k, v in respuesta.items())
            elif isinstance(respuesta,tuple):
                respuesta_formateada = "\n".join(f"{k}: {v}" for k, v in respuesta[0].items())
                respuesta_formateada += f"\nCodigo: {respuesta[1]}"
            else:
                respuesta_formateada = str(respuesta)

            # Enviar el mensaje
            mensaje = f"Headers:\n{headers_formateados}\n\nBody:\n{body}\nRespuesta:\n{respuesta_formateada}"
            self.enviar_email(f"Logs: {ruta}", mensaje)
        except Exception as e:
            manejo_errores(self.logs_requests.__qualname__, 500, False, e)
        
        
    def enviar_email(self, asunto: str, mensaje:str, destinatario: str = None):
        try:
            if destinatario is None:
                destinatario = self.destinatario
            destinatario = [destinatario]
            msg = MIMEMultipart()
            msg['From'] = self.remitente
            msg['To'] = ", ".join(destinatario)
            msg['Subject'] = asunto
            msg.attach(MIMEText(mensaje, 'plain'))

            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(self.usuario, self.contrasenia)
                server.send_message(msg)

            return {"status": 200, "datos": "Correo enviado correctamente"}

        except Exception as e:
            return manejo_errores(self.enviar_email.__qualname__,500,False,e)

gmail = Gmail()

if __name__ == "__main__":
    print(gmail.enviar_email("Test", "Este es un test"))