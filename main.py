import sqlite3
import secrets
import string
import random
import os
from datetime import datetime

from flask import Flask, render_template, request, redirect

from flask_mail import Mail, Message


app = Flask(__name__)

URL_CLANDY = "https://clandy-279a.onrender.com"

app.config["MAIL_SERVER"] = "smtp-relay.brevo.com"
app.config["MAIL_PORT"] = 2525
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_SENDER")

mail = Mail(app)

def conectar():
    return sqlite3.connect("clandy.db")

def enviar_correo(destinatario, asunto, contenido):

    mensaje = Message(
        subject=asunto,
        sender=app.config["MAIL_DEFAULT_SENDER"],
        recipients=[destinatario]
    )

    mensaje.body = contenido

    mail.send(mensaje)

def actualizar_base_datos():
    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            fecha TEXT NOT NULL,
            hora TEXT NOT NULL,
            presupuesto_minimo REAL NOT NULL,
            presupuesto_maximo REAL NOT NULL,
            codigo TEXT,
            codigo_admin TEXT,
            estado TEXT DEFAULT 'abierto'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS participantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evento_id INTEGER NOT NULL,
            nombre TEXT NOT NULL,
            correo TEXT NOT NULL,
            telefono TEXT,
            presupuesto REAL,
            gustos TEXT,
            disgustos TEXT,
            hobbies TEXT,
            colores TEXT,
            tallas TEXT,
            deseos TEXT,
            codigo_acceso TEXT,
            revelo INTEGER DEFAULT 0,
            FOREIGN KEY (evento_id) REFERENCES eventos(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS restricciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evento_id INTEGER NOT NULL,
            participante_id INTEGER NOT NULL,
            restringido_id INTEGER NOT NULL,
            FOREIGN KEY (evento_id) REFERENCES eventos(id),
            FOREIGN KEY (participante_id) REFERENCES participantes(id),
            FOREIGN KEY (restringido_id) REFERENCES participantes(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS asignaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evento_id INTEGER NOT NULL,
            participante_id INTEGER NOT NULL,
            asignado_id INTEGER NOT NULL,
            FOREIGN KEY (evento_id) REFERENCES eventos(id),
            FOREIGN KEY (participante_id) REFERENCES participantes(id),
            FOREIGN KEY (asignado_id) REFERENCES participantes(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mensajes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evento_id INTEGER NOT NULL,
            remitente_id INTEGER NOT NULL,
            destinatario_id INTEGER NOT NULL,
            mensaje TEXT NOT NULL,
            fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (evento_id) REFERENCES eventos(id),
            FOREIGN KEY (remitente_id) REFERENCES participantes(id),
            FOREIGN KEY (destinatario_id) REFERENCES participantes(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pistas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evento_id INTEGER NOT NULL,
            remitente_id INTEGER NOT NULL,
            destinatario_id INTEGER NOT NULL,
            pista TEXT NOT NULL,
            fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (evento_id) REFERENCES eventos(id),
            FOREIGN KEY (remitente_id) REFERENCES participantes(id),
            FOREIGN KEY (destinatario_id) REFERENCES participantes(id)
        )
    """)

    columnas_eventos = [
        fila[1]
        for fila in cursor.execute(
            "PRAGMA table_info(eventos)"
        )
    ]

    if "codigo" not in columnas_eventos:
        cursor.execute("""
            ALTER TABLE eventos
            ADD COLUMN codigo TEXT
        """)

    if "codigo_admin" not in columnas_eventos:
        cursor.execute("""
            ALTER TABLE eventos
            ADD COLUMN codigo_admin TEXT
        """)

    if "estado" not in columnas_eventos:
        cursor.execute("""
            ALTER TABLE eventos
            ADD COLUMN estado TEXT DEFAULT 'abierto'
        """)

    if "presupuesto_minimo" not in columnas_eventos:
        cursor.execute("""
            ALTER TABLE eventos
            ADD COLUMN presupuesto_minimo REAL
        """)

    if "presupuesto_maximo" not in columnas_eventos:
        cursor.execute("""
            ALTER TABLE eventos
            ADD COLUMN presupuesto_maximo REAL
        """)

    columnas_participantes = [
        fila[1]
        for fila in cursor.execute(
            "PRAGMA table_info(participantes)"
        )
    ]

    if "codigo_acceso" not in columnas_participantes:
        cursor.execute("""
            ALTER TABLE participantes
            ADD COLUMN codigo_acceso TEXT
        """)

    if "revelo" not in columnas_participantes:
        cursor.execute("""
            ALTER TABLE participantes
            ADD COLUMN revelo INTEGER DEFAULT 0
        """)

    conexion.commit()
    conexion.close()

def generar_codigo():
    caracteres = string.ascii_uppercase + string.digits

    return "".join(
        secrets.choice(caracteres)
        for _ in range(6)
    )


@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/crear-evento", methods=["GET", "POST"])
def crear_evento():

    if request.method == "POST":

        nombre = request.form["nombre"].strip()
        fecha = request.form["fecha"]
        hora = request.form["hora"]

        minimo = float(request.form["minimo"])
        maximo = float(request.form["maximo"])

        codigo = generar_codigo()
        codigo_admin = generar_codigo()

        conexion = conectar()
        cursor = conexion.cursor()

        cursor.execute("""
            INSERT INTO eventos (
                nombre,
                fecha,
                hora,
                presupuesto_minimo,
                presupuesto_maximo,
                codigo,
                codigo_admin
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            nombre,
            fecha,
            hora,
            minimo,
            maximo,
            codigo,
            codigo_admin
        ))

        conexion.commit()

        id_evento = cursor.lastrowid

        conexion.close()

        enlace = f"/unirse/{codigo}"

        return render_template(
            "evento_creado.html",
            nombre=nombre,
            codigo=codigo,
            codigo_admin=codigo_admin,
            enlace=enlace,
            id_evento=id_evento
        )

    return render_template("crear_evento.html")


@app.route("/unirse/<codigo>", methods=["GET", "POST"])
def unirse(codigo):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            id,
            nombre,
            fecha,
            hora,
            presupuesto_minimo,
            presupuesto_maximo,
            codigo,
            codigo_admin,
            estado
        FROM eventos
        WHERE codigo = ?
    """, (codigo,))

    evento = cursor.fetchone()

    if evento is None:

        conexion.close()

        return """
        <h1>Evento no encontrado</h1>

        <p>
            El enlace de invitación no es válido.
        </p>

        <a href="/">
            Volver a Clandy
        </a>
        """

    if evento[8] == "cerrado":

        conexion.close()

        return """
        <h1>Inscripciones cerradas</h1>

        <p>
            Este evento ya no acepta nuevos participantes.
        </p>

        <a href="/">
            Volver a Clandy
        </a>
        """

    if request.method == "POST":

        nombre = request.form["nombre"].strip()
        correo = request.form["correo"].strip().lower()
        telefono = request.form["telefono"].strip()

        presupuesto = float(
            request.form["presupuesto"]
        )

        gustos = request.form["gustos"].strip()
        disgustos = request.form["disgustos"].strip()
        hobbies = request.form["hobbies"].strip()
        colores = request.form["colores"].strip()
        tallas = request.form["tallas"].strip()
        deseos = request.form["deseos"].strip()

        cursor.execute("""
            SELECT id
            FROM participantes
            WHERE evento_id = ?
            AND correo = ?
        """, (
            evento[0],
            correo
        ))

        participante_existente = cursor.fetchone()

        if participante_existente:

            conexion.close()

            return """
            <h1>Registro duplicado</h1>

            <p>
                Este correo ya está registrado
                en este evento.
            </p>

            <a href="/">
                Volver a Clandy
            </a>
            """

        if (
            presupuesto < evento[4]
            or presupuesto > evento[5]
        ):

            conexion.close()

            return """
            <h1>Presupuesto no válido</h1>

            <p>
                El presupuesto está fuera del rango
                permitido para este evento.
            </p>

            <a href="/">
                Volver a Clandy
            </a>
            """

        codigo_acceso = generar_codigo()

        cursor.execute("""
            INSERT INTO participantes (
                evento_id,
                nombre,
                correo,
                telefono,
                presupuesto,
                gustos,
                disgustos,
                hobbies,
                colores,
                tallas,
                deseos,
                codigo_acceso
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            evento[0],
            nombre,
            correo,
            telefono,
            presupuesto,
            gustos,
            disgustos,
            hobbies,
            colores,
            tallas,
            deseos,
            codigo_acceso
        ))

        conexion.commit()
        
        enlace_privado = (
            f"{URL_CLANDY}/mi-espacio/{codigo_acceso}"
        )        
        
        try:

            enviar_correo(
                correo,
                "🎁 Registro confirmado en Clandy",
                f"""
Hola {nombre}.

Tu inscripción en el evento "{evento[1]}" fue registrada correctamente.

Tu código de acceso privado es:

{codigo_acceso}

Puedes entrar a tu espacio privado desde:

{enlace_privado}

Guarda este correo. Lo necesitarás para acceder a tu espacio de Clandy.

Durante el período secreto podrás consultar información de tu amigo secreto, recibir y enviar pistas y utilizar el chat privado.

¡Mucha suerte! 🎁

Clandy
"""
            )

        except Exception as error:

            print("No fue posible enviar el correo:")
            print(error)
        
        conexion.close()

        enlace_privado =(
            f"{URL_CLANDY}/mi-espacio/{codigo_acceso}"
        )
        
        return render_template(
            "registro_exitoso.html",
            nombre=nombre,
            codigo_acceso=codigo_acceso,
            enlace_privado=enlace_privado
        )

    conexion.close()

    return render_template(
        "unirse.html",
        evento=evento
    )

@app.route("/recuperar-acceso", methods=["GET", "POST"])
def recuperar_acceso():

    mensaje = None

    if request.method == "POST":

        correo = request.form["correo"].strip()

        conexion = conectar()
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT
                p.nombre,
                p.codigo_acceso,
                e.nombre
            FROM participantes p
            JOIN eventos e
                ON p.evento_id = e.id
            WHERE p.correo = ?
        """, (correo,))

        participantes = cursor.fetchall()

        conexion.close()

        if participantes:

            for nombre, codigo_acceso, nombre_evento in participantes:

                enlace = (
                    f"{URL_CLANDY}"
                    f"mi-espacio/{codigo_acceso}"
                )

                try:

                    enviar_correo(
                        correo,
                        "🔐 Recuperación de acceso - Clandy",
                        f"""
Hola {nombre}.

Has solicitado recuperar tu acceso a Clandy.

Evento:
{nombre_evento}

Tu enlace privado es:

{enlace}

Guarda este correo para volver a entrar a tu espacio privado.

Tu amigo secreto y sus datos permanecen protegidos.

Clandy 🎁
"""
                    )

                except Exception as error:

                    print("No se pudo enviar el correo:")
                    print(error)

            mensaje = (
                "Si encontramos una cuenta asociada a ese correo, "
                "te hemos enviado un enlace de acceso."
            )

        else:

            mensaje = (
                "Si encontramos una cuenta asociada a ese correo, "
                "te hemos enviado un enlace de acceso."
            )

    return render_template(
        "recuperar_acceso.html",
        mensaje=mensaje
    )


@app.route("/mi-espacio/<codigo_acceso>")
def mi_espacio(codigo_acceso):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            p.id,
            p.evento_id,
            p.nombre,
            p.correo,
            p.telefono,
            p.presupuesto,
            p.gustos,
            p.disgustos,
            p.hobbies,
            p.colores,
            p.tallas,
            p.deseos,
            p.codigo_acceso,
            e.nombre,
            e.fecha,
            e.hora,
            e.estado
        FROM participantes p
        JOIN eventos e
            ON p.evento_id = e.id
        WHERE p.codigo_acceso = ?
    """, (codigo_acceso,))

    participante = cursor.fetchone()

    if participante is None:

        conexion.close()

        return """
        <h1>Código no válido</h1>

        <p>
            El código de acceso no existe.
        </p>

        <a href="/">
            Volver a Clandy
        </a>
        """

    asignado = None
    revelacion = False

    if participante[16] == "sorteado":

        cursor.execute("""
            SELECT
                p.id,
                p.nombre,
                p.gustos,
                p.disgustos,
                p.hobbies,
                p.colores,
                p.tallas,
                p.deseos
            FROM asignaciones a
            JOIN participantes p
                ON a.asignado_id = p.id
            WHERE a.evento_id = ?
            AND a.participante_id = ?
        """, (
            participante[1],
            participante[0]
        ))

        asignado = cursor.fetchone()

        try:
            fecha_revelacion = datetime.strptime(
                f"{participante[14]} {participante[15]}",
                "%Y-%m-%d %H:%M"
            )

            revelacion = datetime.now() >= fecha_revelacion

        except ValueError:
            revelacion = False

    conexion.close()

    return render_template(
        "mi_espacio.html",
        participante=participante,
        asignado=asignado,
        revelacion=revelacion
    )

