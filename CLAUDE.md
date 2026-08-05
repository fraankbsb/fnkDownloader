# fnkDownloader

Downloader console (Python) para Instagram, TikTok, YouTube e Facebook.
Script principal: `iniciar_download.py`.

## Sistema de auto-update

O app roda em varios PCs (notebook de edicao + PC de casa, as vezes mais).
Em vez de copiar arquivos manualmente entre eles, existe um sistema de
launcher + releases no GitHub:

- **Repositorio**: https://github.com/fraankbsb/fnkDownloader (publico —
  contem so codigo, NUNCA os arquivos de cookies).
- **`launcher.py`** → compilado uma unica vez em `fnkDownloader.exe`
  (PyInstaller `--onefile --windowed`). Tem 2 botoes: "Atualizar App" (baixa
  a release mais recente do GitHub e sobrescreve o payload local) e "Iniciar
  App" (abre `iniciar_download.py` numa nova janela de console). O `.exe`
  NUNCA precisa ser recompilado quando o codigo muda — so o payload muda.
- **`publish.py`** → roda no PC de edicao. `python publish.py auto` sobe a
  versao (patch +1), da commit+push no repo, empacota o payload num zip e
  publica como GitHub Release via `gh release create`.
- **`watch_and_publish.py`** + **`iniciar_vigia.bat`** → vigia que fica
  monitorando `iniciar_download.py`; ao detectar mudanca salva, espera 8s de
  silencio e chama `publish.py auto` sozinho. Dar duplo-clique no `.bat` no
  inicio de uma sessao de edicao.
- **`update_config.json`** → config por projeto: `repo` (OWNER/REPO),
  `entry_point` (arquivo principal), `app_title`, `payload_files` (lista do
  que entra no pacote). `version.json` guarda a versao local instalada.

### Regras importantes
- Cookies ficam numa pasta reservada `cookies/` (nao soltos na raiz):
  `cookies/instagram_cookies.txt`, `cookies/tiktok_cookies.txt`,
  `cookies/youtube_cookies.txt`, `cookies/facebook_cookies.txt`. So o
  `cookies/.gitkeep` e versionado; o `.gitignore` bloqueia `cookies/*.txt`.
  **Nunca** commitar, publicar em release, ou incluir em `payload_files`.
- `gh` CLI ja esta instalado e autenticado (conta `fraankbsb`) globalmente
  no PC de edicao — nao precisa reinstalar/reautenticar para novos repos.
- `publish.py` resolve o caminho do `gh.exe` via `shutil.which` com fallback
  para `C:\Program Files\GitHub CLI\gh.exe`, porque a sessao que roda o
  vigia pode nao ter o PATH atualizado.
- `publish.py` faz `git add -A` (nao so os arquivos do payload) antes de
  commitar — ja rolou de mudancas em `launcher.py`/`publish.py` ficarem sem
  commit porque so o payload era staged.
- Numeracao de versao so pode subir (nunca republicar com o mesmo numero ou
  menor, senao o launcher nao detecta a atualizacao).
- Existe um prompt generico pronto pra replicar esse mesmo sistema em outros
  projetos: https://claude.ai/code/artifact/ac5f44a6-4721-4f5c-8b56-74d0e6ccde86
  (inclui a licao de portabilidade entre discos abaixo).

### Portabilidade entre PCs (D: aqui, C: no PC de casa)
- **Nunca hardcode letra de disco** (`D:/...`) em caminho default. `BASE_VIDEOS`
  e `PASTA_RAIZ` calculam o drive a partir de onde o proprio script esta
  rodando (`Path(__file__).resolve().anchor`), porque nem todo PC tem os
  mesmos discos — deu `FileNotFoundError: D:\` no PC que so tem C:.
- Chrome usa perfil persistente por rede (`chrome_profiles/<rede>/`) —
  loga uma vez, sessao fica salva pras proximas execucoes (sem repetir login).
  Tambem esta no `.gitignore` (equivale a credencial).
- Extracao de videos (Instagram e Facebook) cai pra cookies da sessao viva do
  Chrome (`driver.get_cookies()`) quando o arquivo `cookies/<rede>_cookies.txt`
  nao existe — nao depende só do arquivo manual.

## Redes suportadas (iniciar_download.py)
- Instagram: Selenium + requests via API privada. Cookies em
  `cookies/instagram_cookies.txt` OU sessao do Chrome ja logada.
- Facebook: so REELS (nao "todos os videos" — yt-dlp nao tem extrator de
  listagem de pagina do Facebook, so de reel individual `facebook.com/reel/<id>`).
  Coleta via Selenium rolando a aba `/reels` (scrollIntoView no ultimo reel
  encontrado, nao `window.scrollBy` — a grade nao reage a scroll da janela).
  Download via `yt-dlp` com `--impersonate chrome` (exige `curl_cffi` 0.10.x-0.15.x,
  0.16+ nao e suportado pelo yt-dlp atual) + cookies da sessao do Chrome.
  Sem filtro por data (Facebook nao expoe isso na listagem), so por quantidade.
  **Atencao:** "Cannot parse data" e um bug conhecido e ainda sem correcao no
  proprio yt-dlp (nao e algo pra tentar consertar aqui) — `_pip_atualizar`
  forca update do yt-dlp a cada execucao pra pegar correcoes assim que saem.
- TikTok / YouTube: via `yt-dlp`, cookies opcionais em `cookies/<rede>_cookies.txt`.
  YouTube tem opcao extra de Videos/Shorts/Ambos.
- Modo "por perfil" (com filtro de periodo, exceto Facebook) ou "URLs soltas"
  (cola links direto) para todas as redes.
