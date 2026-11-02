try:
    import httpx
    original_init = httpx.Client.__init__
    def new_init(self, *args, **kwargs):
        kwargs['verify'] = False
        original_init(self, *args, **kwargs)
    httpx.Client.__init__ = new_init
except:
    pass
import os
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''
import ssl
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except:
    pass

import webview
import os
import sys
import json
from core.seguranca import ler_config_seguro, salvar_config_seguro
import base64
import mimetypes
import webbrowser
import winreg as reg
import threading
import pystray
from PIL import Image, ImageGrab
import time

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

from core.seguranca import get_appdata_dir

def get_data_dir():
    """
    Retorna o diretório persistente oficial do Cromak Bridge Vox:
    %APPDATA%\\Cromak Technology\\Bridge Vox
    Mantém 100% de integridade e migra dados legados automaticamente.
    """
    return get_appdata_dir()


sys.path.append(os.path.dirname(os.path.abspath(__file__)))


APP_VERSION = "1.3.5"
APP_BUILD = "2026.10"
APP_NOME = "Cromak Bridge Vox"

from core.gemini_api import AICore
from core.memory_manager import MemoryManager
from core.file_reader import FileReader
from core.audio_engine import AudioEngine
from core.online_sync import CromakOnlineSync

import ctypes

def aplicar_icone_janela(titulo_janela="Cromak Bridge"):
    """Força o ícone oficial cromak-bridge.ico na barra de título (WinForms + Win32 API) e barra de tarefas."""
    def _worker():
        import time, ctypes
        try:
            ico_path = resource_path(os.path.join("web", "lib", "cromak-bridge.ico"))
            if not os.path.exists(ico_path):
                return
            user32 = ctypes.windll.user32
            hicon_small = user32.LoadImageW(None, ico_path, 1, 16, 16, 0x00000010)
            hicon_big = user32.LoadImageW(None, ico_path, 1, 32, 32, 0x00000010)
            for _ in range(25):
                # 1. Tenta via objeto nativo WinForms do pywebview (garante ShowIcon = True mesmo após F11)
                try:
                    import importlib
                    NetIcon = importlib.import_module("System.Drawing").Icon
                    for w in webview.windows:
                        if w.title == titulo_janela and getattr(w, "native", None) is not None:
                            form = w.native
                            def _set_net_icon():
                                form.Icon = NetIcon(ico_path)
                                form.ShowIcon = True
                            if form.InvokeRequired:
                                Action = importlib.import_module("System").Action
                                form.Invoke(Action(_set_net_icon))
                            else:
                                _set_net_icon()
                except Exception:
                    pass

                # 2. Aplica também via Win32 WM_SETICON + SWP_FRAMECHANGED
                hwnd = user32.FindWindowW(None, titulo_janela)
                if hwnd:
                    GWL_STYLE = -16
                    WS_SYSMENU = 0x00080000
                    estilo = user32.GetWindowLongW(hwnd, GWL_STYLE)
                    if not (estilo & WS_SYSMENU):
                        user32.SetWindowLongW(hwnd, GWL_STYLE, estilo | WS_SYSMENU)
                    if hicon_small:
                        user32.SendMessageW(hwnd, 0x0080, 0, hicon_small)
                    if hicon_big:
                        user32.SendMessageW(hwnd, 0x0080, 1, hicon_big)
                    user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0027)
                    break
                time.sleep(0.15)
        except Exception as e:
            print("Aviso ao aplicar ícone Win32:", e)
    threading.Thread(target=_worker, daemon=True).start()

def detectar_idioma_sistema():
    """Detecta automaticamente o idioma padrão do Windows / Sistema Operacional."""
    try:
        import ctypes
        windll = getattr(ctypes, 'windll', None)
        if windll and hasattr(windll, 'kernel32') and hasattr(windll.kernel32, 'GetUserDefaultUILanguage'):
            lang_id = windll.kernel32.GetUserDefaultUILanguage() & 0x3FF
            mapa_lang = {
                0x16: "pt_BR", # Português
                0x09: "en_US", # Inglês
                0x0A: "es_ES", # Espanhol
                0x0C: "fr_FR", # Francês
                0x07: "de_DE", # Alemão
                0x10: "it_IT", # Italiano
                0x04: "zh_CN", # Chinês Simplificado
                0x11: "ja_JP", # Japonês
                0x19: "ru_RU", # Russo
                0x39: "hi_IN", # Hindi
                0x01: "ar_SA"  # Árabe
            }
            if lang_id in mapa_lang:
                return mapa_lang[lang_id]
    except Exception:
        pass
    try:
        import locale
        loc = locale.getdefaultlocale()[0]
        if loc:
            loc = loc.lower()
            prefixos = {
                "pt": "pt_BR",
                "en": "en_US",
                "es": "es_ES",
                "fr": "fr_FR",
                "de": "de_DE",
                "it": "it_IT",
                "zh": "zh_CN",
                "ja": "ja_JP",
                "ru": "ru_RU",
                "hi": "hi_IN",
                "ar": "ar_SA"
            }
            for pref, code_id in prefixos.items():
                if loc.startswith(pref):
                    return code_id
    except Exception:
        pass
    return "pt_BR"


