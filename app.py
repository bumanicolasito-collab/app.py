import pg8000.dbapi
from flask import Flask, request, render_template_string, redirect, url_for, session, Response
import json
import base64

app = Flask(__name__)
app.secret_key = "Institucion_namandu_seguridad" 

DB_HOST = "localhost"
DB_NAME = "institucion_db" 
DB_USER = "postgres" 
DB_PASS = "1523" 
DB_PORT = 5432

admin_data = {"clave": "1234"}

def obtener_conexion():
    return pg8000.dbapi.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT)

def inicializar_bd():
    try:
        conn = obtener_conexion()
        cur = conn.cursor()
        
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS alumno_materias (
                id SERIAL PRIMARY KEY,
                alumno_id INTEGER REFERENCES estudiantes(id) ON DELETE CASCADE,
                materia VARCHAR(100) NOT NULL,
                UNIQUE(alumno_id, materia)
            );
        """)

        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS docente_materias (
                id SERIAL PRIMARY KEY,
                docente_id INTEGER REFERENCES docentes(id) ON DELETE CASCADE,
                materia VARCHAR(100) NOT NULL,
                UNIQUE(docente_id, materia)
            );
        """)

        
        cur.execute("""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='estudiantes' AND column_name='curso') THEN
                    ALTER TABLE estudiantes ADD COLUMN curso VARCHAR(50) DEFAULT '1er Curso';
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='materias' AND column_name='curso') THEN
                    ALTER TABLE materias ADD COLUMN curso VARCHAR(50) DEFAULT '1er Curso';
                END IF;
            END $$;
        """)

        cur.execute("""
            DO $$ 
            BEGIN 
                ALTER TABLE estudiantes ALTER COLUMN matricula DROP NOT NULL;
            EXCEPTION WHEN OTHERS THEN NULL;
            END $$;
        """)
        cur.execute("UPDATE estudiantes SET matricula = NULL WHERE matricula = '' OR matricula = 'None';")

        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error inicializando BD: {e}")

inicializar_bd()

CURSOS_DISPONIBLES = [
    "1er Curso",
    "2do Curso",
    "3er Curso",
    "4to Curso",
    "5to Curso"
]

TEMA_CSS = """
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        :root { --brand-color: #ccff00; --bg-dark: #0a0a0a; --card-dark: #141414; --text-light: #ffffff; --text-muted: #888888; }
        * { box-sizing: border-box; }
        body { font-family: 'Inter', 'Segoe UI', sans-serif; background-color: var(--bg-dark); color: var(--text-light); margin: 0; padding: 0; overflow-x: hidden; }
        
        .brand-card { background: var(--card-dark); border-radius: 20px; padding: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); border: 1px solid #222; }
        input, select, textarea { width: 100%; padding: 14px; margin: 8px 0; background: #1a1a1a; border: 1px solid #333; border-radius: 12px; color: white; outline: none; transition: 0.3s; font-family: inherit; font-size: 14px; }
        input[type="file"] { padding: 10px; background: #222; color: var(--text-muted); cursor: pointer; }
        input:focus, select:focus, textarea:focus { border-color: var(--brand-color); }
        select option { background: #141414; color: white; }
        button { background: var(--brand-color); color: #000; border: none; padding: 14px; width: 100%; border-radius: 30px; cursor: pointer; font-weight: 800; font-size: 13px; text-transform: uppercase; letter-spacing: 1px; transition: 0.3s; margin-top: 10px; }
        button:hover { background: #b3e600; transform: scale(1.01); }

        .btn-editar { background: #333; color: #fff; padding: 6px 10px; font-size: 11px; border-radius: 8px; cursor: pointer; text-decoration: none; border: 1px solid #555; margin: 2px; display: inline-block; }
        .btn-editar:hover { background: var(--brand-color); color: #000; border-color: var(--brand-color); }
        .btn-eliminar { background: #ff3366; color: #fff; padding: 6px 10px; font-size: 11px; border-radius: 8px; cursor: pointer; text-decoration: none; border: 1px solid #ff3366; margin: 2px; display: inline-block; }
        .btn-eliminar:hover { background: #cc0033; }
        .btn-materias { background: #00b4db; color: #000; padding: 6px 10px; font-size: 11px; border-radius: 8px; cursor: pointer; text-decoration: none; font-weight: bold; border: 1px solid #00b4db; margin: 2px; display: inline-block; }

        h2, h3 { margin: 0; font-weight: 800; }
        a { color: var(--brand-color); text-decoration: none; font-weight: bold; }
        a:hover { color: #fff; }

        .header { padding: 20px 40px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #222; }
        .header-izq { display: flex; align-items: center; gap: 15px; }
        .top-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; }
        .layout { display: grid; grid-template-columns: 1fr 2fr; gap: 20px; }
        
        .tabla-scroll { width: 100%; overflow-x: auto; border-radius: 15px; border: 1px solid #222; }
        table { width: 100%; border-collapse: separate; border-spacing: 0; background: var(--card-dark); min-width: 450px; }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #222; font-size: 13px; }
        th { background: #111; color: var(--text-muted); font-size: 11px; text-transform: uppercase; letter-spacing: 1px; }
        tr:hover td { background: #1a1a1a; }

        .logout-btn { border: 1px solid var(--brand-color); padding: 7px 15px; border-radius: 20px; font-size: 11px; margin-left: 10px; }
        .foto-perfil { width: 100px; height: 100px; border-radius: 50%; object-fit: cover; border: 3px solid var(--brand-color); margin-bottom: 15px; background-color: #222; }
        .foto-mini { width: 32px; height: 32px; border-radius: 50%; object-fit: cover; border: 1px solid var(--brand-color); vertical-align: middle; margin-right: 8px; background-color: #222;}
        .home-icon { font-size: 20px; text-decoration: none; }

        .menu-btn-trigger { background: var(--card-dark); border: 1px solid var(--brand-color); color: var(--brand-color); border-radius: 10px; width: 40px; height: 40px; font-size: 18px; display: inline-flex; align-items: center; justify-content: center; cursor: pointer; transition: 0.2s; }
        .menu-btn-trigger:hover { background: #1a1a1a; transform: scale(1.05); }
        .nav-overlay { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.7); z-index: 999; display: none; }
        .nav-drawer { position: fixed; top: 0; left: -280px; width: 260px; height: 100vh; background: #111; z-index: 1000; transition: 0.3s; padding: 30px 20px 20px 20px; border-right: 1px solid #222; display: flex; flex-direction: column; gap: 10px; }
        .nav-drawer.abierto { left: 0; }
        .nav-drawer a { padding: 12px 15px; background: #181818; border-radius: 10px; font-size: 13px; display: block; border: 1px solid #282828; color: #fff; }
        .nav-drawer a:hover { border-color: var(--brand-color); color: var(--brand-color); }

        .alerta-error { background: rgba(255, 51, 102, 0.15); border: 1px solid #ff3366; color: #ff3366; padding: 12px; border-radius: 10px; margin-bottom: 15px; font-size: 13px; text-align: center; }

        @media (max-width: 768px) {
            body { padding: 12px !important; }
            .header { padding: 10px 0 !important; flex-direction: row !important; justify-content: space-between !important; align-items: center !important; flex-wrap: wrap; gap: 10px; }
            .header > div:last-child { display: flex !important; align-items: center; gap: 8px; }
            .header-izq h2 { font-size: 16px !important; }
            .logout-btn { padding: 5px 10px !important; font-size: 10px !important; margin-left: 0 !important; }
            .top-bar { flex-direction: row !important; align-items: center !important; }
            .top-bar h2 { font-size: 16px !important; }
            .layout { grid-template-columns: 1fr !important; gap: 15px !important; }
            .grid-menu { grid-template-columns: 1fr !important; padding: 15px 0 !important; gap: 12px !important; }
            .grafico-container { margin: 15px 0 !important; grid-template-columns: 1fr !important; }
            .brand-card { padding: 15px !important; border-radius: 15px !important; }
            .login-box { width: 100% !important; max-width: 320px; }
            .foto-perfil { width: 85px !important; height: 85px !important; }
        }
    </style>

    <div class="nav-overlay" id="overlay" onclick="toggleMenu()"></div>
    <div class="nav-drawer" id="drawer">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 10px;">
            <span style="font-size: 11px; color: var(--text-muted); text-transform: uppercase;">Menú Principal</span>
            <span onclick="toggleMenu()" style="cursor:pointer; color:#ff3366; font-weight:bold; font-size:16px;">✕</span>
        </div>
        {% if session.get('rol') == 'admin' %}
            <a href="/inicio">🏠 Inicio</a>
            <a href="/docentes">👨‍🏫 Docentes</a>
            <a href="/estudiantes">👨‍🎓 Estudiantes</a>
            <a href="/materias_admin">📚 Materias</a>
            <a href="/calificaciones">📝 Calificaciones</a>
            <a href="/asistencia">📅 Asistencia</a>
            <a href="/tablon">📢 Tablón</a>
            <a href="/reportes">📄 Reportes</a>
        {% elif session.get('rol') == 'docente' %}
            <a href="/inicio">🏠 Inicio</a>
            <a href="/calificaciones">📝 Cargar Notas</a>
            <a href="/asistencia">📅 Asistencia</a>
            <a href="/tablon">📢 Tablón</a>
        {% elif session.get('rol') == 'alumno' %}
            <a href="/inicio">🏠 Mi Portal</a>
            <a href="/tablon">📢 Tablón</a>
        {% endif %}
        <a href="/perfil">⚙️ Mi Perfil</a>
        <a href="/logout" style="color: #ff3366; border-color: #ff3366; margin-top: auto;">Cerrar Sesión</a>
    </div>

    <script>
        function toggleMenu() {
            const drawer = document.getElementById('drawer');
            const overlay = document.getElementById('overlay');
            if (drawer.classList.contains('abierto')) {
                drawer.classList.remove('abierto');
                overlay.style.display = 'none';
            } else {
                drawer.classList.add('abierto');
                overlay.style.display = 'block';
            }
        }
    </script>
"""