@app.route("/entrar-organizador", methods=["GET", "POST"])
def entrar_organizador():

    if request.method == "POST":

        codigo_admin = request.form[
            "codigo_admin"
        ].strip().upper()

        conexion = conectar()
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT id
            FROM eventos
            WHERE codigo_admin = ?
        """, (codigo_admin,))

        evento = cursor.fetchone()

        conexion.close()

        if evento is None:

            return render_template(
                "entrar_organizador.html",
                error="El código del organizador no es válido."
            )

        return redirect(f"/panel/{codigo_admin}")
    
    return render_template(
        "entrar_organizador.html"
    )


@app.route("/entrar-invitacion", methods=["GET", "POST"])
def entrar_invitacion():

    if request.method == "POST":

        codigo = request.form[
            "codigo"
        ].strip().upper()

        conexion = conectar()
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT id
            FROM eventos
            WHERE codigo = ?
        """, (codigo,))

        evento = cursor.fetchone()

        conexion.close()

        if evento is None:

            return render_template(
                "entrar_invitacion.html",
                error="El código de invitación no es válido."
            )

        return redirect(f"/unirse/{codigo}")

    return render_template(
        "entrar_invitacion.html"
    )


@app.route("/cerrar-inscripciones/<codigo_admin>", methods=["POST"])
def cerrar_inscripciones(codigo_admin):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        UPDATE eventos
        SET estado = 'cerrado'
        WHERE codigo_admin = ?
        AND estado = 'abierto'
    """, (codigo_admin,))

    conexion.commit()

    conexion.close()

    return redirect(f"/panel/{codigo_admin}")

@app.route("/agregar-restriccion/<codigo_admin>", methods=["POST"])
def agregar_restriccion(codigo_admin):

    participante_id = int(
        request.form["participante_id"]
    )

    restringido_id = int(
        request.form["restringido_id"]
    )

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id
        FROM eventos
        WHERE codigo_admin = ?
    """, (codigo_admin,))

    evento = cursor.fetchone()

    if evento is None:

        conexion.close()

        return """
        <h1>Evento no encontrado</h1>

        <a href="/">
            Volver a Clandy
        </a>
        """

    evento_id = evento[0]

    if participante_id == restringido_id:

        conexion.close()

        return redirect(
            f"/panel/{codigo_admin}"
        )

    cursor.execute("""
        SELECT id
        FROM participantes
        WHERE id = ?
        AND evento_id = ?
    """, (
        participante_id,
        evento_id
    ))

    participante = cursor.fetchone()

    cursor.execute("""
        SELECT id
        FROM participantes
        WHERE id = ?
        AND evento_id = ?
    """, (
        restringido_id,
        evento_id
    ))

    restringido = cursor.fetchone()

    if participante is None or restringido is None:

        conexion.close()

        return redirect(
            f"/panel/{codigo_admin}"
        )

    cursor.execute("""
        SELECT id
        FROM restricciones
        WHERE evento_id = ?
        AND participante_id = ?
        AND restringido_id = ?
    """, (
        evento_id,
        participante_id,
        restringido_id
    ))

    existente = cursor.fetchone()

    if existente is None:

        cursor.execute("""
            INSERT INTO restricciones (
                evento_id,
                participante_id,
                restringido_id
            )
            VALUES (?, ?, ?)
        """, (
            evento_id,
            participante_id,
            restringido_id
        ))

        conexion.close()

    return redirect(
        f"/panel/{codigo_admin}"
    )

