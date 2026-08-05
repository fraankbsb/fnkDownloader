#!/usr/bin/env python3
"""
fnkDownloaderPerfis v2 — Selenium + requests
Usa o Chrome logado para extrair URLs dos videos e baixa diretamente.
Execute: python iniciar_download.py
"""

import os
import sys
import re
import time
import json
import calendar
import subprocess
import threading
from pathlib import Path
from datetime import datetime, date

# ══════════════════════════════════════════════════════════════
#  DEPENDÊNCIAS — instala tudo antes de importar
# ══════════════════════════════════════════════════════════════

def _pip(pkg, import_name=None):
    import_name = import_name or pkg.replace("-", "_")
    try:
        __import__(import_name)
    except ImportError:
        print(f"  📦  Instalando {pkg}...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", pkg, "--quiet"],
            check=True
        )
        print(f"  ✓  {pkg} instalado!")

print("  🔄  Verificando dependencias...")
_pip("requests")
_pip("selenium")
_pip("webdriver-manager", "webdriver_manager")
print("  ✓  Dependencias OK!\n")

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


# BASE_VIDEOS é definido em runtime pelo usuário
BASE_VIDEOS = Path("D:/FNKSOCIALMIDIA/fnkPerfis")  # valor padrão, sobrescrito no main()

# ── Cores ─────────────────────────────────────────────────────
def cor(t, c):
    return f"\033[{c}m{t}\033[0m"

VERDE   = lambda t: cor(t, "92")
AMARELO = lambda t: cor(t, "93")
AZUL    = lambda t: cor(t, "94")
CIANO   = lambda t: cor(t, "96")
NEGRITO = lambda t: cor(t, "1")
ERRO    = lambda t: cor(t, "91")
CINZA   = lambda t: cor(t, "90")


# ══════════════════════════════════════════════════════════════
#  CONFIGURAÇÃO
# ══════════════════════════════════════════════════════════════

# BASE_VIDEOS é definido em tempo de execução após o usuário escolher a pasta

MESES_PT = {
    1:"Janeiro", 2:"Fevereiro", 3:"Marco",    4:"Abril",
    5:"Maio",    6:"Junho",     7:"Julho",     8:"Agosto",
    9:"Setembro",10:"Outubro",  11:"Novembro", 12:"Dezembro",
}

CATEGORIAS = {
    "1": {"nome": "Homens",       "emoji": "💪"},
    "2": {"nome": "Mulheres",     "emoji": "✨"},
    "3": {"nome": "Fitness",      "emoji": "🏋️"},
    "4": {"nome": "Animais",      "emoji": "🐾"},
    "5": {"nome": "Achadinhos",   "emoji": "🛍️"},
    "6": {"nome": "Mamae e Bebe", "emoji": "👶"},
    "7": {"nome": "Comedia",      "emoji": "😂"},
    "8": {"nome": "Outro",        "emoji": "📁"},
}


# ══════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════

def cabecalho(resumo=None):
    os.system("cls" if os.name == "nt" else "clear")
    print(NEGRITO(CIANO("=" * 58)))
    print(NEGRITO(CIANO("  📥  fnkDownloaderPerfis v2  —  Instagram")))
    print(NEGRITO(CIANO("=" * 58)))
    if resumo:
        print()
        for l in resumo:
            print(f"  {CINZA('✓')}  {l}")
    print()


def contar_videos(pasta: Path) -> int:
    exts = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
    try:
        return sum(1 for f in pasta.iterdir() if f.suffix.lower() in exts)
    except:
        return 0


def detectar_perfis_categoria(cat_key):
    cat  = CATEGORIAS[cat_key]
    pasta_cat = BASE_VIDEOS / cat["nome"]
    if pasta_cat.exists():
        return sorted([p.name for p in pasta_cat.iterdir() if p.is_dir()])
    return []


def _parse_mes_ano(s):
    s = s.strip().replace("-", "/")
    partes = s.split("/")
    mes, ano = int(partes[0]), int(partes[1])
    if 1 <= mes <= 12:
        return ano, mes
    raise ValueError

def _parse_data(s):
    return datetime.strptime(s.strip().replace("-", "/"), "%d/%m/%Y").date()


# ══════════════════════════════════════════════════════════════
#  MENUS
# ══════════════════════════════════════════════════════════════

def passo_categoria(resumo):
    cabecalho(resumo)
    print(AMARELO("  Qual CATEGORIA deste perfil?"))
    print()
    for k, v in CATEGORIAS.items():
        pasta_cat = BASE_VIDEOS / v["nome"]
        n = len([p for p in pasta_cat.iterdir() if p.is_dir()]) if pasta_cat.exists() else 0
        sufixo = CINZA(f"  ({n} perfis)") if n else ""
        print(f"    {VERDE(k)}.  {v['emoji']}  {v['nome']}{sufixo}")
    print()
    while True:
        op = input(AZUL("  Digite o numero: ")).strip()
        if op in CATEGORIAS:
            return op
        print(ERRO("  Opcao invalida.\n"))


def passo_perfil(cat_key, resumo):
    cat  = CATEGORIAS[cat_key]
    nome = cat["nome"]
    cabecalho(resumo)
    print(NEGRITO(AMARELO(f"  {cat['emoji']}  {nome}")))
    print()

    existentes = detectar_perfis_categoria(cat_key)
    if existentes:
        print(CINZA("  Perfis com pasta existente:"))
        for i, h in enumerate(existentes, 1):
            qtd = contar_videos(BASE_VIDEOS / nome / h)
            print(f"    {VERDE(str(i))}.  @{h:<32} {CINZA(str(qtd)+' vid.')}")
        print()

    print(AMARELO("  Digite os @ dos perfis (separados por virgula, sem @):"))
    print()
    while True:
        raw    = input(AZUL("  @: ")).strip()
        partes = [x.strip() for x in raw.split(",") if x.strip()]
        handles = []
        for p in partes:
            if p.isdigit() and existentes and 1 <= int(p) <= len(existentes):
                handles.append(existentes[int(p)-1])
            else:
                handles.append(p.lstrip("@"))
        handles = [h for h in handles if h]
        if handles:
            return handles
        print(ERRO("  Digite pelo menos um handle.\n"))


