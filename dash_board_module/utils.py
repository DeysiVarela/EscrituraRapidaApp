from datetime import datetime
import os
import time
import math
import shutil
import jwt # 2.8.0
from datetime import datetime as Datetime
import traceback
from flask import request, jsonify, send_file, redirect, render_template


def read_file(file_path) -> str:
    return open(file_path, "r", encoding="utf-8").read()


def write_file(file_path, content, format: str = "w"):
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


def token_validation(Token: str, ReturnData: bool = False):
    SecretPassword = "hola"
    if not ReturnData:
        try:
            if jwt.decode(Token, SecretPassword, algorithms="HS256")["Exp"] < time.time():
                return False
        except:
            return False
        return True
    else:
        try:
            if jwt.decode(Token, SecretPassword, algorithms="HS256")["Exp"] < time.time():
                return False
        except:
            return False
        return jwt.decode(Token, SecretPassword, algorithms="HS256")


def create_token(Exp: int = 10) -> str:
    SecretPassword = "hola"
    Exp = float(time.time()) + Exp
    Token = jwt.encode({"Exp": Exp},
                       SecretPassword, algorithm="HS256",
                       headers={"exp": Datetime.now().timestamp() + 3600})
    return Token


def authenticate(user: str, password: int) -> bool:
    try:
        data = evaluador(read_file("dash_board_module/UsersPasswords.txt"))
        user_password = data.get(user)
        return user_password == password
    except:
        return False


def ver_archivos() -> str:
    if token_validation(request.args.get('token', '')):
        path = request.args.get('path', '')
        filename = request.args.get('file', '')
        file_path = f"{path}{filename}".replace("\\", "/").removeprefix("/")
        try:
            return send_file(file_path, as_attachment=True)
        except FileNotFoundError:
            return "Archivo no encontrado, vuelva a intentarlo"


def listar_archivos(absolute_path: str, custom_not_allowed_paths: list = []) -> str:
    try:
        if token_validation(request.args.get('token')):
            path_param = request.args.get('path', '/')
            absolute_path = absolute_path.replace(
                "\\", "/").removesuffix("/dash_board_module/routes.py")
            full_path = absolute_path + path_param

            elementos_eliminar = ["__pycache__/", ".git/", ".vscode", ".idea",
                                  ".gitignore", ".gitattributes", "Procfile", ".env", ".flaskenv", ".gitignore",
                                  ".gitattributes", ".DS_Store", "app.py", ".github/",
                                  "UsersPasswords.txt", "__pycache__", ".github", ".git",
                                  "~$cumentacion.docx", 'antenv/', 'antenv']
            elementos_eliminar.extend(custom_not_allowed_paths)

            if os.path.isdir(full_path):
                files = os.listdir(full_path)
                data_files = []
                for file in files:
                    if ".py" in str(file):
                        continue
                    elif "venv" in str(file):
                        continue
                    elif file in elementos_eliminar:
                        continue

                    time_modified = os.path.getmtime(f"{full_path}{file}")
                    time_modified = Datetime.fromtimestamp(time_modified)
                    time_modified = time_modified.strftime(
                        "%d/%m/%Y %I:%M:%S %p")
                    time_modified = time_modified.replace(
                        "AM", "a.m.").replace("PM", "p.m.")

                    data = {"Name": file + ("" if ("." in file) else "/"),
                            "Time": time_modified,
                            "Size": convert_size(full_path, file)}
                    data_files.append(data)

                data_files.sort(key=lambda x: x['Name'].lower())

                for i, file in enumerate(data_files):
                    data_files[i]["Index"] = f"{i + 1}"

                return jsonify(data_files)
    except Exception as e:
        print(
            f"Error: {str(e)} | {traceback.format_exc().splitlines()[-4:-2]}")
        return jsonify([])


def convert_size(full_path: str, file: str) -> str:
    file_path = full_path + file
    if os.path.isdir(file_path):
        return ""
    size_bytes = os.path.getsize(file_path)
    if size_bytes == 0:
        return "0 B"
    size_unit = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_unit[i]}"


def delete_archivos() -> str:
    if token_validation(request.args.get('token', '')):
        path = request.args.get('path', '')
        file_path = f"{path}".replace("\\", "/").removeprefix("/")
        try:
            if os.path.isdir(file_path):
                shutil.rmtree(file_path)
                return jsonify("Carpeta eliminada")
            else:
                os.remove(file_path)
            return jsonify("Archivo eliminado")
        except FileNotFoundError:
            return "Archivo no encontrado, vuelva a intentarlo"
        except Exception as e:
            return jsonify(f"Error: {str(e)} | {traceback.format_exc().splitlines()[-4:-2]}")
