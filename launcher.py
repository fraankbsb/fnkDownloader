#!/usr/bin/env python3
"""
fnkDownloader — Launcher
Baixa a versao mais recente do codigo (GitHub Releases) e inicia o app.
Este arquivo e compilado uma unica vez em .exe — ele NAO precisa ser
recompilado quando o codigo do downloader muda; so o payload (zip)
publicado no GitHub muda.
"""

import sys
import os
import json
import shutil
import zipfile
import tempfile
import subprocess
import threading
import urllib.request
import urllib.error
from pathlib import Path

import tkinter as tk
from tkinter import scrolledtext, messagebox

# ── Caminhos ──────────────────────────────────────────────────
if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).resolve().parent
else:
    APP_DIR = Path(__file__).resolve().parent

VERSION_FILE = APP_DIR / "version.json"
CONFIG_FILE  = APP_DIR / "update_config.json"
SCRIPT_ALVO  = APP_DIR / "iniciar_download.py"

USER_AGENT = "fnkDownloader-updater"


def _ler_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def ler_versao_local():
    return _ler_json(VERSION_FILE, {"version": "0.0.0"}).get("version", "0.0.0")


def ler_repo():
    repo = _ler_json(CONFIG_FILE, {"repo": ""}).get("repo", "")
    if not repo or "/" not in repo:
        raise RuntimeError("update_config.json sem 'repo' configurado (formato OWNER/REPO).")
    return repo


def buscar_release_mais_recente(repo):
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/vnd.github+json", "User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def verificar_update(log):
    repo   = ler_repo()
    atual  = ler_versao_local()
    log(f"Versao instalada: {atual}")
    log("Consultando GitHub...")
    release = buscar_release_mais_recente(repo)
    remota  = str(release.get("tag_name", "")).lstrip("v")
    return atual, remota, release


def aplicar_update(release, log):
    assets    = release.get("assets", [])
    zip_asset = next((a for a in assets if a["name"].endswith(".zip")), None)
    if not zip_asset:
        raise RuntimeError("Release nao tem nenhum arquivo .zip anexado.")

    with tempfile.TemporaryDirectory() as tmp:
        zip_path = Path(tmp) / "payload.zip"
        log("Baixando atualizacao...")
        req = urllib.request.Request(
            zip_asset["browser_download_url"],
            headers={"User-Agent": USER_AGENT},
        )
        with urllib.request.urlopen(req, timeout=60) as resp, open(zip_path, "wb") as f:
            shutil.copyfileobj(resp, f)

        extract_dir = Path(tmp) / "extract"
        extract_dir.mkdir()
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(extract_dir)

        log("Aplicando atualizacao...")
        for item in extract_dir.rglob("*"):
            if item.is_file():
                destino = APP_DIR / item.relative_to(extract_dir)
                destino.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, destino)


class LauncherApp:
    def __init__(self, root):
        self.root = root
        root.title("fnkDownloader — Launcher")
        root.geometry("520x360")
        root.resizable(False, False)

        self.versao_var = tk.StringVar(value=f"Versao instalada: {ler_versao_local()}")

        tk.Label(root, textvariable=self.versao_var, font=("Segoe UI", 11, "bold")).pack(pady=(14, 6))

        frame_botoes = tk.Frame(root)
        frame_botoes.pack(pady=6)

        self.btn_update = tk.Button(
            frame_botoes, text="🔄  Atualizar App", width=20, height=2,
            command=self.on_atualizar,
        )
        self.btn_update.grid(row=0, column=0, padx=8)

        self.btn_iniciar = tk.Button(
            frame_botoes, text="▶  Iniciar App", width=20, height=2,
            command=self.on_iniciar,
        )
        self.btn_iniciar.grid(row=0, column=1, padx=8)

        self.log_box = scrolledtext.ScrolledText(root, width=64, height=13, state="disabled")
        self.log_box.pack(pady=12, padx=12)

        self.log("Pronto. Clique em 'Atualizar App' para checar novidades.")

    def log(self, msg):
        def _write():
            self.log_box.configure(state="normal")
            self.log_box.insert(tk.END, msg + "\n")
            self.log_box.see(tk.END)
            self.log_box.configure(state="disabled")
        self.root.after(0, _write)

    def _set_botoes(self, ativo):
        estado = "normal" if ativo else "disabled"
        self.btn_update.configure(state=estado)
        self.btn_iniciar.configure(state=estado)

    def on_atualizar(self):
        self._set_botoes(False)
        threading.Thread(target=self._atualizar_thread, daemon=True).start()

    def _atualizar_thread(self):
        try:
            atual, remota, release = verificar_update(self.log)
            if not remota:
                self.log("Nao foi possivel obter a versao remota.")
            elif remota == atual:
                self.log("Voce ja esta na versao mais recente!")
            else:
                aplicar_update(release, self.log)
                self.log(f"Atualizado! {atual} -> {remota}")
                self.root.after(0, lambda: self.versao_var.set(f"Versao instalada: {ler_versao_local()}"))
        except urllib.error.HTTPError as e:
            self.log(f"Erro HTTP ao checar update: {e}")
        except Exception as e:
            self.log(f"Erro ao atualizar: {e}")
        finally:
            self.root.after(0, lambda: self._set_botoes(True))

    def on_iniciar(self):
        if not SCRIPT_ALVO.exists():
            messagebox.showerror("Erro", f"Arquivo nao encontrado:\n{SCRIPT_ALVO}")
            return
        self.log("Iniciando o app em uma nova janela...")
        subprocess.Popen(
            [sys.executable if not getattr(sys, "frozen", False) else "python", str(SCRIPT_ALVO)],
            cwd=str(APP_DIR),
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )


def main():
    root = tk.Tk()
    LauncherApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