class ApiBackend:
    def __init__(self):
        self.data_dir = get_data_dir() # Guarda a pasta persistente
        self.config_path = os.path.join(self.data_dir, "config.json")
        self.config = self.carregar_config()
        
        # Passa o caminho do diretório para o MemoryManager criar o banco lá
        self.db = MemoryManager(self.data_dir) 
        
        self.leitor = FileReader()
        self.audio = AudioEngine()
        self.arquivo_atual = None
        self.ia = None
        self.versao = APP_VERSION
        self.build = APP_BUILD
        self.versao_completa = f"{APP_VERSION} (Build {APP_BUILD})"
        self.sync_engine = CromakOnlineSync(
            nome_programa=APP_NOME,
            site_fallback="https://cromaktechnology.github.io/pt/bridge-vox.html"
        )

    def carregar_config(self):
        try:
            cfg = ler_config_seguro(self.config_path)
            if not cfg:
                idioma_padrao = detectar_idioma_sistema()
                return {"provider": "gemini", "api_key": "", "language": idioma_padrao, "model": "gemini-2.5-flash"}
            precisa_salvar = False
            if "language" not in cfg or not cfg.get("language"):
                cfg["language"] = detectar_idioma_sistema()
                precisa_salvar = True
            if "3.6-flash" in str(cfg.get("model")) or "3.8-flash" in str(cfg.get("model")):
                cfg["model"] = "gemini-2.5-flash"
                precisa_salvar = True
            if cfg.get("interface_mode") == "vox":
                cfg["interface_mode"] = "normal"
                precisa_salvar = True
            if precisa_salvar:
                salvar_config_seguro(self.config_path, cfg)
            return cfg
        except:
            idioma_padrao = detectar_idioma_sistema()
            return {"provider": "gemini", "api_key": "", "language": idioma_padrao, "model": "gemini-2.5-flash"}

    # --- IDIOMAS E LOCALIZAÇÃO (i18n) ---
    def detectar_idioma_sistema(self):
        """Retorna o código do idioma detectado automaticamente no Windows."""
        return detectar_idioma_sistema()

    def listar_idiomas(self):
        """Lista dinamicamente os idiomas presentes na pasta web/locale."""
        pasta = resource_path(os.path.join("web", "locale"))
        idiomas = []
        if os.path.exists(pasta):
            for arq in os.listdir(pasta):
                if arq.endswith(".json"):
                    caminho = os.path.join(pasta, arq)
                    try:
                        with open(caminho, "r", encoding="utf-8") as f:
                            dados = json.load(f)
                        codigo = dados.get("_lang_code", os.path.splitext(arq)[0])
                        nome = dados.get("_lang_name", codigo)
                        idiomas.append({"code": codigo, "name": nome})
                    except Exception:
                        pass
        if not idiomas:
            idiomas = [{"code": "pt_BR", "name": "Português (Brasil)"}, {"code": "en_US", "name": "English (US)"}]
        return idiomas

    def carregar_idioma(self, codigo="pt_BR"):
        """Retorna o dicionário de tradução do idioma solicitado."""
        pasta = resource_path(os.path.join("web", "locale"))
        caminho = os.path.join(pasta, f"{codigo}.json")
        if not os.path.exists(caminho):
            caminho = os.path.join(pasta, "pt_BR.json")
        if os.path.exists(caminho):
            try:
                with open(caminho, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    # --- CONFIGURAÇÃO E API KEY ---


    def ouvir_e_responder_nativo(self):
        """Grava o áudio do microfone do Windows por 6 segundos e envia o WAV bruto para o Gemini."""
        try:
            import sounddevice as sd
            from scipy.io.wavfile import write
            import os
            import tempfile
            import google.generativeai as genai
            import json
            
            # Puxa a chave da API
            config_path = os.path.join(self.data_dir, 'config.json')
            cfg = ler_config_seguro(config_path)
            
            chaves = cfg.get("api_keys", {})
            chave = chaves.get("gemini", cfg.get("api_key", ""))
            
            if not chave:
                return "Erro: Chave do Gemini não configurada."
                
            genai.configure(api_key=chave)
            
            # Grava 6 segundos de áudio
            fs = 44100
            seconds = 6
            print("Gravando microfone nativo (Walkie-Talkie)...")
            myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
            sd.wait() # Aguarda a gravacao terminar
            print("Gravacao finalizada.")
            try:
                import pyttsx3
                engine = pyttsx3.init()
                engine.setProperty('rate', 160)
                engine.say("Processando...")
                engine.runAndWait()
            except: pass
            # Salva o arquivo wav
            temp_path = os.path.join(tempfile.gettempdir(), "walkie_talkie_cromak.wav")
            write(temp_path, fs, myrecording)
            
            # Faz upload pro Gemini
            audio_file = genai.upload_file(path=temp_path)
            
            # Usamos o Gemini 1.5 Flash pois ele ouve áudio direto (Multimodal)
            # E passamos um prompt oculto para ele agir como assistente
            modelo = genai.GenerativeModel('gemini-2.5-flash')
            prompt_contexto = "Você é o assistente virtual da Cromak. Responda de forma direta e natural ao que o usuário falar neste áudio."
            
            resposta = modelo.generate_content([audio_file, prompt_contexto])
            
            try:
                os.remove(temp_path)
            except:
                pass
                
            return resposta.text
            
        except Exception as e:
            return f"Erro no Microfone Blindado: {e}"

    def gerar_voz_neural(self, texto):
        """Gera um áudio hiper-realista usando Edge TTS e retorna em Base64 para o JS tocar"""
        try:
            import edge_tts
            import asyncio
            import tempfile
            import os
            import base64
            import re
            import threading
            
            # Limpeza profunda de Markdown para Leitura
            texto = re.sub(r'```[\s\S]*?```', ' [Trecho de código omitido] ', texto)
            texto = re.sub(r'<[^>]*>', '', texto)
            texto = re.sub(r'[*#`]', '', texto)
            texto = re.sub(r'-', ' ', texto) # Evita ele falar "traço" em listas
            # Escapar caracteres perigosos para o SSML do Edge TTS
            texto = texto.replace('&', ' e ').replace('<', ' menor que ').replace('>', ' maior que ')
            
            if not texto.strip():
                return None
                
            temp_path = os.path.join(tempfile.gettempdir(), "cromak_tts.mp3")
            
            
            # Desabilitar SSL Verification para contornar Proxies/Antivírus que bloqueiam o Edge TTS
            import ssl
            if not hasattr(ssl, '_cromak_patched'):
                orig_create_default_context = ssl.create_default_context
                def create_unverified_context(*args, **kwargs):
                    ctx = orig_create_default_context(*args, **kwargs)
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    return ctx
                ssl.create_default_context = create_unverified_context
                ssl._cromak_patched = True

            try:
                import edge_tts.communicate
                edge_tts.communicate._SSL_CTX.check_hostname = False
                edge_tts.communicate._SSL_CTX.verify_mode = ssl.CERT_NONE
            except Exception:
                pass

            async def _gerar():
                communicate = edge_tts.Communicate(texto, "pt-BR-AntonioNeural")
                await communicate.save(temp_path)
                return temp_path
                
            # Executa de forma blindada contra problemas de Event Loop do Windows/pywebview
            resultado = []
            def _thread_runner():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(_gerar())
                    loop.close()
                    resultado.append(True)
                except Exception as inner_e:
                    print(f"Erro interno edge_tts: {inner_e}")
                    resultado.append(False)
            
            t = threading.Thread(target=_thread_runner)
            t.start()
            t.join()
            
            if not resultado or not resultado[0]:
                return None
            
            with open(temp_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode('utf-8')
                
            try:
                os.remove(temp_path)
            except:
                pass
                
            return b64
        except Exception as e:
            print(f"Erro no TTS Neural: {e}")
            return None

    def obter_versao_app(self):
        """Retorna as informações oficiais de versão para a interface gráfica."""
        return {
            "version": APP_VERSION,
            "build": APP_BUILD,
            "full": f"Version {APP_VERSION} (build {APP_BUILD}) | Matrix Core"
        }

    def verificar_atualizacoes(self):
        """Consulta o motor CromakOnlineSync no repositório da Cromak para checar atualizações."""
        import threading
        resultado = {
            "tem_update": False,
            "versao_atual": f"{APP_VERSION} (Build {APP_BUILD})",
            "versao_online": f"{APP_VERSION} (Build {APP_BUILD})",
            "url_download": "https://cromaktechnology.github.io/pt/bridge-vox.html",
            "erro": None
        }
        evento = threading.Event()

        def _cb(tem_update, nova_v, url_down):
            resultado["tem_update"] = bool(tem_update)
            resultado["versao_online"] = str(nova_v)
            if url_down and str(url_down).startswith("http"):
                resultado["url_download"] = str(url_down)
            evento.set()

        try:
            self.sync_engine.checar_atualizacao(
                versao_atual=f"{APP_VERSION} (Build {APP_BUILD})",
                callback=_cb
            )
            evento.wait(timeout=4.0)
        except Exception as e:
            resultado["erro"] = str(e)

        return resultado

    def verificar_api_key(self):
        chave = self.config.get("api_key", "").strip()
        return bool(chave)

    def salvar_api_key(self, nova_chave):
        """Salva a chave do Primeiro Acesso (assume Gemini como padrão inicial)"""
        self.config["api_key"] = nova_chave
        self.config["provider"] = "gemini"
        salvar_config_seguro(self.config_path, self.config)
        
        modelo_inicial = self.config.get("model", "gemini-2.5-flash")
        self.ia = AICore(nova_chave, model_name=modelo_inicial, provider="gemini")
        return True

    def obter_configuracoes(self):
        """Retorna o dicionário de configurações atual para o front-end preencher o painel (pré-preenchendo as 6 pastas reais do Windows se vazias)."""
        try:
            from core.local_tools import get_real_windows_folder
            for chave_cfg, nome_win in [
                ("pathDesktop", "Desktop"),
                ("pathDocuments", "Documents"),
                ("pathDownloads", "Downloads"),
                ("pathMusic", "Music"),
                ("pathPictures", "Pictures"),
                ("pathVideos", "Videos"),
            ]:
                if not self.config.get(chave_cfg):
                    self.config[chave_cfg] = get_real_windows_folder(nome_win)
        except Exception:
            pass
        return self.config

    def configurar_startup(self, enable):
        """Adiciona ou remove o aplicativo da inicialização do Registro do Windows."""
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "Cromak Bridge Vox"
        exe_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(sys.argv[0])
            
        try:
            key = reg.OpenKey(reg.HKEY_CURRENT_USER, key_path, 0, reg.KEY_ALL_ACCESS)
            if enable:
                reg.SetValueEx(key, app_name, 0, reg.REG_SZ, f'"{exe_path}"')
            else:
                try:
                    reg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass
            reg.CloseKey(key)
        except Exception as e:
            print(f"Erro no registro do Windows: {e}")

    def gerenciar_tray(self, enable):
        """Cria ou destrói o ícone da bandeja do sistema (Tray)."""
        if enable:
            if hasattr(self, 'tray_icon') and self.tray_icon: return
            try:
                icone_path = resource_path(os.path.join('web', 'lib', 'cromak-bridge.ico'))
                image = Image.open(icone_path)
                
                def mostrar_janela(icon, item):
                    import webview
                    if webview.windows:
                        webview.windows[0].show()
                        webview.windows[0].restore()

                def verificar_updates(icon, item):
                    import webbrowser
                    webbrowser.open("https://cromaktechnology.github.io/pt/bridge-vox.html")
                    
                def abrir_suporte(icon, item):
                    import webbrowser
                    webbrowser.open("https://cromaktechnology.github.io/pt/suporte.html")

                def abrir_logs_tray(icon, item):
                    from core.logger import abrir_pasta_logs
                    abrir_pasta_logs()

                def sair_app(icon, item):
                    icon.stop()
                    import os
                    os._exit(0)

                menu = pystray.Menu(
                    pystray.MenuItem("Abrir Cromak Bridge Vox", mostrar_janela, default=True),
                    pystray.Menu.SEPARATOR,
                    pystray.MenuItem("Abrir Pasta de Logs", abrir_logs_tray),
                    pystray.MenuItem("Verificar Atualizações...", verificar_updates),
                    pystray.MenuItem("Suporte", abrir_suporte),
                    pystray.Menu.SEPARATOR,
                    pystray.MenuItem("Sair", sair_app)
                )
                
                self.tray_icon = pystray.Icon("CromakBridge", image, "Cromak Bridge Vox", menu)
                threading.Thread(target=self.tray_icon.run, daemon=True).start()
            except Exception as e:
                print(f"Erro ao carregar Tray: {e}")
        else:
            if hasattr(self, 'tray_icon') and self.tray_icon:
                self.tray_icon.stop()
                self.tray_icon = None

    def salvar_preferencias(self, configs_dict):
        """Recebe um dicionário com todas as preferências estruturadas do painel."""
        provider_antigo = self.config.get("provider", "gemini")
        novo_provedor = configs_dict.get("provider", provider_antigo)
        
        self.config["provider"] = novo_provedor
        
        # 1. Estrutura de múltiplas API Keys
        if "api_keys" not in self.config:
            self.config["api_keys"] = {}
            # Migração de chave legada
            if self.config.get("api_key"):
                self.config["api_keys"][provider_antigo] = self.config.get("api_key")
                
        novas_chaves = configs_dict.get("api_keys", {})
        for provedor, chave in novas_chaves.items():
            if chave.strip():
                self.config["api_keys"][provedor] = chave.strip()
                
        # Mantém a api_key raiz atualizada para manter compatibilidade com métodos antigos
        if novo_provedor in self.config["api_keys"]:
            self.config["api_key"] = self.config["api_keys"][novo_provedor]
            
        # 2. Configurações Globais (Idioma e Comportamento)
        if "language" in configs_dict:
            self.config["language"] = configs_dict["language"]
        if "system_prompt" in configs_dict:
            self.config["system_prompt"] = configs_dict["system_prompt"]
        for k_path in ("pathDesktop", "pathDocuments", "pathDownloads", "pathMusic", "pathPictures", "pathVideos"):
            if k_path in configs_dict:
                self.config[k_path] = configs_dict[k_path]

        # 3. Lógica de redefinição de modelo padrão ao trocar de provedor
        if provider_antigo != novo_provedor:
            if novo_provedor == "gemini":
                self.config["model"] = "gemini-2.5-flash"
            elif novo_provedor == "qwen":
                self.config["model"] = "qwen-plus"
            elif novo_provedor == "openai":
                self.config["model"] = "gpt-4o-mini"
            elif novo_provedor == "claude":
                self.config["model"] = "claude-3-5-sonnet-20240620"
            elif novo_provedor == "groq":
                self.config["model"] = "openai/gpt-oss-120b"
            
        salvar_config_seguro(self.config_path, self.config)
            
        # 4. Reinicializa a IA ativa se houver chave
        chave_ativa = self.config.get("api_key", "")
        sys_prompt = self.config.get("system_prompt", "").strip() # LÊ O PROMPT
        
        if chave_ativa:
            self.ia = AICore(chave_ativa, model_name=self.config["model"], provider=novo_provedor, system_prompt=sys_prompt)

        # Configurações de Sistema
        if "start_fullscreen" in configs_dict:
            self.config["start_fullscreen"] = bool(configs_dict["start_fullscreen"])
        if "start_with_windows" in configs_dict:
            self.config["start_with_windows"] = configs_dict["start_with_windows"]
            self.configurar_startup(configs_dict["start_with_windows"])
            
        if "minimize_to_tray" in configs_dict:
            self.config["minimize_to_tray"] = configs_dict["minimize_to_tray"]
            self.gerenciar_tray(configs_dict["minimize_to_tray"])
            
        if "agent_mode" in configs_dict:
            self.config["agent_mode"] = configs_dict["agent_mode"]
            
        if "auto_tts" in configs_dict:
            self.config["auto_tts"] = configs_dict["auto_tts"]
        if "shortcuts" in configs_dict:
            self.config["shortcuts"] = configs_dict["shortcuts"]
        if "interface_mode" in configs_dict:
            modo = configs_dict["interface_mode"]
            self.config["interface_mode"] = "normal" if modo == "vox" else modo
        if "always_voice" in configs_dict:
            self.config["always_voice"] = configs_dict["always_voice"]
            
        if "email_credentials" in configs_dict:
            self.config["email_credentials"] = configs_dict["email_credentials"]
            
        # Re-save config
        salvar_config_seguro(self.config_path, self.config)
            
        return True

    def configurar_startup(self, habilitar):
        """Adiciona ou remove o programa da inicialização do Windows."""
        try:
            import winreg as reg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            app_name = "Cromak Bridge Vox"
            exe_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(sys.argv[0])
            
            # Conecta ao registro do usuário atual
            key = reg.OpenKey(reg.HKEY_CURRENT_USER, key_path, 0, reg.KEY_ALL_ACCESS)
            if habilitar:
                reg.SetValueEx(key, app_name, 0, reg.REG_SZ, f'"{exe_path}"')
            else:
                try:
                    reg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass
            reg.CloseKey(key)
        except Exception as e:
            print(f"Erro ao configurar startup: {e}")


    def obter_modelos(self):
        chave = self.config.get("api_key", "").strip()
        provedor = self.config.get("provider", "gemini")
        
        if provedor == "qwen":
            return ["qwen-plus", "qwen-max", "qwen-turbo", "qwen-vl-plus"]
        elif provedor == "openai":
            return ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
        elif provedor == "claude":
            return ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229", "claude-3-haiku-20240307"]
        elif provedor == "groq":
            modelos_groq = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]
            if chave:
                try:
                    from openai import OpenAI
                    client = OpenAI(api_key=chave, base_url="https://api.groq.com/openai/v1")
                    lista = client.models.list()
                    descobertos = [m.id for m in lista.data if "whisper" not in m.id and "guard" not in m.id]
                    if descobertos:
                        return descobertos
                except Exception as e:
                    print(f"Erro ao listar modelos Groq: {e}")
            return modelos_groq
            
        modelos_oficiais = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash", "gemini-1.5-pro"]
        if not chave:
            return modelos_oficiais
        
        try:
            from google import genai
            client = genai.Client(api_key=chave)
            modelos = client.models.list()
            modelos_disponiveis = []
            for m in modelos:
                nome_puro = m.name.replace("models/", "")
                if nome_puro in modelos_oficiais and nome_puro not in modelos_disponiveis:
                    modelos_disponiveis.append(nome_puro)
            return modelos_disponiveis if modelos_disponiveis else modelos_oficiais
        except Exception as e:
            print(f"Erro ao buscar modelos: {e}")
            return modelos_oficiais

    def mudar_modelo(self, novo_modelo):
        self.config["model"] = novo_modelo
        salvar_config_seguro(self.config_path, self.config)
            
        chave = self.config.get("api_key", "").strip()
        provedor = self.config.get("provider", "gemini")
        if chave:
            self.ia = AICore(chave, model_name=novo_modelo, provider=provedor)
        return True

    def salvar_preferencias_duelo(self, prov1, mod1, prov2, mod2):
        self.config["duel"] = {
            "prov1": prov1, "mod1": mod1,
            "prov2": prov2, "mod2": mod2
        }
        salvar_config_seguro(self.config_path, self.config)
        return True

    def abrir_janela_ajuda(self):
        """Abre a página help.html em uma nova janela do pywebview"""
        try:
            help_path = resource_path(os.path.join('web', 'help.html'))
            jan_ajuda = webview.create_window(
                'Ajuda - Cromak Bridge', 
                url=help_path, 
                width=850, 
                height=700,
                background_color='#09090b',
                frameless=False
            )
            jan_ajuda.events.shown += lambda: aplicar_icone_janela('Ajuda - Cromak Bridge')
            aplicar_icone_janela('Ajuda - Cromak Bridge')
            return True
        except Exception as e:
            print(f"Erro ao abrir janela de ajuda: {e}")
            return False

    # --- GERENCIAMENTO DE SESSÕES ---
    def obter_sessoes(self):
        return self.db.listar_sessoes()

    def criar_sessao(self):
        return self.db.criar_sessao("Nova Conversa")

    def abrir_sessao(self, session_id):
        historico_api = self.db.carregar_historico_api(session_id)
        provider = self.config.get("provider", "gemini")
        modelo_padrao = "gemini-2.5-flash" if provider == "gemini" else ("openai/gpt-oss-120b" if provider == "groq" else "qwen-plus")
        modelo_inicial = self.config.get("model", modelo_padrao)
        api_key = self.config.get("api_key", "")
        sys_prompt = self.config.get("system_prompt", "").strip()
        
        self.ia = AICore(api_key, model_name=modelo_inicial, historico=historico_api, provider=provider)
        
        mensagens = self.db.carregar_historico_ui(session_id)
        historico_formatado = []
        for role, content in mensagens:
            role_ui = 'user' if role == 'user' else 'ia'
            historico_formatado.append([role_ui, content])
        return historico_formatado

    def renomear_sessao_manual(self, session_id, novo_nome):
        self.db.renomear_sessao(session_id, novo_nome)

    def excluir_sessao(self, session_id):
        self.db.excluir_sessao(session_id)

    def fixar_sessao(self, session_id, status):
        self.db.fixar_sessao(session_id, status)

    def formatar_compartilhamento(self, session_id):
        mensagens = self.db.carregar_historico_ui(session_id, limite=100)
        texto_export = "--- Sessão Exportada: Cromak Bridge ---\n\n"
        for role, content in mensagens:
            remetente = "Usuário" if role == "user" else "Cromak Bridge"
            texto_export += f"[{remetente}]:\n{content}\n\n"
        return texto_export

    def abrir_link(self, url):
        """Abre links no navegador padrão do Windows, preservando o aplicativo."""
        webbrowser.open(url)
        
    def abrir_arquivo(self, caminho):
        """Abre o arquivo anexado no visualizador padrão do Windows"""
        import os
        caminho_abs = os.path.abspath(caminho)
        if os.path.exists(caminho_abs):
            try:
                os.startfile(caminho_abs)
            except Exception as e:
                print(f"Erro ao abrir arquivo: {e}")

    def abrir_pasta_logs(self):
        """Abre a pasta de logs técnicos de diagnóstico no Windows Explorer mantendo a privacidade do usuário."""
        from core.logger import abrir_pasta_logs
        return abrir_pasta_logs()

    # --- FERRAMENTAS E ARQUIVOS ---
    def gravar_audio(self):
        return self.audio.ouvir()

    def cancelar_audio(self):
        """Interrompe imediatamente a gravação e cancela a escuta de voz."""
        try:
            if hasattr(self, "audio") and self.audio:
                self.audio.cancelar()
        except Exception:
            pass
        try:
            import sounddevice as sd
            sd.stop()
        except Exception:
            pass
        return True


    def selecionar_projeto(self):
        try:
            import webview
            import os
            
            if webview.windows:
                resultado = webview.windows[0].create_file_dialog(webview.FOLDER_DIALOG)
                if resultado and len(resultado) > 0:
                    pasta = resultado[0]
                    
                    extensoes_validas = {'.py', '.js', '.html', '.css', '.json', '.md', '.txt', '.java', '.cpp', '.c', '.cs', '.go', '.rs', '.php'}
                    pastas_ignoradas = {'node_modules', '.git', '__pycache__', '.venv', 'venv', 'env', '.idea', '.vscode'}
                    
                    conteudo_total = []
                    conteudo_total.append(f"=== PROJETO ANEXADO: {os.path.basename(pasta)} ===\n")
                    
                    for root, dirs, files in os.walk(pasta):
                        dirs[:] = [d for d in dirs if d not in pastas_ignoradas]
                        for file in files:
                            ext = os.path.splitext(file)[1].lower()
                            if ext in extensoes_validas:
                                caminho_completo = os.path.join(root, file)
                                try:
                                    with open(caminho_completo, 'r', encoding='utf-8') as f:
                                        conteudo_total.append(f"\n--- ARQUIVO: {os.path.relpath(caminho_completo, pasta)} ---\n")
                                        # Le ate 50.000 caracteres por arquivo
                                        conteudo = f.read(50000)
                                        conteudo_total.append(conteudo)
                                except:
                                    pass
                                    
                    texto_final = "".join(conteudo_total)
                    if len(texto_final) > 1000000:
                        texto_final = texto_final[:1000000]
                    
                    temp_dir = os.path.join(self.data_dir, "temp")
                    os.makedirs(temp_dir, exist_ok=True)
                    arquivo_contexto = os.path.join(temp_dir, "contexto_projeto.txt")
                    
                    with open(arquivo_contexto, 'w', encoding='utf-8') as f:
                        f.write(texto_final)
                        
                    self.arquivo_atual = arquivo_contexto
                    return arquivo_contexto
            return None
        except Exception as e:
            print(f"Erro ao selecionar projeto: {e}")
            return None

    def escolher_arquivo(self, tipo="todos"):
        janela = webview.windows[0]
        
        if tipo == "imagem":
            tipos_permitidos = ('Imagens (*.png;*.jpg;*.jpeg;*.webp)', 'Todos os Arquivos (*.*)')
        elif tipo == "documento":
            tipos_permitidos = ('Documentos (*.pdf;*.docx;*.txt;*.csv;*.md)', 'Todos os Arquivos (*.*)')
        elif tipo == "codigo":
            tipos_permitidos = ('Códigos (*.py;*.json;*.html;*.css;*.js)', 'Todos os Arquivos (*.*)')
        else:
            tipos_permitidos = ('Todos os Suportados (*.png;*.jpg;*.pdf;*.docx;*.txt;*.py;*.json)', 'Todos os Arquivos (*.*)')
            
        arquivos = janela.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=False, file_types=tipos_permitidos)
        if arquivos and len(arquivos) > 0:
            self.arquivo_atual = arquivos[0]
            return os.path.basename(self.arquivo_atual)
        return None
    def capturar_tela(self):
        """Minimiza a janela, captura a tela inteira, restaura a janela e salva o anexo"""
        janela = webview.windows[0]
        try:
            # 1. Esconde a janela para não aparecer no print
            janela.minimize()
            time.sleep(0.5) # Aguarda a animação do Windows de minimizar
            
            # 2. Captura a tela
            print_screen = ImageGrab.grab()
            
            # 3. Restaura a janela
            janela.restore()
            
            # 4. Salva temporariamente
            temp_dir = os.path.join(self.data_dir, "temp")
            os.makedirs(temp_dir, exist_ok=True)
            caminho_temp = os.path.join(temp_dir, "screenshot.png")
            print_screen.save(caminho_temp, "PNG")
            
            self.arquivo_atual = caminho_temp
            return "screenshot.png"
        except Exception as e:
            print(f"Erro ao capturar tela: {e}")
            if hasattr(janela, 'restore'): janela.restore()
            return None

    def receber_arquivo_drop(self, nome, b64_conteudo):
        """Recebe o arquivo arrastado (nome e base64), salva temporariamente e prepara para envio."""
        try:
            temp_dir = os.path.join(self.data_dir, "temp")
            os.makedirs(temp_dir, exist_ok=True)
            caminho_temp = os.path.join(temp_dir, nome)
            
            # Extrai apenas os dados base64 (ignora o cabeçalho data:mime/type;base64,)
            if "," in b64_conteudo:
                b64_conteudo = b64_conteudo.split(",")[1]
                
            dados = base64.b64decode(b64_conteudo)
            with open(caminho_temp, "wb") as f:
                f.write(dados)
                
            self.arquivo_atual = caminho_temp
            return nome
        except Exception as e:
            print(f"Erro ao processar arquivo Drop: {e}")
            return None

    def limpar_arquivo(self):
        self.arquivo_atual = None

    def obter_imagem_base64(self):
        if hasattr(self, 'arquivo_atual') and self.arquivo_atual:
            try:
                mime_type, _ = mimetypes.guess_type(self.arquivo_atual)
                if mime_type and mime_type.startswith('image'):
                    with open(self.arquivo_atual, "rb") as img_file:
                        b64_string = base64.b64encode(img_file.read()).decode('utf-8')
                    return f"data:{mime_type};base64,{b64_string}"
            except: pass
        return None

    def processar_prompt(self, session_id, texto):
        prompt_final = texto
        texto_db = texto

        if hasattr(self, 'arquivo_atual') and self.arquivo_atual:
            try:
                extensao = self.arquivo_atual.lower().split('.')[-1]
                conteudo = None
                
                if extensao in ['txt', 'csv', 'py', 'json', 'html', 'md', 'log', 'bat', 'js', 'css', 'java', 'cpp', 'c']:
                    with open(self.arquivo_atual, 'r', encoding='utf-8', errors='ignore') as f:
                        conteudo = f.read()
                elif extensao == 'pdf':
                    import fitz # PyMuPDF
                    doc = fitz.open(self.arquivo_atual)
                    text_blocks = []
                    for page in doc:
                        text_blocks.append(page.get_text())
                    conteudo = "\n--- NOVA PÁGINA ---\n".join(text_blocks)
                    if len(conteudo) > 500000:
                        conteudo = conteudo[:500000]
                elif extensao == 'docx':
                    import docx2txt
                    conteudo = docx2txt.process(self.arquivo_atual)
                
                if conteudo is not None:
                    prompt_final = f"Conteúdo do arquivo anexo ({os.path.basename(self.arquivo_atual)}):\n\n{conteudo}\n\nInstrução do usuário: {texto}"
                    caminho_escapado = self.arquivo_atual.replace('\\', '/')
                    texto_db = f"<div class='attachment-chip' onclick='pywebview.api.abrir_arquivo(\"{caminho_escapado}\")' title='Clique para abrir'>📎 Arquivo: {os.path.basename(self.arquivo_atual)}</div>\n\n{texto}"
                    self.arquivo_atual = None
            except Exception as e:
                self.arquivo_atual = None
                return f"❌ Erro ao extrair texto do documento: {e}"

        sessoes = self.db.listar_sessoes()
        for s_id, title, is_pinned in sessoes:
            if s_id == session_id and title == "Nova Conversa":
                nome = texto if texto else "Análise de Arquivo"
                self.db.renomear_sessao(session_id, nome[:25] + "...")
                break

        if hasattr(self, 'arquivo_atual') and self.arquivo_atual:
            b64_url = self.obter_imagem_base64()
            if b64_url:
                texto_db = f"![Anexo]({b64_url})\n\n{texto}"
            else:
                caminho_escapado = self.arquivo_atual.replace('\\', '/')
                texto_db = f"<div class='attachment-chip' onclick='pywebview.api.abrir_arquivo(\"{caminho_escapado}\")' title='Clique para abrir'>📑 Documento: {os.path.basename(self.arquivo_atual)}</div>\n\n{texto}"

        self.db.salvar_mensagem(session_id, "user", texto_db)
        
        try:
            if hasattr(self, 'arquivo_atual') and self.arquivo_atual:
                resposta = self.ia.enviar_prompt(prompt_final, self.arquivo_atual)
                self.arquivo_atual = None
            else:
                resposta = self.ia.enviar_prompt(prompt_final)
        except Exception as e:
            resposta = f"⚠️ [Erro Crítico]: {e}"
            
        self.db.salvar_mensagem(session_id, "model", resposta)
        return resposta

    def obter_modelos_por_provedor(self, provedor):
        chave = self.config.get("api_keys", {}).get(provedor, "")
        
        if provedor == "qwen":
            return ["qwen-plus", "qwen-max", "qwen-turbo", "qwen-vl-plus"]
        elif provedor == "openai":
            return ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo", "o1-mini", "o1-preview"]
        elif provedor == "claude":
            return ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229", "claude-3-haiku-20240307"]
        elif provedor == "groq":
            return ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]
            
        modelos_oficiais = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash", "gemini-1.5-pro"]
        if not chave:
            return modelos_oficiais
        
        try:
            from google import genai
            client = genai.Client(api_key=chave)
            modelos = client.models.list()
            modelos_disponiveis = []
            for m in modelos:
                nome_puro = m.name.replace("models/", "")
                if nome_puro in modelos_oficiais and nome_puro not in modelos_disponiveis:
                    modelos_disponiveis.append(nome_puro)
            return modelos_disponiveis if modelos_disponiveis else modelos_oficiais
        except Exception as e:
            print(f"Erro ao buscar modelos para {provedor}: {e}")
            return modelos_oficiais

    def processar_duelo(self, texto, prov1="gemini", mod1="", prov2="claude", mod2=""):
        import concurrent.futures
        
        # --- Processamento de Anexo (Idêntico ao fluxo de conversa) ---
        prompt_final = texto
        arquivo_para_enviar = None
        if hasattr(self, 'arquivo_atual') and self.arquivo_atual:
            arquivo_para_enviar = self.arquivo_atual
            try:
                extensao = self.arquivo_atual.lower().split('.')[-1]
                conteudo = None
                
                if extensao in ['txt', 'csv', 'py', 'json', 'html', 'md', 'log', 'bat', 'js', 'css', 'java', 'cpp', 'c']:
                    with open(self.arquivo_atual, 'r', encoding='utf-8', errors='ignore') as f:
                        conteudo = f.read()
                elif extensao == 'pdf':
                    import fitz # PyMuPDF
                    doc = fitz.open(self.arquivo_atual)
                    text_blocks = []
                    for page in doc:
                        text_blocks.append(page.get_text())
                    conteudo = "\n--- NOVA PÁGINA ---\n".join(text_blocks)
                    if len(conteudo) > 500000: conteudo = conteudo[:500000]
                elif extensao == 'docx':
                    import docx2txt
                    conteudo = docx2txt.process(self.arquivo_atual)
                
                if conteudo is not None:
                    import os
                    prompt_final = f"Conteúdo do arquivo anexo ({os.path.basename(self.arquivo_atual)}):\n\n{conteudo}\n\nInstrução do usuário: {texto}"
                    arquivo_para_enviar = None # O texto já foi extraído, não envia o binário bruto
            except Exception as e:
                pass
        # ----------------------------------------------------------------
        
        sys_prompt = self.config.get("system_prompt", "")
        # Busca as chaves de API específicas de cada provedor
        key1 = self.config.get("api_keys", {}).get(prov1, "")
        key2 = self.config.get("api_keys", {}).get(prov2, "")
        
        # Puxa modelos padrão para o duelo
        def default_model(p):
            if p == "gemini": return "gemini-2.5-flash"
            if p == "claude": return "claude-3-5-sonnet-20240620"
            if p == "openai": return "gpt-4o-mini"
            if p == "qwen": return "qwen-plus"
            if p == "groq": return "openai/gpt-oss-120b"
            return ""
            
        m1 = mod1 if mod1 else default_model(prov1)
        m2 = mod2 if mod2 else default_model(prov2)
            
        ia1 = AICore(key1, model_name=m1, provider=prov1, system_prompt=sys_prompt)
        ia2 = AICore(key2, model_name=m2, provider=prov2, system_prompt=sys_prompt)
        
        def fetch(ia):
            # Valida se o motor foi criado corretamente
            if not getattr(ia, 'engine', None) or isinstance(ia.engine, str):
                return "⚠️ **Motor inativo:** Faltando chave de API para este provedor."
            if arquivo_para_enviar:
                return ia.enviar_prompt(prompt_final, arquivo_para_enviar)
            return ia.enviar_prompt(prompt_final)
            
        # Roda as duas IAs em paralelo usando threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(fetch, ia1)
            future2 = executor.submit(fetch, ia2)
            
            res1 = future1.result()
            res2 = future2.result()
            
        if hasattr(self, 'arquivo_atual'):
            self.arquivo_atual = None
            
        return {"col1": res1, "col2": res2}
    def processar_comando_spotlight(self, texto):
        """Processa um comando rápido vindo do Spotlight e retorna a resposta."""
        # Usa o provedor atual para dar uma resposta rápida
        try:
            return self.ia.enviar_prompt("Responda de forma extremamente curta e direta: " + texto)
        except Exception as e:
            return f"Erro: {e}"

    def enviar_comando_texto(self, texto):
        """Compatibilidade para comandos diretos enviados via atalhos do teclado."""
        try:
            return self.processar_prompt(None, texto)
        except Exception as e:
            return f"Erro: {e}"

    def alternar_tela_cheia(self):
        """Alterna a janela entre modo normal e tela cheia (F11) preservando o ícone na barra de título"""
        import webview
        try:
            if webview.windows:
                janela = webview.windows[0]
                janela.toggle_fullscreen()
                aplicar_icone_janela("Cromak Bridge")
                return True
        except Exception as e:
            print("Erro ao alternar tela cheia:", e)
        return False

    def encerrar_sistema(self):
        """Encerra completamente o aplicativo de forma imediata (kill total de processos e threads)."""
        try:
            if hasattr(self, "tray_icon") and self.tray_icon:
                self.tray_icon.stop()
        except Exception:
            pass
        try:
            import webview
            for w in webview.windows:
                w.destroy()
        except Exception:
            pass
        import os
        os._exit(0)

    def parar_audio(self):
        """Interrompe qualquer reprodução de áudio ativa ou gravação de microfone."""
        try:
            self.cancelar_audio()
        except Exception:
            pass
        try:
            import pyttsx3
            eng = pyttsx3.init()
            eng.stop()
        except Exception:
            pass
        return True

