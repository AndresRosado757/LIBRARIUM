import json, os, requests, time

def descargar(url, ruta):
    """Descarga robusta con verificación de integridad."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        r = requests.get(url, timeout=15, headers=headers)
        if r.status_code == 200 and len(r.content) > 3000:
            with open(ruta, 'wb') as f: f.write(r.content)
            return True
    except: pass
    return False

def buscar_google(query):
    """Busca en Google Books API y fuerza alta resolución."""
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=1"
    try:
        data = requests.get(url, timeout=10).json()
        if 'items' in data:
            v = data['items'][0]['volumeInfo'].get('imageLinks', {})
            img = v.get('thumbnail') or v.get('smallThumbnail')
            if img:
                return img.replace("http://", "https://").replace("&zoom=1", "&zoom=2")
    except: pass
    return None

def motor_portadas(libro):
    """Algoritmo incansable de 4 niveles."""
    libro_id = str(libro['id']).strip()
    ruta = f"portadas/{libro_id}.jpg"
    if os.path.exists(ruta): return ruta

    isbns = libro['isbn'] if isinstance(libro['isbn'], list) else [libro['isbn']]

    for isbn in isbns:
        isbn_c = str(isbn).strip()
        if descargar(f"https://covers.openlibrary.org/b/isbn/{isbn_c}-L.jpg?default=false", ruta):
            return ruta
        g_link = buscar_google(f"isbn:{isbn_c}")
        if g_link and descargar(g_link, ruta):
            return ruta

    t_link = buscar_google(f"intitle:{libro['titulo']}+inauthor:{libro['autor']}")
    if t_link and descargar(t_link, ruta):
        return ruta

    return None

def layout(titulo, contenido, depth=0):
    """Genera el layout con soporte para carpetas anidadas."""
    prefix = "../" * depth
    return f"""<!DOCTYPE html>
<html lang='es'>
<head>
    <meta charset='UTF-8'>
    <title>Librarium | {titulo}</title>
    <link rel='stylesheet' href='{prefix}style.css'>
</head>
<body>
    <nav class='main-nav'>
        <div class='logo'>LIBRARIUM.</div>
        <ul class='nav-links'>
            <li><a href='{prefix}index.html'>Inicio</a></li>
            <li><a href='{prefix}explorar.html'>Explorar</a></li>
            <li><a href='{prefix}ranking.html'>Ranking</a></li>
        </ul>
    </nav>
    {contenido}
</body>
</html>"""

def generar_web():
    # Asegurar directorios
    if not os.path.exists('portadas'): os.makedirs('portadas')
    if not os.path.exists('criticas'): os.makedirs('criticas')

    try:
        with open('libros.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"🔴 Error de lectura: {e}")
        return

    libros = [data] if isinstance(data, dict) else data
    libros = [b for b in libros if isinstance(b, dict) and 'id' in b]

    print(f"🚀 Procesando {len(libros)} libros...")

    # INDEX
    cards = ""
    for b in libros:
        motor_portadas(b)
        # Ruta corregida hacia la carpeta criticas/
        cards += f"""<a href="criticas/critica_{b['id']}.html" class="card">
            <img src="portadas/{b['id']}.jpg" onerror="this.src='https://via.placeholder.com/400x600?text={b['titulo']}'">
            <div class="card-info"><h3>{b['titulo']}</h3><p>{b['autor']}</p></div>
        </a>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(layout("Inicio", f"<main class='container'><h1>Críticas Destacadas</h1><div class='grid-books'>{cards}</div></main>"))

    # EXPLORAR
    filas = "".join([f"<tr><td>{b['titulo']}</td><td>{b['autor']}</td><td>{b.get('genero','-')}</td><td><a href='criticas/critica_{b['id']}.html' class='btn-table'>Análisis</a></td></tr>" for b in libros])
    with open("explorar.html", "w", encoding="utf-8") as f:
        f.write(layout("Explorar", f"<main class='container'><h1>Catálogo Maestro</h1><table class='book-table'><thead><tr><th>Título</th><th>Autor</th><th>Género</th><th>Acción</th></tr></thead><tbody>{filas}</tbody></table></main>"))

    # RANKING
    libros_ord = sorted(libros, key=lambda x: x.get('ranking', 99))
    r_cards = "".join([f'<a href="criticas/critica_{b["id"]}.html" class="card"><div class="card-info"><h3>#{b.get("ranking","?")} {b["titulo"]}</h3><p>{b["autor"]}</p></div></a>' for b in libros_ord])
    with open("ranking.html", "w", encoding="utf-8") as f:
        f.write(layout("Ranking", f"<main class='container'><h1>Top Editorial</h1><div class='grid-books'>{r_cards}</div></main>"))

    # CRÍTICAS (Guardado en criticas/ con depth=1)
    for b in libros:
        cont = f"""<article class='critique-body' style='max-width:800px; margin:40px auto; background:white; padding:40px; text-align:center; border-radius:12px; box-shadow: 0 10px 30px rgba(0,0,0,0.05);'>
            <img src='../portadas/{b['id']}.jpg' style='width:250px; border-radius:8px; margin-bottom:20px;' onerror='this.style.display="none"'>
            <h1>{b['titulo']}</h1>
            <h3 style='color:#777;'>{b['autor']}</h3>
            <hr style='margin:20px 0; opacity:0.1;'>
            <p style='text-align:justify; font-size:1.15rem; line-height:2;'>{b['critica']}</p>
            <br>
            <a href='../index.html' style='font-weight:bold; color:#b08d57; text-decoration:none;'>← Volver a la Biblioteca</a>
        </article>"""

        # Guardar dentro de la carpeta criticas
        with open(f"criticas/critica_{b['id']}.html", "w", encoding="utf-8") as f:
            f.write(layout(b['titulo'], cont, depth=1))

    print(f"\n✅ PROCESO COMPLETADO. Críticas guardadas en 'criticas/'.")

if __name__ == "__main__":
    generar_web()
