"""
==========================================================
  🎌  ANIME MULTITHREAD EXPLORER
  API: AniList GraphQL (graphql.anilist.co) — Gratis, sin API key
  Autor: Threading Project
==========================================================

Hilos que se ejecutan en paralelo:
  1. 📰 Noticias / Anime más populares del momento (TRENDING)
  2. 🎬 Estrenos de la temporada actual (RELEASING)
  3. 🔍 Búsqueda de un anime específico
"""

import threading
import requests
from datetime import datetime

# Introduce El anime a buscar!
AnimeSearch = input("Ingrese el nombre del anime a buscar: ")
# ─────────────────────────────────────────────
#  CONFIGURACIÓN
# ─────────────────────────────────────────────
ANILIST_URL  = "https://graphql.anilist.co"
ANIME_BUSCAR = AnimeSearch  # ← Anime buscado por el usuario

# Resultados compartidos (cada hilo escribe aquí)
resultados = {
    "trending":  None,
    "temporada": None,
    "busqueda":  None,
}

# Lock para imprimir sin mezclar salidas de hilos
print_lock = threading.Lock()


# ─────────────────────────────────────────────
#  UTILIDADES
# ─────────────────────────────────────────────
def log(hilo: str, mensaje: str):
    """Imprime un mensaje con el nombre del hilo de forma segura."""
    with print_lock:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [{hilo}] {mensaje}")


