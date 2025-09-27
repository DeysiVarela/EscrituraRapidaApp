import re

def evaluador(texto, lista=False, make_list=False):
    try:
        return eval(texto)
    except:
        texto = eliminador_texto(texto, lista)
        try:
            return eval(texto)
        except:
            return [] if lista else {}


def eliminador_texto(texto, lista: bool):
    indice1 = texto.find("{") if not lista else texto.find("[")
    indice2 = texto.rfind("}") if not lista else texto.rfind("]")
    return texto[indice1 if indice1 != -1 else 0: indice2+1 if indice2 != -1 else None]


def parseador_de_mensajes(texto):
    """
    Convierte un mensaje con un formato específico en una lista de tuplas que representan los recursos y sus tipos MIME.

    Args:
        texto (str): El mensaje que contiene los recursos.

    Returns:
        list: Una lista de tuplas, cada una conteniendo el tipo MIME y el recurso, representado como una cadena.

    Example:
    Input: 
    >>> '''
        Claro mira aca hay una imagen sin texto alternativo:
        <RECURSO-IMAGEN>https://www.example.com/imagen.png</RECURSO-IMAGEN>
        Y aqui hay una imagen con texto alternativo:
        <RECURSO-IMAGEN>https://www.example.com/imagen.png ; texto_alternativo</RECURSO-IMAGEN>
        Por supuesto aqui tienes un archivo PDF:
        RECURSO-PDF>https://www.example.com/archivo.pdf</RECURSO-PDF>
        Y por último, un video:
        <RECURSO-VIDEO>https://www.example.com/video.mp4</RECURSO-VIDEO>
        '''

    Output:
    >>> [
            ("text", "Claro mira aca hay una imagen sin texto alternativo:"),
            ("image/png", "https://www.example.com/imagen.png"),
            ("text", "Y aqui hay una imagen con texto alternativo:"),
            ("image/png", "https://www.example.com/imagen.png", "texto_alternativo"),
            ("text", "Por supuesto aqui tienes un archivo PDF:"),
            ("application/pdf", "https://www.example.com/archivo.pdf"),
            ("text", "Y por último, un video:"),
            ("video/mp4", "https://www.example.com/video.mp4"),
        ]
    """
    # Expresiones regulares para encontrar los recursos
    regex_imagen = r"<RECURSO-IMAGEN>(.*?)</RECURSO-IMAGEN>"
    regex_pdf = r"<RECURSO-PDF>(.*?)</RECURSO-PDF>"
    regex_video = r"<RECURSO-VIDEO>(.*?)</RECURSO-VIDEO>"

    # Lista para almacenar los bloques de texto y HTML
    resultado = []

    # Dividir el texto en partes usando las expresiones regulares
    partes = []
    start = 0
    while True:
        # Find the next match for any of the defined regular expressions
        match = re.search(f"({regex_imagen}|{regex_pdf}|{regex_video})", texto[start:])
        if not match:
            break

        # Extract and append the text before the matched resource
        end = start + match.start()
        text_part = texto[start:end].strip()
        if text_part:
            partes.append(text_part)

        # Append the matched resource itself
        partes.append(match.group(0))

        # Move the start pointer past the current match
        start += match.end()

    # Append any remaining text after the last match
    remaining_text = texto[start:].strip()
    if remaining_text:
        partes.append(remaining_text)

    for parte in partes:
        if re.match(regex_imagen, parte):
            # Si es una imagen, agregar la URL de la imagen
            contenido = re.search(regex_imagen, parte).group(1)
            url = contenido.split(';')[0].strip()
            texto_alternativo = contenido.split(';')[1].strip() if ';' in contenido else None
            mime_type = "image/{}".format(url.split('.')[-1])
            if texto_alternativo:
                resultado.append((mime_type, url, texto_alternativo))
            else:
                resultado.append((mime_type, url))
        elif re.match(regex_pdf, parte):
            # Si es un PDF, agregar la URL del PDF
            url = re.search(regex_pdf, parte).group(1)
            resultado.append(("application/pdf", url))
        elif re.match(regex_video, parte):
            # Si es un video, agregar la URL del video
            url = re.search(regex_video, parte).group(1)
            resultado.append(("video/mp4", url))
        else:
            # Si no es un recurso, agregar el texto normal
            if parte.strip():
                resultado.append(("text", parte.strip()))

    return resultado  

if __name__ == "__main__":
    # Ejemplo de uso
    texto = '''
        Claro mira aca hay una imagen sin texto alternativo:
        <RECURSO-IMAGEN>https://www.example.com/imagen.png</RECURSO-IMAGEN>
        Y aqui hay una imagen con texto alternativo:
        <RECURSO-IMAGEN>https://www.example.com/imagen.png ; texto_alternativo</RECURSO-IMAGEN>
        Por supuesto aqui tienes un archivo PDF:
        <RECURSO-PDF>https://www.example.com/archivo.pdf</RECURSO-PDF>
        Y por último, un video:
        <RECURSO-VIDEO>https://www.example.com/video.mp4</RECURSO-VIDEO>
    '''
    print(parseador_de_mensajes(texto))  
    