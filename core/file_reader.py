import os
from pathlib import Path

class FileReader:
    def __init__(self, base_dir=None):
        if base_dir:
            self.base_dir = Path(base_dir).resolve()
        else:
            self.base_dir = Path(__file__).resolve().parent.parent

    def ler_arquivo(self, caminho_arquivo: str) -> str:
        try:
            from core.local_tools import ler_arquivo_local
            caminho_str = os.path.expanduser(os.path.expandvars(str(caminho_arquivo).strip('"\'')))
            path = Path(caminho_str)

            # Se for relativo, resolve a partir do base_dir
            if not path.is_absolute() and self.base_dir:
                path = (self.base_dir / path).resolve()
            
            return ler_arquivo_local(str(path))
        except Exception as e:
            return f"[Erro] Não foi possível ler o arquivo: {e}"