import speech_recognition as sr
import sounddevice as sd
from scipy.io.wavfile import write
import tempfile
import os
import threading
import time
import socket

class AudioEngine:
    def __init__(self, language="pt-BR"):
        self.recognizer = sr.Recognizer()
        self.language = language
        self._cancel_event = threading.Event()
        self.esta_gravando = False

    def cancelar(self):
        """Cancela imediatamente qualquer gravação e processamento de áudio."""
        self._cancel_event.set()
        self.esta_gravando = False
        try:
            sd.stop()
        except Exception:
            pass

    def _bip(self, freq, dur):
        try:
            import winsound
            winsound.Beep(freq, dur)
        except Exception:
            pass

    def ouvir(self):
        caminho_temp = os.path.join(tempfile.gettempdir(), f"comando_temp_{os.getpid()}.wav")
        self._cancel_event.clear()
        self.esta_gravando = True
        try:
            freq = 16000  # 16kHz é ideal e leve para Whisper e SpeechRecognition
            duracao = 5.0 # 5 segundos de captura

            # Sinal sonoro de início (agudo) para orientar usuário que o microfone abriu
            self._bip(880, 140)

            if self._cancel_event.is_set():
                return "[Cancelado] Gravação cancelada."

            gravacao = sd.rec(int(duracao * freq), samplerate=freq, channels=1, dtype="int16")
            
            # Aguarda a gravação checando o cancelamento a cada 100ms
            tempo_decorrido = 0.0
            while tempo_decorrido < duracao:
                if self._cancel_event.is_set():
                    try:
                        sd.stop()
                    except Exception:
                        pass
                    return "[Cancelado] Gravação cancelada."
                time.sleep(0.1)
                tempo_decorrido += 0.1

            try:
                sd.wait()
            except Exception:
                pass

            if self._cancel_event.is_set():
                return "[Cancelado] Gravação cancelada."

            # Sinal sonoro de fim (grave) indicando que terminou de ouvir
            self._bip(587, 140)

            write(caminho_temp, freq, gravacao)

            if self._cancel_event.is_set():
                return "[Cancelado] Gravação cancelada."

            # 1ª Tentativa: Groq Whisper (whisper-large-v3-turbo) se houver chave Groq configurada
            try:
                from .seguranca import ler_config_seguro
                base_dir = os.getenv("APPDATA") or os.path.expanduser("~")
                for sub in ("Bridge Vox", "Bridge"):
                    cfg_p = os.path.join(base_dir, "Cromak Technology", sub, "config.json")
                    if os.path.exists(cfg_p):
                        cfg = ler_config_seguro(cfg_p) or {}
                        groq_key = cfg.get("api_keys", {}).get("groq", "") or (cfg.get("api_key", "") if cfg.get("provider") == "groq" else "")
                        if groq_key:
                            from openai import OpenAI
                            client = OpenAI(api_key=groq_key, base_url="https://api.groq.com/openai/v1", timeout=8.0)
                            with open(caminho_temp, "rb") as af:
                                trans = client.audio.transcriptions.create(
                                    file=("comando_temp.wav", af.read()),
                                    model="whisper-large-v3-turbo",
                                    language="pt"
                                )
                            texto_w = (trans.text or "").strip()
                            if texto_w:
                                return texto_w
                            break
            except Exception as e_w:
                print("Fallback de Whisper para SpeechRecognition:", e_w)

            if self._cancel_event.is_set():
                return "[Cancelado] Gravação cancelada."

            # 2ª Tentativa (Fallback universal gratuito): Google SpeechRecognition
            # Timeout no socket para evitar travar a requisição indefinidamente
            timeout_padrao = socket.getdefaulttimeout()
            socket.setdefaulttimeout(8.0)
            try:
                with sr.AudioFile(caminho_temp) as source:
                    audio_data = self.recognizer.record(source)
                    texto = self.recognizer.recognize_google(audio_data, language=self.language)
            finally:
                socket.setdefaulttimeout(timeout_padrao)

            if self._cancel_event.is_set():
                return "[Cancelado] Gravação cancelada."

            return texto

        except sr.UnknownValueError:
            if self._cancel_event.is_set():
                return "[Cancelado] Gravação cancelada."
            return "[Erro] Não consegui entender o áudio. Fale mais perto do microfone."
        except Exception as e:
            if self._cancel_event.is_set():
                return "[Cancelado] Gravação cancelada."
            return f"[Erro] Falha no serviço de voz: {e}"
        finally:
            self.esta_gravando = False
            try:
                if os.path.exists(caminho_temp):
                    os.remove(caminho_temp)
            except Exception:
                pass