def vigia_agenda_background():
    """Vigia inteligente da Agenda Fixa em segundo plano:
    1. Notifica e fala em voz alta quando o compromisso chega na hora exata (HH:MM).
    2. Notifica com 15 minutos de antecedência para o usuário se preparar.
    """
    import sqlite3
    from datetime import datetime, timedelta
    from core.local_tools import _inicializar_db_agenda
    
    # Conjuntos em memória para não repetir notificação na mesma hora
    notificados_15min = set()
    notificados_hora = set()

    while True:
        try:
            db_path = _inicializar_db_agenda()
            agora = datetime.now()
            data_hoje = agora.strftime("%d/%m/%Y")
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("SELECT id, titulo, hora_evento, detalhes FROM agenda_itens WHERE data_evento = ? AND hora_evento != ''", (data_hoje,))
            eventos_hoje = cur.fetchall()
            conn.close()

            for ev_id, ev_tit, ev_hora, ev_det in eventos_hoje:
                try:
                    partes = [int(p) for p in ev_hora.split(":")]
                    dt_evento = agora.replace(hour=partes[0], minute=partes[1], second=0, microsecond=0)
                    diff_seg = (dt_evento - agora).total_seconds()
                    diff_min = diff_seg / 60.0

                    # 1. Alerta de 15 Minutos de Antecedência (entre 14 e 16 minutos)
                    chave_15m = f"{ev_id}_{data_hoje}_15m"
                    if 13.5 <= diff_min <= 16.0 and chave_15m not in notificados_15min:
                        notificados_15min.add(chave_15m)
                        try:
                            import winsound
                            winsound.Beep(659, 150)
                            winsound.Beep(880, 250)
                        except Exception: pass
                        try:
                            from win11toast import toast
                            msg_15 = f"{ev_tit} às {ev_hora} (em 15 minutos)" + (f" — {ev_det}" if ev_det else "")
                            toast("⏳ Lembrete em 15 Minutos!", msg_15, app_id="Cromak Bridge")
                        except Exception: pass
                        try:
                            import pyttsx3
                            def _falar_15m():
                                try:
                                    engine = pyttsx3.init()
                                    engine.setProperty('rate', 180)
                                    engine.say(f"Lembrete da sua agenda: Em 15 minutos você tem {ev_tit}.")
                                    engine.runAndWait()
                                except Exception: pass
                            threading.Thread(target=_falar_15m, daemon=True).start()
                        except Exception: pass

                    # 2. Alarme da Hora Exata (entre 0 e 1 minuto restante)
                    chave_hora = f"{ev_id}_{data_hoje}_hora"
                    if -0.5 <= diff_min <= 1.0 and chave_hora not in notificados_hora:
                        notificados_hora.add(chave_hora)
                        # Atualiza no banco como notificado
                        try:
                            c_up = sqlite3.connect(db_path)
                            c_up.execute("UPDATE agenda_itens SET notificado = 1 WHERE id = ?", (ev_id,))
                            c_up.commit()
                            c_up.close()
                        except Exception: pass

                        try:
                            import winsound
                            winsound.Beep(784, 180)
                            winsound.Beep(987, 250)
                            winsound.Beep(1174, 300)
                        except Exception: pass
                        try:
                            from win11toast import toast
                            msg_h = f"{ev_tit}" + (f" — {ev_det}" if ev_det else "")
                            toast("🔔 Seu Compromisso é Agora!", msg_h, app_id="Cromak Bridge")
                        except Exception: pass
                        try:
                            import pyttsx3
                            def _falar_agora():
                                try:
                                    engine = pyttsx3.init()
                                    engine.setProperty('rate', 180)
                                    engine.say(f"Atenção: Seu compromisso é agora: {ev_tit}.")
                                    engine.runAndWait()
                                except Exception: pass
                            threading.Thread(target=_falar_agora, daemon=True).start()
                        except Exception: pass

                except Exception: pass

        except Exception: pass
        time.sleep(25)

