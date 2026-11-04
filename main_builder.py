import os
import shutil
import subprocess
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# =======================================================
# CONFIGURAÇÃO DO BUILD - CROMAK BRIDGE VOX
# =======================================================
NOME_APP = "BridgeVox"
ICONE = "web/lib/cromak-bridge.ico"
MAIN_SCRIPT = "main.py"
VERSION_FILE = "versao_info.txt"

def criar_arquivo_versao():
    conteudo = '''# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 3, 7, 0),
    prodvers=(1, 3, 7, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        '041604b0', # 0416 = Português do Brasil
        [StringStruct('CompanyName', 'Cromak Technology'),
        StringStruct('FileDescription', 'Cromak Bridge Vox'),
        StringStruct('FileVersion', '1.3.7'),
        StringStruct('InternalName', 'BridgeVox.exe'),
        StringStruct('LegalCopyright', 'Copyright 2026 Cromak Technology. Todos os direitos reservados.'),
        StringStruct('OriginalFilename', 'BridgeVox.exe'),
        StringStruct('ProductVersion', '1.3.7'),
        StringStruct('ProductName', 'Cromak Bridge Vox'),
        StringStruct('Comments', 'Cromak Bridge Vox - Assistente de IA Multimodal e Acessibilidade')])
      ]),
    VarFileInfo([VarStruct('Translation', [1046, 1200])])
  ]
)
'''
    with open(VERSION_FILE, "w", encoding="utf-8") as f:
        f.write(conteudo)

def realizar_build():
    print(f"🚀 Iniciando Build Oficial: {NOME_APP} v1.3.7...")
    
    # 1. Cria o arquivo de metadados
    criar_arquivo_versao()
    print("📋 Metadados (Version Info) preparados.")

    # Detecta automaticamente o python da .venv se existir
    venv_python = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv", "Scripts", "python.exe")
    python_bin = venv_python if os.path.exists(venv_python) else sys.executable
    print(f"🐍 Interpretador Python para o build: {python_bin}")

    # 2. Comando PyInstaller com saída direta para dist/BridgeVox
    comando = [
        python_bin, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--log-level=INFO",            
        f"--icon={ICONE}",
        "--add-data=web;web",
        "--add-data=plugins;plugins",
        "--hidden-import=core.online_sync",
        "--collect-all=google.genai",
        "--collect-all=groq",
        "--collect-all=anthropic",
        "--collect-all=openai",
        "--copy-metadata=google-genai",
        f"--name={NOME_APP}",
        f"--version-file={VERSION_FILE}",
        MAIN_SCRIPT
    ]

    try:
        print("⏳ Compilando e gerando log de rastreamento (build_log.txt)...")
        
        with open("build_log.txt", "w", encoding="utf-8") as log_file:
            processo = subprocess.Popen(
                comando, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            
            for linha in processo.stdout:
                print(linha, end="") 
                log_file.write(linha) 
                log_file.flush()
            
            processo.wait()
            
            if processo.returncode != 0:
                raise Exception(f"Processo abortado com código {processo.returncode}.")

        dist_dir = os.path.join("dist", NOME_APP)
        print(f"\n📁 Organizando e finalizando a pasta '{dist_dir}'...")

        # Garante que APENAS os documentos oficiais do cliente estejam na pasta 'docs'
        docs_dest = os.path.join(dist_dir, "docs")
        if os.path.exists(docs_dest):
            shutil.rmtree(docs_dest, ignore_errors=True)
        os.makedirs(docs_dest, exist_ok=True)

        for doc_nome in ["EULA.txt", "PRIVACY.txt", "README.txt"]:
            src_doc = os.path.join("docs", doc_nome)
            if os.path.exists(src_doc):
                shutil.copy2(src_doc, os.path.join(docs_dest, doc_nome))

        # Remove completamente qualquer pasta docs de dentro de _internal (evita vazamento de roteiros de teste)
        internal_docs = os.path.join(dist_dir, "_internal", "docs")
        if os.path.exists(internal_docs):
            try:
                shutil.rmtree(internal_docs, ignore_errors=True)
                print("   [OK] Removida pasta 'docs' de dentro de '_internal'.")
            except Exception as e:
                print(f"   [AVISO] Falha ao remover _internal/docs: {e}")

        print(f"✅ Executável e arquivos organizados com sucesso em '{dist_dir}'.")

        # 3. LIMPEZA DE LIXO (Cleanup)
        print("🧹 Iniciando limpeza de arquivos temporários...")
        if os.path.exists("build"):
            shutil.rmtree("build")
            print("   [OK] Pasta 'build' temporária removida.")

        arquivo_spec = f"{NOME_APP}.spec"
        if os.path.exists(arquivo_spec):
            os.remove(arquivo_spec)
            print(f"   [OK] Arquivo '{arquivo_spec}' removido.")
            
        if os.path.exists(VERSION_FILE):
            os.remove(VERSION_FILE)
            print("   [OK] Arquivo de metadados temporário removido.")

        print(f"\n✨ Build finalizado com sucesso! Tudo pronto na pasta 'dist\\{NOME_APP}' para o Inno Setup.")

    except Exception as e:
        print(f"\n❌ Erro durante o processo de Build: {e}")
        print("⚠️ Verifique o arquivo 'build_log.txt' para ver o rastreio completo do erro.")

if __name__ == "__main__":
    realizar_build()