def graphql_query(query: str, variables: dict = None) -> dict:
    """Ejecuta una consulta GraphQL contra AniList."""
    try:
        resp = requests.post(
            ANILIST_URL,
            json={"query": query, "variables": variables or {}},
            headers={"Content-Type": "application/json"},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


# ─────────────────────────────────────────────
#  HILO 1 — TRENDING (lo más popular ahora)
# ─────────────────────────────────────────────
def obtener_trending():
    nombre_hilo = "Hilo-Trending"
    log(nombre_hilo, "Iniciando — buscando anime más populares del momento...")

    query = """
    query {
      Page(page: 1, perPage: 5) {
        media(type: ANIME, sort: TRENDING_DESC) {
          title { romaji english }
          episodes
          status
          averageScore
          genres
          siteUrl
        }
      }
    }
    """
    data = graphql_query(query)

    if "data" in data:
        animes = data["data"]["Page"]["media"]
        resultados["trending"] = animes
        log(nombre_hilo, f"{len(animes)} anime trending obtenidos.")
    else:
        resultados["trending"] = []
        log(nombre_hilo, f"Error: {data.get('error', 'desconocido')}")


# ─────────────────────────────────────────────
#  HILO 2 — TEMPORADA ACTUAL (ESTRENOS)
# ─────────────────────────────────────────────
def obtener_temporada_actual():
    nombre_hilo = "Hilo-Temporada"
    log(nombre_hilo, "Iniciando — buscando estrenos de la temporada actual...")

    query = """
    query {
      Page(page: 1, perPage: 10) {
        media(type: ANIME, status: RELEASING, sort: POPULARITY_DESC) {
          title { romaji english }
          episodes
          status
          season
          seasonYear
          averageScore
          nextAiringEpisode {
            episode
            airingAt
          }
          genres
        }
      }
    }
    """
    data = graphql_query(query)

    if "data" in data:
        animes = data["data"]["Page"]["media"]
        resultados["temporada"] = animes
        log(nombre_hilo, f"{len(animes)} estrenos en emisión encontrados.")
    else:
        resultados["temporada"] = []
        log(nombre_hilo, f"Error: {data.get('error', 'desconocido')}")


# ─────────────────────────────────────────────
#  HILO 3 — BÚSQUEDA DE ANIME ESPECÍFICO
# ─────────────────────────────────────────────
def buscar_anime(nombre: str):
    nombre_hilo = "Hilo-Busqueda"
    log(nombre_hilo, f"Iniciando — buscando '{nombre}'...")

    query = """
    query ($search: String) {
      Page(page: 1, perPage: 3) {
        media(type: ANIME, search: $search) {
          title { romaji english }
          episodes
          status
          averageScore
          genres
          season
          seasonYear
          siteUrl
        }
      }
    }
    """
    data = graphql_query(query, variables={"search": nombre})

    if "data" in data:
        animes = data["data"]["Page"]["media"]
        resultados["busqueda"] = animes
        log(nombre_hilo, f"{len(animes)} resultados para '{nombre}'.")
    else:
        resultados["busqueda"] = []
        log(nombre_hilo, f"Error: {data.get('error', 'desconocido')}")


# ─────────────────────────────────────────────
#  MOSTRAR RESULTADOS
# ─────────────────────────────────────────────
def mostrar_trending():
    print("\n" + "═" * 65)
    print("ANIME MAS POPULARES DEL MOMENTO (TRENDING)")
    print("═" * 65)
    animes = resultados.get("trending") or []
    if not animes:
        print("  Sin datos disponibles.")
        return
    for i, a in enumerate(animes, 1):
        titulo  = a["title"].get("english") or a["title"].get("romaji", "?")
        score   = a.get("averageScore", "N/A")
        eps     = a.get("episodes", "?")
        estado  = a.get("status", "?")
        generos = ", ".join(a.get("genres", [])[:3])
        url     = a.get("siteUrl", "")
        print(f"  {i}. {titulo}")
        print(f"      Score: {score}/100  |  Eps: {eps}  |  Estado: {estado}")
        print(f"      Géneros: {generos}")
        if url:
            print(f"      URL: {url}")
        print()


def mostrar_temporada():
    print("\n" + "═" * 65)
    print("ANIME EN EMISION AHORA (TEMPORADA ACTUAL)")
    print("═" * 65)
    animes = resultados.get("temporada") or []
    if not animes:
        print("  Sin datos de temporada.")
        return
    for i, a in enumerate(animes, 1):
        titulo   = a["title"].get("english") or a["title"].get("romaji", "?")
        score    = a.get("averageScore", "N/A")
        temporada = f"{a.get('season', '?')} {a.get('seasonYear', '')}"
        generos  = ", ".join(a.get("genres", [])[:3])
        proximo  = a.get("nextAiringEpisode")
        if proximo:
            ep_info = f"Próx. ep: #{proximo['episode']}"
        else:
            ep_info = f"Total eps: {a.get('episodes', '?')}"
        print(f"  {i}. {titulo}")
        print(f"      Score: {score}/100  |  Temporada: {temporada}  |  {ep_info}")
        print(f"      Géneros: {generos}")
        print()


def mostrar_busqueda():
    print("\n" + "═" * 65)
    print(f"BUSQUEDA: '{ANIME_BUSCAR}'")
    print("═" * 65)
    animes = resultados.get("busqueda") or []
    if not animes:
        print("  Sin resultados.")
        return
    for i, a in enumerate(animes, 1):
        titulo    = a["title"].get("english") or a["title"].get("romaji", "?")
        titulo_ro = a["title"].get("romaji", "")
        score     = a.get("averageScore", "N/A")
        eps       = a.get("episodes", "?")
        temporada = f"{a.get('season', '?')} {a.get('seasonYear', '')}"
        generos   = ", ".join(a.get("genres", [])[:4])
        url       = a.get("siteUrl", "")
        print(f"  {i}. {titulo}  ({titulo_ro})")
        print(f"      Score: {score}/100  |  Eps: {eps}  |  Temporada: {temporada}")
        print(f"      Géneros: {generos}")
        if url:
            print(f"      URL: {url}")
        print()


# ─────────────────────────────────────────────
#  PROGRAMA PRINCIPAL
# ─────────────────────────────────────────────
def main():
    print("=" * 65)
    print("ANIME MULTITHREAD EXPLORER")
    print(f"    API: AniList GraphQL ({ANILIST_URL})")
    print(f"    Anime a buscar: {ANIME_BUSCAR}")
    print("=" * 65)
    print("\nLanzando 3 hilos en paralelo...\n")

    # Crear los 3 hilos
    hilo_trending  = threading.Thread(target=obtener_trending,          name="Hilo-Trending")
    hilo_temporada = threading.Thread(target=obtener_temporada_actual,  name="Hilo-Temporada")
    hilo_busqueda  = threading.Thread(target=buscar_anime,              args=(ANIME_BUSCAR,), name="Hilo-Busqueda")

    inicio = datetime.now()

    # ── Iniciar todos los hilos al mismo tiempo ──
    hilo_trending.start()
    hilo_temporada.start()
    hilo_busqueda.start()

    # ── Esperar a que todos finalicen ──
    hilo_trending.join()
    hilo_temporada.join()
    hilo_busqueda.join()

    fin = datetime.now()
    duracion = (fin - inicio).total_seconds()

    print(f"\nTodos los hilos terminaron en {duracion:.2f} segundos.\n")

    # Mostrar resultados consolidados
    mostrar_trending()
    mostrar_temporada()
    mostrar_busqueda()

    print("═" * 65)
    print("  FIN DEL PROGRAMA — Fuente: AniList (anilist.co)")
    print("═" * 65 + "\n")


if __name__ == "__main__":
    main()
