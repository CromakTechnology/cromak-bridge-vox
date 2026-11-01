import speech_recognition as sr
import sounddevice as sd
from scipy.io.wavfile import write
import tempfile
import os

class AudioEngine:
    def __init__(self, language="pt-BR"):
        self.recognizer = sr.Recognizer()
        self.language = language

    def _bip(self, freq, dur):
        try:
            import winsound
            winsound.Beep(freq, dur)
        except Exception:
            pass

    def ouvir(self):
        caminho_temp = os.path.join(tempfile.gettempdir(), "comando_temp.wav")
        try:
            freq = 16000  # 16kHz é ideal e leve para Whisper e SpeechRecognition
            duracao = 5   # 5 segundos de captura

            # Sinal sonoro de início (agudo) para orientar usuário cego que o microfone abriu
            self._bip(880, 140)

            gravacao = sd.rec(int(duracao * freq), samplerate=freq, channels=1, dtype="int16")
            sd.wait()

            # Sinal sonoro de fim (grave) indicando que terminou de ouvir
            self._bip(587, 140)

            write(caminho_temp, freq, gravacao)

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
                            client = OpenAI(api_key=groq_key, base_url="https://api.groq.com/openai/v1")
                            with open(caminho_temp, "rb") as af:
                                trans = client.audio.transcriptions.create(
                                    file=("comando_temp.wav", af.read()),
                                    model="whisper-large-v3-turbo",
                                    language="pt"
                                )
                            texto_w = (trans.text or "").strip()
                            if texto_w:
                                try: os.remove(caminho_temp)
                                except Exception: pass
                                return texto_w
                            break
            except Exception as e_w:
                print("Fallback de Whisper para SpeechRecognition:", e_w)

            # 2ª Tentativa (Fallback universal gratuito): Google SpeechRecognition
            with sr.AudioFile(caminho_temp) as source:
                audio_data = self.recognizer.record(source)
                texto = self.recognizer.recognize_google(audio_data, language=self.language)

            try: os.remove(caminho_temp)
            except Exception: pass
            return texto

        except sr.UnknownValueError:
            try: os.remove(caminho_temp)
            except Exception: pass
            return "[Erro] Não consegui entender o áudio. Fale mais perto do microfone."
        except Exception as e:
            try: os.remove(caminho_temp)
            except Exception: pass
            return f"[Erro] Falha no serviço de voz: {e}"
