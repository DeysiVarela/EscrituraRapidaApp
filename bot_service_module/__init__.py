#NOTE: Ultima actualiacion el 01-04-2025
from flask import Blueprint


def create_bot_service_module(app, configuration):
    bot_service_bp = Blueprint(
        'bot_service', __name__)
    bot_service_bp.configuration = configuration
    from . import routes
    routes.init_app(bot_service_bp)
    app.register_blueprint(bot_service_bp, url_prefix='/api')


class ConfiguracionBotService():
    def __init__(self, funcion_proyecto):
        """
        """
        self.funcion_proyecto = funcion_proyecto
