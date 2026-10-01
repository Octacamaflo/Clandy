import sqlite3


def conectar():
    return sqlite3.connect("clandy.db")


def crear_tablas():
    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            fecha TEXT NOT NULL,
            hora TEXT NOT NULL,
            presupuesto_minimo REAL NOT NULL,
            presupuesto_maximo REAL NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS participantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evento_id INTEGER NOT NULL,
            nombre TEXT NOT NULL,
            correo TEXT NOT NULL,
            telefono TEXT NOT NULL,
            presupuesto REAL NOT NULL,
            gustos TEXT,
            disgustos TEXT,
            hobbies TEXT,
            colores TEXT,
            tallas TEXT,
            deseos TEXT,
            FOREIGN KEY (evento_id) REFERENCES eventos(id)
        )
    """)

    conexion.commit()
    conexion.close()


def crear_evento():
    print("\n========== CREAR EVENTO ==========")

    nombre = input("Nombre del evento: ").strip()
    fecha = input("Fecha de revelación (AAAA-MM-DD): ").strip()
    hora = input("Hora de revelación (HH:MM): ").strip()

    minimo = float(input("Presupuesto mínimo: "))
    maximo = float(input("Presupuesto máximo: "))

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        INSERT INTO eventos
        (nombre, fecha, hora, presupuesto_minimo, presupuesto_maximo)
        VALUES (?, ?, ?, ?, ?)
    """, (nombre, fecha, hora, minimo, maximo))

    conexion.commit()

    id_evento = cursor.lastrowid

    conexion.close()

    print("\nEvento creado correctamente.")
    print(f"ID del evento: {id_evento}")


def ver_eventos():
    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id, nombre, fecha, hora,
               presupuesto_minimo, presupuesto_maximo
        FROM eventos
    """)

    eventos = cursor.fetchall()

    conexion.close()

    print("\n========== EVENTOS ==========")

    if not eventos:
        print("No existen eventos.")
        return

    for evento in eventos:
        print(f"\nID: {evento[0]}")
        print(f"Nombre: {evento[1]}")
        print(f"Revelación: {evento[2]} {evento[3]}")
        print(
            f"Presupuesto: "
            f"${evento[4]:,.0f} - ${evento[5]:,.0f}"
        )


def registrar_participante():
    print("\n========== REGISTRAR PARTICIPANTE ==========")

    ver_eventos()

    try:
        evento_id = int(input("\nID del evento: "))
    except ValueError:
        print("ID inválido.")
        return

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id, nombre, presupuesto_minimo, presupuesto_maximo
        FROM eventos
        WHERE id = ?
    """, (evento_id,))

    evento = cursor.fetchone()

    if evento is None:
        print("El evento no existe.")
        conexion.close()
        return

    nombre = input("Nombre: ").strip()
    correo = input("Correo: ").strip()
    telefono = input("WhatsApp / teléfono: ").strip()

    try:
        presupuesto = float(
            input("Presupuesto disponible: ")
        )
    except ValueError:
        print("Presupuesto inválido.")
        conexion.close()
        return

    if presupuesto < evento[2] or presupuesto > evento[3]:
        print(
            f"El presupuesto debe estar entre "
            f"${evento[2]:,.0f} y ${evento[3]:,.0f}."
        )
        conexion.close()
        return

    gustos = input(
        "Gustos (separados por coma): "
    ).strip()

    disgustos = input(
        "Disgustos (separados por coma): "
    ).strip()

    hobbies = input(
        "Hobbies (separados por coma): "
    ).strip()

    colores = input(
        "Colores preferidos (separados por coma): "
    ).strip()

    tallas = input(
        "Tallas (separadas por coma): "
    ).strip()

    deseos = input(
        "Lista de deseos (separados por coma): "
    ).strip()

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
            deseos
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
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
        deseos
    ))

    conexion.commit()

    participante_id = cursor.lastrowid

    conexion.close()

    print("\nParticipante registrado correctamente.")
    print(f"ID del participante: {participante_id}")


def ver_participantes():
    print("\n========== PARTICIPANTES ==========")

    ver_eventos()

    try:
        evento_id = int(input("\nID del evento: "))
    except ValueError:
        print("ID inválido.")
        return

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            id,
            nombre,
            correo,
            telefono,
            presupuesto,
            gustos,
            disgustos,
            hobbies,
            colores,
            tallas,
            deseos
        FROM participantes
        WHERE evento_id = ?
    """, (evento_id,))

    participantes = cursor.fetchall()

    conexion.close()

    if not participantes:
        print("\nNo hay participantes.")
        return

    for participante in participantes:
        print("\n--------------------------------")
        print(f"ID: {participante[0]}")
        print(f"Nombre: {participante[1]}")
        print(f"Correo: {participante[2]}")
        print(f"WhatsApp: {participante[3]}")
        print(f"Presupuesto: ${participante[4]:,.0f}")
        print(f"Gustos: {participante[5]}")
        print(f"Disgustos: {participante[6]}")
        print(f"Hobbies: {participante[7]}")
        print(f"Colores: {participante[8]}")
        print(f"Tallas: {participante[9]}")
        print(f"Deseos: {participante[10]}")


def menu():
    while True:
        print("\n================================")
        print("             CLANDY")
        print("================================")
        print("1. Crear evento")
        print("2. Ver eventos")
        print("3. Registrar participante")
        print("4. Ver participantes")
        print("5. Salir")
        print("================================")

        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            crear_evento()

        elif opcion == "2":
            ver_eventos()

        elif opcion == "3":
            registrar_participante()

        elif opcion == "4":
            ver_participantes()

        elif opcion == "5":
            print("\nGracias por usar Clandy.")
            break

        else:
            print("\nOpción no válida.")


crear_tablas()
menu()