def realizar_sorteo(evento_id):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id
        FROM participantes
        WHERE evento_id = ?
    """, (evento_id,))

    participantes = [
        fila[0]
        for fila in cursor.fetchall()
    ]

    if len(participantes) < 2:
        conexion.close()
        return False

    cursor.execute("""
        SELECT
            participante_id,
            restringido_id
        FROM restricciones
        WHERE evento_id = ?
    """, (evento_id,))

    restricciones = {}

    for participante_id, restringido_id in cursor.fetchall():

        if participante_id not in restricciones:
            restricciones[participante_id] = set()

        restricciones[participante_id].add(
            restringido_id
        )

    for _ in range(10000):

        disponibles = participantes.copy()
        random.shuffle(disponibles)

        asignaciones = {}
        valido = True

        for participante_id in participantes:

            candidatos = [
                persona
                for persona in disponibles
                if persona != participante_id
                and persona not in restricciones.get(
                    participante_id,
                    set()
                )
            ]

            if not candidatos:
                valido = False
                break

            asignado = random.choice(candidatos)

            asignaciones[participante_id] = asignado
            disponibles.remove(asignado)

        if valido and not disponibles:

            cursor.execute("""
                DELETE FROM asignaciones
                WHERE evento_id = ?
            """, (evento_id,))

            for participante_id, asignado_id in asignaciones.items():

                cursor.execute("""
                    INSERT INTO asignaciones (
                        evento_id,
                        participante_id,
                        asignado_id
                    )
                    VALUES (?, ?, ?)
                """, (
                    evento_id,
                    participante_id,
                    asignado_id
                ))

            cursor.execute("""
                UPDATE eventos
                SET estado = 'sorteado'
                WHERE id = ?
            """, (evento_id,))

            conexion.commit()

            cursor.execute("""
                SELECT
                    p.correo,
                    p.nombre
                FROM participantes p
                WHERE p.evento_id = ?
            """, (evento_id,))

            participantes_correo = cursor.fetchall()

            conexion.close()

            for correo, nombre in participantes_correo:

                try:

                    enviar_correo(
                        correo,
                        "🎁 Tu amigo secreto ya fue asignado",
                        f"""
