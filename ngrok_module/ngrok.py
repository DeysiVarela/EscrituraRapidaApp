from ngrok_module.auxiliar_funtions import read_file, write_file, print_consola
from threading import Thread
import os
import time


def ngrok(port, dominio, ngrok_domain):
    try:
        time.sleep(2)
        if not os.path.exists("consola.txt"):
            write_file("consola.txt", "")
        consola = read_file("consola.txt")
        if "run_ngrok" in consola:
            return 0
        write_file("consola.txt", "run_ngrok")
        if dominio:
            try:
                # Use relative path with backslashes for Windows
                comando = f".\\ngrok_module\\ngrok.exe http --domain {ngrok_domain} {port}"
                print_consola("\n" + comando)
                os.system(comando)
            except:
                # Use relative path with backslashes for Windows
                comando = f".\\ngrok_module\\ngrok.exe http --url={ngrok_domain} {port}"
                print_consola("\n" + comando)
                os.system(comando)
        else:
            # Use relative path with backslashes for Windows
            comando = f".\\ngrok_module\\ngrok.exe http {port}"
            print_consola("\n" + comando)
            os.system(comando)

    except Exception as e:
        print("Error al iniciar ngrok:", e)


def run_ngrok(port, dominio=False, ngrok_domain=""):
    """
    Inicia un hilo para ejecutar el comando ngrok en un puerto específico.

    Args:
        port (int): El puerto que se utilizará para ejecutar ngrok.
        dominio (bool): Indicador de si se debe utilizar un dominio personalizado o no (opcional, por defecto es True).
        ngrok_domain (str): El dominio personalizado que se utilizará si `dominio` es False (opcional, por defecto es una cadena vacía).

    Example:
        >>> run_ngrok(8080, dominio=False)
    """
    Thread(target=ngrok, args=(port, dominio, ngrok_domain)).start()
