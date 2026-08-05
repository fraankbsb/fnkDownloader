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
- Arquivos de cookies (`instagram_cookies.txt`, `tiktok_cookies.txt`,
  `youtube_cookies.txt`, `facebook_cookies.txt`) estao no `.gitignore` e
  **nunca** devem ser commitados, publicados em release, ou entrar em
  `payload_files` — sao segredos de sessao.
- `gh` CLI ja esta instalado e autenticado (conta `fraankbsb`) globalmente
  no PC de edicao — nao precisa reinstalar/reautenticar para novos repos.
- `publish.py` resolve o caminho do `gh.exe` via `shutil.which` com fallback
  para `C:\Program Files\GitHub CLI\gh.exe`, porque a sessao que roda o
  vigia pode nao ter o PATH atualizado.
- Numeracao de versao so pode subir (nunca republicar com o mesmo numero ou
  menor, senao o launcher nao detecta a atualizacao).
- Existe um prompt generico pronto para replicar esse mesmo sistema em
  outros projetos (guardado como artifact do usuario — ver conversa de
  2026-08-05 sobre "replicar metodologia").

## Redes suportadas (iniciar_download.py)
- Instagram: Selenium + requests via API privada, cookies em
  `instagram_cookies.txt`.
- TikTok / YouTube / Facebook: via `yt-dlp`, cookies opcionais em
  `<rede>_cookies.txt`. YouTube tem opcao extra de Videos/Shorts/Ambos.
- Modo "por perfil" (com filtro de periodo) ou "URLs soltas" (cola links
  direto) para todas as redes.