def passo_filtro(resumo):
    cabecalho(resumo)
    print(AMARELO("  O que deseja baixar?"))
    print()
    print(f"    {VERDE('1')}.  📥  Tudo           — todos os videos disponiveis")
    print(f"    {VERDE('2')}.  📅  Por mes         — ex: Junho/2026")
    print(f"    {VERDE('3')}.  📆  Por intervalo   — ex: 01/06/2026 a 30/06/2026")
    print(f"    {VERDE('4')}.  🔢  Por quantidade  — ex: ultimos 50 videos")
    print()

    while True:
        op = input(AZUL("  Escolha [1/2/3/4]: ")).strip()

        if op == "1":
            return None, None, None, "Tudo (sem limite)"

        elif op == "2":
            print()
            print(CINZA("  Formato: MM/AAAA"))
            while True:
                try:
                    ano, mes = _parse_mes_ano(input(AZUL("  Mes/Ano: ")))
                    ultimo   = calendar.monthrange(ano, mes)[1]
                    d_ini    = date(ano, mes, 1)
                    d_fim    = date(ano, mes, ultimo)
                    desc     = f"{MESES_PT[mes]}/{ano}"
                    return d_ini, d_fim, None, desc
                except:
                    print(ERRO("  Formato invalido. Use MM/AAAA.\n"))

        elif op == "3":
            print()
            print(CINZA("  Formato: DD/MM/AAAA"))
            while True:
                try:
                    d_ini = _parse_data(input(AZUL("  Data inicio: ")))
                    d_fim = _parse_data(input(AZUL("  Data fim   : ")))
                    if d_fim < d_ini:
                        print(ERRO("  Data fim anterior ao inicio.\n"))
                        continue
                    desc = f"{d_ini.strftime('%d/%m/%Y')} ate {d_fim.strftime('%d/%m/%Y')}"
                    return d_ini, d_fim, None, desc
                except:
                    print(ERRO("  Data invalida. Use DD/MM/AAAA.\n"))

        elif op == "4":
            print()
            while True:
                try:
                    qtd = int(input(AZUL("  Quantos videos? ")).strip())
                    if qtd < 1: raise ValueError
                    return None, None, qtd, f"Ultimos {qtd} videos"
                except:
                    print(ERRO("  Numero invalido.\n"))
        else:
            print(ERRO("  Opcao invalida.\n"))


# ══════════════════════════════════════════════════════════════
#  SELENIUM — extrai URLs de video e baixa
# ══════════════════════════════════════════════════════════════

# Pasta raiz dos perfis para escolha
PASTA_RAIZ = Path("D:/FNKSOCIALMIDIA/fnkPerfis")

# Cookies ficam na pasta do script
_SCRIPT_DIR         = Path(__file__).parent
COOKIES_FILE          = _SCRIPT_DIR / "instagram_cookies.txt"
TIKTOK_COOKIES_FILE   = _SCRIPT_DIR / "tiktok_cookies.txt"
YOUTUBE_COOKIES_FILE  = _SCRIPT_DIR / "youtube_cookies.txt"
FACEBOOK_COOKIES_FILE = _SCRIPT_DIR / "facebook_cookies.txt"

def _encontrar_cookies(nome_arquivo):
    """Busca o arquivo de cookies na pasta do script e também na PASTA_RAIZ."""
    candidatos = [
        _SCRIPT_DIR / nome_arquivo,
        PASTA_RAIZ / nome_arquivo,
        Path(nome_arquivo),
    ]
    for c in candidatos:
        if c.exists():
            return c
    return _SCRIPT_DIR / nome_arquivo  # retorna o caminho padrão mesmo não existindo


def iniciar_chrome():
    """Abre Chrome com seleniumwire para capturar trafego de rede."""
    opts = Options()
    opts.add_argument("--start-maximized")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)

    service = Service(ChromeDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=opts)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    # Navega para o Instagram primeiro (necessario para setar cookies no dominio)
    print("  🌐  Carregando Instagram...")
    driver.get("https://www.instagram.com/")
    time.sleep(2)

    # Injeta cookies do arquivo exportado
    if COOKIES_FILE.exists():
        print("  🍪  Injetando cookies...")
        _injetar_cookies(driver, COOKIES_FILE)
        driver.refresh()
        time.sleep(3)
        print("  ✓  Cookies injetados!")
    else:
        print(f"  ⚠️  Arquivo de cookies nao encontrado: {COOKIES_FILE}")
        print("  ℹ️  Faca login manualmente no Chrome que abriu.")
        input("  Pressione Enter apos fazer login no Instagram...")

    return driver


def _injetar_cookies(driver, cookies_path):
    """Le cookies no formato Netscape e injeta no driver."""
    try:
        for linha in cookies_path.read_text(encoding="utf-8").splitlines():
            linha = linha.strip()
            if not linha or linha.startswith("#"):
                continue
            partes = linha.split("\t")
            if len(partes) < 7:
                continue
            domain, _, path, secure, expiry, name, value = partes[:7]
            try:
                cookie = {
                    "name":   name,
                    "value":  value,
                    "domain": domain.lstrip("."),
                    "path":   path,
                    "secure": secure.upper() == "TRUE",
                }
                if expiry and expiry != "0":
                    cookie["expiry"] = int(expiry)
                driver.add_cookie(cookie)
            except Exception:
                pass
    except Exception as e:
        print(f"  ⚠️  Erro ao ler cookies: {e}")


def _get_cookies_dict(cookies_file):
    """Le cookies Netscape e retorna dict para requests."""
    cookies = {}
    try:
        for linha in cookies_file.read_text(encoding="utf-8").splitlines():
            linha = linha.strip()
            if not linha or linha.startswith("#"):
                continue
            partes = linha.split("\t")
            if len(partes) >= 7:
                cookies[partes[5]] = partes[6]
    except Exception as e:
        print(f"  ⚠️  Erro lendo cookies: {e}")
    return cookies


