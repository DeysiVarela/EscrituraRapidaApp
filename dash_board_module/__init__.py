from flask import Blueprint


def create_dash_board_module(app, configuration):
    dash_board_bp = Blueprint(
        'dash_board', __name__, template_folder='templates', static_folder='static')
    dash_board_bp.configuration = configuration
    from . import routes
    routes.init_app(dash_board_bp)
    app.register_blueprint(dash_board_bp, url_prefix='/dashboard')


class Configuration():
    def __init__(self):
        """
        Clase Configuration que contiene configuraciones generales del tablero.

        Attributes:
            nombre_aplicacion (str): El nombre de la aplicación.
            estilos (Estilos): Un objeto que contiene los estilos visuales para el tablero.
            atajos (list): Una lista de diccionarios que contiene accesos directos disponibles para el tablero. Cada diccionario incluye:
                - titulo (str): El título del acceso directo.
                - icono (str): El nombre del ícono.
                - ruta (str): La ruta del acceso directo.
                - esArchivo (bool, opcional): Un booleano que indica si el acceso directo es un archivo (por defecto es False).
            rutas_custom_no_permitidas (list): Una lista de rutas personalizadas que no están permitidas en el tablero.
            
        """
        self.estilos = Estilos()
        self.nombre_aplicacion = "Test Programa"
        self.atajos = [
            {
                "titulo": "Pacientes",
                "icono": "person",
                "ruta": "/Version1/Temp/Users/"
            },
            {
                "titulo": "Médicos",
                "icono": "medical_services",
                "ruta": "/Version1/Temp/Practitioners/"
            },
            {
                "titulo": "Documentación",
                "icono": "description",
                "ruta": "templates/Version1/documentacion.html",
                "esArchivo": True
            }
        ]
        self.estilos = Estilos()
        self.nombre_aplicacion = "Test Programa"
        self.atajos = [
                        {
                            "titulo": "Pacientes",
                            "icono": "person",
                            "ruta": "/Version1/Temp/Users/"
                        },
                        {
                            "titulo": "Médicos",
                            "icono": "medical_services",
                            "ruta": "/Version1/Temp/Practitioners/"
                        },
                        {
                            "titulo": "Documentación",
                            "icono": "description",
                            "ruta": "templates/Version1/documentacion.html",
                            "esArchivo": True
                        }
                    ]
        self.rutas_custom_no_permitidas = ['Prompts', "README.md"]
    def get_atajos(self):
        return str(self.atajos)


class Estilos():
    def __init__(self):
        """
        Clase Estilos que define los estilos visuales del tablero.
        # Color de fondo de la tabla al pasar el cursor, un tono verde oscuro.
        self.color_fondo_tabla_hover = "#2b8b4b"
        # Color del texto de la tabla al pasar el cursor, un tono blanco cremoso.
        self.color_texto_tabla_hover = "#FEFDF8"
        # Color del borde de la tabla, un tono marrón oscuro.
        self.color_borde_tabla = "#504741"
        # Color del texto de la tabla, igual al del borde.
        self.color_texto_tabla = "#504741"
        # Color de fondo del botón de ruta al pasar el cursor, un tono verde muy oscuro.
        self.color_fondo_boton_ruta_hover = "#095636"
        # Color de fondo del botón de ruta, un tono verde oscuro.
        self.color_fondo_boton_ruta = "#2b8b4b"
        # Color del texto del botón de ruta, un tono amarillo.
        self.color_boton_ruta = "#fddc53"
        # Color de fondo del botón de eliminar, un tono rosa fuerte.
        self.color_fondo_boton_eliminar = "#fd4973"
        # Color de fondo del botón de eliminar al pasar el cursor, un tono rosa más oscuro.
        self.color_fondo_boton_eliminar_hover = "#fa1a4f"
        # Color del texto del botón de eliminar, un tono blanco cremoso.
        self.color_boton_eliminar = "#FEFDF8"
        # Color de fondo de la página, un tono blanco cremoso.
        self.color_fondo_pagina = "#FEFDF8"
        # Color del texto de la ruta actual, un tono marrón oscuro.
        self.color_texto_ruta_actual = "#504741"
        # Color del texto de la ruta actual cuando está activa, un tono verde oscuro.
        self.color_texto_ruta_actual_activa = "#2b8b4b"
        # Color del texto del título, un tono marrón oscuro.
        self.color_texto_titulo = "#504741"
        # Color de fondo del login, un tono blanco cremoso.
        self.color_fondo_login = "#FEFDF8"
        # Color del texto del login, un tono marrón oscuro.
        self.color_texto_login = "#504741"
        # Color del botón del login, un tono verde oscuro.
        self.color_boton_login = "#2b8b4b"
        # Color del texto del botón del login, un tono blanco cremoso.
        self.color_texto_boton_login = "#FEFDF8"
        """
        self.color_fondo_tabla_hover = "#2b8b4b"
        self.color_texto_tabla_hover = "#FEFDF8"
        self.color_borde_tabla = "#504741"
        self.color_texto_tabla = "#504741"
        self.color_fondo_boton_ruta_hover = "#095636"
        self.color_fondo_boton_ruta = "#2b8b4b"
        self.color_boton_ruta = "#fddc53"
        self.color_fondo_boton_eliminar = "#fd4973"
        self.color_fondo_boton_eliminar_hover = "#fa1a4f"
        self.color_boton_eliminar = "#FEFDF8"
        self.color_fondo_pagina = "#FEFDF8"
        self.color_texto_ruta_actual = "#504741"
        self.color_texto_ruta_actual_activa = "#2b8b4b"
        self.color_texto_titulo = "#504741"
        self.color_fondo_login = "#FEFDF8"
        self.color_texto_login = "#504741"
        self.color_boton_login = "#2b8b4b"
        self.color_texto_boton_login = "#FEFDF8"
    def json(self):
        """
        Método que devuelve los estilos en formato JSON.
        Returns:
            dict: Un diccionario con los colores de los diferentes elementos del tablero.
        """
        return {
            "ColorFondoTablaHover": self.color_fondo_tabla_hover,
            "ColorTextoTablaHover": self.color_texto_tabla_hover,
            "ColorBordeTabla": self.color_borde_tabla,
            "ColorTextoTabla": self.color_texto_tabla,
            "ColorFondoBotonRutaHover": self.color_fondo_boton_ruta_hover,
            "ColorFondoBotonRuta": self.color_fondo_boton_ruta,
            "ColorBotonRuta": self.color_boton_ruta,
            "ColorFondoBotonEliminar": self.color_fondo_boton_eliminar,
            "ColorFondoBotonEliminarHover": self.color_fondo_boton_eliminar_hover,
            "ColorBotonEliminar": self.color_boton_eliminar,
            "ColorFondoPagina": self.color_fondo_pagina,
            "ColorTextoRutaActual": self.color_texto_ruta_actual,
            "ColorTextoRutaActualActiva": self.color_texto_ruta_actual_activa,
            "ColorTextoTitulo": self.color_texto_titulo,
            "ColorFondoLogin": self.color_fondo_login,
            "ColorTextoLogin": self.color_texto_login,
            "ColorBotonLogin": self.color_boton_login,
            "ColorTextoBotonLogin": self.color_texto_boton_login
        }