Hola {nombre}.

El sorteo de tu evento ya fue realizado.

Tu amigo secreto ya está asignado y puedes entrar a tu espacio privado para consultar sus preferencias.

La identidad permanecerá oculta hasta la fecha oficial de revelación.

¡Mucha suerte! 🎁

Clandy
"""
                    )

                except Exception as error:

                    print(
                        f"No se pudo enviar el correo a {correo}:"
                    )

                    print(error)

            return True

    conexion.close()

    return False

@app.route("/realizar-sorteo/<codigo_admin>", methods=["POST"])
def realizar_sorteo_ruta(codigo_admin):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id, estado
        FROM eventos
        WHERE codigo_admin = ?
    """, (codigo_admin,))

    evento = cursor.fetchone()

    conexion.close()

    if evento is None:

        return redirect("/")

    if evento[1] != "cerrado":

        return redirect(
            f"/panel/{codigo_admin}"
        )

    resultado = realizar_sorteo(evento[0])

    return redirect(
        f"/panel/{codigo_admin}"
    )

@app.route("/panel/<codigo_admin>")
def panel(codigo_admin):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT *
        FROM eventos
        WHERE codigo_admin = ?
    """, (codigo_admin,))

    evento = cursor.fetchone()

    if evento is None:

        conexion.close()

        return """
        <h1>Acceso denegado</h1>

        <p>
            El código del organizador no es válido.
        </p>

        <a href="/">
            Volver a Clandy
        </a>
        """

    cursor.execute("""
        SELECT *
        FROM participantes
        WHERE evento_id = ?
    """, (evento[0],))

    participantes = cursor.fetchall()

    cursor.execute("""
    SELECT
        restricciones.participante_id,
        restricciones.restringido_id,
        p1.nombre,
        p2.nombre
    FROM restricciones
    JOIN participantes p1
        ON restricciones.participante_id = p1.id
    JOIN participantes p2
        ON restricciones.restringido_id = p2.id
    WHERE restricciones.evento_id = ?
    """, (evento[0],))

    restricciones = cursor.fetchall()

    conexion.close()

    return render_template(
        "panel.html",
        evento=evento,
        participantes=participantes,
        restricciones=restricciones
    )


actualizar_base_datos()

@app.route("/mi-espacio/<codigo_acceso>/chat", methods=["GET", "POST"])
def chat_secreto(codigo_acceso):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            id,
            evento_id,
            nombre,
            codigo_acceso
        FROM participantes
        WHERE codigo_acceso = ?
    """, (codigo_acceso,))

    participante = cursor.fetchone()

    if participante is None:
        conexion.close()
        return "Código de acceso no válido."

    participante_id = participante[0]
    evento_id = participante[1]

    cursor.execute("""
        SELECT asignado_id
        FROM asignaciones
        WHERE evento_id = ?
        AND participante_id = ?
    """, (
        evento_id,
        participante_id
    ))

    asignacion = cursor.fetchone()

    if asignacion is None:
        conexion.close()

        return """
        <h1>Chat secreto</h1>
        <p>El sorteo todavía no ha sido realizado.</p>
        """

    asignado_id = asignacion[0]

    if request.method == "POST":

        mensaje = request.form["mensaje"].strip()

        if mensaje:

            cursor.execute("""
                INSERT INTO mensajes (
                    evento_id,
                    remitente_id,
                    destinatario_id,
                    mensaje
                )
                VALUES (?, ?, ?, ?)
            """, (
                evento_id,
                participante_id,
                asignado_id,
                mensaje
            ))

            conexion.commit()

    cursor.execute("""
        SELECT
            remitente_id,
            mensaje,
            fecha
        FROM mensajes
        WHERE evento_id = ?
        AND (
            (remitente_id = ?
             AND destinatario_id = ?)
            OR
            (remitente_id = ?
             AND destinatario_id = ?)
        )
        ORDER BY fecha ASC
    """, (
        evento_id,
        participante_id,
        asignado_id,
        asignado_id,
        participante_id
    ))

    mensajes = cursor.fetchall()

    conexion.close()

    return render_template(
        "chat.html",
        participante=participante,
        mensajes=mensajes
    )