HTML_LOGIN = f"""
<!DOCTYPE html>
<html>
<head><title>Institución Ñamandu - Acceso</title>{TEMA_CSS}
<style>body {{ height: 100vh; display: flex; justify-content: center; align-items: center; }} .login-box {{ width: 320px; text-align: center; }} .estado {{ font-size: 12px; padding: 8px; margin-bottom: 20px; border-radius: 20px; background: rgba(204, 255, 0, 0.1); color: var(--brand-color); border: 1px solid var(--brand-color); display: inline-block; }} .error {{ color: #ff3366; font-size: 13px; margin-bottom: 15px; font-weight: bold; background: rgba(255, 51, 102, 0.1); padding: 10px; border-radius: 10px; }}</style>
</head>
<body>
    <div class="brand-card login-box">
        <h2 style="font-size: 28px; margin-bottom: 5px;">Institución Ñamandu</h2>
        <p style="color: var(--text-muted); font-size: 14px; margin-bottom: 20px;">Portal Académico</p>
        <div class="estado">● Sistema Online</div>
        {{% if mensaje_error %}} <div class="error">{{{{ mensaje_error }}}}</div> {{% endif %}}
        <form method="POST">
            <input type="text" name="usuario" placeholder="Admin o N° de Cédula" required>
            <input type="password" name="clave" placeholder="Contraseña" required>
            <button type="submit">Ingresar</button>
        </form>
    </div>
</body>
</html>
"""

HTML_PERFIL = f"""
<!DOCTYPE html>
<html>
<head><title>Editar Perfil - Institución Ñamandu</title>{TEMA_CSS}<style>body {{ padding: 40px; max-width: 600px; margin: auto; text-align: center; }}</style></head>
<body>
    <div class="top-bar">
        <div class="header-izq">
            <div class="menu-btn-trigger" onclick="toggleMenu()" title="Menú">☰</div>
            <a href="/inicio" class="home-icon" title="Ir al Panel Principal">🏠</a>
            <h2 style="margin:0;">Editar Perfil</h2>
        </div>
        <a href="#" onclick="history.back();">← Volver</a>
    </div>
    <div class="brand-card">
        {{% if mensaje %}} <div style="color: var(--brand-color); margin-bottom: 15px; font-weight:bold;">{{{{ mensaje }}}}</div> {{% endif %}}
        <form method="POST" enctype="multipart/form-data">
            {{% if rol == 'admin' %}}
                <h3>Seguridad de Administrador</h3>
                <input type="password" name="nueva_clave" placeholder="Nueva Contraseña" required>
            {{% else %}}
                {{% if usuario_datos[1] %}}
                    <img src="data:image/jpeg;base64,{{{{ usuario_datos[1] }}}}" class="foto-perfil">
                {{% else %}}
                    <div class="foto-perfil" style="display:inline-block; line-height:100px; color:#888;">Sin Foto</div>
                {{% endif %}}
                <br>
                <label style="color: var(--text-muted); font-size: 12px; display:block; text-align:left; margin-left:2%;">Actualizar Foto (Opcional):</label>
                <input type="file" name="foto" accept="image/*">
                
                <label style="color: var(--text-muted); font-size: 12px; display:block; text-align:left; margin-left:2%; margin-top:10px;">N° de Cédula:</label>
                <input type="text" name="cedula" value="{{{{ usuario_datos[0] }}}}" readonly style="background:#222; color:#777;">
                
                <label style="color: var(--text-muted); font-size: 12px; display:block; text-align:left; margin-left:2%; margin-top:10px;">Fecha de Nacimiento:</label>
                <input type="date" name="anio_nacimiento" value="{{{{ usuario_datos[2] }}}}">
                
                {{% if rol == 'alumno' %}}
                    <label style="color: var(--text-muted); font-size: 12px; display:block; text-align:left; margin-left:2%; margin-top:10px;">Carrera o Bachillerato:</label>
                    <input type="text" name="carrera" value="{{{{ usuario_datos[3] }}}}" placeholder="Carrera">
                {{% endif %}}
                
                <hr style="border:0; border-top: 1px solid #333; margin:20px 0;">
                <label style="color: var(--text-muted); font-size: 12px; display:block; text-align:left; margin-left:2%;">Cambiar Contraseña:</label>
                <input type="password" name="nueva_clave" placeholder="Nueva Contraseña">
            {{% endif %}}
            <button type="submit">Actualizar Perfil</button>
        </form>
    </div>
</body>
</html>
"""