def global_hotkey_listener():
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    # MOD_ALT = 0x0001, MOD_CONTROL = 0x0002, MOD_SHIFT = 0x0004, VK_SPACE = 0x20
    # Tenta registrar Alt + Espaço primeiro; se o Windows recusar, registra Ctrl + Espaço
    hotkey_id = 99
    registrado = False
    nome_atalho = ""

    # IDs independentes para registrar Alt+Espaço E Ctrl+Espaço simultaneamente
    HOTKEY_ALT_SPACE = 99
    HOTKEY_CTRL_SPACE = 100
    HOTKEY_CTRL_SHIFT_SPACE = 101
    HOTKEY_ALT_C = 102

    registrados = []
    if user32.RegisterHotKey(None, HOTKEY_ALT_SPACE, 0x0001, 0x20):
        registrados.append("Alt+Espaço")
    if user32.RegisterHotKey(None, HOTKEY_CTRL_SPACE, 0x0002, 0x20):
        registrados.append("Ctrl+Espaço")
    if user32.RegisterHotKey(None, HOTKEY_CTRL_SHIFT_SPACE, 0x0006, 0x20):
        registrados.append("Ctrl+Shift+Espaço")

    if not registrados:
        if user32.RegisterHotKey(None, HOTKEY_ALT_C, 0x0001, 0x43):
            registrados.append("Alt+C")

    from core.logger import log_info, log_warning
    if registrados:
        log_info(f"Atalhos globais de invocação ativados: [{', '.join(registrados)}]")
        print(f"Atalhos globais de invocação ativados: [{', '.join(registrados)}] (Restauram o app da bandeja de qualquer lugar)")
    else:
        log_warning("Aviso: Windows não permitiu registrar atalhos globais de invocação (conflito de hotkey).")
        print("Aviso: Windows não permitiu registrar atalhos globais de invocação.")
        return

    ids_invocacao = {HOTKEY_ALT_SPACE, HOTKEY_CTRL_SPACE, HOTKEY_CTRL_SHIFT_SPACE, HOTKEY_ALT_C}
    msg = wintypes.MSG()
    while user32.GetMessageA(ctypes.byref(msg), None, 0, 0) != 0:
        if msg.message == 0x0312:
            if msg.wParam in ids_invocacao:
                try:
                    import webview
                    if webview.windows:
                        janela = webview.windows[0]
                        janela.show()
                        janela.restore()
                        # Foca na janela e coloca o cursor no campo de texto para o NVDA falar
                        janela.evaluate_js("window.focus(); const inp = document.getElementById('userInput'); if(inp) { inp.focus(); }")
                except Exception as e:
                    print("Erro ao restaurar janela pelo atalho global:", e)
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageA(ctypes.byref(msg))


