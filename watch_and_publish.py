#!/usr/bin/env python3
"""
watch_and_publish.py — roda no notebook (PC de edicao).
Fica de olho no(s) arquivo(s) do app e, quando detecta uma alteracao
salva, espera um tempo de "silencio" (para nao publicar a cada letra
digitada) e entao chama publish.py auto sozinho.

Uso:
    python watch_and_publish.py
    (deixe essa janela aberta enquanto estiver editando)
"""

import subprocess
import sys
import time
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent

# Arquivos monitorados — mudou algum deles, dispara publish automatico
ARQUIVOS_MONITORADOS = [
    APP_DIR / "iniciar_download.py",
]

ESPERA_SILENCIO_SEG = 8  # espera esse tempo sem novas mudancas antes de publicar


def mtimes():
    return {a: a.stat().st_mtime for a in ARQUIVOS_MONITORADOS if a.exists()}


def main():
    print("=" * 58)
    print("  👀  Vigia de auto-publicacao — fnkDownloader")
    print("=" * 58)
    print(f"  Monitorando: {', '.join(a.name for a in ARQUIVOS_MONITORADOS)}")
    print(f"  Publica sozinho {ESPERA_SILENCIO_SEG}s depois da ultima alteracao salva.")
    print("  Deixe esta janela aberta. Ctrl+C para parar.\n")

    estado_anterior = mtimes()
    pendente_desde  = None

    while True:
        time.sleep(1)
        atual = mtimes()

        mudou = atual != estado_anterior
        if mudou:
            estado_anterior = atual
            pendente_desde  = time.time()
            print("  ✏️   Alteracao detectada, aguardando voce parar de editar...")

        if pendente_desde and (time.time() - pendente_desde) >= ESPERA_SILENCIO_SEG:
            pendente_desde = None
            print("  🚀  Publicando automaticamente...\n")
            resultado = subprocess.run(
                [sys.executable, str(APP_DIR / "publish.py"), "auto"],
                cwd=APP_DIR,
            )
            if resultado.returncode == 0:
                print("\n  ✅  Publicado! Voltando a vigiar...\n")
            else:
                print("\n  ❌  Falha ao publicar. Voltando a vigiar...\n")
            estado_anterior = mtimes()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Vigia encerrado.\n")
