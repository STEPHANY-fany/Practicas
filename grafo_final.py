import sqlite3
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import random
import networkx as nx
from pyvis.network import Network
import re

def solicitud_a_rae(url):
    #web scraping utilizando la libreria de playwright, que simula un navegador 
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )

        page = browser.new_page(user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
        ))

        try:
            page.goto(url, timeout=60000)
            page.wait_for_load_state("networkidle", timeout=60000)
        except Exception as e:
            print(f"Error al cargar {url}: {e}")

        time.sleep(1)
        html = page.content()
        browser.close()
        return html
    

def limpiar_palabra(palabra):
    #dado que muchas plabras de la rae tiene más de una acepción, se limpia la palabra ya que al extraerlas de la RAE puede contener en su posición -1 , un número por ejemplo andar1 
    return re.sub(r'\d+$', '', palabra)

def iniciar_db():
    conn = sqlite3.connect("diccionario_rae.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS palabras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        palabra TEXT UNIQUE,
        explorada INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS relaciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        palabra_id INTEGER,
        relacionada_id INTEGER,
        tipo TEXT,
        UNIQUE(palabra_id, relacionada_id, tipo)
    )
    """)

    conn.commit()
    return conn


def extraer_sinonimos_y_antonimos(palabra,):
    print(palabra)
    palabra_limpia=limpiar_palabra(palabra)
    print(palabra_limpia)
    url = f"https://dle.rae.es/{palabra_limpia}" #consultar de namenra automatica la nueva palabra 
    print(url)
    html = solicitud_a_rae(url)
    soup = BeautifulSoup(html, "html.parser")
    
    sinonimos, antonimos = [], []



    #primer metódo para terminos (palabras normales que no tienen otras acepciones ya que sus datos dentro del html están guardados en la etiqueta h2 y class_=c-related-words)
    seccion_sin = soup.find("h2", string=lambda s: s and "Sinónimos" in s)
    if seccion_sin:
        ul_sin = seccion_sin.find_next("ul", class_="c-related-words")
        if ul_sin:
            sinonimos = [span.get_text(strip=True) for span in ul_sin.select("span.sin")]

    seccion_ant = soup.find("h2", string=lambda s: s and "Antónimos" in s)
    if seccion_ant:
        ul_ant = seccion_ant.find_next("ul", class_="c-related-words")
        if ul_ant:
            antonimos = [span.get_text(strip=True) for span in ul_ant.select("span.sin")]
    

   #segundo metodo , este metodo funciona para las palbras que tienen acepciones, a diferencia de los terminos normales los datos (sin y ant) se guardan en la etiqueta section
    if not sinonimos  and not  antonimos :
        seccion_sin = soup.find("section", id=re.compile("^sinonimos"))
        if seccion_sin:
            ul_sin = seccion_sin.find("ul", class_="c-related-words")
            if ul_sin:
                sinonimos = [
                    limpiar_palabra(span.get_text(strip=True))
                    for span in ul_sin.select("span.sin")
                ]

        seccion_ant = soup.find("section", id=re.compile("^antonimos"))
        if seccion_ant:
            ul_ant = seccion_ant.find("ul", class_="c-related-words")
            if ul_ant:
                antonimos = [
                    limpiar_palabra(span.get_text(strip=True))
                    for span in ul_ant.select("span.sin")
                ]

    return sinonimos, antonimos
    


def guardar_palabra(conn, palabra):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO palabras (palabra) VALUES (?)",
        (palabra,)
    )
    conn.commit()

def obtener_id(conn, palabra):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM palabras WHERE palabra = ?",
        (palabra,)
    )
    r = cursor.fetchone()
    return r[0] if r else None


def guardar_relacion(conn, p1, p2, tipo):
    id1 = obtener_id(conn, p1)
    id2 = obtener_id(conn, p2)

    if id1 and id2:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR IGNORE INTO relaciones (palabra_id, relacionada_id, tipo)
        VALUES (?, ?, ?)
        """, (id1, id2, tipo))
        conn.commit()