# VARIÁVEL GLOBAL PARA OS ATALHOS DO BRIDGE VOX (Linguagem Universal)
cromak_window_global = None

def registrar_aumid_windows():
    aumid = "Cromak Bridge Vox"
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(aumid)
    except Exception:
        pass
    
    # Registra no registro do Windows (HKCU\Software\Classes\AppUserModelId\...)
    # para garantir que as notificações Toast do Windows exibam o ícone e nome oficiais
    try:
        caminhos_ico = [
            resource_path(os.path.join("web", "lib", "cromak-bridge.ico")),
            resource_path("cromak-bridge.ico"),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "web", "lib", "cromak-bridge.ico")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "cromak-bridge.ico")),
            os.path.abspath(os.path.join(os.getcwd(), "web", "lib", "cromak-bridge.ico")),
            os.path.abspath(os.path.join(os.getcwd(), "cromak-bridge.ico")),
        ]
        ico_final = None
        for p in caminhos_ico:
            if os.path.exists(p):
                ico_final = os.path.abspath(p)
                break
        
        if ico_final:
            key_path = fr"Software\Classes\AppUserModelId\{aumid}"
            with reg.CreateKey(reg.HKEY_CURRENT_USER, key_path) as key:
                reg.SetValueEx(key, "DisplayName", 0, reg.REG_SZ, "Cromak Bridge Vox")
                reg.SetValueEx(key, "IconUri", 0, reg.REG_SZ, ico_final)
                reg.SetValueEx(key, "ShowInSettings", 0, reg.REG_DWORD, 1)

            # Também cria/atualiza o atalho com AUMID no Menu Iniciar do usuário
            # para que a Central de Ações do Windows associe o ícone e nome à notificação
            try:
                import importlib
                win32com_client = importlib.import_module("win32com.client")
                propsys = importlib.import_module("win32com.propsys.propsys")
                programs_dir = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Cromak Technology")
                os.makedirs(programs_dir, exist_ok=True)
                lnk_path = os.path.join(programs_dir, "Cromak Bridge Vox.lnk")
                wscript = win32com_client.Dispatch("WScript.Shell")
                shortcut = wscript.CreateShortcut(lnk_path)
                shortcut.TargetPath = sys.executable
                shortcut.WorkingDirectory = os.path.dirname(sys.executable)
                shortcut.IconLocation = f"{ico_final},0"
                shortcut.Description = "Assistente de IA Acessível Cromak Bridge Vox"
                shortcut.Save()
                
                store = propsys.SHGetPropertyStoreFromParsingName(lnk_path, None, 2)
                pk = propsys.PSGetPropertyKeyFromName("System.AppUserModel.ID")
                prop = propsys.PROPVARIANTType(aumid)
                store.SetValue(pk, prop)
                store.Commit()
            except Exception:
                pass
    except Exception as e:
        print("Aviso ao registrar AUMID no Windows:", e)