HTML_DASHBOARD_ADMIN = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Institución Ñamandu - Panel Admin</title>
    {TEMA_CSS}
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .grid-menu {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 20px; padding: 40px; padding-bottom: 20px; }}
        .modulo-btn {{ background: var(--card-dark); padding: 25px; border-radius: 20px; text-align: left; border: 1px solid #222; transition: 0.3s; display: block; }}
        .modulo-btn:hover {{ border-color: var(--brand-color); transform: translateY(-5px); background: #1a1a1a; }}
        .icon-circle {{ width: 35px; height: 35px; background: var(--brand-color); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-bottom: 12px; color: #000; font-weight: bold; font-size: 18px; }}
        .grafico-container {{ margin: 0 40px 40px 40px; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="header-izq">
            <div class="menu-btn-trigger" onclick="toggleMenu()" title="Menú">☰</div>
            <h2>Panel Administrativo</h2>
        </div>
        <div>
            <a href="/perfil" style="color: var(--text-light);">Editar Perfil</a>
            <a href="/logout" class="logout-btn">CERRAR SESIÓN</a>
        </div>
    </div>
    <div class="grid-menu">
        <a href="/docentes" class="modulo-btn"><div class="icon-circle">D</div><h3>Docentes</h3><p style="color: var(--text-muted); font-size: 13px;">Asignar profesores y materias</p></a>
        <a href="/estudiantes" class="modulo-btn"><div class="icon-circle">E</div><h3>Estudiantes</h3><p style="color: var(--text-muted); font-size: 13px;">Matrículas y cursos</p></a>
        <a href="/materias_admin" class="modulo-btn"><div class="icon-circle">M</div><h3>Materias</h3><p style="color: var(--text-muted); font-size: 13px;">Cursos y profesores</p></a>
        <a href="/calificaciones" class="modulo-btn"><div class="icon-circle">C</div><h3>Calificaciones</h3><p style="color: var(--text-muted); font-size: 13px;">Actas de notas globales</p></a>
        <a href="/asistencia" class="modulo-btn"><div class="icon-circle">A</div><h3>Asistencia</h3><p style="color: var(--text-muted); font-size: 13px;">Control diario de asistencia</p></a>
        <a href="/tablon" class="modulo-btn"><div class="icon-circle">T</div><h3>Tablón de Materias</h3><p style="color: var(--text-muted); font-size: 13px;">Anuncios y avisos</p></a>
        <a href="/reportes" class="modulo-btn"><div class="icon-circle">R</div><h3>Reportes</h3><p style="color: var(--text-muted); font-size: 13px;">Generar actas oficiales</p></a>
    </div>
    <div class="grafico-container" style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px; margin: 0 40px 40px 40px;">
        <div class="brand-card">
            <h3 style="text-align: center; margin-bottom: 15px; font-size: 16px;">Promedio de Rendimiento por Materia</h3>
            <div style="position: relative; height: 230px; width: 100%;">
                <canvas id="graficoPromedios"></canvas>
            </div>
        </div>

        <div class="brand-card">
            <h3 style="text-align: center; margin-bottom: 15px; font-size: 16px;">Balance de Asistencia</h3>
            <div style="position: relative; height: 230px; width: 100%;">
                <canvas id="graficoAsistencia"></canvas>
            </div>
        </div>
    </div>

    <script>
        document.addEventListener("DOMContentLoaded", function() {{
            const ctxProm = document.getElementById('graficoPromedios');
            if (ctxProm) {{
                new Chart(ctxProm, {{
                    type: 'bar',
                    data: {{
                        labels: {{{{ labels_materias|safe }}}},
                        datasets: [{{
                            label: 'Nota Promedio (1 - 5)',
                            data: {{{{ promedios_materias|safe }}}},
                            backgroundColor: '#ccff00',
                            borderRadius: 8
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{ legend: {{ display: false }} }},
                        scales: {{
                            y: {{ beginAtZero: true, max: 5, grid: {{ color: '#222' }}, ticks: {{ color: '#fff', stepSize: 1 }} }},
                            x: {{ grid: {{ display: false }}, ticks: {{ color: '#fff' }} }}
                        }}
                    }}
                }});
            }}

            const ctxAsis = document.getElementById('graficoAsistencia');
            if (ctxAsis) {{
                new Chart(ctxAsis, {{
                    type: 'doughnut',
                    data: {{
                        labels: ['Presentes', 'Ausentes', 'Tardanzas'],
                        datasets: [{{
                            data: {{{{ asistencia_data|safe }}}},
                            backgroundColor: ['#ccff00', '#ff3366', '#ff9900'],
                            borderColor: '#141414',
                            borderWidth: 3
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{ position: 'bottom', labels: {{ color: '#fff', font: {{ size: 11 }} }} }}
                        }}
                    }}
                }});
            }}
        }});
    </script>
</body>
</html>
"""

HTML_DASHBOARD_DOCENTE = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Portal Docente - Institución Ñamandu</title>
    {TEMA_CSS}
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .grid-menu {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 25px; padding: 40px; }}
        .modulo-btn {{ background: var(--card-dark); padding: 30px; border-radius: 20px; text-align: left; border: 1px solid #222; transition: 0.3s; display: block; }}
        .modulo-btn:hover {{ border-color: var(--brand-color); transform: translateY(-5px); background: #1a1a1a; }}
        .icon-circle {{ width: 40px; height: 40px; background: var(--brand-color); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-bottom: 15px; color: #000; font-weight: bold; font-size: 20px; }}
        .grafico-container {{ margin: 0 40px 40px 40px; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="header-izq">
            <div class="menu-btn-trigger" onclick="toggleMenu()" title="Menú">☰</div>
            <h2 style="display:flex; align-items:center;">
                {{% if foto %}}<img src="data:image/jpeg;base64,{{{{ foto }}}}" class="foto-mini">{{% endif %}}
                Profesor/a: {{{{ nombre_docente }}}}
            </h2>
        </div>
        <div><a href="/perfil" style="color: var(--text-light);">Editar Perfil</a><a href="/logout" class="logout-btn">CERRAR SESIÓN</a></div>
    </div>
    <div class="grid-menu">
        <a href="/calificaciones" class="modulo-btn"><div class="icon-circle">C</div><h3>Cargar Notas</h3><p style="color: var(--text-muted); font-size: 14px;">Módulo de calificaciones</p></a>
        <a href="/asistencia" class="modulo-btn"><div class="icon-circle">A</div><h3>Tomar Asistencia</h3><p style="color: var(--text-muted); font-size: 14px;">Registro diario</p></a>
        <a href="/tablon" class="modulo-btn"><div class="icon-circle">T</div><h3>Tablón de Materias</h3><p style="color: var(--text-muted); font-size: 14px;">Publicar avisos a alumnos</p></a>
    </div>
    <div class="brand-card grafico-container">
        <h3 style="text-align: center; margin-bottom: 20px;">Promedio de Calificaciones por Materia</h3>
        <div style="position: relative; height: 260px; width: 100%;">
            <canvas id="graficoDocente"></canvas>
        </div>
    </div>
    <script>
        document.addEventListener("DOMContentLoaded", function() {{
            const ctx = document.getElementById('graficoDocente');
            if (ctx) {{
                const labels = {{{{ mat_json|safe }}}};
                const data = {{{{ prom_json|safe }}}};
                new Chart(ctx, {{
                    type: 'bar',
                    data: {{
                        labels: labels.length > 0 ? labels : ['Sin Materias'],
                        datasets: [{{
                            label: 'Promedio',
                            data: data.length > 0 ? data : [0],
                            backgroundColor: '#ccff00',
                            borderRadius: 8
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{ legend: {{ display: false }} }},
                        scales: {{
                            y: {{ beginAtZero: true, max: 5, grid: {{ color: '#222' }}, ticks: {{ color: '#fff', stepSize: 1 }} }},
                            x: {{ grid: {{ display: false }}, ticks: {{ color: '#fff' }} }}
                        }}
                    }}
                }});
            }}
        }});
    </script>
</body>
</html>
"""

HTML_MATERIAS_ADMIN = f"""
<!DOCTYPE html>
<html>
<head><title>Materias - Institución Ñamandu</title>{TEMA_CSS}<style>body {{ padding: 40px; max-width: 1050px; margin: auto; }}</style></head>
<body>
    <div class="top-bar">
        <div class="header-izq">
            <div class="menu-btn-trigger" onclick="toggleMenu()" title="Menú">☰</div>
            <a href="/inicio" class="home-icon" title="Ir al Panel Principal">🏠</a>
            <h2 style="margin:0;">Administración de Materias</h2>
        </div>
        <a href="/inicio">← Volver</a>
    </div>
    <div class="layout">
        <div class="brand-card" style="padding: 25px; height: fit-content;">
            <h3 id="titulo-form" style="margin-bottom: 15px;">Nueva Materia</h3>
            <form method="POST" id="form-mat">
                <input type="hidden" name="id" id="form_id">
                <input type="text" name="nombre_materia" id="form_nombre" placeholder="Nombre de la Materia (Ej: Física)" required>
                
                <label style="color: var(--text-muted); font-size: 12px; display:block; margin-top:8px;">Curso al que pertenece:</label>
                <select name="curso" id="form_curso" required>
                    {{% for c in cursos_lista %}}
                        <option value="{{{{ c }}}}">{{{{ c }}}}</option>
                    {{% endfor %}}
                </select>

                <label style="color: var(--text-muted); font-size: 12px; display:block; margin-top:8px;">Docente Asignado:</label>
                <select name="docente_id">
                    <option value="">-- Sin Profesor Asignado --</option>
                    {{% for doc in lista_docentes %}}
                        <option value="{{{{ doc[0] }}}}">{{{{ doc[1] }}}}</option>
                    {{% endfor %}}
                </select>

                <label style="color: var(--text-muted); font-size: 12px; display:block; margin-top:8px;">Matricular Alumnos (Ctrl + click para varios):</label>
                <select name="alumnos_ids" multiple style="height: 120px; border-radius: 8px;">
                    {{% for est in lista_estudiantes %}}
                        <option value="{{{{ est[0] }}}}">{{{{ est[1] }}}} ({{{{ est[2] }}}})</option>
                    {{% endfor %}}
                </select>

                <button type="submit" id="btn-submit">Guardar Materia</button>
                <button type="button" onclick="cancelar()" id="btn-cancel" style="display:none; background:#333; color:white;">Cancelar Edición</button>
            </form>
        </div>
        <div class="tabla-scroll">
            <table>
                <tr><th>ID</th><th>Materia</th><th>Curso</th><th>Docente</th><th>Alumnos</th><th>Acciones</th></tr>
                {{% for m in lista_materias %}}
                <tr>
                    <td style="color: var(--brand-color); font-weight: bold;">#{{{{ m[0] }}}}</td>
                    <td><b>{{{{ m[1] }}}}</b></td>
                    <td style="color: var(--brand-color); font-weight: bold; font-size: 12px;">{{{{ m[2] }}}}</td>
                    <td style="color: var(--text-muted); font-size: 13px;">{{{{ m[3] }}}}</td>
                    <td style="color: var(--text-muted); font-size: 12px;">{{{{ m[4] }}}}</td>
                    <td>
                        <button type="button" class="btn-editar" onclick="editar('{{{{ m[0] }}}}', '{{{{ m[1] }}}}', '{{{{ m[2] }}}}')">Modificar</button>
                        <a href="/eliminar/materias/{{{{ m[0] }}}}" class="btn-eliminar" onclick="return confirm('¿Eliminar esta materia?');">Eliminar</a>
                    </td>
                </tr>
                {{% endfor %}}
            </table>
        </div>
    </div>
    <script>
        function editar(id, nombre, curso) {{
            document.getElementById('form_id').value = id;
            document.getElementById('form_nombre').value = nombre;
            document.getElementById('form_curso').value = curso;
            document.getElementById('titulo-form').innerText = 'Modificar Materia';
            document.getElementById('btn-submit').innerText = 'Actualizar Materia';
            document.getElementById('btn-cancel').style.display = 'block';
        }}
        function cancelar() {{
            document.getElementById('form-mat').reset();
            document.getElementById('form_id').value = '';
            document.getElementById('titulo-form').innerText = 'Nueva Materia';
            document.getElementById('btn-submit').innerText = 'Guardar Materia';
            document.getElementById('btn-cancel').style.display = 'none';
        }}
    </script>
</body>
</html>
"""

HTML_ESTUDIANTES = f"""
<!DOCTYPE html>
<html>
<head><title>Estudiantes - Institución Ñamandu</title>{TEMA_CSS}<style>body {{ padding: 40px; max-width: 1050px; margin: auto; }}</style></head>
<body>
    <div class="top-bar">
        <div class="header-izq">
            <div class="menu-btn-trigger" onclick="toggleMenu()" title="Menú">☰</div>
            <a href="/inicio" class="home-icon" title="Ir al Panel Principal">🏠</a>
            <h2 style="margin:0;">Registro de Estudiantes</h2>
        </div>
        <a href="/inicio">← Volver</a>
    </div>
    <div class="layout">
        <div class="brand-card" style="padding: 30px; height: fit-content;">
            <h3 id="titulo-form" style="margin-bottom: 20px;">Nuevo Ingreso</h3>
            {{% if error_mensaje %}}
                <div class="alerta-error">{{{{ error_mensaje }}}}</div>
            {{% endif %}}
            <form method="POST" id="form-est">
                <input type="hidden" name="id" id="form_id">
                <input type="text" name="nombre" id="form_nombre" placeholder="Nombre Completo" required>
                <input type="text" name="cedula" id="form_cedula" placeholder="N° de Cédula (Para Login)" required>
                
                <label style="color: var(--text-muted); font-size: 12px; display:block; margin-top:8px;">Curso:</label>
                <select name="curso" id="form_curso" required>
                    {{% for c in cursos_lista %}}
                        <option value="{{{{ c }}}}">{{{{ c }}}}</option>
                    {{% endfor %}}
                </select>

                <input type="text" name="matricula" id="form_matricula" placeholder="N° de Matrícula">
                <input type="password" name="clave" id="form_clave" placeholder="Contraseña de Acceso">
                <button type="submit" id="btn-submit">Guardar</button>
                <button type="button" onclick="cancelar()" id="btn-cancel" style="display:none; background:#333; color:white;">Cancelar Edición</button>
            </form>
        </div>
        <div class="tabla-scroll">
            <table>
                <tr><th>ID</th><th>Nombre</th><th>Curso</th><th>Cédula</th><th>Matrícula</th><th>Acción</th></tr>
                {{% for a in lista_alumnos %}}
                <tr>
                    <td style="color: var(--brand-color); font-weight: bold;">#{{{{ a[0] }}}}</td>
                    <td><b>{{{{ a[1] }}}}</b></td>
                    <td style="color: var(--brand-color); font-weight: bold; font-size: 12px;">{{{{ a[4] }}}}</td>
                    <td style="color: var(--text-muted);">{{{{ a[3] }}}}</td>
                    <td style="color: var(--text-muted);">{{{{ a[2] if a[2] else 'S/M' }}}}</td>
                    <td>
                        <button type="button" class="btn-editar" onclick="editar('{{{{ a[0] }}}}', '{{{{ a[1] }}}}', '{{{{ a[2] if a[2] else "" }}}}', '{{{{ a[3] }}}}', '{{{{ a[4] }}}}')">Modificar</button>
                        <a href="/eliminar/estudiantes/{{{{ a[0] }}}}" class="btn-eliminar" onclick="return confirm('¿Seguro que deseas eliminar este estudiante?');">Eliminar</a>
                    </td>
                </tr>
                {{% endfor %}}
            </table>
        </div>
    </div>
    <script>
        function editar(id, nombre, matricula, cedula, curso) {{ 
            document.getElementById('form_id').value = id; 
            document.getElementById('form_nombre').value = nombre; 
            document.getElementById('form_matricula').value = matricula; 
            document.getElementById('form_cedula').value = cedula; 
            document.getElementById('form_curso').value = curso;
            document.getElementById('titulo-form').innerText = 'Modificar Estudiante'; 
            document.getElementById('btn-submit').innerText = 'Actualizar Datos'; 
            document.getElementById('btn-cancel').style.display = 'block'; 
        }}
        function cancelar() {{ 
            document.getElementById('form-est').reset(); 
            document.getElementById('form_id').value = ''; 
            document.getElementById('titulo-form').innerText = 'Nuevo Ingreso'; 
            document.getElementById('btn-submit').innerText = 'Guardar'; 
            document.getElementById('btn-cancel').style.display = 'none'; 
        }}
    </script>
</body>
</html>
"""

HTML_DOCENTES = f"""
<!DOCTYPE html>
<html>
<head><title>Docentes - Institución Ñamandu</title>{TEMA_CSS}<style>body {{ padding: 40px; max-width: 1100px; margin: auto; }}</style></head>
<body>
    <div class="top-bar">
        <div class="header-izq">
            <div class="menu-btn-trigger" onclick="toggleMenu()" title="Menú">☰</div>
            <a href="/inicio" class="home-icon" title="Ir al Panel Principal">🏠</a>
            <h2 style="margin:0;">Gestión de Docentes</h2>
        </div>
        <a href="/inicio">← Volver</a>
    </div>
    <div class="layout">
        <div class="brand-card" style="padding: 30px; height: fit-content;">
            <h3 id="titulo-form">Nuevo Docente</h3>
            <form method="POST" id="form-doc">
                <input type="hidden" name="id" id="form_id">
                <input type="text" name="nombre" id="form_nombre" placeholder="Nombre Completo (Ej: Luis Arce)" required>
                <input type="text" name="cedula" id="form_cedula" placeholder="N° de Cédula (Ej: 5892921)" required>
                
                <label style="color: var(--text-muted); font-size: 12px; display:block; margin-top:8px;">
                    Materias a Asignar (Ctrl + clic para seleccionar varias):
                </label>
                <select name="materias_sel" id="form_materias_sel" multiple style="height: 120px; border-radius: 8px;">
                    {{% for m in materias_existentes %}}
                        <option value="{{{{ m[0] }}}}">{{{{ m[0] }}}} ({{{{ m[1] }}}})</option>
                    {{% endfor %}}
                </select>

                <div style="margin-top: 10px;">
                    <label style="font-size: 12px; color: var(--brand-color); cursor: pointer;">
                        <input type="checkbox" id="check_nueva_mat" onchange="toggleNuevaMateria(this)" style="width: auto; margin: 0; vertical-align: middle;">
                        + ¿Deseas crear una nueva materia para este docente?
                    </label>
                </div>
                
                <div id="div_nueva_mat" style="display:none; background:#181818; padding:12px; border-radius:10px; margin-top:8px; border:1px dashed #444;">
                    <input type="text" name="especialidad_nueva" id="input_nueva_mat" placeholder="Nombre de la nueva materia">
                    <label style="color: var(--text-muted); font-size: 11px; display:block; margin-top:5px;">Curso para la nueva materia:</label>
                    <select name="curso_nueva_mat">
                        {{% for c in cursos_lista %}}
                            <option value="{{{{ c }}}}">{{{{ c }}}}</option>
                        {{% endfor %}}
                    </select>
                </div>

                <input type="password" name="clave" id="form_clave" placeholder="Contraseña de Acceso (Opcional)">
                <button type="submit" id="btn-submit">Guardar</button>
                <button type="button" onclick="cancelar()" id="btn-cancel" style="display:none; background:#333; color:white;">Cancelar Edición</button>
            </form>
        </div>
        <div class="tabla-scroll">
            <table>
                <tr><th>ID</th><th>Docente</th><th>Cédula</th><th>Materias Asignadas</th><th>Acciones</th></tr>
                {{% for d in lista_docentes %}}
                <tr>
                    <td style="color: var(--brand-color); font-weight: bold;">#{{{{ d[0] }}}}</td>
                    <td><b>{{{{ d[1] }}}}</b></td>
                    <td style="color: var(--text-muted);">{{{{ d[2] }}}}</td>
                    <td style="color: var(--brand-color); font-size: 12px; line-height: 1.4;">{{{{ d[4] }}}}</td>
                    <td>
                        <a href="/asignar_materias/{{{{ d[0] }}}}" class="btn-materias">Administrar</a>
                        <button type="button" class="btn-editar" onclick="editar('{{{{ d[0] }}}}', '{{{{ d[1] }}}}', '{{{{ d[2] }}}}', '{{{{ d[4] }}}}')">Modificar</button>
                        <a href="/eliminar/docentes/{{{{ d[0] }}}}" class="btn-eliminar" onclick="return confirm('¿Seguro que deseas eliminar este docente?');">Eliminar</a>
                    </td>
                </tr>
                {{% endfor %}}
            </table>
        </div>
    </div>
    <script>
        function toggleNuevaMateria(chk) {{
            const div = document.getElementById('div_nueva_mat');
            const input = document.getElementById('input_nueva_mat');
            if (chk.checked) {{
                div.style.display = 'block';
                input.focus();
            }} else {{
                div.style.display = 'none';
                input.value = '';
            }}
        }}

        function editar(id, nombre, cedula, materiasStr) {{ 
            document.getElementById('form_id').value = id; 
            document.getElementById('form_nombre').value = nombre; 
            document.getElementById('form_cedula').value = cedula; 
            
            const sel = document.getElementById('form_materias_sel');
            const matArray = materiasStr.split(',').map(m => m.trim());
            for (let i = 0; i < sel.options.length; i++) {{
                sel.options[i].selected = matArray.includes(sel.options[i].value);
            }}

            document.getElementById('check_nueva_mat').checked = false;
            document.getElementById('div_nueva_mat').style.display = 'none';
            document.getElementById('titulo-form').innerText = 'Modificar Docente'; 
            document.getElementById('btn-submit').innerText = 'Actualizar Datos'; 
            document.getElementById('btn-cancel').style.display = 'block'; 
        }}

        function cancelar() {{ 
            document.getElementById('form-doc').reset(); 
            document.getElementById('form_id').value = ''; 
            document.getElementById('check_nueva_mat').checked = false;
            document.getElementById('div_nueva_mat').style.display = 'none';
            document.getElementById('titulo-form').innerText = 'Nuevo Docente'; 
            document.getElementById('btn-submit').innerText = 'Guardar'; 
            document.getElementById('btn-cancel').style.display = 'none'; 
        }}
    </script>
</body>
</html>
"""

HTML_ASIGNAR_MATERIAS = f"""
<!DOCTYPE html>
<html>
<head><title>Asignar Materias - Institución Ñamandu</title>{TEMA_CSS}<style>body {{ padding: 40px; max-width: 600px; margin: auto; text-align: center; }}</style></head>
<body>
    <div class="top-bar">
        <div class="header-izq">
            <div class="menu-btn-trigger" onclick="toggleMenu()" title="Menú">☰</div>
            <a href="/docentes" class="home-icon" title="Volver a Docentes">←</a>
            <h2 style="margin:0;">Asignar Materias: {{{{ nombre_docente }}}}</h2>
        </div>
    </div>
    <div class="brand-card" style="text-align: left;">
        <h3 style="margin-bottom: 20px; text-align: center;">Materias Asignadas</h3>
        {{% if materias_asignadas %}}
            <ul style="list-style: none; padding: 0;">
                {{% for m in materias_asignadas %}}
                    <li style="background: #1a1a1a; padding: 12px 20px; margin-bottom: 10px; border-radius: 10px; display: flex; justify-content: space-between; align-items: center; border: 1px solid #333;">
                        <span>{{{{ m[1] }}}}</span>
                        <a href="/quitar_materia/{{{{ m[0] }}}}/{{{{ docente_id }}}}" style="color: #ff3366; font-size: 13px;">[ Quitar ]</a>
                    </li>
                {{% endfor %}}
            </ul>
        {{% else %}}
            <p style="color: var(--text-muted); text-align: center;">Este profesor aún no tiene materias asignadas.</p>
        {{% endif %}}

        <hr style="border:0; border-top:1px solid #333; margin:30px 0;">

        <h3 style="margin-bottom: 20px; text-align: center;">Añadir Nueva Materia</h3>
        <form method="POST">
            <select name="materia" required>
                <option value="" disabled selected>Selecciona una Materia...</option>
                {{% for m in materias_totales %}}
                    <option value="{{{{ m[1] }}}}">{{{{ m[1] }}}} ({{{{ m[2] }}}})</option>
                {{% endfor %}}
            </select>
            <button type="submit">Agregar Materia</button>
        </form>
    </div>
</body>
</html>
"""

HTML_CALIFICACIONES = f"""
<!DOCTYPE html>
<html>
<head><title>Calificaciones - Institución Ñamandu</title>{TEMA_CSS}<style>body {{ padding: 40px; max-width: 1000px; margin: auto; }}</style></head>
<body>
    <div class="top-bar">
        <div class="header-izq">
            <div class="menu-btn-trigger" onclick="toggleMenu()" title="Menú">☰</div>
            <a href="/inicio" class="home-icon" title="Ir al Panel Principal">🏠</a>
            <h2 style="margin:0;">Carga de Notas</h2>
        </div>
        <a href="/inicio">← Volver</a>
    </div>
    <div class="layout">
        <div class="brand-card" style="padding: 30px; height: fit-content;">
            <h3 id="titulo-form">Nueva Calificación</h3>
            <form method="POST" id="form-cal">
                <input type="hidden" name="id" id="form_id">
                
                <select name="alumno" id="form_alumno" required>
                    <option value="" disabled selected>Selecciona un Alumno...</option>
                    {{% for est in estudiantes_dropdown %}}
                        <option value="{{{{ est[0] }}}}">{{{{ est[0] }}}} ({{{{ est[1] }}}})</option>
                    {{% endfor %}}
                </select>

                <select name="materia" id="form_materia" required>
                    <option value="" disabled selected>Selecciona una Materia...</option>
                    {{% for mat in materias_disponibles %}}
                        <option value="{{{{ mat }}}}">{{{{ mat }}}}</option>
                    {{% endfor %}}
                </select>

                <input type="number" name="nota" id="form_nota" placeholder="Nota Final (1 al 5)" min="1" max="5" required>
                <button type="submit" id="btn-submit">Guardar Nota</button>
                <button type="button" onclick="cancelar()" id="btn-cancel" style="display:none; background:#333; color:white;">Cancelar Edición</button>
            </form>
        </div>
        <div class="tabla-scroll">
            <table>
                <tr><th>ID</th><th>Alumno</th><th>Materia</th><th>Nota</th><th>Acción</th></tr>
                {{% for c in lista_calificaciones %}}
                <tr>
                    <td style="color: var(--brand-color); font-weight: bold;">#{{{{ c[0] }}}}</td><td>{{{{ c[1] }}}}</td><td style="color: var(--text-muted);">{{{{ c[2] }}}}</td><td style="color: var(--brand-color); font-weight: bold; font-size: 16px;">{{{{ c[3] }}}}</td>
                    <td>
                        <button type="button" class="btn-editar" onclick="editar('{{{{ c[0] }}}}', '{{{{ c[1] }}}}', '{{{{ c[2] }}}}', '{{{{ c[3] }}}}')">Modificar</button>
                        <a href="/eliminar/calificaciones/{{{{ c[0] }}}}" class="btn-eliminar" onclick="return confirm('¿Seguro que deseas eliminar esta calificación?');">Eliminar</a>
                    </td>
                </tr>
                {{% endfor %}}
            </table>
        </div>
    </div>
    <script>
        function editar(id, alumno, materia, nota) {{ document.getElementById('form_id').value = id; document.getElementById('form_alumno').value = alumno; document.getElementById('form_materia').value = materia; document.getElementById('form_nota').value = nota; document.getElementById('titulo-form').innerText = 'Modificar Calificación'; document.getElementById('btn-submit').innerText = 'Actualizar Nota'; document.getElementById('btn-cancel').style.display = 'block'; }}
        function cancelar() {{ document.getElementById('form-cal').reset(); document.getElementById('form_id').value = ''; document.getElementById('titulo-form').innerText = 'Nueva Calificación'; document.getElementById('btn-submit').innerText = 'Guardar Nota'; document.getElementById('btn-cancel').style.display = 'none'; }}
    </script>
</body>
</html>
"""

HTML_ASISTENCIA = f"""
<!DOCTYPE html>
<html>
<head><title>Asistencia - Institución Ñamandu</title>{TEMA_CSS}<style>body {{ padding: 40px; max-width: 1000px; margin: auto; }}</style></head>
<body>
    <div class="top-bar">
        <div class="header-izq">
            <div class="menu-btn-trigger" onclick="toggleMenu()" title="Menú">☰</div>
            <a href="/inicio" class="home-icon" title="Ir al Panel Principal">🏠</a>
            <h2 style="margin:0;">Control de Asistencia</h2>
        </div>
        <a href="/inicio">← Volver</a>
    </div>
    <div class="layout">
        <div class="brand-card" style="padding: 30px; height: fit-content;">
            <h3 style="margin-bottom: 20px;">Registrar Asistencia</h3>
            <form method="POST">
                <select name="alumno" required>
                    <option value="" disabled selected>Selecciona Alumno...</option>
                    {{% for est in estudiantes_dropdown %}}
                        <option value="{{{{ est[0] }}}}">{{{{ est[0] }}}} ({{{{ est[1] }}}})</option>
                    {{% endfor %}}
                </select>
                <select name="materia" required>
                    <option value="" disabled selected>Selecciona Materia...</option>
                    {{% for mat in materias_disponibles %}}
                        <option value="{{{{ mat }}}}">{{{{ mat }}}}</option>
                    {{% endfor %}}
                </select>
                <select name="estado" required>
                    <option value="Presente">Presente</option>
                    <option value="Ausente">Ausente</option>
                    <option value="Tardanza">Tardanza</option>
                </select>
                <button type="submit">Guardar Asistencia</button>
            </form>
        </div>
        <div class="tabla-scroll">
            <table>
                <tr><th>Fecha</th><th>Alumno</th><th>Materia</th><th>Estado</th><th>Acción</th></tr>
                {{% for a in lista_asistencia %}}
                <tr>
                    <td style="color: var(--text-muted); font-size: 13px;">{{{{ a[4] }}}}</td>
                    <td>{{{{ a[1] }}}}</td>
                    <td>{{{{ a[2] }}}}</td>
                    <td style="font-weight: bold; color: {{% if a[3] == 'Presente' %}}var(--brand-color){{% elif a[3] == 'Ausente' %}}#ff3366{{% else %}}#ff9900{{% endif %}};">{{{{ a[3] }}}}</td>
                    <td><a href="/eliminar/asistencia/{{{{ a[0] }}}}" class="btn-eliminar">Borrar</a></td>
                </tr>
                {{% endfor %}}
            </table>
        </div>
    </div>
</body>
</html>
"""

HTML_TABLON = f"""
<!DOCTYPE html>
<html>
<head><title>Tablón de Materias - Institución Ñamandu</title>{TEMA_CSS}<style>body {{ padding: 40px; max-width: 900px; margin: auto; }}</style></head>
<body>
    <div class="top-bar">
        <div class="header-izq">
            <div class="menu-btn-trigger" onclick="toggleMenu()" title="Menú">☰</div>
            <a href="/inicio" class="home-icon" title="Ir al Panel Principal">🏠</a>
            <h2 style="margin:0;">Tablón de Anuncios y Avisos</h2>
        </div>
        <a href="/inicio">← Volver</a>
    </div>
    
    {{% if rol_usuario in ['admin', 'docente'] %}}
    <div class="brand-card" style="margin-bottom: 30px;">
        <h3 style="margin-bottom: 15px;">Publicar Anuncio</h3>
        <form method="POST">
            <select name="materia" required>
                <option value="" disabled selected>Selecciona Materia...</option>
                {{% for mat in materias_disponibles %}}
                    <option value="{{{{ mat }}}}">{{{{ mat }}}}</option>
                {{% endfor %}}
            </select>
            <textarea name="mensaje" rows="3" placeholder="Escribe el aviso, tarea o material para los alumnos..." required></textarea>
            <button type="submit">Publicar en el Tablón</button>
        </form>
    </div>
    {{% endif %}}

    <h3 style="margin-bottom: 20px;">Muro de Anuncios</h3>
    {{% for t in tablon_posts %}}
    <div class="brand-card" style="margin-bottom: 20px; padding: 25px;">
        <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #222; padding-bottom: 10px; margin-bottom: 15px;">
            <span style="color: var(--brand-color); font-weight: bold;">{{{{ t[1] }}}}</span>
            <span style="color: var(--text-muted); font-size: 12px;">Por: {{{{ t[3] }}}} ( {{{{ t[4] }}}} )</span>
        </div>
        <p style="font-size: 15px; line-height: 1.5; margin: 0;">{{{{ t[2] }}}}</p>
        {{% if rol_usuario == 'admin' %}}
        <div style="text-align: right; margin-top: 10px;">
            <a href="/eliminar/tablon/{{{{ t[0] }}}}" style="color: #ff3366; font-size: 12px;">Eliminar aviso</a>
        </div>
        {{% endif %}}
    </div>
    {{% endfor %}}
</body>
</html>
"""

HTML_REPORTES = f"""
<!DOCTYPE html>
<html>
<head><title>Reportes Académicos - Institución Ñamandu</title>{TEMA_CSS}<style>body {{ padding: 40px; max-width: 900px; margin: auto; }}</style></head>
<body>
    <div class="top-bar">
        <div class="header-izq">
            <div class="menu-btn-trigger" onclick="toggleMenu()" title="Menú">☰</div>
            <a href="/inicio" class="home-icon" title="Ir al Panel Principal">🏠</a>
            <h2 style="margin:0;">Generador de Reportes</h2>
        </div>
        <a href="/inicio">← Volver</a>
    </div>
    <div class="brand-card" style="text-align: center; padding: 50px;">
        <h3>Acta General de Calificaciones</h3>
        <p style="color: var(--text-muted); margin-bottom: 30px;">Descarga el reporte oficial consolidado de notas en formato de texto imprimible o acta institucional.</p>
        <a href="/descargar_reporte" target="_blank" style="background: var(--brand-color); color: #000; padding: 15px 30px; border-radius: 30px; font-weight: 800; text-transform: uppercase; display: inline-block;">Descargar Acta Oficial (.TXT)</a>
    </div>
</body>
</html>
"""

HTML_PORTAL_ALUMNO = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Mi Portal - Institución Ñamandu</title>
    {TEMA_CSS}
    <style>
        body {{ padding: 20px; max-width: 1000px; margin: auto; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; border-bottom: 1px solid #222; padding-bottom: 15px; }}
        .layout-alumno {{ display: grid; grid-template-columns: 1fr 1.3fr; gap: 20px; margin-bottom: 25px; }}
        
        .card-materia {{ background: #181818; border: 1px solid #252525; border-radius: 12px; padding: 14px; margin-bottom: 12px; }}
        .card-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }}
        .barra-progreso-bg {{ background: #222; border-radius: 10px; height: 10px; width: 100%; overflow: hidden; }}
        .barra-progreso-fill {{ height: 100%; border-radius: 10px; transition: width 0.5s ease; }}
        
        .badge-materia {{ display: inline-block; background: #1e1e1e; border: 1px solid #333; padding: 6px 12px; border-radius: 20px; font-size: 12px; margin: 4px; color: #eee; }}

        @media (max-width: 768px) {{
            body {{ padding: 10px !important; }}
            .layout-alumno {{ grid-template-columns: 1fr !important; gap: 15px !important; }}
            .header {{ flex-direction: row !important; align-items: center !important; justify-content: space-between !important; }}
            .header > div:last-child {{ display: flex !important; }}
            .brand-card {{ padding: 15px !important; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="header-izq">
            <div class="menu-btn-trigger" onclick="toggleMenu()" title="Menú">☰</div>
            <h2 style="display:flex; align-items:center;">
                {{% if usuario_datos[1] %}}<img src="data:image/jpeg;base64,{{{{ usuario_datos[1] }}}}" class="foto-mini">{{% endif %}}
                Portal Alumno
            </h2>
        </div>
        <div>
            <a href="/tablon" style="color: var(--text-light); margin-right: 12px; font-size: 12px;">Tablón</a>
            <a href="/perfil" style="color: var(--text-light); margin-right: 12px; font-size: 12px;">Perfil</a>
            <a href="/logout" class="logout-btn">CERRAR SESIÓN</a>
        </div>
    </div>

    <!-- Fila 1: Perfil, Curso y Asignaturas -->
    <div class="layout-alumno">
        <div class="brand-card" style="text-align: center;">
            {{% if usuario_datos[1] %}}
                <img src="data:image/jpeg;base64,{{{{ usuario_datos[1] }}}}" class="foto-perfil">
            {{% else %}}
                <div class="foto-perfil" style="display:inline-block; line-height:100px; color:#888;">Sin Foto</div>
            {{% endif %}}
            <h3 style="color: var(--text-muted); margin-top: 5px; font-size: 13px;">Estudiante</h3>
            <h2 style="color: var(--brand-color); font-size: 24px; margin-bottom: 4px;">{{{{ nombre_estudiante }}}}</h2>
            <p style="color: var(--brand-color); font-weight: bold; font-size: 14px; margin-bottom: 4px;">{{{{ usuario_datos[4] }}}}</p>
            <p style="color: var(--text-muted); font-size: 12px; margin-bottom: 15px;">{{{{ usuario_datos[3] }}}} | Cédula: {{{{ usuario_datos[0] }}}}</p>
            
            <hr style="border:0; border-top:1px solid #222; margin: 15px 0;">
            <h4 style="color: #fff; font-size: 13px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px;">Mis Asignaturas</h4>
            <div style="display: flex; flex-wrap: wrap; justify-content: center;">
                {{% for mat in materias_alumno %}}
                    <span class="badge-materia">📚 {{{{ mat }}}}</span>
                {{% else %}}
                    <p style="color: var(--text-muted); font-size: 12px;">No tienes materias inscriptas aún.</p>
                {{% endfor %}}
            </div>
        </div>

        <!-- Módulo de Rendimiento y Calificaciones -->
        <div class="brand-card">
            <h3 style="margin-bottom: 15px; font-size: 16px; border-bottom: 1px solid #222; padding-bottom: 8px;">Mis Calificaciones Oficiales</h3>
            {{% for nota in notas %}}
            <div class="card-materia">
                <div class="card-header">
                    <span style="font-weight: bold; font-size: 13px; color: #fff;">{{{{ nota[0] }}}}</span>
                    <span style="font-weight: 900; font-size: 16px; color: {{% if nota[1] <= 2 %}}#ff3366{{% elif nota[1] == 3 %}}#ff9900{{% else %}}var(--brand-color){{% endif %}};">
                        {{{{ nota[1] }}}}/5
                    </span>
                </div>
                <div class="barra-progreso-bg">
                    <div class="barra-progreso-fill" style="width: calc(({{{{ nota[1] }}}} / 5) * 100%); background: {{% if nota[1] <= 2 %}}#ff3366{{% elif nota[1] == 3 %}}#ff9900{{% else %}}var(--brand-color){{% endif %}};"></div>
                </div>
            </div>
            {{% else %}}
                <p style="color: var(--text-muted); text-align: center; padding: 20px 0;">No hay calificaciones registradas todavía.</p>
            {{% endfor %}}
        </div>
    </div>

    <!-- Fila 2: Registro de Asistencias -->
    <div class="brand-card">
        <h3 style="margin-bottom: 15px; font-size: 16px;">Historial de Asistencia</h3>
        <div class="tabla-scroll">
            <table>
                <tr><th>Fecha</th><th>Materia</th><th>Estado</th></tr>
                {{% for asis in mis_asistencias %}}
                <tr>
                    <td style="color: var(--text-muted);">{{{{ asis[2] }}}}</td>
                    <td><b>{{{{ asis[0] }}}}</b></td>
                    <td style="font-weight: bold; color: {{% if asis[1] == 'Presente' %}}var(--brand-color){{% elif asis[1] == 'Ausente' %}}#ff3366{{% else %}}#ff9900{{% endif %}};">
                        {{{{ asis[1] }}}}
                    </td>
                </tr>
                {{% else %}}
                <tr><td colspan="3" style="text-align: center; color: var(--text-muted);">No hay registros de asistencia disponibles.</td></tr>
                {{% endfor %}}
            </table>
        </div>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def login():
    mensaje_error = None
    if request.method == 'POST':
        usuario = request.form['usuario'].strip()
        clave = request.form['clave']
        
        if usuario == "admin" and clave == admin_data["clave"]:
            session['rol'] = 'admin'
            session['nombre'] = 'Administrador'
            return redirect(url_for('inicio'))
            
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        
        cursor.execute("SELECT nombre_completo, id FROM estudiantes WHERE cedula = %s AND clave = %s", (usuario, clave))
        alumno = cursor.fetchone()
        
        cursor.execute("SELECT nombre_completo, id FROM docentes WHERE cedula = %s AND clave = %s", (usuario, clave))
        docente = cursor.fetchone()
        
        cursor.close()
        conexion.close()
        
        if alumno:
            session['rol'] = 'alumno'
            session['nombre'] = alumno[0]
            session['alumno_id'] = alumno[1]
            return redirect(url_for('inicio'))
        elif docente:
            session['rol'] = 'docente'
            session['nombre'] = docente[0]
            session['docente_id'] = docente[1]
            return redirect(url_for('inicio'))
        else:
            mensaje_error = "Credenciales incorrectas (Verifica tu Cédula o Contraseña)."
    return render_template_string(HTML_LOGIN, mensaje_error=mensaje_error)

@app.route('/inicio')
def inicio():
    rol = session.get('rol')
    if rol in ['admin', 'docente']:
        return redirect(url_for('dashboard'))
    elif rol == 'alumno':
        return redirect(url_for('mi_portal'))
    return redirect(url_for('login'))

@app.route('/perfil', methods=['GET', 'POST'])
def perfil():
    rol = session.get('rol')
    if not rol: return redirect(url_for('login'))
    
    mensaje = None
    usuario_datos = ["", "", "", ""]
    
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    if rol == 'alumno':
        cursor.execute("SELECT cedula, foto, anio_nacimiento, carrera FROM estudiantes WHERE id = %s", (session['alumno_id'],))
        usuario_datos = cursor.fetchone() or ["", "", "", ""]
    elif rol == 'docente':
        cursor.execute("SELECT cedula, foto, anio_nacimiento, '' FROM docentes WHERE id = %s", (session['docente_id'],))
        usuario_datos = cursor.fetchone() or ["", "", "", ""]

    if request.method == 'POST':
        nueva_clave = request.form.get('nueva_clave')
        
        if rol == 'admin':
            if nueva_clave: admin_data["clave"] = nueva_clave
            mensaje = "¡Contraseña de Administrador actualizada!"
        else:
            anio = request.form.get('anio_nacimiento')
            carrera = request.form.get('carrera') if rol == 'alumno' else ""
            foto_file = request.files.get('foto')
            
            foto_b64 = usuario_datos[1]
            if foto_file and foto_file.filename != '':
                foto_b64 = base64.b64encode(foto_file.read()).decode('utf-8')
            
            if rol == 'alumno':
                if nueva_clave:
                    cursor.execute("UPDATE estudiantes SET anio_nacimiento=%s, carrera=%s, foto=%s, clave=%s WHERE id=%s", (anio, carrera, foto_b64, nueva_clave, session['alumno_id']))
                else:
                    cursor.execute("UPDATE estudiantes SET anio_nacimiento=%s, carrera=%s, foto=%s WHERE id=%s", (anio, carrera, foto_b64, session['alumno_id']))
            elif rol == 'docente':
                if nueva_clave:
                    cursor.execute("UPDATE docentes SET anio_nacimiento=%s, foto=%s, clave=%s WHERE id=%s", (anio, foto_b64, nueva_clave, session['docente_id']))
                else:
                    cursor.execute("UPDATE docentes SET anio_nacimiento=%s, foto=%s WHERE id=%s", (anio, foto_b64, session['docente_id']))
            
            conexion.commit()
            mensaje = "¡Perfil actualizado con éxito!"
            usuario_datos = (usuario_datos[0], foto_b64, anio, carrera)

    cursor.close()
    conexion.close()
    
    return render_template_string(HTML_PERFIL, mensaje=mensaje, rol=rol, usuario_datos=usuario_datos)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    rol = session.get('rol')
    if rol == 'admin':
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM docentes")
        t_docentes = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM estudiantes")
        t_estudiantes = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM materias")
        t_materias = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM calificaciones")
        t_calificaciones = cursor.fetchone()[0]

        cursor.execute("""
            SELECT m.nombre, COALESCE(ROUND(AVG(c.nota), 2), 0)
            FROM materias m
            LEFT JOIN calificaciones c ON m.nombre = c.materia
            GROUP BY m.nombre
            ORDER BY m.nombre ASC
        """)
        datos_notas = cursor.fetchall()
        labels_materias = [d[0] for d in datos_notas]
        promedios_materias = [float(d[1]) for d in datos_notas]

        cursor.execute("SELECT COUNT(*) FROM asistencia WHERE estado = 'Presente'")
        total_presentes = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM asistencia WHERE estado = 'Ausente'")
        total_ausentes = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM asistencia WHERE estado = 'Tardanza'")
        total_tardanzas = cursor.fetchone()[0]

        cursor.close()
        conexion.close()

        return render_template_string(
            HTML_DASHBOARD_ADMIN,
            total_docentes=t_docentes,
            total_estudiantes=t_estudiantes,
            total_materias=t_materias,
            total_calificaciones=t_calificaciones,
            labels_materias=json.dumps(labels_materias),
            promedios_materias=json.dumps(promedios_materias),
            asistencia_data=json.dumps([total_presentes, total_ausentes, total_tardanzas])
        )

    elif rol == 'docente':
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("SELECT foto FROM docentes WHERE id = %s", (session['docente_id'],))
        doc_foto_res = cursor.fetchone()
        doc_foto = doc_foto_res[0] if doc_foto_res else None
        
        cursor.execute("SELECT materia FROM docente_materias WHERE docente_id = %s", (session['docente_id'],))
        mats_doc = [m[0] for m in cursor.fetchall()]
        
        promedios_doc = []
        for m in mats_doc:
            cursor.execute("SELECT AVG(nota) FROM calificaciones WHERE materia = %s", (m,))
            prom = cursor.fetchone()[0]
            promedios_doc.append(round(float(prom), 2) if prom else 0.0)
            
        cursor.close()
        conexion.close()
        return render_template_string(HTML_DASHBOARD_DOCENTE, nombre_docente=session['nombre'], foto=doc_foto, mat_json=json.dumps(mats_doc), prom_json=json.dumps(promedios_doc))

    return redirect(url_for('login'))

@app.route('/materias_admin', methods=['GET', 'POST'])
def materias_admin():
    if session.get('rol') != 'admin': return redirect(url_for('login'))
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    if request.method == 'POST':
        id_mat = request.form.get('id')
        nombre_materia = request.form['nombre_materia'].strip()
        curso = request.form.get('curso', '1er Curso')
        docente_id = request.form.get('docente_id')
        alumnos_ids = request.form.getlist('alumnos_ids')
        
        if id_mat:
            cursor.execute("SELECT nombre FROM materias WHERE id = %s", (id_mat,))
            m_antigua = cursor.fetchone()
            if m_antigua:
                nombre_viejo = m_antigua[0]
                cursor.execute("UPDATE materias SET nombre=%s, curso=%s WHERE id=%s", (nombre_materia, curso, id_mat))
                cursor.execute("UPDATE docente_materias SET materia=%s WHERE materia=%s", (nombre_materia, nombre_viejo))
                cursor.execute("UPDATE alumno_materias SET materia=%s WHERE materia=%s", (nombre_materia, nombre_viejo))
                cursor.execute("UPDATE calificaciones SET materia=%s WHERE materia=%s", (nombre_materia, nombre_viejo))
                cursor.execute("UPDATE asistencia SET materia=%s WHERE materia=%s", (nombre_materia, nombre_viejo))
                cursor.execute("UPDATE tablon_materias SET materia=%s WHERE materia=%s", (nombre_materia, nombre_viejo))
        else:
            if nombre_materia:
                try:
                    cursor.execute("INSERT INTO materias (nombre, curso) VALUES (%s, %s)", (nombre_materia, curso))
                except Exception:
                    conexion.rollback()
        
        if docente_id:
            try:
                cursor.execute("DELETE FROM docente_materias WHERE materia = %s", (nombre_materia,))
                cursor.execute("INSERT INTO docente_materias (docente_id, materia) VALUES (%s, %s)", (docente_id, nombre_materia))
            except Exception:
                conexion.rollback()

        for al_id in alumnos_ids:
            try:
                cursor.execute("INSERT INTO alumno_materias (alumno_id, materia) VALUES (%s, %s) ON CONFLICT (alumno_id, materia) DO NOTHING", (al_id, nombre_materia))
            except Exception:
                conexion.rollback()

        conexion.commit()
                
    cursor.execute("""
        SELECT m.id, m.nombre, COALESCE(m.curso, '1er Curso'),
               COALESCE(STRING_AGG(DISTINCT d.nombre_completo, ', '), 'Sin profesor') AS profesor,
               COALESCE(STRING_AGG(DISTINCT e.nombre_completo, ', '), 'Sin alumnos') AS alumnos
        FROM materias m
        LEFT JOIN docente_materias dm ON m.nombre = dm.materia
        LEFT JOIN docentes d ON dm.docente_id = d.id
        LEFT JOIN alumno_materias am ON m.nombre = am.materia
        LEFT JOIN estudiantes e ON am.alumno_id = e.id
        GROUP BY m.id, m.nombre, m.curso
        ORDER BY m.curso ASC, m.nombre ASC
    """)
    lista_materias = cursor.fetchall()
    
    cursor.execute("SELECT id, nombre_completo FROM docentes ORDER BY nombre_completo ASC")
    lista_docentes = cursor.fetchall()

    cursor.execute("SELECT id, nombre_completo, COALESCE(curso, '1er Curso') FROM estudiantes ORDER BY nombre_completo ASC")
    lista_estudiantes = cursor.fetchall()

    cursor.close()
    conexion.close()
    return render_template_string(HTML_MATERIAS_ADMIN, lista_materias=lista_materias, lista_docentes=lista_docentes, lista_estudiantes=lista_estudiantes, cursos_lista=CURSOS_DISPONIBLES)

@app.route('/estudiantes', methods=['GET', 'POST'])
def estudiantes():
    if session.get('rol') != 'admin': return redirect(url_for('login'))
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    error_mensaje = None

    if request.method == 'POST':
        id_est = request.form.get('id')
        nombre = request.form['nombre'].strip()
        cedula = request.form['cedula'].strip()
        curso = request.form.get('curso', '1er Curso')
        matricula_raw = request.form.get('matricula', '').strip()
        
        matricula = matricula_raw if matricula_raw else None
        clave = request.form.get('clave', '').strip()

        try:
            if id_est:
                if clave: 
                    cursor.execute("UPDATE estudiantes SET nombre_completo=%s, cedula=%s, matricula=%s, clave=%s, curso=%s WHERE id=%s", (nombre, cedula, matricula, clave, curso, id_est))
                else:
                    cursor.execute("UPDATE estudiantes SET nombre_completo=%s, cedula=%s, matricula=%s, curso=%s WHERE id=%s", (nombre, cedula, matricula, curso, id_est))
            else:
                if not clave: clave = 'alumno123'
                cursor.execute("INSERT INTO estudiantes (nombre_completo, cedula, matricula, clave, curso) VALUES (%s, %s, %s, %s, %s)", (nombre, cedula, matricula, clave, curso))
            conexion.commit()
        except Exception as e:
            conexion.rollback()
            err_str = str(e).lower()
            if "cedula" in err_str and "unique" in err_str:
                error_mensaje = "Error: El número de cédula ya está registrado en el sistema."
            elif "matricula" in err_str and "unique" in err_str:
                error_mensaje = "Error: El número de matrícula ya pertenece a otro estudiante."
            else:
                error_mensaje = f"Error al guardar el estudiante: {e}"

    cursor.execute("SELECT id, nombre_completo, matricula, cedula, COALESCE(curso, '1er Curso') FROM estudiantes ORDER BY id DESC")
    datos = cursor.fetchall()
    cursor.close()
    conexion.close()
    return render_template_string(HTML_ESTUDIANTES, lista_alumnos=datos, error_mensaje=error_mensaje, cursos_lista=CURSOS_DISPONIBLES)

@app.route('/docentes', methods=['GET', 'POST'])
def docentes():
    if session.get('rol') != 'admin': return redirect(url_for('login'))
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    if request.method == 'POST':
        id_doc = request.form.get('id')
        nombre = request.form['nombre'].strip()
        cedula = request.form['cedula'].strip()
        clave = request.form.get('clave', '').strip()
        
        materias_seleccionadas = request.form.getlist('materias_sel')
        
        esp_nueva = request.form.get('especialidad_nueva', '').strip()
        curso_nueva_mat = request.form.get('curso_nueva_mat', '1er Curso')
        
        if esp_nueva:
            try:
                cursor.execute("INSERT INTO materias (nombre, curso) VALUES (%s, %s) ON CONFLICT DO NOTHING", (esp_nueva, curso_nueva_mat))
                conexion.commit()
                if esp_nueva not in materias_seleccionadas:
                    materias_seleccionadas.append(esp_nueva)
            except Exception:
                conexion.rollback()

        especialidad_display = ", ".join(materias_seleccionadas) if materias_seleccionadas else "General"

        if id_doc:
            if clave:
                cursor.execute("UPDATE docentes SET nombre_completo=%s, cedula=%s, especialidad=%s, clave=%s WHERE id=%s", (nombre, cedula, especialidad_display, clave, id_doc))
            else:
                cursor.execute("UPDATE docentes SET nombre_completo=%s, cedula=%s, especialidad=%s WHERE id=%s", (nombre, cedula, especialidad_display, id_doc))
            
            cursor.execute("DELETE FROM docente_materias WHERE docente_id = %s", (id_doc,))
            for mat in materias_seleccionadas:
                try:
                    cursor.execute("INSERT INTO docente_materias (docente_id, materia) VALUES (%s, %s)", (id_doc, mat))
                except Exception:
                    conexion.rollback()
        else:
            if not clave: clave = 'profe123'
            cursor.execute(
                "INSERT INTO docentes (nombre_completo, cedula, clave, especialidad) VALUES (%s, %s, %s, %s) RETURNING id", 
                (nombre, cedula, clave, especialidad_display)
            )
            nuevo_id = cursor.fetchone()[0]
            for mat in materias_seleccionadas:
                try:
                    cursor.execute("INSERT INTO docente_materias (docente_id, materia) VALUES (%s, %s)", (nuevo_id, mat))
                except Exception:
                    conexion.rollback()

        conexion.commit()

    cursor.execute("""
        SELECT d.id, d.nombre_completo, d.cedula, d.especialidad,
               COALESCE(STRING_AGG(DISTINCT dm.materia, ', '), 'Sin materias') AS materias_asignadas
        FROM docentes d
        LEFT JOIN docente_materias dm ON d.id = dm.docente_id
        GROUP BY d.id, d.nombre_completo, d.cedula, d.especialidad
        ORDER BY d.id DESC
    """)
    datos = cursor.fetchall()
    
    cursor.execute("SELECT nombre, COALESCE(curso, '1er Curso') FROM materias ORDER BY nombre ASC")
    materias_existentes = cursor.fetchall()

    cursor.close()
    conexion.close()
    return render_template_string(HTML_DOCENTES, lista_docentes=datos, materias_existentes=materias_existentes, cursos_lista=CURSOS_DISPONIBLES)

@app.route('/asignar_materias/<int:docente_id>', methods=['GET', 'POST'])
def asignar_materias(docente_id):
    if session.get('rol') != 'admin': return redirect(url_for('login'))
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    cursor.execute("SELECT nombre_completo FROM docentes WHERE id = %s", (docente_id,))
    doc = cursor.fetchone()
    nombre_docente = doc[0] if doc else "Docente"
    
    if request.method == 'POST':
        materia = request.form['materia']
        try:
            cursor.execute("INSERT INTO docente_materias (docente_id, materia) VALUES (%s, %s) ON CONFLICT (docente_id, materia) DO NOTHING", (docente_id, materia))
            cursor.execute("SELECT STRING_AGG(materia, ', ') FROM docente_materias WHERE docente_id = %s", (docente_id,))
            todas_mats = cursor.fetchone()[0] or "General"
            cursor.execute("UPDATE docentes SET especialidad = %s WHERE id = %s", (todas_mats, docente_id))
            conexion.commit()
        except Exception:
            conexion.rollback()
            
    cursor.execute("SELECT id, materia FROM docente_materias WHERE docente_id = %s", (docente_id,))
    materias_asignadas = cursor.fetchall()
    
    cursor.execute("SELECT id, nombre, COALESCE(curso, '1er Curso') FROM materias ORDER BY nombre ASC")
    materias_totales = cursor.fetchall()
    
    cursor.close()
    conexion.close()
    return render_template_string(HTML_ASIGNAR_MATERIAS, nombre_docente=nombre_docente, docente_id=docente_id, materias_asignadas=materias_asignadas, materias_totales=materias_totales)

@app.route('/quitar_materia/<int:mat_id>/<int:docente_id>')
def quitar_materia(mat_id, docente_id):
    if session.get('rol') != 'admin': return redirect(url_for('login'))
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM docente_materias WHERE id = %s", (mat_id,))
    
    cursor.execute("SELECT STRING_AGG(materia, ', ') FROM docente_materias WHERE docente_id = %s", (docente_id,))
    resto = cursor.fetchone()
    cadena_mats = resto[0] if resto and resto[0] else "General"
    cursor.execute("UPDATE docentes SET especialidad = %s WHERE id = %s", (cadena_mats, docente_id))
    
    conexion.commit()
    cursor.close()
    conexion.close()
    return redirect(url_for('asignar_materias', docente_id=docente_id))

@app.route('/calificaciones', methods=['GET', 'POST'])
def calificaciones():
    rol = session.get('rol')
    if rol not in ['admin', 'docente']: return redirect(url_for('login'))
    
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    if request.method == 'POST':
        id_cal = request.form.get('id')
        alumno = request.form['alumno']
        materia = request.form['materia']
        nota = request.form['nota']
        
        if rol == 'docente':
            cursor.execute("SELECT 1 FROM docente_materias WHERE docente_id = %s AND materia = %s", (session['docente_id'], materia))
            if not cursor.fetchone():
                cursor.close()
                conexion.close()
                return redirect(url_for('calificaciones'))
        
        if id_cal:
            cursor.execute("UPDATE calificaciones SET alumno=%s, materia=%s, nota=%s WHERE id=%s", (alumno, materia, nota, id_cal))
        else:
            try:
                cursor.execute("INSERT INTO calificaciones (alumno, materia, nota) VALUES (%s, %s, %s)", (alumno, materia, nota))
            except Exception:
                conexion.rollback()
        conexion.commit()
        
    if rol == 'admin':
        cursor.execute("SELECT id, alumno, materia, nota FROM calificaciones ORDER BY id DESC")
        datos = cursor.fetchall()
        cursor.execute("SELECT nombre_completo, COALESCE(curso, '1er Curso') FROM estudiantes ORDER BY nombre_completo ASC")
        lista_est = cursor.fetchall()
        cursor.execute("SELECT nombre FROM materias ORDER BY nombre ASC")
        materias_disponibles = [m[0] for m in cursor.fetchall()]
    else:
        cursor.execute("SELECT materia FROM docente_materias WHERE docente_id = %s", (session['docente_id'],))
        materias_disponibles = [m[0] for m in cursor.fetchall()]
        
        if materias_disponibles:
            format_strings = ','.join(['%s'] * len(materias_disponibles))
            cursor.execute(f"SELECT id, alumno, materia, nota FROM calificaciones WHERE materia IN ({format_strings}) ORDER BY id DESC", tuple(materias_disponibles))
            datos = cursor.fetchall()
            
            cursor.execute(f"""
                SELECT DISTINCT e.nombre_completo, COALESCE(e.curso, '1er Curso')
                FROM estudiantes e
                JOIN alumno_materias am ON e.id = am.alumno_id
                WHERE am.materia IN ({format_strings})
                ORDER BY e.nombre_completo ASC
            """, tuple(materias_disponibles))
            lista_est = cursor.fetchall()
        else:
            datos = []
            lista_est = []
    
    cursor.close()
    conexion.close()
    return render_template_string(HTML_CALIFICACIONES, lista_calificaciones=datos, estudiantes_dropdown=lista_est, materias_disponibles=materias_disponibles)

@app.route('/asistencia', methods=['GET', 'POST'])
def asistencia():
    rol = session.get('rol')
    if rol not in ['admin', 'docente']: return redirect(url_for('login'))
    
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    if request.method == 'POST':
        alumno = request.form.get('alumno')
        materia = request.form.get('materia')
        estado = request.form.get('estado')
        
        if rol == 'docente':
            cursor.execute("SELECT 1 FROM docente_materias WHERE docente_id = %s AND materia = %s", (session['docente_id'], materia))
            if not cursor.fetchone():
                cursor.close()
                conexion.close()
                return redirect(url_for('asistencia'))

        if alumno and materia and estado:
            cursor.execute("INSERT INTO asistencia (alumno, materia, estado, fecha) VALUES (%s, %s, %s, CURRENT_DATE)", (alumno, materia, estado))
            conexion.commit()
        
    if rol == 'admin':
        cursor.execute("SELECT id, alumno, materia, estado, fecha FROM asistencia ORDER BY id DESC")
        datos = cursor.fetchall()
        cursor.execute("SELECT nombre_completo, COALESCE(curso, '1er Curso') FROM estudiantes ORDER BY nombre_completo ASC")
        lista_est = cursor.fetchall()
        cursor.execute("SELECT nombre FROM materias ORDER BY nombre ASC")
        materias_disponibles = [m[0] for m in cursor.fetchall()]
    else:
        cursor.execute("SELECT materia FROM docente_materias WHERE docente_id = %s", (session['docente_id'],))
        materias_disponibles = [m[0] for m in cursor.fetchall()]
        
        if materias_disponibles:
            format_strings = ','.join(['%s'] * len(materias_disponibles))
            cursor.execute(f"SELECT id, alumno, materia, estado, fecha FROM asistencia WHERE materia IN ({format_strings}) ORDER BY id DESC", tuple(materias_disponibles))
            datos = cursor.fetchall()
            
            cursor.execute(f"""
                SELECT DISTINCT e.nombre_completo, COALESCE(e.curso, '1er Curso')
                FROM estudiantes e
                JOIN alumno_materias am ON e.id = am.alumno_id
                WHERE am.materia IN ({format_strings})
                ORDER BY e.nombre_completo ASC
            """, tuple(materias_disponibles))
            lista_est = cursor.fetchall()
        else:
            datos = []
            lista_est = []
            
    cursor.close()
    conexion.close()
    return render_template_string(HTML_ASISTENCIA, lista_asistencia=datos, estudiantes_dropdown=lista_est, materias_disponibles=materias_disponibles)

@app.route('/tablon', methods=['GET', 'POST'])
def tablon():
    rol = session.get('rol')
    if not rol: return redirect(url_for('login'))
    
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    if request.method == 'POST' and rol in ['admin', 'docente']:
        materia = request.form['materia']
        mensaje = request.form['mensaje']
        autor = session.get('nombre', 'Administrador')
        
        if rol == 'docente':
            cursor.execute("SELECT 1 FROM docente_materias WHERE docente_id = %s AND materia = %s", (session['docente_id'], materia))
            if not cursor.fetchone():
                cursor.close()
                conexion.close()
                return redirect(url_for('tablon'))
                
        cursor.execute("INSERT INTO tablon_materias (materia, mensaje, autor) VALUES (%s, %s, %s)", (materia, mensaje, autor))
        conexion.commit()
        
    cursor.execute("SELECT id, materia, mensaje, autor, fecha FROM tablon_materias ORDER BY id DESC")
    posts = cursor.fetchall()
    
    if rol == 'admin':
        cursor.execute("SELECT nombre FROM materias ORDER BY nombre ASC")
        materias_disponibles = [m[0] for m in cursor.fetchall()]
    elif rol == 'docente':
        cursor.execute("SELECT materia FROM docente_materias WHERE docente_id = %s", (session['docente_id'],))
        materias_disponibles = [m[0] for m in cursor.fetchall()]
    else:
        materias_disponibles = []
        
    cursor.close()
    conexion.close()
    return render_template_string(HTML_TABLON, tablon_posts=posts, materias_disponibles=materias_disponibles, rol_usuario=rol)

@app.route('/reportes')
def reportes():
    if session.get('rol') != 'admin': return redirect(url_for('login'))
    return render_template_string(HTML_REPORTES)

@app.route('/descargar_reporte')
def descargar_reporte():
    if session.get('rol') != 'admin': return redirect(url_for('login'))
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT alumno, materia, nota FROM calificaciones ORDER BY alumno ASC")
    filas = cursor.fetchall()
    cursor.close()
    conexion.close()
    
    contenido = "=== ACTA OFICIAL DE CALIFICACIONES - INSTITUCION ÑAMANDU ===\n\n"
    for f in filas:
        contenido += f"Alumno: {f[0]} | Materia: {f[1]} | Nota Final: {f[2]}\n"
        
    return Response(
        contenido,
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment;filename=acta_calificaciones.txt"}
    )

@app.route('/eliminar/<tipo>/<int:id>')
def eliminar(tipo, id):
    rol = session.get('rol')
    if not rol: return redirect(url_for('login'))
    
    tabla_valida = ""
    if tipo in ['estudiantes', 'docentes', 'materias'] and rol == 'admin':
        tabla_valida = tipo
    elif tipo in ['calificaciones', 'asistencia', 'tablon_materias']:
        tabla_valida = tipo
    elif tipo == 'tablon':
        tabla_valida = 'tablon_materias'
        
    if tabla_valida:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        
        if rol == 'docente' and tabla_valida in ['calificaciones', 'asistencia', 'tablon_materias']:
            cursor.execute(f"SELECT materia FROM {tabla_valida} WHERE id = %s", (id,))
            res = cursor.fetchone()
            if res:
                mat = res[0]
                cursor.execute("SELECT 1 FROM docente_materias WHERE docente_id = %s AND materia = %s", (session['docente_id'], mat))
                if not cursor.fetchone():
                    cursor.close()
                    conexion.close()
                    return redirect(request.referrer or url_for('inicio'))
                    
        cursor.execute(f"DELETE FROM {tabla_valida} WHERE id = %s", (id,))
        conexion.commit()
        cursor.close()
        conexion.close()
        
    return redirect(request.referrer or url_for('inicio'))

@app.route('/mi_portal')
def mi_portal():
    if session.get('rol') != 'alumno': return redirect(url_for('login'))
    nombre_alumno = session['nombre']
    alumno_id = session['alumno_id']
    
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    cursor.execute("SELECT cedula, foto, anio_nacimiento, carrera, COALESCE(curso, '1er Curso') FROM estudiantes WHERE id = %s", (alumno_id,))
    usuario_datos = cursor.fetchone() or ["", "", "", "", "1er Curso"]
    
    cursor.execute("SELECT materia, nota FROM calificaciones WHERE alumno = %s ORDER BY materia ASC", (nombre_alumno,))
    mis_notas = cursor.fetchall()

    cursor.execute("SELECT materia, estado, fecha FROM asistencia WHERE alumno = %s ORDER BY fecha DESC", (nombre_alumno,))
    mis_asistencias = cursor.fetchall()

    cursor.execute("""
        SELECT DISTINCT materia FROM (
            SELECT materia FROM alumno_materias WHERE alumno_id = %s
            UNION
            SELECT materia FROM calificaciones WHERE alumno = %s
        ) as mats ORDER BY materia ASC
    """, (alumno_id, nombre_alumno))
    materias_alumno = [m[0] for m in cursor.fetchall()]

    cursor.close()
    conexion.close()
    
    return render_template_string(
        HTML_PORTAL_ALUMNO,
        nombre_estudiante=nombre_alumno,
        usuario_datos=usuario_datos,
        notas=mis_notas,
        mis_asistencias=mis_asistencias,
        materias_alumno=materias_alumno
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)