def extrair_urls_videos(driver, handle, d_ini=None, d_fim=None, max_videos=None):
    """
    Usa a API privada do Instagram diretamente via requests
    com os cookies do arquivo exportado.
    """
    print(f"\n  🔍  Buscando videos de @{handle} via API...")

    # Carrega cookies
    _cf = _encontrar_cookies("instagram_cookies.txt")
    cookies = _get_cookies_dict(_cf) if _cf.exists() else {}
    if not cookies:
        print(ERRO(f"  ❌  Cookies nao encontrados."))
        print(AMARELO(f"  ℹ️  Coloque o instagram_cookies.txt em: {_SCRIPT_DIR}"))
        print(AMARELO(f"       ou em: {PASTA_RAIZ}"))
        return []

    session = requests.Session()
    session.headers.update({
        "User-Agent":      "Instagram 275.0.0.27.98 Android",
        "Accept":          "*/*",
        "Accept-Language": "pt-BR,pt;q=0.9",
        "X-IG-App-ID":     "936619743392459",
        "X-ASBD-ID":       "198387",
        "Referer":         "https://www.instagram.com/",
        "Origin":          "https://www.instagram.com",
    })
    session.cookies.update(cookies)

    # Pega o user_id do perfil — tenta varios endpoints
    print(f"  🔎  Buscando user_id de @{handle}...")
    user_id = None
    import re as _re

    endpoints = [
        {
            "url": f"https://www.instagram.com/api/v1/users/web_profile_info/?username={handle}",
            "headers": {"X-Requested-With": "XMLHttpRequest", "X-IG-App-ID": "936619743392459"},
            "extractor": lambda j: j["data"]["user"]["id"],
        },
        {
            "url": f"https://i.instagram.com/api/v1/users/web_profile_info/?username={handle}",
            "headers": {"X-Requested-With": "XMLHttpRequest", "X-IG-App-ID": "936619743392459"},
            "extractor": lambda j: j["data"]["user"]["id"],
        },
        {
            "url": f"https://www.instagram.com/{handle}/?__a=1&__d=dis",
            "headers": {"X-Requested-With": "XMLHttpRequest"},
            "extractor": lambda j: j["graphql"]["user"]["id"],
        },
    ]

    for ep in endpoints:
        try:
            hdrs = dict(session.headers)
            hdrs.update(ep["headers"])
            r = session.get(ep["url"], headers=hdrs, timeout=15)
            if r.status_code != 200 or not r.text.strip():
                continue
            j = r.json()
            user_id = ep["extractor"](j)
            print(f"  ✓  user_id: {user_id}")
            break
        except Exception as e:
            print(f"  ⚠️  Endpoint falhou: {ep['url'][:60]}... ({e})")

    # Fallback: extrai do HTML da pagina
    if not user_id:
        try:
            print("  🔎  Tentando via pagina HTML...")
            r = session.get(
                f"https://www.instagram.com/{handle}/",
                headers={"Accept": "text/html"},
                timeout=15,
            )
            for pattern in [
                r'"pk"\s*:\s*"(\d+)"',
                r'"user_id"\s*:\s*"(\d+)"',
                r'"id"\s*:\s*"(\d+)"',
                r'profilePage_(\d+)',
                r'"owner"\s*:\s*\{[^}]*"id"\s*:\s*"(\d+)"',
            ]:
                m = _re.search(pattern, r.text)
                if m:
                    user_id = m.group(1)
                    print(f"  ✓  user_id via HTML: {user_id}")
                    break
        except Exception as e:
            print(f"  ❌  HTML fallback falhou: {e}")

    # Fallback final: usa o Selenium (Chrome ja aberto) para pegar o user_id
    if not user_id and driver:
        try:
            print("  🔎  Tentando via Chrome (Selenium)...")
            driver.get(f"https://www.instagram.com/{handle}/")
            time.sleep(3)
            html = driver.page_source
            for pattern in [
                r'"pk"\s*:\s*"(\d+)"',
                r'"user_id"\s*:\s*"(\d+)"',
                r'profilePage_(\d+)',
            ]:
                m = _re.search(pattern, html)
                if m:
                    user_id = m.group(1)
                    print(f"  ✓  user_id via Selenium: {user_id}")
                    break
        except Exception as e:
            print(f"  ❌  Selenium fallback falhou: {e}")

    if not user_id:
        print("  ❌  Nao foi possivel obter user_id. Cookies podem estar expirados.")
        print("  ℹ️  Exporte novos cookies do Instagram e salve em instagram_cookies.txt")
        return []

    urls_video      = []
    urls_set        = set()
    total_coletados = 0
    max_id          = None
    pagina          = 1

    def _add(v_url, pd, post_id):
        nonlocal total_coletados
        # Usa o ID do post como chave unica — evita duplicatas feed+reels
        chave = str(post_id) if post_id else v_url
        if v_url and chave not in urls_set:
            urls_set.add(chave)
            urls_video.append((v_url, pd, chave))
            total_coletados += 1
            print(f"  ✓  {total_coletados} videos encontrados...", end="\r")

    def _processar_items(items):
        nonlocal pagina
        # Conta quantos items desta pagina estao fora do periodo inferior
        # Só para quando TODOS os items da pagina sao anteriores a d_ini
        fora_periodo = 0
        for item in items:
            ts = item.get("taken_at")
            post_date = date.fromtimestamp(int(ts)) if ts else None
            post_id   = item.get("pk") or item.get("id") or item.get("code")

            # Pula posts mais novos que d_fim
            if d_fim and post_date and post_date > d_fim:
                continue

            # Conta posts mais antigos que d_ini mas nao para imediatamente
            if d_ini and post_date and post_date < d_ini:
                fora_periodo += 1
                continue

            mt = item.get("media_type", 0)
            if mt == 2:
                vers = item.get("video_versions", [])
                if vers:
                    _add(vers[0].get("url"), post_date, post_id)
            elif mt == 8:
                for idx_m, m in enumerate(item.get("carousel_media", [])):
                    if m.get("media_type") == 2:
                        vers = m.get("video_versions", [])
                        if vers:
                            _add(vers[0].get("url"), post_date, f"{post_id}_c{idx_m}")

            if max_videos and total_coletados >= max_videos:
                print(f"\n  ✓  Limite de {max_videos} videos atingido.")
                return True, True

        # Para quando todos os items da pagina sao anteriores ao periodo
        if d_ini and fora_periodo == len(items):
            print(f"\n  📅  Toda a pagina anterior a {d_ini}. Parando.")
            return True, False
        return False, False

    # ── 1. Reels (aba principal — endpoint clips) ─────────
    print(f"  🎬  Buscando Reels da aba /reels/...")
    max_id   = None
    pagina_r = 1
    while True:
        print(f"  📄  Reels página {pagina_r}...", end="\r")
        try:
            payload = {
                "target_user_id":     user_id,
                "page_size":          50,
                "include_feed_video": "1",
            }
            if max_id:
                payload["max_id"] = max_id

            r = session.post(
                "https://www.instagram.com/api/v1/clips/user/",
                data=payload,
                timeout=30,
            )
            j = r.json()
        except Exception as e:
            print(f"\n  ⚠️  Erro reels página {pagina_r}: {e}")
            break

        items_raw = j.get("items", [])
        if not items_raw:
            print(f"\n  ✓  Reels — sem mais itens.")
            break

        # Extrai o objeto "media" de cada item
        items = [it.get("media", it) for it in items_raw]

        parar_data, parar_max = _processar_items(items)
        if parar_max:
            break
        if parar_data:
            break

        paging = j.get("paging_info", {})
        more   = paging.get("more_available", False)
        max_id = paging.get("max_id") or paging.get("next_max_id")

        if not more or not max_id:
            print(f"\n  ✓  Reels completos — {pagina_r} página(s).")
            break

        pagina_r += 1
        time.sleep(1.0)

    # ── 2. Feed principal — pega videos que nao sao Reels ─
    print(f"\n  📋  Buscando videos do feed principal...")
    max_id = None
    while True:
        print(f"  📄  Feed página {pagina}...", end="\r")
        try:
            params = {"count": 50, "target_user_id": user_id}
            if max_id:
                params["max_id"] = max_id
            r = session.get(
                f"https://www.instagram.com/api/v1/feed/user/{user_id}/",
                params=params,
                timeout=30,
            )
            j = r.json()
        except Exception as e:
            print(f"\n  ⚠️  Erro feed página {pagina}: {e}")
            break

        items = j.get("items", [])
        if not items:
            print(f"\n  ✓  Feed principal completo.")
            break

        parar_data, parar_max = _processar_items(items)
        if parar_data or parar_max:
            break

        more   = j.get("more_available", False)
        max_id = j.get("next_max_id")
        if not more or not max_id:
            print(f"\n  ✓  Feed completo — {pagina} página(s).")
            break
        pagina += 1
        time.sleep(1.0)

    print(f"\n  📊  Total de URLs coletadas: {len(urls_video)}")
    return urls_video


