from flask import Flask, jsonify, request  # , url_for, redirect, session, render_template
from flask_mysqldb import MySQL
from flask_cors import CORS
from config import config

# from flask_login import login_user, current_user, logout_user, LoginManager
# from datetime import datetime
# from flask_mail import Message, mail


app = Flask(__name__)
CORS(app, resources={r"/dashboard/*": {"origins": "http://localhost:4200"}})
conexion = MySQL(app)


@app.errorhandler(Exception)
def error_handler(error):
    message = str(error) if app.config["DEBUG"] else "Ocurrió un error interno. Contacte al administrador."
    return jsonify({"mensaje": message, "exito": False}), 50


@app.route("/dashboard/all", methods=["GET"])
def listar_usuarios():
    try:
        cursor = conexion.connection.cursor()
        sql = "SELECT * FROM usuarios ORDER BY tiempo_registro DESC"
        cursor.execute(sql)
        datos = cursor.fetchall()

        usuarios = []
        for fila in datos:
            usuario = {
                "ID": fila[0],
                "nombre_usuario": fila[1],
                "tipo_cuenta": fila[2],
                "tiempo_registro": fila[3]  # .strftime('%Y-%m-%d %H:%M:%S')
            }
            usuarios.append(usuario)

        cursor.close()
        return jsonify({'usuarios': usuarios, 'mensaje': 'Usuarios listados', "exito": True})

    except Exception as ex:
        return jsonify({"mensaje": "Error al conectar con la DB: {}".format(ex), 'exito': False})


# Función para obtener un usuario por su correo
def leer_usuario_bd(correo):
    try:
        cursor = conexion.connection.cursor()
        sql = "SELECT ID, nombre_usuario, tipo_cuenta, tiempo_registro FROM usuarios WHERE nombre_usuario = %s"
        cursor.execute(sql, (correo,))
        datos = cursor.fetchone()
        if datos != None:
            usuario = {
                'ID': datos[0],
                'nombre_usuario': datos[1],
                'tipo_cuenta': datos[2],
                'tiempo_registro': datos[3].strftime('%Y-%m-%d %H:%M:%S')
            }
            return usuario
        else:
            return None
    except Exception as ex:
        raise ex


# Leer un usuario específico por su nombre de usuario
@app.route('/dashboard/usuarios/<correo>', methods=['GET'])
def leer_usuario(correo):
    try:
        usuario = leer_usuario_bd(correo)
        if usuario != None:
            return jsonify({'usuario': usuario, 'mensaje': "Usuario encontrado.", 'exito': True})
        else:
            return jsonify({'mensaje': "Usuario no encontrado.", 'exito': False})
    except Exception as ex:
        return jsonify({'mensaje': "Error al obtener los datos del usuario.", 'exito': False})


# Registrar un nuevo usuario
@app.route('/dashboard/usuarios', methods=['POST'])
def registrar_usuario():
    try:
        correo = request.json['correo']
        usuario = leer_usuario_bd(correo)
        if usuario != None:
            return jsonify({'mensaje': "El usuario ya existe, no se puede duplicar.", 'exito': False})
        else:
            cursor = conexion.connection.cursor()
            sql = """INSERT INTO usuarios (nombre_usuario, contraseña, tipo_cuenta, tiempo_registro)
            VALUES (%s, %s, %s, NOW())"""
            cursor.execute(sql, (
                request.json['nombre_usuario'],
                request.json['contrasena'],
                request.json['tipo_cuenta']
            ))
            conexion.connection.commit()
            return jsonify({'mensaje': "Usuario registrado exitosamente.", 'exito': True})
    except Exception as ex:
        return jsonify({'mensaje': "Error al registrar el usuario.", 'exito': False})


# Actualizar los datos de un usuario
@app.route('/dashboard/usuarios/<correo>', methods=['PUT'])
def actualizar_usuario(correo):
    try:
        usuario = leer_usuario_bd(correo)
        if usuario != None:
            cursor = conexion.connection.cursor()
            sql = """UPDATE usuarios SET nombre_usuario = %s, contraseña = %s, tipo_cuenta = %s WHERE nombre_usuario = %s"""
            cursor.execute(sql, (
                request.json['nombre_usuario'],
                request.json['contraseña'],
                request.json['tipo_cuenta'],
                correo
            ))
            conexion.connection.commit()
            return jsonify({'mensaje': "Usuario actualizado.", 'exito': True})
        else:
            return jsonify({'mensaje': "Usuario no encontrado.", 'exito': False})
    except Exception as ex:
        return jsonify({'mensaje': "Error al actualizar el usuario.", 'exito': False})


@app.route("/dashboard/prueba", methods=["GET"])
def prueba():
    try:
        cursor = conexion.connection.cursor()
        sql = "SELECT * FROM usuario_login"
        cursor.execute(sql)
        datos = cursor.fetchall()

        usuarios = []
        for fila in datos:
            usuario = {
                "correo": fila[0],
                "contraseña": fila[1]
            }
            usuarios.append(usuario)

        cursor.close()
        return jsonify({'usuarios': usuarios, 'mensaje': 'Usuarios listados', "exito": True})

    except Exception as ex:
        return jsonify({"mensaje": f"Error al conectar con la DB: {str(ex)}", 'exito': False})


# Leer datos de un usuario
def leer_datos(correo):
    try:
        cursor = conexion.connection.cursor()
        sql = "SELECT * FROM usuario_login WHERE correo = %s"
        cursor.execute(sql, (correo,))
        datos = cursor.fetchone()

        if datos:
            usuario = {'correo': datos[0], 'contrasena': datos[1]}
            return usuario
        else:
            return None

    except Exception as ex:
        raise Exception(f"Error al leer datos del usuario: {str(ex)}")


# Ruta para probar login
@app.route('/dashboard/login/<correo>', methods=['GET'])
def login_usuario(correo):
    try:
        usuario = leer_datos(correo)
        if usuario:
            return jsonify({'usuario': usuario, 'mensaje': "Usuario encontrado.", 'exito': True})
        else:
            return jsonify({'mensaje': "Usuario no encontrado.", 'exito': False})
    except Exception as ex:
        return jsonify({'mensaje': f"Error en la ruta de login: {str(ex)}", 'exito': False})


# Ruta para el login

@app.route('/dashboard/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        nombre = data['correo']
        contrasena = data['contrasena']

        cursor = conexion.connection.cursor()
        sql = "SELECT correo, puesto FROM usuario_login WHERE correo = %s AND contrasena = %s"
        cursor.execute(sql, (nombre, contrasena))

        datos = cursor.fetchone()
        if datos is not None:
            usuario = {
                'correo': datos[0],
                'puesto': datos[1],
            }
            return jsonify({
                'usuario': usuario,
                'mensaje': "Login exitoso",
                'exito': True
            })
        else:
            return jsonify({
                'mensaje': "Usuario o contraseña incorrectos",
                'exito': False
            })

    except Exception as ex:
        return jsonify({
            'mensaje': "Error: {}".format(ex),
            'exito': False
        })

def pagina_no_encontrada(error):
    return jsonify({"mensaje": "{}".format(app.url_map), 'exito': False})


if __name__ == "__main__":
    app.config.from_object(config['development'])
    app.register_error_handler(404, pagina_no_encontrada)
    app.run()
