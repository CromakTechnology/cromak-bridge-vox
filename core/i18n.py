import json
import os

class Translator:
    def __init__(self, language_code="pt_BR"):
        self.language_code = language_code
        self.translations = {}
        self.load_language()

    def load_language(self):
        """Carrega o arquivo JSON de idioma correspondente."""
        # Caminho absoluto para evitar erros quando rodar o main.py de outras pastas
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        locale_path = os.path.join(base_dir, "locale", f"{self.language_code}.json")

        try:
            with open(locale_path, "r", encoding="utf-8") as file:
                self.translations = json.load(file)
        except FileNotFoundError:
            print(f"[Aviso] Pacote de idioma '{self.language_code}' não encontrado. Voltando para en_US.")
            # Fallback seguro caso o arquivo não exista
            if self.language_code != "en_US":
                self.language_code = "en_US"
                self.load_language()

    def get(self, key, **kwargs):
        """
        Busca a tradução pela chave. 
        Suporta formatação dinâmica. Ex: get("status_reading_file", file_name="main.py")
        """
        text = self.translations.get(key, f"[{key}]") # Retorna a chave entre colchetes se não achar a tradução
        
        if kwargs:
            try:
                return text.format(**kwargs)
            except KeyError:
                return text
                
        return text

# Teste rápido de uso (só roda se você executar este arquivo diretamente)
if __name__ == "__main__":
    _ = Translator("pt_BR")
    print(_.get("welcome_message"))
    print(_.get("status_reading_file", file_name="desinstalador.py"))