def baixar_video(url, pasta, nome, session):
    """Baixa um video diretamente por URL."""
    try:
        resp = session.get(url, stream=True, timeout=60)
        resp.raise_for_status()
        caminho = pasta / nome
        with open(caminho, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"\n  ⚠️  Erro ao baixar {nome}: {e}")
        return False


def baixar_perfil_selenium(item, driver):
    handle     = item["handle"]
    nome_cat   = item["categoria"]
    d_ini      = item["data_ini"]
    d_fim      = item["data_fim"]
    max_videos = item["max_videos"]
    desc       = item["desc_filtro"]

    pasta = BASE_VIDEOS / handle.lower()
    pasta.mkdir(parents=True, exist_ok=True)

    # Arquivo de historico para nao re-baixar
    hist_path = pasta / "historico_downloads.txt"
    historico = set()
    if hist_path.exists():
        historico = set(hist_path.read_text(encoding="utf-8").splitlines())

    print()
    print(NEGRITO(f"  ▶  @{handle}  [{nome_cat}]"))
    print(CINZA( f"     Filtro : {desc}"))
    print(CINZA( f"     Pasta  : {pasta}"))
    print()

    inicio = time.time()

    # Coleta URLs via Selenium
    urls = extrair_urls_videos(driver, handle, d_ini, d_fim, max_videos)

    if not urls:
        print(AMARELO("  ⚠️  Nenhum video encontrado."))
        return {"handle": handle, "categoria": nome_cat, "videos": 0, "ok": False, "tempo": 0, "filtro": desc}

    # Baixa os videos
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0 Safari/537.36",
        "Referer": "https://www.instagram.com/",
    })

    # Passa cookies do driver para o requests
    for cookie in driver.get_cookies():
        session.cookies.set(cookie["name"], cookie["value"], domain=cookie.get("domain", ""))

    baixados = 0
    pulados  = 0

    print(f"\n  ⬇️   Baixando {len(urls)} videos...\n")

    for i, (url, post_date, post_id) in enumerate(urls, 1):
        data_str = post_date.strftime("%Y-%m-%d") if post_date else "sem-data"
        nome_arquivo = f"{data_str}_{i:04d}.mp4"

        # Usa ID do post como chave no historico — evita re-download
        chave = str(post_id)
        if chave in historico:
            pulados += 1
            continue

        print(f"  [{i}/{len(urls)}]  {nome_arquivo}  ", end="", flush=True)
        ok = baixar_video(url, pasta, nome_arquivo, session)

        if ok:
            baixados += 1
            historico.add(str(post_id))
            with open(hist_path, "a", encoding="utf-8") as f:
                f.write(str(post_id) + "\n")
            print(VERDE("✓"))
        else:
            print(ERRO("✗"))

    elapsed = time.time() - inicio
    qtd_total = contar_videos(pasta)

    print()
    print(VERDE(f"  ✓  {baixados} novos  |  {pulados} ja existiam  |  {qtd_total} total  |  {elapsed:.0f}s"))

    return {"handle": handle, "categoria": nome_cat, "videos": baixados, "ok": True, "tempo": elapsed, "filtro": desc}



# ══════════════════════════════════════════════════════════════
#  TIKTOK — API privada via requests
# ══════════════════════════════════════════════════════════════

def _sessao_tiktok():
    """Cria sessao requests com cookies do TikTok."""
    session = requests.Session()
    session.headers.update({
        "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Referer":         "https://www.tiktok.com/",
        "Origin":          "https://www.tiktok.com",
        "Accept-Language": "pt-BR,pt;q=0.9",
    })
    if TIKTOK_COOKIES_FILE.exists():
        cookies = _get_cookies_dict(TIKTOK_COOKIES_FILE)
        session.cookies.update(cookies)
    return session


def _tiktok_user_info(handle, session):
    """Busca user_id e sec_uid do perfil TikTok."""
    print(f"  🔎  Buscando info de @{handle} no TikTok...")

    # Tenta via API
    try:
        r = session.get(
            f"https://www.tiktok.com/@{handle}",
            timeout=15,
            allow_redirects=True,
        )
        import re as _re
        # Extrai sec_uid e user_id do HTML
        m_sec = _re.search(r'"secUid"\s*:\s*"([^"]+)"', r.text)
        m_uid = _re.search(r'"authorId"\s*:\s*"(\d+)"', r.text) or                 _re.search(r'"uniqueId"\s*:\s*"' + re.escape(handle) + r'"[^}]*"id"\s*:\s*"(\d+)"', r.text)

        sec_uid = m_sec.group(1) if m_sec else None
        user_id = m_uid.group(1) if m_uid else None

        if sec_uid:
            print(f"  ✓  sec_uid encontrado")
            return user_id, sec_uid
    except Exception as e:
        print(f"  ⚠️  Erro buscando perfil: {e}")

    return None, None


def extrair_urls_tiktok(handle, d_ini=None, d_fim=None, max_videos=None):
    """
    Busca videos do TikTok via API privada usando yt-dlp como motor
    (mais confiável que a API direta que exige device_id complexo).
    """
    import subprocess as _sp

    print(f"\n  🎵  Buscando videos de @{handle} no TikTok...")

    pasta_temp = BASE_VIDEOS / "_temp_tiktok"
    pasta_temp.mkdir(parents=True, exist_ok=True)
    json_file  = pasta_temp / f"{handle}_urls.txt"

    # Monta comando yt-dlp para extrair só URLs (sem baixar)
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--get-url",
        "--no-download",
        "--no-warnings",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--flat-playlist",
    ]

    if TIKTOK_COOKIES_FILE.exists():
        cmd += ["--cookies", str(TIKTOK_COOKIES_FILE)]

    if d_ini:
        cmd += ["--dateafter",  d_ini.strftime("%Y%m%d")]
    if d_fim:
        cmd += ["--datebefore", d_fim.strftime("%Y%m%d")]
    if max_videos:
        cmd += ["--max-downloads", str(max_videos)]

    cmd.append(f"https://www.tiktok.com/@{handle}")

    print(f"  📋  Coletando lista de videos (pode demorar)...")

    try:
        result = _sp.run(cmd, capture_output=True, text=True, timeout=300)
        linhas = [l.strip() for l in result.stdout.splitlines() if l.strip().startswith("http")]
        print(f"  ✓  {len(linhas)} URLs coletadas")
        return [(url, None, f"tt_{i}") for i, url in enumerate(linhas, 1)]
    except Exception as e:
        print(f"  ❌  Erro: {e}")
        return []


