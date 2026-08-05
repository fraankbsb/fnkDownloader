#!/usr/bin/env python3
"""
publish.py — roda no notebook (onde voce edita o codigo).
Empacota os arquivos do app num zip e publica uma nova Release no
GitHub usando o GitHub CLI (gh). Tambem commita e da push no repo.

Uso manual:
    python publish.py 1.0.1 "Corrige bug X"

Uso automatico (versao/mensagem geradas sozinhas):
    python publish.py auto
"""

import sys
import json
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path

APP_DIR      = Path(__file__).resolve().parent
VERSION_FILE = APP_DIR / "version.json"
CONFIG_FILE  = APP_DIR / "update_config.json"
SCRIPT_ALVO  = APP_DIR / "iniciar_download.py"

# Arquivos que entram no pacote de atualizacao (NUNCA incluir cookies!)
ARQUIVOS_PAYLOAD = [SCRIPT_ALVO, VERSION_FILE]


def ler_repo():
    cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    repo = cfg.get("repo", "")
    if not repo or "/" not in repo or repo == "OWNER/REPO":
        print("ERRO: configure 'repo' em update_config.json (formato OWNER/REPO) antes de publicar.")
        sys.exit(1)
    return repo


def ler_versao_atual():
    try:
        return json.loads(VERSION_FILE.read_text(encoding="utf-8")).get("version", "1.0.0")
    except Exception:
        return "1.0.0"


def proxima_versao_patch(versao_atual):
    partes = versao_atual.split(".")
    while len(partes) < 3:
        partes.append("0")
    major, minor, patch = partes[0], partes[1], partes[2]
    return f"{major}.{minor}.{int(patch) + 1}"


def commitar_e_dar_push(mensagem):
    subprocess.run(["git", "add"] + [str(a) for a in ARQUIVOS_PAYLOAD], cwd=APP_DIR)
    resultado = subprocess.run(
        ["git", "commit", "-m", mensagem], cwd=APP_DIR, capture_output=True, text=True
    )
    if resultado.returncode != 0 and "nothing to commit" not in resultado.stdout:
        print(f"  ⚠️  git commit: {resultado.stdout.strip()} {resultado.stderr.strip()}")
    subprocess.run(["git", "push"], cwd=APP_DIR)


def main():
    modo_auto = len(sys.argv) >= 2 and sys.argv[1] == "auto"

    if modo_auto:
        atual       = ler_versao_atual()
        nova_versao = proxima_versao_patch(atual)
        mensagem    = f"Auto update {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    elif len(sys.argv) >= 2:
        nova_versao = sys.argv[1].lstrip("v")
        mensagem    = sys.argv[2] if len(sys.argv) > 2 else f"Versao {nova_versao}"
    else:
        print("Uso: python publish.py <versao> [mensagem]  |  python publish.py auto")
        print('Exemplo: python publish.py 1.0.1 "Corrige bug do Facebook"')
        sys.exit(1)

    repo = ler_repo()

    # 1. Atualiza version.json
    VERSION_FILE.write_text(json.dumps({"version": nova_versao}, indent=2), encoding="utf-8")
    print(f"  ✓  version.json atualizado para {nova_versao}")

    # 2. Commit + push do codigo-fonte (mantem o repo em dia)
    commitar_e_dar_push(mensagem)

    # 3. Monta o zip do payload
    zip_path = APP_DIR / f"payload_v{nova_versao}.zip"
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for arquivo in ARQUIVOS_PAYLOAD:
            zf.write(arquivo, arcname=arquivo.name)
    print(f"  ✓  Pacote criado: {zip_path.name}")

    # 4. Cria a release no GitHub via gh CLI
    tag = f"v{nova_versao}"
    cmd = [
        "gh", "release", "create", tag,
        str(zip_path),
        "--repo", repo,
        "--title", tag,
        "--notes", mensagem,
    ]
    print(f"  🚀  Publicando release {tag} no GitHub ({repo})...")
    resultado = subprocess.run(cmd, cwd=APP_DIR)

    zip_path.unlink()

    if resultado.returncode == 0:
        print(f"  ✅  Release {tag} publicada! O botao 'Atualizar App' ja vai encontrar essa versao.")
    else:
        print("  ❌  Falha ao publicar a release. Veja o erro acima.")
        sys.exit(resultado.returncode)


if __name__ == "__main__":
    main()
