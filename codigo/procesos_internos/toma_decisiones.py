from codigo.conexiones_externas.modelos_ia import modelos_ia
from codigo.variables import PROMPTS
from codigo.funciones_auxiliares import manejo_errores


class TomaDecisiones:
    def __init__(self):
        pass

    def cambio_bot(self, conversacion: list, bot_actual: str) -> bool:
        try:

            if bot_actual == "bot_ia":
                nuevo_bot = "cambio_a_pva"

            else:
                nuevo_bot = "cambio_a_bot_ia"
                
            pregunta = "Debo cambiar de bot?"

            while True:
                respuesta_modelo = modelos_ia.llm.manejar_chat(PROMPTS["toma_decisiones"][nuevo_bot],
                                                            conversacion,pregunta)
                if respuesta_modelo["status"] != 200:
                    return manejo_errores(self.cambio_bot.__qualname__,
                                        respuesta_modelo["status"],
                                        error_base=respuesta_modelo["error"],
                                        usar_traceback=False)
                texto_respuesta = respuesta_modelo["message"]
                if "true" in texto_respuesta.lower():
                    return {"status": 200, "cambio_bot": True}

                elif "false" in texto_respuesta.lower():
                    return {"status": 200, "cambio_bot": False}

        except Exception as e:
            return manejo_errores(self.cambio_bot.__qualname__,
                                  500,
                                  error_base=e)

toma_decisiones = TomaDecisiones()