def verificar_webview2_instalado():
    """
    Verifica se o Microsoft Edge WebView2 Runtime está presente no sistema operacional.
    Retorna True se instalado, False caso contrário.
    """
    import winreg
    locais = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-942A-42c4-9B14-5F33630F7078}"),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\EdgeUpdate\Clients\{F3017226-942A-42c4-9B14-5F33630F7078}"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-942A-42c4-9B14-5F33630F7078}"),
    ]
    for hkey, subkey in locais:
        for flag in [0, winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY]:
            try:
                with winreg.OpenKey(hkey, subkey, 0, winreg.KEY_READ | flag) as k:
                    val, _ = winreg.QueryValueEx(k, "pv")
                    if val and val.strip() != "" and val.strip() != "0.0.0.0":
                        return True
            except Exception:
                pass

    pastas_padrao = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\EdgeWebView\Application"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\EdgeWebView\Application"),
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\EdgeWebView\Application"),
    ]
    for pasta in pastas_padrao:
        if os.path.exists(pasta):
            try:
                subitens = os.listdir(pasta)
                for item in subitens:
                    if item and item[0].isdigit() and os.path.isdir(os.path.join(pasta, item)):
                        return True
            except Exception:
                pass
    return False

def alertar_falta_webview2():
    """
    Exibe um diálogo nativo e 100% acessível (compatível com NVDA, JAWS e Narrador)
    notificando que o Microsoft Edge WebView2 Runtime está ausente no Windows e
    oferecendo redirecionamento imediato para download gratuito.
    """
    mensagem = (
        "O Microsoft Edge WebView2 Runtime não foi detectado neste computador.\n\n"
        "O Cromak Bridge Vox necessita deste componente oficial para renderizar a interface gráfica acessível.\n"
        "(Em edições padrão do Windows 10 e 11 ele já vem pré-instalado, mas edições como Windows 10 LTSC, "
        "Windows Server ou Windows IoT requerem instalação avulsa).\n\n"
        "Deseja abrir agora a página oficial da Microsoft para baixar o instalador gratuito do WebView2 Runtime?"
    )
    titulo = "Cromak Bridge Vox - Requisito do Sistema Ausente"
    # 0x04 = MB_YESNO, 0x10 = MB_ICONERROR, 0x1000 = MB_SYSTEMMODAL
    resposta = ctypes.windll.user32.MessageBoxW(0, mensagem, titulo, 0x04 | 0x10 | 0x1000)
    if resposta == 6:  # IDYES
        webbrowser.open("https://go.microsoft.com/fwlink/p/?LinkId=2124703")
    import os
    os._exit(1)

