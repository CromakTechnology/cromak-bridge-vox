import json
import os

class CromakConnectionBlock:
    def __init__(self):
        self.config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
        self.licenca_ativa = False
        self.tipo_plano = "Free"

    def _carregar_chave(self):
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config.get("license_key", "")
        except:
            return ""

    def validar_licenca(self):
        """Verifica se a chave salva é válida no sistema da Cromak Technology."""
        chave = self._carregar_chave()
        
        # Simulação da regra de negócios do Keygen Admin
        if not chave:
            self.licenca_ativa = False
            self.tipo_plano = "Bloqueado"
            return False, "Nenhuma licença encontrada."
            
        # Exemplo: chaves que começam com CRK-ENT são Enterprise, CRK-PRO são Pro
        if chave.startswith("CRK-ENT-"):
            self.licenca_ativa = True
            self.tipo_plano = "Enterprise"
            return True, "Licença Enterprise validada com sucesso."
        elif chave.startswith("CRK-PRO-"):
            self.licenca_ativa = True
            self.tipo_plano = "Pro"
            return True, "Licença Pro validada."
        else:
            self.licenca_ativa = False
            self.tipo_plano = "Inválido"
            return False, "Chave de licença inválida ou expirada."

    def salvar_chave(self, nova_chave):
        """Salva a nova chave de licença no config.json."""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except:
            config = {}
            
        config["license_key"] = nova_chave
        
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)