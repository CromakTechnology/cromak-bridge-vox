import os
import sys
import re
import logging
from logging.handlers import RotatingFileHandler
from .seguranca import get_appdata_dir

# Filtro de Privacidade para Anonimizar Chaves de API e Segredos
class PrivacyFilter(logging.Filter):
    # Padrões de chaves de API conhecidas
    PATTERNS = [
        (re.compile(r'gsk_[A-Za-z0-9_-]{20,}', re.IGNORECASE), 'gsk_***[REDACTED]***'),
        (re.compile(r'AIza[A-Za-z0-9_-]{30,}', re.IGNORECASE), 'AIza***[REDACTED]***'),
        (re.compile(r'sk-[A-Za-z0-9_-]{20,}', re.IGNORECASE), 'sk-***[REDACTED]***'),
        (re.compile(r'xai-[A-Za-z0-9_-]{20,}', re.IGNORECASE), 'xai-***[REDACTED]***'),
        (re.compile(r'Bearer\s+[A-Za-z0-9_\-\.]{20,}', re.IGNORECASE), 'Bearer ***[REDACTED]***'),
        (re.compile(r'(api[_-]?key["\']?\s*[:=]\s*["\'])([^"\']{8,})(["\'])', re.IGNORECASE), r'\1***[REDACTED]***\3'),
    ]

    def filter(self, record):
        if isinstance(record.msg, str):
            for pattern, repl in self.PATTERNS:
                record.msg = pattern.sub(repl, record.msg)
        if record.args:
            args_list = []
            for arg in record.args:
                if isinstance(arg, str):
                    for pattern, repl in self.PATTERNS:
                        arg = pattern.sub(repl, arg)
                args_list.append(arg)
            record.args = tuple(args_list)
        return True


_logger_instancia = None

def get_logger():
    global _logger_instancia
    if _logger_instancia is not None:
        return _logger_instancia

    pasta_vox = get_appdata_dir()
    pasta_logs = os.path.join(pasta_vox, "logs")
    os.makedirs(pasta_logs, exist_ok=True)
    caminho_log = os.path.join(pasta_logs, "bridge_vox.log")

    logger = logging.getLogger("CromakBridgeVox")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Evita duplicar handlers
    if not logger.handlers:
        # Rotating File Handler: máx 2MB por arquivo, até 1 backup (máx 4MB em disco)
        file_handler = RotatingFileHandler(
            caminho_log,
            maxBytes=2 * 1024 * 1024,
            backupCount=1,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        file_handler.addFilter(PrivacyFilter())
        logger.addHandler(file_handler)

        # Se for terminal ou depuração, também escreve no console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(PrivacyFilter())
        logger.addHandler(console_handler)

    _logger_instancia = logger
    return _logger_instancia


def log_info(msg: str):
    get_logger().info(msg)

def log_warning(msg: str):
    get_logger().warning(msg)

def log_error(msg: str, exc_info=False):
    get_logger().error(msg, exc_info=exc_info)

def log_api_call(provider: str, model: str, duration_sec: float, status_code: int = 200, tokens: int = None, error: str = None):
    """Registra métricas técnicas de chamadas à API sem registrar conteúdos de mensagens privadas."""
    tokens_str = f" | Tokens: {tokens}" if tokens else ""
    error_str = f" | Erro: {error}" if error else ""
    msg = f"[API] Provedor: {provider} | Modelo: {model} | Duração: {duration_sec:.2f}s | Status: {status_code}{tokens_str}{error_str}"
    if status_code == 200:
        get_logger().info(msg)
    elif status_code == 429:
        get_logger().warning(f"[Rate-Limit 429] Provedor: {provider} | Modelo: {model} | Duração: {duration_sec:.2f}s{error_str}")
    else:
        get_logger().error(msg)

def log_tool_exec(tool_name: str, duration_sec: float, success: bool, details: str = ""):
    """Registra execução de ferramentas locais."""
    status = "OK" if success else "FALHA"
    extra = f" ({details})" if details else ""
    get_logger().info(f"[Tool] {tool_name} -> {status} em {duration_sec:.2f}s{extra}")

def obter_caminho_logs() -> str:
    pasta_vox = get_appdata_dir()
    return os.path.join(pasta_vox, "logs", "bridge_vox.log")

def abrir_pasta_logs() -> str:
    pasta_vox = get_appdata_dir()
    pasta_logs = os.path.join(pasta_vox, "logs")
    os.makedirs(pasta_logs, exist_ok=True)
    try:
        if os.name == 'nt':
            os.startfile(pasta_logs)
            return pasta_logs
        else:
            import subprocess
            subprocess.Popen(['xdg-open', pasta_logs])
            return pasta_logs
    except Exception as e:
        log_error(f"Erro ao abrir pasta de logs: {e}")
        return ""
