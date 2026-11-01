import os
import json
import base64
import socket

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
        import os
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = json.dumps(cfg, indent=4).encode('utf-8')
        encrypted_data = xor_bytes(data, get_machine_key())
        encrypted_b64 = base64.b64encode(encrypted_data)
        with open(path, 'wb') as f_out:
            f_out.write(encrypted_b64)
    except Exception as e:
        pass