def aplicar_atalhos_bridgevox():
    # Os atalhos de janela (F1, F2, F3, F4, F5, F10, F11, Esc) são gerenciados localmente no script.js
    # apenas quando a janela do Bridge está ativa, evitando conflito com outros programas do Windows.
    pass

if __name__ == '__main__':
    registrar_aumid_windows()
    if not verificar_webview2_instalado():
        alertar_falta_webview2()
    api = ApiBackend()
    
    modo_interface = api.config.get("interface_mode", "normal")
    if modo_interface == "vox":
        api.config["interface_mode"] = "normal"
        api.salvar_preferencias(api.config)
    html_path = resource_path(os.path.join('web', 'index.html'))
    
    # Inicia listener do atalho global (Alt+Space)
    t = threading.Thread(target=global_hotkey_listener, daemon=True)
    t.start()
    threading.Thread(target=vigia_agenda_background, daemon=True).start()
    
    start_fullscreen = api.config.get("start_fullscreen", True)

    try:
        import webview.platforms.winforms as _wf
        _wf._state['icon'] = resource_path(os.path.join('web', 'lib', 'cromak-bridge.ico'))
    except Exception:
        pass

    from core.logger import log_info
    log_info(f"Iniciando Cromak Bridge Vox v{APP_VERSION} (Build {APP_BUILD})")
    log_info(f"Provedor ativo: {api.config.get('provider')} | Modelo: {api.config.get('model')}")

    janela = webview.create_window(
        'Cromak Bridge Vox', 
        url=html_path, 
        width=1100, 
        height=750, 
        min_size=(900, 600),
        js_api=api,
        background_color='#09090b',
        frameless=False,
        transparent=False,
        fullscreen=False
    )

    cromak_window_global = janela
    aplicar_atalhos_bridgevox()

    # Intercepta o evento de fechamento da janela
    def on_closing():
        if api.config.get("minimize_to_tray", False):
            janela.hide()
            if hasattr(api, 'tray_icon') and api.tray_icon:
                try:
                    # Envia a notificação Toast nativa sem repetir o título no corpo
                    # O cabeçalho da notificação no Windows já exibe: [Ícone] Cromak Bridge Vox
                    api.tray_icon._message(
                        pystray._win32.win32.NIM_MODIFY,
                        pystray._win32.win32.NIF_INFO,
                        szInfo="O Bridge Vox está em segundo plano. Pressione Ctrl+Espaço para reabrir a janela principal a qualquer momento.",
                        szInfoTitle=""
                    )
                except Exception:
                    try:
                        api.tray_icon.notify(
                            "O Bridge Vox está em segundo plano. Pressione Ctrl+Espaço para reabrir a janela principal a qualquer momento."
                        )
                    except Exception:
                        pass
            return False # Impede o encerramento do processo
        return True # Permite que o app feche normalmente

    def on_main_shown():
        aplicar_icone_janela('Cromak Bridge')
        if start_fullscreen:
            try:
                janela.toggle_fullscreen()
            except Exception:
                pass
        # Foco intencional e imediato para o NVDA entrar no Modo de Foco com role="application"
        try:
            janela.evaluate_js("if (typeof focarCampoMensagem === 'function') focarCampoMensagem();")
        except Exception:
            pass

    janela.events.closing += on_closing
    janela.events.shown += on_main_shown
    
    # Se configurado, já cria o tray icon ao iniciar o app
    if api.config.get("minimize_to_tray", False):
        api.gerenciar_tray(True)
        
    try:
        webview.start(icon=resource_path(os.path.join('web', 'lib', 'cromak-bridge.ico')))
    except Exception as e:
        print("Erro crítico ao inicializar interface WebView2:", e)
        alertar_falta_webview2()
    
    # Ao fechar a janela, garante o encerramento total de todos os processos e threads (kill limpo)
    try:
        if hasattr(api, "tray_icon") and api.tray_icon:
            api.tray_icon.stop()
    except Exception:
        pass
    import os
    os._exit(0)