def baixar_perfil_tiktok(item):
    """Baixa videos do TikTok para a pasta correta."""
    handle     = item["handle"]
    nome_cat   = item["categoria"]
    d_ini      = item["data_ini"]
    d_fim      = item["data_fim"]
    max_videos = item["max_videos"]
    desc       = item["desc_filtro"]

    pasta = BASE_VIDEOS / handle.lower()
    pasta.mkdir(parents=True, exist_ok=True)

    hist_path = pasta / "historico_downloads.txt"
    historico = set()
    if hist_path.exists():
        historico = set(hist_path.read_text(encoding="utf-8").splitlines())

    print()
    print(NEGRITO(f"  ▶  @{handle}  [{nome_cat}]  🎵 TikTok"))
    print(CINZA( f"     Filtro : {desc}"))
    print(CINZA( f"     Pasta  : {pasta}"))
    print()

    inicio = time.time()

    # Usa yt-dlp diretamente para baixar (mais confiável para TikTok)
    _pip("yt-dlp", "yt_dlp")

    cmd = [
        sys.executable, "-m", "yt_dlp",
        "-f", "bestvideo+bestaudio/best",
        "--merge-output-format", "mp4",
        "--audio-quality", "0",
        "-o", str(pasta / "%(upload_date>%Y-%m-%d)s_%(id)s.%(ext)s"),
        "--download-archive", str(hist_path),
        "--no-warnings",
        "--retries", "5",
        "--ignore-errors",
        "--sleep-interval", "1",
    ]

    if TIKTOK_COOKIES_FILE.exists():
        cmd += ["--cookies", str(TIKTOK_COOKIES_FILE)]
    else:
        print(AMARELO("  ℹ️  Sem cookies — perfis publicos apenas."))

    if d_ini:
        cmd += ["--dateafter",  d_ini.strftime("%Y%m%d")]
    if d_fim:
        cmd += ["--datebefore", d_fim.strftime("%Y%m%d")]
    if max_videos:
        cmd += ["--max-downloads", str(max_videos)]

    cmd.append(f"https://www.tiktok.com/@{handle}")

    resultado = subprocess.run(cmd)

    elapsed   = time.time() - inicio
    qtd_total = contar_videos(pasta)
    ok        = resultado.returncode == 0

    print()
    print(VERDE(f"  ✓  {qtd_total} video(s) na pasta  |  {elapsed:.0f}s"))

    return {
        "handle":    handle,
        "categoria": nome_cat,
        "videos":    qtd_total,
        "ok":        ok,
        "tempo":     elapsed,
        "filtro":    desc,
        "rede":      "tiktok",
    }

# ══════════════════════════════════════════════════════════════
#  YOUTUBE — via yt-dlp (mesmo padrao do TikTok)
# ══════════════════════════════════════════════════════════════

def _youtube_url_canal(handle, tipo="videos"):
    """Monta a URL do canal a partir do handle informado.
    tipo: 'videos', 'shorts' ou 'ambos'."""
    h = handle.strip()
    if h.startswith("http"):
        return h
    aba = "shorts" if tipo == "shorts" else "videos"
    if h.startswith("@"):
        return f"https://www.youtube.com/{h}/{aba}"
    return f"https://www.youtube.com/@{h}/{aba}"


def passo_tipo_youtube(resumo):
    """Pergunta se quer baixar videos normais, shorts ou ambos."""
    cabecalho(resumo)
    print(AMARELO("  ▶️  YouTube  —  O que deseja baixar?"))
    print()
    print(f"    {VERDE('1')}.  🎬  Videos       — videos normais do canal")
    print(f"    {VERDE('2')}.  📱  Shorts       — apenas shorts do canal")
    print(f"    {VERDE('3')}.  📦  Ambos        — videos e shorts")
    print()
    while True:
        op = input(AZUL("  Escolha [1/2/3]: ")).strip()
        if op == "1":
            return "videos"
        elif op == "2":
            return "shorts"
        elif op == "3":
            return "ambos"
        print(ERRO("  Opcao invalida.\n"))


def baixar_perfil_youtube(item):
    """Baixa videos de um canal do YouTube para a pasta correta."""
    handle     = item["handle"]
    nome_cat   = item["categoria"]
    d_ini      = item["data_ini"]
    d_fim      = item["data_fim"]
    max_videos = item["max_videos"]
    desc       = item["desc_filtro"]
    tipo       = item.get("tipo_youtube", "videos")

    pasta = BASE_VIDEOS / handle.lower().lstrip("@")
    pasta.mkdir(parents=True, exist_ok=True)

    hist_path = pasta / "historico_downloads.txt"

    tipo_label = {"videos": "Videos", "shorts": "Shorts", "ambos": "Videos + Shorts"}[tipo]
    print()
    print(NEGRITO(f"  ▶  @{handle}  [{nome_cat}]  ▶️ YouTube ({tipo_label})"))
    print(CINZA( f"     Filtro : {desc}"))
    print(CINZA( f"     Pasta  : {pasta}"))
    print()

    inicio = time.time()

    _pip("yt-dlp", "yt_dlp")

    abas = ["videos", "shorts"] if tipo == "ambos" else [tipo]
    ok = True

    for aba in abas:
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "--merge-output-format", "mp4",
            "--audio-quality", "0",
            "-o", str(pasta / "%(upload_date>%Y-%m-%d)s_%(id)s.%(ext)s"),
            "--download-archive", str(hist_path),
            "--no-warnings",
            "--retries", "5",
            "--ignore-errors",
            "--sleep-interval", "1",
        ]

        if YOUTUBE_COOKIES_FILE.exists():
            cmd += ["--cookies", str(YOUTUBE_COOKIES_FILE)]
        else:
            print(AMARELO("  ℹ️  Sem cookies — apenas videos publicos."))

        if d_ini:
            cmd += ["--dateafter",  d_ini.strftime("%Y%m%d")]
        if d_fim:
            cmd += ["--datebefore", d_fim.strftime("%Y%m%d")]
        if max_videos:
            cmd += ["--max-downloads", str(max_videos)]

        cmd.append(_youtube_url_canal(handle, aba))

        resultado = subprocess.run(cmd)
        ok = ok and resultado.returncode == 0

    elapsed   = time.time() - inicio
    qtd_total = contar_videos(pasta)

    print()
    print(VERDE(f"  ✓  {qtd_total} video(s) na pasta  |  {elapsed:.0f}s"))

    return {
        "handle":    handle,
        "categoria": nome_cat,
        "videos":    qtd_total,
        "ok":        ok,
        "tempo":     elapsed,
        "filtro":    desc,
        "rede":      "youtube",
    }


# ══════════════════════════════════════════════════════════════
#  FACEBOOK — via yt-dlp (mesmo padrao do TikTok/YouTube)
# ══════════════════════════════════════════════════════════════

def _facebook_url_perfil(handle):
    """Monta a URL da aba de videos do perfil/pagina a partir do handle."""
    h = handle.strip()
    if h.startswith("http"):
        return h
    return f"https://www.facebook.com/{h.lstrip('@')}/videos"


