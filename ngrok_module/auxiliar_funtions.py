from datetime import datetime  # Import datetime to use the current timestamp
def read_file(file_path) -> str:
    """
    Lee el contenido de un archivo de texto.

    Args:
        file_path (str): La ruta del archivo a leer.

    Returns:
        str: El contenido del archivo.

    Example:
        >>> content = read_file("archivo.txt")
    """
    return open(file_path, "r", encoding="utf-8").read()


def write_file(file_path, content, format: str = "w"):
    """
    Escribe contenido en un archivo de texto.

    Args:
        file_path (str): La ruta del archivo en el que se escribirá el contenido.
        content (str): El contenido que se escribirá en el archivo.
        format (str): El modo de escritura del archivo (opcional, por defecto es "w").

    Example:
        >>> write_file("archivo.txt", "Este es el contenido que se escribirá en el archivo.")
    """
    try:
        with open(file_path, format, encoding="utf-8") as f:
            f.write(str(content))

    except Exception as e:
        return {"error": f"Error al escribir el archivo {e}"}


def print_consola(texto: str):
    try:
        timestamped_text = f"{datetime.now()} - {texto}\n"
        write_file("Consola.txt", timestamped_text, format="a")
    except Exception as e:
        print("Error al escribir en Consola.txt:", e)
