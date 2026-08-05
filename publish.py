#!/usr/bin/env python3
"""
publish.py — roda no notebook (onde voce edita o codigo).
Empacota o iniciar_download.py + version.json num zip e publica
uma nova Release no GitHub usando o GitHub CLI (gh).

Uso:
    python publish.py 1.0.1 "Corrige bug X"
"""

import sys
import json
import shutil
import zipfile
import subprocess
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


def main():
    if len(sys.argv) < 2:
        print("Uso: python publish.py <versao> [mensagem]")
        print('Exemplo: python publish.py 1.0.1 "Corrige bug do Facebook"')
        sys.exit(1)

    nova_versao = sys.argv[1].lstrip("v")
    mensagem    = sys.argv[2] if len(sys.argv) > 2 else f"Versao {nova_versao}"
    repo        = ler_repo()

    # 1. Atualiza version.json
    VERSION_FILE.write_text(json.dumps({"version": nova_versao}, indent=2), encoding="utf-8")
    print(f"  ✓  version.json atualizado para {nova_versao}")

    # 2. Monta o zip do payload
    zip_path = APP_DIR / f"payload_v{nova_versao}.zip"
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for arquivo in ARQUIVOS_PAYLOAD:
            zf.write(arquivo, arcname=arquivo.name)
    print(f"  ✓  Pacote criado: {zip_path.name}")

    # 3. Cria a release no GitHub via gh CLI
    tag = f"v{nova_versao}"
    cmd = [
        "gh", "release", "create", tag,
        str(zip_path),
        "--repo", repo,
        "--title", tag,
        "--notes", mensagem,
    ]
    print(f"  🚀  Publicando release {tag} no GitHub ({repo})...")
    resultado = subprocess.run(cmd)

    zip_path.unlink()

    if resultado.returncode == 0:
        print(f"  ✅  Release {tag} publicada! O botao 'Atualizar App' ja vai encontrar essa versao.")
    else:
        print("  ❌  Falha ao publicar a release. Veja o erro acima.")
        sys.exit(resultado.returncode)


if __name__ == "__main__":
    main()
