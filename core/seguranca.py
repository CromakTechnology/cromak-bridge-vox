import os
import json
import base64
import socket

def get_appdata_dir() -> str:
    """
    Retorna o diretório persistente oficial do Cromak Bridge Vox:
    %APPDATA%\\Cromak Technology\\Bridge Vox
    Garante integridade de pastas, organiza os bancos de dados em 'banco_de_dados'
    e migra qualquer arquivo residual da pasta legada 'Bridge' para manter o sistema limpo.
    """
    if os.name == 'nt':
        base_dir = os.getenv('APPDATA') or os.path.expanduser('~')
    else:
        base_dir = os.path.expanduser('~')
        
    pasta_vox = os.path.join(base_dir, "Cromak Technology", "Bridge Vox")
    pasta_legada = os.path.join(base_dir, "Cromak Technology", "Bridge")
    
    os.makedirs(pasta_vox, exist_ok=True)
    pasta_db = os.path.join(pasta_vox, "banco_de_dados")
    os.makedirs(pasta_db, exist_ok=True)
    
    # 1. Migração e higienização da pasta legada 'Bridge'
    if os.path.exists(pasta_legada) and os.path.abspath(pasta_legada) != os.path.abspath(pasta_vox):
        try:
            import shutil
            for item in os.listdir(pasta_legada):
                origem = os.path.join(pasta_legada, item)
                destino = os.path.join(pasta_vox, item)
                if item == "agenda_pessoal.db":
                    destino = os.path.join(pasta_db, item)
                if not os.path.exists(destino):
                    shutil.move(origem, destino)
            try:
                shutil.rmtree(pasta_legada, ignore_errors=True)
            except Exception:
                pass
        except Exception:
            pass

    # 2. Garante que agenda_pessoal.db fique sempre dentro de 'banco_de_dados'
    agenda_solta = os.path.join(pasta_vox, "agenda_pessoal.db")
    agenda_organizada = os.path.join(pasta_db, "agenda_pessoal.db")
    if os.path.exists(agenda_solta) and not os.path.exists(agenda_organizada):
        try:
            import shutil
            shutil.move(agenda_solta, agenda_organizada)
        except Exception:
            pass
            
    return pasta_vox

# Gera uma chave estática baseada no hostname
def get_machine_key():
    hostname = socket.gethostname()
    salt = 'CromakBridge_2026_SecureKey'
    raw_key = (hostname + salt).encode('utf-8')
    import hashlib
    m = hashlib.sha256()
    m.update(raw_key)
    return m.digest()

def xor_bytes(data: bytes, key: bytes) -> bytes:
    key_len = len(key)
    return bytes([b ^ key[i % key_len] for i, b in enumerate(data)])

def ler_config_seguro(path):
    if not os.path.exists(path):
        return {}
    
    # Try reading as Base64 XOR
    try:
        with open(path, 'rb') as f:
            encrypted_b64 = f.read()
        encrypted_data = base64.b64decode(encrypted_b64)
        decrypted_data = xor_bytes(encrypted_data, get_machine_key())
        return json.loads(decrypted_data.decode('utf-8'))
    except Exception:
        # Tenta ler como json puro (migração)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            # Salva no novo formato
            salvar_config_seguro(path, cfg)
            return cfg
        except:
            pass
            
    # Try to read as the old Fernet if it exists
    try:
        from cryptography.fernet import Fernet
        with open(path, 'rb') as f:
            enc_fernet = f.read()
        f_obj = Fernet(base64.urlsafe_b64encode(get_machine_key()))
        dec = f_obj.decrypt(enc_fernet)
        cfg = json.loads(dec.decode('utf-8'))
        salvar_config_seguro(path, cfg)
        return cfg
    except:
        return {}

def salvar_config_seguro(path, cfg):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = json.dumps(cfg, indent=4).encode('utf-8')
        encrypted_data = xor_bytes(data, get_machine_key())
        encrypted_b64 = base64.b64encode(encrypted_data)
        with open(path, 'wb') as f_out:
            f_out.write(encrypted_b64)
    except Exception as e:
        pass
