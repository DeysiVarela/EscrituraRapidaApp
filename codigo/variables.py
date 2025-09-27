import os
def cargar_errores() -> dict:
    """
    Esta funcion se encarga de cargar los errores de la aplicacion
    """
    try:
        with open("assets/lista_opcion_mensajes.json", "r", encoding="utf-8") as file:
            data = eval(file.read())
    except:
        data = {}
    return data

def cargar_prompts() -> dict:
    
    """
    Carga y procesa los prompts desde un archivo de texto y los organiza en un diccionario.

    Returns:
        dict: Un diccionario que contiene categorías de prompts y sus respectivos prompts.

    Example:
        >>> PROMPTS = cargar_prompts()
    """
    try:
        propts = {}
        for tipo in os.listdir("prompts"):
            if not os.path.isdir(f"prompts/{tipo}"):
                continue
            propts[tipo] = {}
            for prompt in os.listdir(f"prompts/{tipo}"):
                with open(f"prompts/{tipo}/{prompt}", "r", encoding="utf-8") as file:
                    propts[tipo][prompt.removesuffix(".txt")] = file.read()
        return propts
    except Exception as e:
        return {}           
 


PROMPTS = cargar_prompts()
LISTA_MENSAJES = cargar_errores()