def baixar_perfil_facebook(item):
    """Baixa videos de um perfil/pagina do Facebook para a pasta correta."""
    handle     = item["handle"]
    nome_cat   = item["categoria"]
    d_ini      = item["data_ini"]
    d_fim      = item["data_fim"]
    max_videos = item["max_videos"]
    desc       = item["desc_filtro"]

    pasta = BASE_VIDEOS / handle.lower().lstrip("@")
    pasta.mkdir(parents=True, exist_ok=True)

    hist_path = pasta / "historico_downloads.txt"

    print()
    print(NEGRITO(f"  ▶  @{handle}  [{nome_cat}]  📘 Facebook"))
    print(CINZA( f"     Filtro : {desc}"))
    print(CINZA( f"     Pasta  : {pasta}"))
    print()

    inicio = time.time()

    _pip("yt-dlp", "yt_dlp")

    cmd = [
        sys.executable, "-m", "yt_dlp",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "--audio-quality", "0",
        "-o", str(pasta / "%(upload_date>%Y-%m-%d)s_%(id)s.%(ext)s"),
        "--download-archive", str(hist_path),
        "--no-warnings",
        "--retries", "5",
        "--ignore-errors",
        "--sleep-interval", "1",
    ]

    if FACEBOOK_COOKIES_FILE.exists():
        cmd += ["--cookies", str(FACEBOOK_COOKIES_FILE)]
    else:
        print(AMARELO("  ℹ️  Sem cookies — apenas videos publicos."))
        print(CINZA (f"     Salve como: {FACEBOOK_COOKIES_FILE}"))

    if d_ini:
        cmd += ["--dateafter",  d_ini.strftime("%Y%m%d")]
    if d_fim:
        cmd += ["--datebefore", d_fim.strftime("%Y%m%d")]
    if max_videos:
        cmd += ["--max-downloads", str(max_videos)]

    cmd.append(_facebook_url_perfil(handle))

    resultado = subprocess.run(cmd)

    elapsed   = time.time() - inicio
    qtd_total = contar_videos(pasta)
    ok        = resultado.returncode == 0

    print()
    print(VERDE(f"  ✓  {qtd_total} video(s) na pasta  |  {elapsed:.0f}s"))

    return {
        "handle":    handle,
        "categoria": nome_cat,
        "videos":    qtd_total,
        "ok":        ok,
        "tempo":     elapsed,
        "filtro":    desc,
        "rede":      "facebook",
    }


# ══════════════════════════════════════════════════════════════
#  FLUXO PRINCIPAL
# ══════════════════════════════════════════════════════════════

def passo_modo_download(resumo, rede_emoji, rede_nome):
    """Pergunta se quer baixar por perfil ou por URLs soltas."""
    cabecalho(resumo)
    print(AMARELO(f"  {rede_emoji}  {rede_nome}  —  Como deseja baixar?"))
    print()
    print(f"    {VERDE('1')}.  👤  Por perfil     — informa o @ e escolhe periodo")
    print(f"    {VERDE('2')}.  🔗  Por URLs        — cola as URLs dos videos")
    print()
    while True:
        op = input(AZUL("  Escolha [1/2]: ")).strip()
        if op in ("1", "2"):
            return op
        print(ERRO("  Opcao invalida.\n"))


def passo_periodo(resumo):
    """Pergunta tudo ou periodo personalizado."""
    cabecalho(resumo)
    print(AMARELO("  Qual periodo deseja baixar?"))
    print()
    print(f"    {VERDE('1')}.  📥  Tudo           — todos os videos do perfil")
    print(f"    {VERDE('2')}.  📅  Personalizado   — ex: 01/05/2026 a 31/05/2026")
    print()
    while True:
        op = input(AZUL("  Escolha [1/2]: ")).strip()
        if op == "1":
            return None, None, "Tudo"
        elif op == "2":
            print()
            print(CINZA("  Formato: DD/MM/AAAA"))
            while True:
                try:
                    d_ini = datetime.strptime(
                        input(AZUL("  Data inicio: ")).strip().replace("-", "/"), "%d/%m/%Y"
                    ).date()
                    d_fim = datetime.strptime(
                        input(AZUL("  Data fim   : ")).strip().replace("-", "/"), "%d/%m/%Y"
                    ).date()
                    if d_fim < d_ini:
                        print(ERRO("  Data fim anterior ao inicio.\n"))
                        continue
                    desc = f"{d_ini.strftime('%d/%m/%Y')} a {d_fim.strftime('%d/%m/%Y')}"
                    return d_ini, d_fim, desc
                except ValueError:
                    print(ERRO("  Data invalida. Use DD/MM/AAAA.\n"))
        print(ERRO("  Opcao invalida.\n"))


def passo_urls_soltas(resumo, rede_emoji, rede_nome):
    """Coleta URLs soltas que o usuario quer baixar."""
    cabecalho(resumo)
    print(NEGRITO(AMARELO(f"  {rede_emoji}  {rede_nome}  —  URLs soltas")))
    print()
    print(CINZA("  Cole as URLs dos videos, uma por linha."))
    print(CINZA("  Quando terminar, deixe uma linha em branco e pressione Enter."))
    print()

    urls = []
    while True:
        linha = input(AZUL("  URL: ")).strip()
        if not linha:
            if urls:
                break
            print(CINZA("  Digite pelo menos uma URL."))
            continue
        if linha.startswith("http"):
            urls.append(linha)
            print(VERDE(f"  ✓  {len(urls)} URL(s) adicionada(s)"), end="\r")
        else:
            print(ERRO("  URL invalida (deve comecar com http)."))

    print()
    return urls