@app.route("/mi-espacio/<codigo_acceso>/pistas", methods=["GET", "POST"])
def pistas(codigo_acceso):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            id,
            evento_id,
            nombre,
            codigo_acceso
        FROM participantes
        WHERE codigo_acceso = ?
    """, (codigo_acceso,))

    participante = cursor.fetchone()

    if participante is None:
        conexion.close()
        return "Código de acceso no válido."

    participante_id = participante[0]
    evento_id = participante[1]

    cursor.execute("""
        SELECT asignado_id
        FROM asignaciones
        WHERE evento_id = ?
        AND participante_id = ?
    """, (
        evento_id,
        participante_id
    ))

    asignacion = cursor.fetchone()

    if asignacion is None:
        conexion.close()

        return """
        <h1>Pistas</h1>
        <p>El sorteo todavía no ha sido realizado.</p>
        """

    asignado_id = asignacion[0]

    if request.method == "POST":

        pista = request.form["pista"].strip()

        if pista:

            cursor.execute("""
                INSERT INTO pistas (
                    evento_id,
                    remitente_id,
                    destinatario_id,
                    pista
                )
                VALUES (?, ?, ?, ?)
            """, (
                evento_id,
                participante_id,
                asignado_id,
                pista
            ))

            conexion.commit()

    cursor.execute("""
        SELECT
            pista,
            fecha
        FROM pistas
        WHERE evento_id = ?
        AND destinatario_id = ?
        ORDER BY fecha ASC
    """, (
        evento_id,
        participante_id
    ))

    pistas_recibidas = cursor.fetchall()

    conexion.close()

    return render_template(
        "pistas.html",
        participante=participante,
        pistas=pistas_recibidas
    )

@app.route("/mi-espacio/<codigo_acceso>/revelar", methods=["POST"])
def revelar_amigo(codigo_acceso):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            p.id,
            p.nombre,
            p.evento_id,
            p.revelo,
            p.codigo_acceso,
            e.fecha,
            e.hora,
            e.estado
        FROM participantes p
        JOIN eventos e
            ON p.evento_id = e.id
        WHERE p.codigo_acceso = ?
    """, (codigo_acceso,))

    participante = cursor.fetchone()

    if not participante:

        conexion.close()

        return "Acceso no válido."

    participante_id = participante[0]
    evento_id = participante[2]
    revelo = participante[3]
    codigo_acceso = participante[4]
    fecha = participante[5]
    hora = participante[6]
    estado = participante[7]

    if estado != "sorteado":

        conexion.close()

        return "El sorteo todavía no está disponible."

    fecha_revelacion = datetime.strptime(
        f"{fecha} {hora}",
        "%Y-%m-%d %H:%M"
    )

    if datetime.now() < fecha_revelacion:

        conexion.close()

        return "Todavía no es la fecha de revelación."

    cursor.execute("""
        SELECT
            p.nombre,
            p.gustos,
            p.disgustos,
            p.hobbies,
            p.colores,
            p.tallas,
            p.deseos
        FROM asignaciones a
        JOIN participantes p
            ON a.asignado_id = p.id
        WHERE a.evento_id = ?
        AND a.participante_id = ?
    """, (evento_id, participante_id))

    asignado = cursor.fetchone()

    if not asignado:

        conexion.close()

        return "No se encontró tu asignación."

    if revelo == 0:

        cursor.execute("""
            UPDATE participantes
            SET revelo = 1
            WHERE id = ?
        """, (participante_id,))

        conexion.commit()

    conexion.close()

    return render_template(
        "revelacion.html",
        participante=participante,
        asignado=asignado
    )

actualizar_base_datos()

if __name__ == "__main__":
    app.run(debug=True)