def marcar_explorada(conn, palabra):
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE palabras SET explorada = 1 WHERE palabra = ?",
        (palabra,)
    )
    conn.commit()


def explorar_desde_db(limite=250):
    conn = iniciar_db()
    cursor = conn.cursor()
    contador = 0

    while contador < limite:
        cursor.execute("""
        SELECT palabra FROM palabras
        WHERE explorada = 0
        LIMIT 1
        """)
        fila = cursor.fetchone()

        if not fila:
            print("✔ No hay más palabras pendientes")
            break

        palabra = fila[0]
        print("🔍 Explorando:", palabra)

        sin, ant = extraer_sinonimos_y_antonimos(palabra)

        for s in sin:
            s = limpiar_palabra(s)
            guardar_palabra(conn, s)
            guardar_relacion(conn, palabra, s, "sinonimo")

        for a in ant:
            a = limpiar_palabra(a)
            guardar_palabra(conn, a)
            guardar_relacion(conn, palabra, a, "antonimo")

        marcar_explorada(conn, palabra)
        contador += 1
        time.sleep(random.uniform(0.5, 0.8))

    conn.close()


def extraer_conjugaciones(palabra):
    print("Extrayendo todas las conjugaciones para la palabra", palabra)
    palabra = limpiar_palabra(palabra)
    url = f"https://dle.rae.es/{palabra}"
    html = solicitud_a_rae(url)
    soup = BeautifulSoup(html, "html.parser")

    conjugaciones = {}

    tablas = soup.select("table.c-table")

    if not tablas:
        print("No se encontraron conjugaciones.")
        return {}

    for tabla in tablas:
        h3 = tabla.find_previous("h3")
        tiempo = h3.get_text(strip=True) if h3 else "Tiempo verbal"

        conjugaciones[tiempo] = {}

        for fila in tabla.select("tr"):
            th = fila.find("th")
            td = fila.find("td")

            if th and td:
                persona = th.get_text(strip=True)
                forma = td.get_text(strip=True)
                conjugaciones[tiempo][persona] = forma
                print("Conjugación lista:", forma)

    print("\nConjugaciones para la palabra", palabra, "\n")

    for tiempo, formas in conjugaciones.items():
        print(f"{tiempo}")
        for persona, verbo in formas.items():
            print(f"  {persona}: {verbo}")
        print()

    return conjugaciones


def grafo_desde_db():
    conn = sqlite3.connect("diccionario_rae.db")
    cursor = conn.cursor()

    G = nx.Graph()

    cursor.execute("""
    SELECT p1.palabra, p2.palabra, r.tipo
    FROM relaciones r
    JOIN palabras p1 ON r.palabra_id = p1.id
    JOIN palabras p2 ON r.relacionada_id = p2.id
    """)

    for p1, p2, tipo in cursor.fetchall():
        color = "#3cff10" if tipo == "sinonimo" else "#f10fa5"
        G.add_edge(p1, p2, color=color)

    net = Network(
        height="800px",
        width="100%",
        bgcolor="#00294E",
        font_color="white",
        notebook=False  
    )

    net.show_buttons(filter_=["nodes", "interaction"])
    net.from_nx(G)

    net.write_html("grafo_rae_persistente.html", open_browser=True)

    conn.close()


menu = input("""
Menu:
1. Expandir grafo (nueva semilla)
2. Mostrar grafo
3. Conjugaciones
Seleccione opción: """)

if menu == "1":
    semilla = input("Ingrese palabra semilla: ").strip()
    conn = iniciar_db()
    guardar_palabra(conn, limpiar_palabra(semilla))
    conn.close()
    explorar_desde_db(limite=250)
    print("Base de datos actualizada")


elif menu == "2":
    grafo_desde_db()

elif menu == "3":
    palabra = input("Ingrese verbo para conjugar: ").strip()
    extraer_conjugaciones(palabra)