def baixar_urls_soltas(urls, categoria, rede, driver=None):
    """Baixa uma lista de URLs soltas para a pasta da categoria."""
    pasta = BASE_VIDEOS / "_urls_avulsas"
    pasta.mkdir(parents=True, exist_ok=True)

    hist_path = pasta / "historico_downloads.txt"
    historico = set()
    if hist_path.exists():
        historico = set(hist_path.read_text(encoding="utf-8").splitlines())

    print()
    print(NEGRITO(f"  ▶  {len(urls)} URLs  [{categoria}]"))
    print(CINZA( f"     Pasta : {pasta}"))
    print()

    inicio   = time.time()
    baixados = 0
    erros    = 0

    if rede in ("TikTok", "YouTube", "Facebook"):
        # yt-dlp para TikTok / YouTube / Facebook
        cookies_file = {
            "TikTok":   TIKTOK_COOKIES_FILE,
            "YouTube":  YOUTUBE_COOKIES_FILE,
            "Facebook": FACEBOOK_COOKIES_FILE,
        }[rede]
        _pip("yt-dlp", "yt_dlp")
        for i, url in enumerate(urls, 1):
            chave = url.split("?")[0].rstrip("/").split("/")[-1]
            if chave in historico:
                print(f"  [{i}/{len(urls)}]  ja baixado — pulando")
                continue

            print(f"  [{i}/{len(urls)}]  {url[:60]}...")
            cmd = [
                sys.executable, "-m", "yt_dlp",
                "-f", "bestvideo+bestaudio/best",
                "--merge-output-format", "mp4",
                "--audio-quality", "0",
                "-o", str(pasta / "%(upload_date>%Y-%m-%d)s_%(id)s.%(ext)s"),
                "--no-warnings", "--retries", "5",
            ]
            if cookies_file.exists():
                cmd += ["--cookies", str(cookies_file)]
            cmd.append(url)
            r = subprocess.run(cmd, capture_output=True)
            if r.returncode == 0:
                baixados += 1
                historico.add(chave)
                with open(hist_path, "a", encoding="utf-8") as f:
                    f.write(chave + "\n")
                print(VERDE(f"  ✓"))
            else:
                erros += 1
                print(ERRO(f"  ✗"))

    else:
        # Instagram — requests com cookies
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0 Safari/537.36",
            "Referer": "https://www.instagram.com/",
        })
        _cf     = _encontrar_cookies("instagram_cookies.txt")
        cookies = _get_cookies_dict(_cf) if _cf.exists() else {}
        if not _cf.exists():
            print(AMARELO(f"  ℹ️  Copie o instagram_cookies.txt para: {_SCRIPT_DIR}"))
        session.cookies.update(cookies)
        if driver:
            for c in driver.get_cookies():
                session.cookies.set(c["name"], c["value"], domain=c.get("domain", ""))

        # Usa yt-dlp para Instagram tbm (mais confiavel para URLs individuais)
        _pip("yt-dlp", "yt_dlp")
        for i, url in enumerate(urls, 1):
            chave = url.split("?")[0].rstrip("/").split("/")[-1]
            if chave in historico:
                print(f"  [{i}/{len(urls)}]  ja baixado — pulando")
                continue

            print(f"  [{i}/{len(urls)}]  {url[:60]}...")
            cmd = [
                sys.executable, "-m", "yt_dlp",
                "-f", "bestvideo+bestaudio/best",
                "--merge-output-format", "mp4",
                "--audio-quality", "0",
                "-o", str(pasta / "%(upload_date>%Y-%m-%d)s_%(id)s.%(ext)s"),
                "--no-warnings", "--retries", "5",
            ]
            if _cf.exists():
                cmd += ["--cookies", str(_cf)]
            cmd.append(url)
            r = subprocess.run(cmd, capture_output=True)
            if r.returncode == 0:
                baixados += 1
                historico.add(chave)
                with open(hist_path, "a", encoding="utf-8") as f:
                    f.write(chave + "\n")
                print(VERDE(f"  ✓"))
            else:
                erros += 1
                print(ERRO(f"  ✗"))

    elapsed = time.time() - inicio
    print()
    print(VERDE(f"  ✓  {baixados} baixados  |  {erros} erros  |  {elapsed:.0f}s"))
    return {"handle": "_urls_avulsas", "categoria": categoria, "videos": baixados, "ok": erros == 0, "tempo": elapsed, "filtro": f"{len(urls)} URLs"}


def escolher_pasta_destino():
    """
    Abre o explorador de arquivos do Windows para escolher a pasta de destino.
    Começa em PASTA_RAIZ. Se cancelar, oferece criar nova pasta ou digitar.
    """
    import tkinter as tk
    from tkinter import filedialog, simpledialog, messagebox

    cabecalho()
    print(AMARELO("  📁  Abrindo seletor de pasta..."))
    print(CINZA (f"     (Navegue ate a pasta desejada e clique em OK)"))
    print()

    # Garante que PASTA_RAIZ existe
    PASTA_RAIZ.mkdir(parents=True, exist_ok=True)

    # Janela tkinter oculta (só para o dialog)
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)   # fica na frente

    pasta_str = filedialog.askdirectory(
        title="Escolha a pasta onde salvar os videos",
        initialdir=str(PASTA_RAIZ),
        mustexist=False,
        parent=root,
    )
    root.destroy()

    if not pasta_str:
        # Usuário cancelou — oferece criar nova pasta
        cabecalho()
        print(AMARELO("  Nenhuma pasta selecionada."))
        print()
        print(f"    {VERDE('1')}.  Criar nova pasta em {PASTA_RAIZ}")
        print(f"    {VERDE('2')}.  Digitar caminho completo")
        print(f"    {VERDE('3')}.  Tentar abrir seletor novamente")
        print()
        while True:
            op = input(AZUL("  Escolha: ")).strip()
            if op == "1":
                nome  = input(AZUL("  Nome da nova pasta: ")).strip()
                pasta = PASTA_RAIZ / nome
                pasta.mkdir(parents=True, exist_ok=True)
                print(VERDE(f"  ✓  Pasta criada: {pasta}"))
                return pasta
            elif op == "2":
                caminho = input(AZUL("  Caminho completo: ")).strip()
                pasta   = Path(caminho)
                pasta.mkdir(parents=True, exist_ok=True)
                return pasta
            elif op == "3":
                return escolher_pasta_destino()
            print(ERRO("  Opcao invalida.\n"))

    pasta = Path(pasta_str)
    pasta.mkdir(parents=True, exist_ok=True)
    print(VERDE(f"  ✓  Pasta selecionada: {pasta}"))
    time.sleep(0.5)
    return pasta


