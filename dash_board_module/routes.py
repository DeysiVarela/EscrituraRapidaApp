from flask import request, render_template,Response, redirect, current_app
from .utils import *
import json

def init_app(dash_board_bp):
    @dash_board_bp.route('/list')
    def main_listar_archivos():
        return listar_archivos(__file__,dash_board_bp.configuration.rutas_custom_no_permitidas)

    @dash_board_bp.route('/content')
    def main_ver_archivos():
        return ver_archivos()

    @dash_board_bp.route('/delete')
    def main_delete_archivos():
        return delete_archivos()

    @dash_board_bp.route('/login')
    def login():
        return render_template('Login.html',nombreProyecto = dash_board_bp.configuration.nombre_aplicacion,)

    @dash_board_bp.route('/')
    def dash_board():
        if token_validation(request.args.get('Token')):
            return render_template('DashBoard.html', 
                                   Token=create_token(Exp=3600), 
                                   nombreProyecto = dash_board_bp.configuration.nombre_aplicacion,
                                   Atajos=dash_board_bp.configuration.get_atajos())
        else:
            return redirect('/dashboard/login')
        
    @dash_board_bp.route('/authenticate', methods=['POST', 'GET'])
    def authenticate_user():
        user = request.form.get('user')
        password = request.form.get('password')
        if authenticate(user, password):
            token = create_token(Exp=10)
            return redirect(f'/dashboard?Token={token}')
        else:
            return redirect('/dashboard/login')
    
    @dash_board_bp.route('/dynamic_styles.css')
    def dynamic_styles():
        # Leer los colores desde el archivo JSON
        
        # Renderizar el CSS con los colores
        css = render_template('dynamic_styles.css', colors=dash_board_bp.configuration.estilos.json())
        return Response(css, mimetype='text/css')

