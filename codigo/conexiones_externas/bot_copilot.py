import os
import requests
import time
class BotCopilot:
    def __init__(self):
        self.base_url = os.getenv("COPILOT_URL")
        self.direct_line_url = "https://directline.botframework.com/v3/directline/conversations"
        self.headers = {"Content-Type": "application/json"}

    def crear_token(self):
        response = requests.get(self.base_url)
        return response.json().get("token")

    def refrescar_token(self, token):
        self.headers["Authorization"] = f"Bearer {token}"
        response = requests.get(self.base_url, headers=self.headers)
        return response.json().get("token", token)
    
    def iniciar_conversacion(self, token):
        self.headers["Authorization"] = f"Bearer {token}"
        response = requests.post(self.direct_line_url, headers=self.headers)
        return response.json().get("conversationId")

    def enviar_mensaje(self, token, conversacion_id, mensaje="", lenguaje="es"):
        self.headers["Authorization"] = f"Bearer {token}"
        url = f"{self.direct_line_url}/{conversacion_id}/activities"
        data = {
            "type": "message",
            "locale": "es-MX" if lenguaje == "es" else "en-US",
            "from": {"id": "Usuario1", "role": "user"},
            "text": mensaje,
            "textFormat": "plain"
        }
        response = requests.post(url, headers=self.headers, json=data)
        status = "id" in response.json()
        return status

    def obtener_mensajes(self, token, conversacion_id):
        url = f"{self.direct_line_url}/{conversacion_id}/activities"
        self.headers["Authorization"] = f"Bearer {token}"
        while True:
            response = requests.get(url, headers=self.headers)
            data = response.json()
            if response.status_code != 200:
                break
            last_activity = data["activities"][-1]
            if last_activity.get("valueType") == "DynamicPlanFinished":
                break
            if "role" not in last_activity["from"]:
                continue
            if last_activity["from"]["role"] == "bot" and "text" in last_activity:
                data["activities"] = [last_activity, None]
                break
            time.sleep(1)
        return data
    
    def llamar(self,mensaje: str):
        token = bot_copilot.crear_token()
        conversacion_id = bot_copilot.iniciar_conversacion(token)
        estado = bot_copilot.enviar_mensaje(token, conversacion_id, mensaje, "es")
        if not estado:
            return "No se pudo procesar la solicitud"
        mensajes = bot_copilot.obtener_mensajes(token, conversacion_id)
        return mensajes["activities"][-2]["text"]
        


bot_copilot = BotCopilot()
if __name__ == "__main__":        

    while True:
        mensaje = input("Mensaje: ")
        print(bot_copilot.llamar(mensaje))