def main():
    os.system("color")

    # ── 0. Escolha da pasta de destino ───────────────────────
    global BASE_VIDEOS
    BASE_VIDEOS = escolher_pasta_destino()

    # ── 1. Rede social ────────────────────────────────────────
    cabecalho()
    print(AMARELO("  Qual rede deseja baixar?"))
    print()
    print(f"    {VERDE('1')}.  📸  Instagram")
    print(f"    {VERDE('2')}.  🎵  TikTok")
    print(f"    {VERDE('3')}.  ▶️  YouTube")
    print(f"    {VERDE('4')}.  📘  Facebook")
    print()
    while True:
        rede = input(AZUL("  Escolha [1/2/3/4]: ")).strip()
        if rede in ("1", "2", "3", "4"):
            break
        print(ERRO("  Opcao invalida.\n"))

    eh_tiktok    = rede == "2"
    eh_youtube   = rede == "3"
    eh_facebook  = rede == "4"
    rede_nome  = ("TikTok" if eh_tiktok else
                  "YouTube" if eh_youtube else
                  "Facebook" if eh_facebook else "Instagram")
    rede_emoji = ("🎵" if eh_tiktok else
                  "▶️" if eh_youtube else
                  "📘" if eh_facebook else "📸")

    if eh_tiktok:
        _pip("yt-dlp", "yt_dlp")
        if not TIKTOK_COOKIES_FILE.exists():
            cabecalho()
            print(AMARELO("  ℹ️  Cookies do TikTok nao encontrados (opcional)."))
            print(CINZA (f"     Salve como: {TIKTOK_COOKIES_FILE}"))
            print(CINZA ("  Perfis publicos funcionam sem cookies."))
            print()
            input(AZUL("  Pressione Enter para continuar..."))

    if eh_youtube:
        _pip("yt-dlp", "yt_dlp")
        if not YOUTUBE_COOKIES_FILE.exists():
            cabecalho()
            print(AMARELO("  ℹ️  Cookies do YouTube nao encontrados (opcional)."))
            print(CINZA (f"     Salve como: {YOUTUBE_COOKIES_FILE}"))
            print(CINZA ("  Videos publicos funcionam sem cookies."))
            print()
            input(AZUL("  Pressione Enter para continuar..."))

    if eh_facebook:
        _pip("yt-dlp", "yt_dlp")
        if not FACEBOOK_COOKIES_FILE.exists():
            cabecalho()
            print(AMARELO("  ℹ️  Cookies do Facebook nao encontrados (opcional)."))
            print(CINZA (f"     Salve como: {FACEBOOK_COOKIES_FILE}"))
            print(CINZA ("  Videos publicos funcionam sem cookies; a maioria exige login."))
            print()
            input(AZUL("  Pressione Enter para continuar..."))

    resumo = []

    # ── 2. Modo: por perfil ou URLs soltas ───────────────────
    modo = passo_modo_download(resumo, rede_emoji, rede_nome)

    lote       = []
    lote_urls  = []   # para URLs soltas

    if modo == "2":
        # ── URLs SOLTAS ──────────────────────────────────────
        urls = passo_urls_soltas(resumo, rede_emoji, rede_nome)
        lote_urls.append({
            "urls": urls,
            "categoria": str(BASE_VIDEOS.name),
            "rede": rede_nome,
        })
        resumo.append(f"{rede_emoji}  {len(urls)} URLs")

    else:
        # ── POR PERFIL ───────────────────────────────────────
        while True:
            cabecalho(resumo)
            print(AMARELO("  Digite os @ dos perfis (separados por virgula, sem @):"))
            print()
            while True:
                raw = input(AZUL("  @: ")).strip()
                handles = [h.strip().lstrip("@") for h in raw.split(",") if h.strip()]
                if handles:
                    break
                print(ERRO("  Digite pelo menos um handle.\n"))

            d_ini, d_fim, desc = passo_periodo(
                resumo + [f"{rede_emoji}  @{', @'.join(handles)}"]
            )

            tipo_youtube = "videos"
            if eh_youtube:
                tipo_youtube = passo_tipo_youtube(
                    resumo + [f"{rede_emoji}  @{', @'.join(handles)}  —  {desc}"]
                )

            for h in handles:
                lote.append({
                    "handle":      h,
                    "categoria":   str(BASE_VIDEOS.name),
                    "data_ini":    d_ini,
                    "data_fim":    d_fim,
                    "max_videos":  None,
                    "desc_filtro": desc,
                    "rede":        rede_nome,
                    "tipo_youtube": tipo_youtube,
                })
                tipo_label = {"videos": "Videos", "shorts": "Shorts", "ambos": "Videos+Shorts"}[tipo_youtube]
                sufixo = f"  [{tipo_label}]" if eh_youtube else ""
                resumo.append(f"{rede_emoji}  @{h}  —  {desc}{sufixo}")

            cabecalho(resumo)
            mais = input(AZUL("  Adicionar mais perfis? [S/N]: ")).strip().upper()
            if mais != "S":
                break

    # ── 3. Confirmação ────────────────────────────────────────
    cabecalho(resumo)
    print(AMARELO("  ─" * 29))
    print(NEGRITO(AMARELO("  RESUMO DO LOTE")))
    print(AMARELO("  ─" * 29))
    print(f"  📁 Destino    : {BASE_VIDEOS}")
    print(f"  🌐 Rede       : {rede_emoji} {rede_nome}")
    print(f"  📋 Modo       : {'URLs soltas' if modo == '2' else 'Por perfil'}")
    print()
    for linha in resumo:
        print(f"  {CINZA('•')}  {linha}")
    print()

    if not eh_tiktok and not eh_youtube and not eh_facebook and modo == "1":
        print(AMARELO("  ⚠️  O Chrome vai abrir com sua conta do Instagram."))
        print(CINZA ("     Nao feche o Chrome durante o processo."))
        print()

    confirma = input(AZUL("  Tudo certo? S para iniciar / N para cancelar: ")).strip().upper()
    if confirma != "S":
        print(ERRO("\n  Cancelado.\n"))
        sys.exit(0)

    # ── 4. Execução ───────────────────────────────────────────
    resultados = []
    driver     = None

    if modo == "2":
        # URLs soltas
        cabecalho(resumo)
        print(CIANO(f"  🚀  Iniciando download de URLs...\n"))

        if not eh_tiktok and not eh_youtube and not eh_facebook:
            print(CIANO("  🌐  Abrindo Chrome para autenticacao..."))
            driver = iniciar_chrome()

        for i, item in enumerate(lote_urls, 1):
            print(NEGRITO(CIANO(f"  [{i}/{len(lote_urls)}]  {item['categoria']}  —  {len(item['urls'])} URLs")))
            r = baixar_urls_soltas(item["urls"], item["categoria"], item["rede"], driver)
            resultados.append(r)

    elif eh_tiktok:
        # TikTok por perfil
        cabecalho(resumo)
        print(CIANO(f"  🚀  Iniciando downloads TikTok...\n"))
        for i, item in enumerate(lote, 1):
            print(NEGRITO(CIANO(f"  [{i}/{len(lote)}]  @{item['handle']}")))
            r = baixar_perfil_tiktok(item)
            resultados.append(r)

    elif eh_youtube:
        # YouTube por perfil/canal
        cabecalho(resumo)
        print(CIANO(f"  🚀  Iniciando downloads YouTube...\n"))
        for i, item in enumerate(lote, 1):
            print(NEGRITO(CIANO(f"  [{i}/{len(lote)}]  @{item['handle']}")))
            r = baixar_perfil_youtube(item)
            resultados.append(r)

    elif eh_facebook:
        # Facebook por perfil/pagina
        cabecalho(resumo)
        print(CIANO(f"  🚀  Iniciando downloads Facebook...\n"))
        for i, item in enumerate(lote, 1):
            print(NEGRITO(CIANO(f"  [{i}/{len(lote)}]  @{item['handle']}")))
            r = baixar_perfil_facebook(item)
            resultados.append(r)

    else:
        # Instagram por perfil
        print()
        print(CIANO("  🚀  Abrindo Chrome..."))
        driver = iniciar_chrome()

        for i, item in enumerate(lote, 1):
            print(NEGRITO(CIANO(f"\n  [{i}/{len(lote)}]  @{item['handle']}")))
            r = baixar_perfil_selenium(item, driver)
            resultados.append(r)

    if driver:
        driver.quit()

    # ── 5. Resumo final ───────────────────────────────────────
    print()
    print(NEGRITO(CIANO("=" * 58)))
    print(NEGRITO(CIANO("  📊  RESUMO FINAL")))
    print(NEGRITO(CIANO("=" * 58)))
    print()

    total = 0
    for r in resultados:
        s = VERDE("✓") if r["ok"] else ERRO("✗")
        label = f"@{r['handle']}" if r['handle'] != '_urls_avulsas' else "URLs avulsas"
        print(f"  {s}  {label:<28} {r['videos']} vid.  |  {r['tempo']:.0f}s  |  {CINZA(r['filtro'])}")
        total += r["videos"]

    print()
    print(VERDE(f"  ✅  {total} videos baixados"))
    print(VERDE(f"  📁  {BASE_VIDEOS}"))
    print()
    input("  Pressione Enter para sair...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Interrompido.\n")
    except Exception:
        import traceback
        print("\n" + "=" * 58)
        print("  ERRO:")
        print("=" * 58)
        traceback.print_exc()
        print()
    finally:
        input("  Pressione Enter para fechar...")
