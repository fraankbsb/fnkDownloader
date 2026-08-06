# fnkDownloader

Downloader console (Python) para Instagram, TikTok, YouTube e Facebook.
Script principal: `iniciar_download.py`.

## Sistema de auto-update

O app roda em varios PCs (notebook de edicao + PC de casa, as vezes mais).
Em vez de copiar arquivos manualmente entre eles, existe um sistema de
launcher + releases no GitHub:

- **Repositorio**: https://github.com/fraankbsb/fnkDownloader (publico —
  contem so codigo, NUNCA os arquivos de cookies).
- **`launcher.py`** → compilado em `fnkDownloader.exe` (PyInstaller
  `--onefile --windowed`). Tem 2 botoes: "Atualizar App" (baixa a release
  mais recente do GitHub e sobrescreve o payload local) e "Iniciar App"
  (abre `iniciar_download.py` numa nova janela de console). So precisa
  recompilar quando `launcher.py` MESMO muda (mudancas em
  `iniciar_download.py` nao exigem recompilar nada, so publicar release
  normal). Comando de build:
  `python -m PyInstaller --onefile --windowed --name fnkDownloader --distpath . --workpath build launcher.py`
  — depois rodar `rm -rf build fnkDownloader.spec` e reanexar o `.exe` +
  `update_config.json` na release mais recente (nao sao republicados via
  `publish.py`, que so mexe no payload):
  `gh release upload <tag> fnkDownloader.exe update_config.json --repo fraankbsb/fnkDownloader --clobber`.
  **Atencao:** isso precisa ser refeito a cada nova release (mesmo uma so de
  docs) — o asset fica preso na tag antiga, e a tag "latest" muda a cada
  `publish.py`. Se pular esse passo, PCs novos que baixarem da release mais
  recente ficam sem o `.exe`/`update_config.json` de bootstrap.
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
  Tambem esta no `.gitignore` (equivale a credencial). Se o Chrome nao abrir
  ("session not created: Chrome instance exited"), geralmente e um
  `chromedriver.exe` orfao de execucao anterior segurando o perfil —
  `iniciar_chrome()` mata processos `chromedriver.exe` (nunca janelas normais
  do usuario) e tenta 1x de novo automaticamente antes de desistir.
- Extracao de videos (Instagram e Facebook) cai pra cookies da sessao viva do
  Chrome (`driver.get_cookies()`) quando o arquivo `cookies/<rede>_cookies.txt`
  nao existe — nao depende só do arquivo manual. Cookies exportados manualmente
  (extensao "Get cookies.txt LOCALLY" no Chrome, logado em instagram.com ou
  facebook.com → Export → salvar como `cookies/instagram_cookies.txt` /
  `cookies/facebook_cookies.txt`) tendem a ser mais completos/estaveis que a
  sessao do Selenium e sao tentados primeiro. Expiram com o tempo — se voltar
  erro de cookies invalidos, e so reexportar.
- Erros nao tratados (crash) sao salvos automaticamente em
  `erros/erro_AAAA-MM-DD_HHMMSS.txt` (alem de aparecer no console) — pasta
  local, no `.gitignore`, nao versionada.
- Qualidade de download: NUNCA restringir a busca de formato a `ext=mp4` no
  yt-dlp (`-f bestvideo[ext=mp4]+...`) — a melhor qualidade do YouTube em
  particular costuma vir em WebM, nao mp4. Usar sempre
  `-f bestvideo+bestaudio/best` (sem restricao de ext) e deixar
  `--merge-output-format mp4` cuidar do container final.

## Redes suportadas (iniciar_download.py)
- Instagram: Selenium + requests via API privada. Cookies em
  `cookies/instagram_cookies.txt` OU sessao do Chrome ja logada.
  **Cuidado com falha silenciosa:** qualquer resposta da API sem a chave
  "items" (rate-limit, checkpoint, sessao expirada) parece igual a "lista
  acabou" se nao for tratada — foi a causa de downloads incompletos/perfis
  falhando em lote. `_requisicao_ig()` detecta isso (HTTP != 200, status !=
  "ok", resposta nao-JSON), tenta de novo ate 2x mais (20s, depois 45s), e so
  entao desiste com aviso explicito. HTTP 429 falha na hora sem retry (rate
  limit real do Instagram, esperar minutos/horas nao segundos). Ha pausa de
  5s entre perfis no loop principal e 2.5s entre paginas — reduz (nao
  elimina) risco de bloqueio ao rodar varios perfis no mesmo lote.
  **HTTP 400 no endpoint de clips/reels** (diferente do 429) e sintoma de
  faltar o header `X-CSRFToken` nas requisicoes POST — Instagram exige o
  cookie `csrftoken` tambem como header em POST (GET nao exige, por isso o
  feed as vezes funciona mais paginas que o reels antes de falhar). A sessao
  ja seta esse header automaticamente a partir do cookie.
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
  **`--max-downloads` retorna exit code 101** quando para de proposito (limite
  de quantidade atingido) — NAO e erro, mas olhar so o returncode fazia todo
  download "por quantidade" aparecer como falha (✗) mesmo baixando tudo
  certinho. `_yt_dlp_ok()` trata 101 como sucesso quando `max_videos` foi
  pedido. Tambem usar sempre `--playlist-end N` junto com `--max-downloads N`
  — sem isso, o yt-dlp enumera o PERFIL INTEIRO antes de comecar a baixar
  (visto num teste real: 100 paginas/1462 videos varridos so pra baixar 3),
  o que e lento e aumenta risco de rate-limit em contas grandes.
- Modo "por perfil" (com filtro de periodo, exceto Facebook) ou "URLs soltas"
  (cola links direto) para todas as redes.

### Como testar sem a conta do usuario
Instagram e Facebook exigem login real — nao da pra testar essas duas ao
vivo numa sessao de agente (sem credenciais do usuario). TikTok e YouTube
funcionam com perfis publicos e JA foram validados de ponta a ponta (listagem
+ download real de video com o comando exato do script) contra canais/perfis
publicos conhecidos, sem precisar de cookies — use esse mesmo approach pra
qualquer teste futuro de TikTok/YouTube.
