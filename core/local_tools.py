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

import winreg

def get_real_windows_folder(folder_name):
    """Obtém o caminho real das 6 pastas principais do usuário (priorizando configuração customizada e depois Registro do Windows, mesmo se movidas para D: ou E:)."""
    import os
    mapa_cfg = {
        "Desktop": "pathDesktop",
        "Documents": "pathDocuments",
        "Downloads": "pathDownloads",
        "Music": "pathMusic",
        "Pictures": "pathPictures",
        "Videos": "pathVideos"
    }
    # 1. Verifica se o usuário definiu um caminho customizado no config.json
    try:
        from .seguranca import ler_config_seguro, get_appdata_dir
        cfg_p = os.path.join(get_appdata_dir(), "config.json")
        if os.path.exists(cfg_p):
            cfg = ler_config_seguro(cfg_p) or {}
            chave_cfg = mapa_cfg.get(folder_name)
            if chave_cfg and cfg.get(chave_cfg) and os.path.exists(cfg.get(chave_cfg)):
                return cfg.get(chave_cfg)
    except Exception:
        pass

    # 2. Lê do Registro oficial do Windows (Shell Folders)
    mapa_reg = {
        "Desktop": "Desktop",
        "Documents": "Personal",
        "Downloads": "{374DE290-123F-4565-9164-39C4925E467B}",
        "Music": "My Music",
        "Pictures": "My Pictures",
        "Videos": "My Video"
    }
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders") as key:
            reg_val = mapa_reg.get(folder_name)
            if reg_val:
                caminho_reg = winreg.QueryValueEx(key, reg_val)[0]
                if caminho_reg:
                    return caminho_reg
    except Exception:
        pass
    return os.path.join(os.path.expanduser('~'), folder_name)

def obter_todas_pastas_usuario() -> dict:
    """Retorna o dicionário com as 6 pastas seguras (sandboxed) do perfil do usuário."""
    return {
        "Área de Trabalho": get_real_windows_folder("Desktop"),
        "Documentos": get_real_windows_folder("Documents"),
        "Downloads": get_real_windows_folder("Downloads"),
        "Músicas": get_real_windows_folder("Music"),
        "Imagens": get_real_windows_folder("Pictures"),
        "Vídeos": get_real_windows_folder("Videos"),
    }

import os
import platform
import datetime
import unicodedata
import difflib

def _normalizar_nome_busca(texto: str) -> str:
    """Remove acentos, converte para minúsculas e limpa espaços para busca tolerante."""
    if not texto:
        return ""
    nfkd = unicodedata.normalize("NFKD", texto.lower().strip())
    return "".join([c for c in nfkd if not unicodedata.combining(c)])

def resolver_caminho_inteligente(caminho_informado: str) -> str:
    """Resolve automaticamente caminhos parciais, pastas do Windows (Desktop/Documentos/Downloads)
    e descobre a extensão ou nome completo do arquivo mesmo quando o usuário diz apenas parte do nome
    (ex: potifolio -> encontra potifolio-marcos.txt)."""
    caminho_limpo = os.path.expanduser(os.path.expandvars(caminho_informado.strip('"\'')))
    if os.path.exists(caminho_limpo) and os.path.isfile(caminho_limpo):
        return caminho_limpo

    pasta_alvo = os.path.dirname(caminho_limpo)
    nome_alvo = os.path.basename(caminho_limpo)

    pasta_lower = pasta_alvo.lower().replace("/", "\\")
    if not pasta_alvo or not os.path.exists(pasta_alvo):
        if any(k in pasta_lower for k in ["desktop", "area de trabalho", "área de trabalho"]):
            pasta_alvo = get_real_windows_folder("Desktop")
        elif any(k in pasta_lower for k in ["documents", "documentos", "meus documentos"]):
            pasta_alvo = get_real_windows_folder("Documents")
        elif "download" in pasta_lower:
            pasta_alvo = get_real_windows_folder("Downloads")
        elif any(k in pasta_lower for k in ["music", "musica", "música", "musicas", "músicas"]):
            pasta_alvo = get_real_windows_folder("Music")
        elif any(k in pasta_lower for k in ["picture", "imagen", "imagem", "imagens", "fotos", "foto"]):
            pasta_alvo = get_real_windows_folder("Pictures")
        elif any(k in pasta_lower for k in ["video", "vídeo", "videos", "vídeos", "filmes"]):
            pasta_alvo = get_real_windows_folder("Videos")
        elif not pasta_alvo:
            pasta_alvo = get_real_windows_folder("Desktop")

    tentativa_direta = os.path.join(pasta_alvo, nome_alvo)
    if os.path.exists(tentativa_direta) and os.path.isfile(tentativa_direta):
        return tentativa_direta

    if not os.path.exists(pasta_alvo) or not os.path.isdir(pasta_alvo):
        return caminho_limpo

    alvo_sem_ext, ext_pedida = os.path.splitext(nome_alvo)
    alvo_norm = _normalizar_nome_busca(alvo_sem_ext or nome_alvo)
    if not alvo_norm:
        return caminho_limpo

    extensoes_prioritarias = {".txt", ".pdf", ".docx", ".doc", ".md", ".csv", ".json", ".xlsx", ".xls", ".html", ".py", ".log"}
    candidatos = []

    try:
        for item in os.listdir(pasta_alvo):
            caminho_item = os.path.join(pasta_alvo, item)
            if not os.path.isfile(caminho_item):
                continue
            nome_item_sem_ext, ext_item = os.path.splitext(item)
            ext_item_lower = ext_item.lower()
            if ext_item_lower == ".lnk" and ext_pedida.lower() != ".lnk":
                continue

            item_norm = _normalizar_nome_busca(nome_item_sem_ext)
            bonus_ext = 0.08 if ext_item_lower in extensoes_prioritarias else 0.0

            if item_norm == alvo_norm:
                score = 1.0 + bonus_ext
            elif item_norm.startswith(alvo_norm) or alvo_norm.startswith(item_norm):
                score = 0.90 + bonus_ext
            elif alvo_norm in item_norm or item_norm in alvo_norm:
                score = 0.82 + bonus_ext
            else:
                ratio = difflib.SequenceMatcher(None, alvo_norm, item_norm).ratio()
                score = (ratio + bonus_ext) if ratio >= 0.68 else 0.0

            if score > 0:
                candidatos.append((score, caminho_item))

        if candidatos:
            candidatos.sort(key=lambda x: x[0], reverse=True)
            melhor_score = candidatos[0][0]
            # Verifica se há mais de 1 arquivo empatado ou muito próximo (ex: relatorio.pdf e relatorio.docx)
            empatados = [os.path.basename(c[1]) for c in candidatos if (melhor_score - c[0]) <= 0.12 and c[0] >= 0.80]
            if len(empatados) > 1 and not ext_pedida:
                lista_str = ", ".join(empatados[:6])
                return f"AMBIGUO|{pasta_alvo}|{lista_str}"
            return candidatos[0][1]
    except Exception:
        pass

    return caminho_limpo

def ler_arquivo_local(caminho_absoluto: str) -> str:
    """Lê o conteúdo de um arquivo (texto, PDF, DOCX, planilha, código) no computador do usuário.
    Aceita o nome parcial ou sem extensão (ex: D:\\Users\\Nome\\Área de Trabalho\\potifolio),
    pois descobre automaticamente a extensão e o nome completo na pasta.
    
    Args:
        caminho_absoluto: Caminho para o arquivo (mesmo sem extensão ou com nome aproximado).
    """
    try:
        caminho_limpo = resolver_caminho_inteligente(caminho_absoluto)
        if caminho_limpo.startswith("AMBIGUO|"):
            _, pasta_amb, lista_amb = caminho_limpo.split("|", 2)
            return f"Atenção: Foram encontrados múltiplos arquivos parecidos na pasta ({pasta_amb}): {lista_amb}. Pergunte educadamente ao usuário qual deles exatamente ele deseja ler."
        if not os.path.exists(caminho_limpo):
            return f"Erro: Arquivo não encontrado no caminho fornecido: {caminho_limpo}" 
        
        if os.path.isdir(caminho_limpo):
            return f"Erro: O caminho informado é uma pasta/diretório, não um arquivo: {caminho_limpo}"

        extensao = os.path.splitext(caminho_limpo)[1].lower()

        # 1. Suporte a PDF Nativo
        if extensao == ".pdf":
            import pypdf
            leitor = pypdf.PdfReader(caminho_limpo)
            paginas = []
            for num, pag in enumerate(leitor.pages):
                txt = pag.extract_text() or ""
                if txt.strip():
                    paginas.append(f"--- Página {num + 1} ---\n{txt}")
            conteudo = "\n\n".join(paginas)
            if not conteudo.strip():
                return f"Aviso: O arquivo PDF '{os.path.basename(caminho_limpo)}' foi lido, mas parece conter apenas imagens digitalizadas/escaneadas sem texto selecionável."

        # 2. Suporte a DOCX Nativo (Word)
        elif extensao in [".docx", ".doc"]:
            import docx
            doc = docx.Document(caminho_limpo)
            linhas = [p.text for p in doc.paragraphs if p.text.strip()]
            # Também lê tabelas dentro do Word (essencial para demonstrativos e holerites!)
            for tabela in doc.tables:
                for linha in tabela.rows:
                    celulas = [c.text.strip() for c in linha.cells if c.text.strip()]
                    if celulas:
                        linhas.append(" | ".join(celulas))
            conteudo = "\n".join(linhas)

        # 3. Arquivos de Texto / Código / CSV / JSON (com fallback de encoding do Windows)
        else:
            with open(caminho_limpo, 'rb') as f:
                raw_bytes = f.read()
            
            conteudo = None
            for enc in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
                try:
                    conteudo = raw_bytes.decode(enc)
                    break
                except UnicodeDecodeError:
                    continue
            
            if conteudo is None:
                return f"Erro: O arquivo '{os.path.basename(caminho_limpo)}' é um arquivo binário não suportado para leitura direta de texto."

        # Proteção de tamanho para a IA
        limite_caracteres = 40000
        if len(conteudo) > limite_caracteres:
            return conteudo[:limite_caracteres] + f"\n\n... [Conteúdo truncado: arquivo muito extenso. Total lido: {len(conteudo)} caracteres]"

        return conteudo

    except Exception as e:
        return f"Erro ao ler o arquivo {caminho_absoluto}: {str(e)}"

def listar_diretorio(caminho_diretorio: str) -> str:
    """Lista todos os arquivos e pastas dentro de um diretório no computador do usuário.
    Use para descobrir nomes de arquivos quando o usuário pedir para analisar uma pasta.
    
    Args:
        caminho_diretorio: Caminho absoluto para a pasta (ex: C:\\Users\\Nome\\Documentos).
    """
    try:
        caminho = os.path.expanduser(os.path.expandvars(caminho_diretorio))
        if not os.path.exists(caminho):
            return f"Erro: Diretório não encontrado no caminho {caminho}"
        if not os.path.isdir(caminho):
            return f"Erro: O caminho especificado ({caminho}) não é uma pasta."
            
        arquivos = os.listdir(caminho)
        if not arquivos:
            return "O diretório está vazio."
            
        return f"Conteúdo de {caminho}:\n- " + "\n- ".join(arquivos)
    except Exception as e:
        return f"Erro ao listar o diretório: {str(e)}"

def obter_informacoes_sistema() -> str:
    """Retorna diagnosticos e informacoes de hardware e sistema operacional da maquina onde o assistente roda."""
    try:
        import psutil
        ram = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=0.5)
        ram_total = f"{ram.total / (1024**3):.2f} GB"
        ram_livre = f"{ram.available / (1024**3):.2f} GB"
        hw_info = f"CPU Uso: {cpu}% | RAM Total: {ram_total} | RAM Livre: {ram_livre}"
    except ImportError:
        hw_info = "Informacao de hardware indisponivel (psutil nao instalado)."
        
    agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"Sistema Operacional: {platform.system()} {platform.release()} ({platform.machine()})\nHora atual do PC: {agora}\nHardware: {hw_info}"

def executar_comando(comando: str) -> str:
    """Executa um comando no terminal do Windows (PowerShell/CMD) e retorna a saida.
    CUIDADO: Use apenas para comandos seguros como abrir programas, consultar configuracoes de rede ou sistema.
    
    Args:
        comando: O comando exato a ser executado (ex: 'ping google.com', 'start chrome', 'ipconfig').
    """
    import subprocess
    import json
    from .seguranca import ler_config_seguro
    
    # Checa a trava de segurança
    try:
        config_path = os.path.join(get_appdata_dir(), 'config.json')
        cfg = ler_config_seguro(config_path)
        if cfg.get("agent_mode", True) == False:
                    return "ERRO DE PERMISSÃO: O Modo Agente Jarvis está DESLIGADO nas configurações. Você não tem permissão para executar comandos neste momento."
    except: pass
    
    try:
        resultado = subprocess.run(comando, shell=True, capture_output=True, text=True, timeout=15)
        if resultado.returncode == 0:
            return f"Sucesso:\n{resultado.stdout}"
        else:
            return f"Erro na execução:\n{resultado.stderr}"
    except Exception as e:
        return f"Falha ao executar o comando: {str(e)}"


def pesquisar_na_web(termo_de_busca: str) -> str:
    """Pesquisa informações na internet usando o buscador DuckDuckGo e retorna os principais resultados.
    Use sempre que precisar de informações recentes, notícias, previsão do tempo, ou fatos que você não sabe de cor.
    
    Args:
        termo_de_busca: A frase ou palavra-chave para buscar na web (ex: 'notícias do brasil de hoje', 'preço do dolar').
    """
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            resultados = list(ddgs.text(termo_de_busca, max_results=5))
            
        if not resultados:
            return "Nenhum resultado encontrado para esta busca."
            
        texto_resultado = f"Resultados da web para '{termo_de_busca}':\n\n"
        for i, res in enumerate(resultados, 1):
            texto_resultado += f"{i}. {res.get('title')}\nLink: {res.get('href')}\nResumo: {res.get('body')}\n\n"
            
        return texto_resultado
    except Exception as e:
        return f"Erro ao pesquisar na web: {str(e)}"


def ler_pagina_web(url: str) -> str:
    """Lê o conteúdo de uma página web específica (URL) e extrai todo o texto limpo dela.
    Use quando o usuário pedir para você resumir um link, ler uma documentação online ou extrair dados de uma página específica.
    
    Args:
        url: O link completo da página (ex: 'https://pt.wikipedia.org/wiki/Python').
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove scripts e estilos
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.extract()
            
        texto = soup.get_text(separator='\n', strip=True)
        
        # Limita para não estourar tokens se for uma página monstruosa
        if len(texto) > 40000:
            texto = texto[:40000] + "\n... [Conteúdo truncado]"
            
        return f"Conteúdo extraído de {url}:\n\n{texto}"
    except Exception as e:
        return f"Erro ao acessar a página {url}: {str(e)}"


def criar_planilha_excel(nome_arquivo: str, dados_json: str) -> str:
    """Gera e salva um arquivo de planilha do Excel (.xlsx).
    
    Args:
        nome_arquivo: O nome do arquivo (ex: 'Relatorio').
        dados_json: Uma string JSON contendo uma lista de dicionários.
    """
    import os
    import json
    from .seguranca import ler_config_seguro
    
    try:
        import pandas as pd
        
        try:
            dados = json.loads(dados_json)
        except json.JSONDecodeError:
            return "Erro: 'dados_json' não é um formato JSON válido."
            
        if not isinstance(dados, list) or len(dados) == 0:
            return "Erro: Os dados precisam ser uma lista contendo ao menos um item."
            
        df = pd.DataFrame(dados)
        
        # Garante que seja apenas o nome do arquivo, ignorando caminhos absolutos tentados pela IA
        nome_limpo = os.path.basename(nome_arquivo.replace('\\', '/'))
        if not nome_limpo.lower().endswith('.xlsx'):
            nome_limpo += '.xlsx'
            
                # Tenta na ordem: Área de Trabalho (Real) -> Documentos (Real) -> Pasta atual do projeto
        pastas_tentativa = [
            get_real_windows_folder('Desktop'),
            get_real_windows_folder('Documents'),
            os.getcwd()
        ]
        
        caminho_salvo = None
        erro_ultimo = ""
        
        for pasta in pastas_tentativa:
            if os.path.exists(pasta):
                caminho_completo = os.path.join(pasta, nome_limpo)
                try:
                    df.to_excel(caminho_completo, index=False)
                    caminho_salvo = caminho_completo
                    break
                except Exception as e:
                    erro_ultimo = str(e)
                    continue
                    
        if caminho_salvo:
            return f"Planilha criada com sucesso! O arquivo foi salvo em: {caminho_salvo}"
        else:
            return f"Erro de Permissão: Não foi possível salvar em nenhum dos diretórios padrão do usuário. (Último erro: {erro_ultimo})"
            
    except ImportError:
        return "Erro: As bibliotecas 'pandas' ou 'openpyxl' não estão instaladas."
    except Exception as e:
        return f"Erro ao criar a planilha: {str(e)}"


def controlar_mouse_teclado(acao: str, parametro: str = "") -> str:
    """Simula interações físicas do usuário com o mouse e teclado usando RPA (Automação de Processos Robóticos).
    Use isso para automatizar tarefas repetitivas, fechar janelas, digitar textos sozinho ou controlar a interface.
    
    Args:
        acao: O tipo de ação. Pode ser: 'digitar', 'pressionar_tecla', 'clicar', 'mover_mouse', 'scroll'.
        parametro: O valor da ação.
                   Se acao='digitar', o texto a digitar.
                   Se acao='pressionar_tecla', o nome da tecla (ex: 'enter', 'win', 'esc', 'ctrl', 'alt', 'tab').
                   Se acao='clicar' ou 'mover_mouse', passe as coordenadas 'X,Y' (ex: '500,300') ou deixe vazio para clicar onde o mouse está.
                   Se acao='scroll', passe a quantidade (ex: '-500' para baixo, '500' para cima).
    """
    try:
        import pyautogui
        pyautogui.FAILSAFE = True
        
        if acao == 'digitar':
            pyautogui.write(parametro, interval=0.02)
            return f"Texto '{parametro}' digitado com sucesso."
            
        elif acao == 'pressionar_tecla':
            pyautogui.press(parametro)
            return f"Tecla '{parametro}' pressionada com sucesso."
            
        elif acao in ['clicar', 'mover_mouse']:
            if parametro:
                try:
                    x, y = map(int, parametro.split(','))
                    if acao == 'mover_mouse':
                        pyautogui.moveTo(x, y, duration=2.0)
                        return f"Mouse movido para {x}, {y}."
                    else:
                        pyautogui.click(x, y)
                        return f"Clique realizado em {x}, {y}."
                except ValueError:
                    return "Erro: Coordenadas inválidas. Use o formato 'X,Y' (ex: '100,200')."
            else:
                if acao == 'clicar':
                    pyautogui.click()
                    return "Clique realizado na posição atual do mouse."
                
        elif acao == 'scroll':
            try:
                qtd = int(parametro)
                pyautogui.scroll(qtd)
                return f"Scroll de {qtd} realizado."
            except ValueError:
                return "Erro: Parâmetro de scroll deve ser um número inteiro."
                
        return f"Ação '{acao}' não reconhecida."
        
    except ImportError:
        return "Erro: Biblioteca 'pyautogui' não está instalada no ambiente."
    except Exception as e:
        return f"Erro ao executar automação RPA: {str(e)}"


def editar_arquivo_codigo(caminho_absoluto: str, conteudo_completo: str) -> str:
    """Cria ou sobrescreve um arquivo no computador do usuário com o conteúdo fornecido.
    Use isso para escrever códigos, scripts, gerar textos ou salvar configurações a pedido do usuário.
    ATENÇÃO: Você DEVE fornecer o conteúdo completo do arquivo, pois esta ferramenta sobrescreve tudo.
    
    Args:
        caminho_absoluto: O caminho absoluto do arquivo a ser criado ou editado (ex: 'C:\\Users\\Nome\\script.py' ou './novo_arquivo.html').
        conteudo_completo: O código ou texto completo que será salvo no arquivo.
    """
    import os
    
    try:
        caminho = os.path.expanduser(os.path.expandvars(caminho_absoluto))
        
        caminho_lower = caminho.lower().replace('/', '\\')
        if caminho_lower.startswith("c:\\users\\") and not os.path.exists(os.path.dirname(caminho)):
            if "desktop" in caminho_lower or "área de trabalho" in caminho_lower:
                caminho = os.path.join(get_real_windows_folder('Desktop'), os.path.basename(caminho))
            elif "downloads" in caminho_lower:
                caminho = os.path.join(get_real_windows_folder('Downloads'), os.path.basename(caminho))
            elif "documents" in caminho_lower or "documentos" in caminho_lower:
                caminho = os.path.join(get_real_windows_folder('Documents'), os.path.basename(caminho))
            else:
                caminho = os.path.join(get_real_windows_folder('Desktop'), os.path.basename(caminho))
        elif len(caminho) <= 4 or "d:\\" in caminho_lower and len(caminho.split("\\")) <= 2:
            caminho = os.path.join(get_real_windows_folder('Desktop'), os.path.basename(caminho))
            
        diretorio = os.path.dirname(caminho)
        if diretorio and not os.path.exists(diretorio):
            os.makedirs(diretorio, exist_ok=True)
            
        try:
            with open(caminho, 'w', encoding='utf-8') as f:
                f.write(conteudo_completo)
        except PermissionError:
            caminho = os.path.join(get_real_windows_folder('Desktop'), os.path.basename(caminho))
            with open(caminho, 'w', encoding='utf-8') as f:
                f.write(conteudo_completo)
            
        return f"Sucesso: Arquivo salvo/atualizado em {caminho}"
    except Exception as e:
        return f"Erro ao salvar arquivo em {caminho_absoluto}: {str(e)}"


def analisar_tela(instrucao: str = "Descreva detalhadamente o que você está vendo na tela") -> str:
    """Tira uma captura (print) invisível da tela do usuário e usa Visão Computacional para analisar a imagem.
    Use sempre que precisar 'ver' um erro que o usuário mencionou, ler um gráfico, ou entender a interface aberta.
    
    Args:
        instrucao: O que você quer que o módulo de visão procure, leia ou descreva na imagem. Ex: 'Leia o texto do erro'.
    """
    import os
    import json
    from .seguranca import ler_config_seguro
    
    try:
        from PIL import ImageGrab
        
        # 1. Tira print da tela inteira
        tela = ImageGrab.grab()
        
        # 2. Busca chave da Groq (Visão Qwen 3.8) ou Gemini nas configurações do app
        config_path = os.path.join(get_appdata_dir(), 'config.json')
        cfg = ler_config_seguro(config_path) or {}
        chaves = cfg.get("api_keys", {})
        groq_key = chaves.get("groq", "") or (cfg.get("api_key", "") if cfg.get("provider") == "groq" else "")
        gemini_key = chaves.get("gemini", "") or (cfg.get("api_key", "") if cfg.get("provider") == "gemini" else "")

        if groq_key:
            import io, base64
            from openai import OpenAI
            tela_rgb = tela.convert("RGB")
            tela_rgb.thumbnail((1280, 720))
            buf = io.BytesIO()
            tela_rgb.save(buf, format="JPEG", quality=80)
            b64_img = base64.b64encode(buf.getvalue()).decode("utf-8")
            client = OpenAI(api_key=groq_key, base_url="https://api.groq.com/openai/v1")
            resp = client.chat.completions.create(
                model="qwen/qwen3.8-27b",
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": instrucao + ". Descreva detalhadamente em português o que você vê na tela para auxiliar um usuário com deficiência visual."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
                ]}],
                max_tokens=1024
            )
            return f"Resultado da análise visual da tela:\n{resp.choices[0].message.content}"

        if not gemini_key:
            return "Erro: Nenhuma chave de API com suporte a Visão (Groq ou Gemini) configurada nas preferências."
            
        from google import genai
        import httpx
        http_client = httpx.Client(verify=False)
        client = genai.Client(api_key=gemini_key, http_options={'client': http_client})
        
        resposta = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[instrucao + '. DESCREVA DETALHADAMENTE O QUE VOCÊ VÊ PARA O USUÁRIO.', tela]
        )
        
        return f"Resultado da análise visual da tela:\n{resposta.text}"
        
    except ImportError:
        return "Erro: Bibliotecas 'Pillow' ou 'google-genai' faltando."
    except Exception as e:
        return f"Erro ao analisar tela: {str(e)}"


def consultar_banco_sqlite(caminho_db: str, query_sql: str) -> str:
    """Conecta a um banco de dados SQLite (.db ou .sqlite) local, executa uma consulta SQL (SELECT) e retorna os resultados.
    Use esta ferramenta para responder perguntas do usuário sobre dados estruturados, relatórios ou usuários.
    CUIDADO: É permitido apenas consultas de leitura (SELECT). Comandos como INSERT, UPDATE, DELETE ou DROP serão bloqueados por segurança.
    
    Args:
        caminho_db: O caminho absoluto para o arquivo do banco de dados SQLite (ex: 'C:\\dados\\sistema.db').
        query_sql: A instrução SQL de leitura a ser executada (ex: 'SELECT * FROM usuarios LIMIT 10').
    """
    import sqlite3
    import os
    
    try:
        caminho_db = os.path.expanduser(os.path.expandvars(caminho_db))
        if not os.path.exists(caminho_db):
            return f"Erro: O arquivo de banco de dados não foi encontrado em '{caminho_db}'"
            
        # Filtro de segurança super rigoroso (Apenas Leitura)
        query_upper = query_sql.upper().strip()
        palavras_proibidas = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE', 'REPLACE', 'TRUNCATE', 'EXEC', 'PRAGMA']
        
        # Verifica se alguma palavra proibida está no início da query ou sendo usada
        for palavra in palavras_proibidas:
            if palavra in query_upper:
                return f"Erro de Segurança: A execução de '{palavra}' não é permitida. Esta ferramenta suporta apenas instruções SELECT (Leitura)."
                
        if not query_upper.startswith('SELECT'):
            return "Erro de Segurança: A query deve começar com SELECT."
            
        # Conecta e executa
        conn = sqlite3.connect(caminho_db)
        cursor = conn.cursor()
        
        cursor.execute(query_sql)
        colunas = [descricao[0] for descricao in cursor.description]
        linhas = cursor.fetchall()
        
        conn.close()
        
        # Formata o resultado
        if not linhas:
            return "A consulta foi executada com sucesso, mas retornou 0 resultados."
            
        resultado_str = f"Colunas: {', '.join(colunas)}\nResultados:\n"
        for i, linha in enumerate(linhas):
            if i >= 50: # Limita a 50 linhas para não estourar os tokens da IA
                resultado_str += "... (truncado, mais resultados omitidos para economizar memória)\n"
                break
            resultado_str += f"- {linha}\n"
            
        return resultado_str
        
    except sqlite3.Error as e:
        return f"Erro de SQL ao executar a query: {str(e)}"
    except Exception as e:
        return f"Erro genérico ao acessar o banco: {str(e)}"


def memorizar_conhecimento(assunto: str, detalhes: str) -> str:
    """Salva uma informação, preferência do usuário ou conhecimento importante na Memória de Longo Prazo (Disco Rígido).
    Diferente do histórico normal que se perde ao iniciar uma nova conversa, informações salvas aqui duram para sempre e cruzam todas as sessões futuras.
    Use isso proativamente quando o usuário compartilhar algo sobre ele mesmo, sobre as regras do projeto, ou soluções de bugs difíceis.
    
    Args:
        assunto: O tópico ou categoria da memória (ex: 'Preferência de Código', 'Configuração de Servidor', 'Perfil do Usuário').
        detalhes: O conhecimento detalhado a ser salvo para uso futuro.
    """
    import os
    import json
    from .seguranca import ler_config_seguro
    from datetime import datetime
    
    try:
        caminho_memoria = os.path.join(get_appdata_dir(), 'memoria_longo_prazo.json')
        
        memorias = []
        if os.path.exists(caminho_memoria):
            with open(caminho_memoria, 'r', encoding='utf-8') as f:
                memorias = json.load(f)
                
        nova_memoria = {
            "data": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "assunto": assunto,
            "detalhes": detalhes
        }
        
        memorias.append(nova_memoria)
        
        with open(caminho_memoria, 'w', encoding='utf-8') as f:
            json.dump(memorias, f, indent=4, ensure_ascii=False)
            
        return f"Memória gravada com sucesso! Agora eu nunca mais vou me esquecer de: {assunto}"
    except Exception as e:
        return f"Erro ao gravar memória: {str(e)}"

def pesquisar_memoria_permanente(termo_busca: str) -> str:
    """Pesquisa a Memória de Longo Prazo do sistema em busca de conhecimentos, regras ou fatos salvos em sessões anteriores.
    Use isso se o usuário perguntar 'Você lembra de X?' ou se você suspeitar que uma configuração antiga pode resolver um problema atual.
    
    Args:
        termo_busca: A palavra-chave ou conceito a ser pesquisado nas memórias salvas.
    """
    import os
    import json
    from .seguranca import ler_config_seguro
    
    try:
        caminho_memoria = os.path.join(get_appdata_dir(), 'memoria_longo_prazo.json')
        
        if not os.path.exists(caminho_memoria):
            return "Nenhuma memória de longo prazo foi gravada ainda."
            
        with open(caminho_memoria, 'r', encoding='utf-8') as f:
            memorias = json.load(f)
            
        resultados = []
        termo_busca = termo_busca.lower()
        
        for m in memorias:
            if termo_busca in m.get('assunto', '').lower() or termo_busca in m.get('detalhes', '').lower():
                resultados.append(f"[{m.get('data')}] {m.get('assunto')}: {m.get('detalhes')}")
                
        if not resultados:
            return f"Nenhuma memória encontrada sobre '{termo_busca}'."
            
        return "Memórias Recuperadas:\n" + "\n".join(resultados)
    except Exception as e:
        return f"Erro ao buscar memória: {str(e)}"


def controlar_navegador_fantasma(url: str, script_js: str = "") -> str:
    """Abre um navegador invisível (Selenium WebDriver), navega até uma URL e, opcionalmente, executa comandos JavaScript na página para clicar, preencher formulários ou extrair dados.
    Use quando o 'ler_pagina_web' normal falhar por causa de sites que exigem clique, login ou carregamento dinâmico.
    
    Args:
        url: A URL completa para acessar (ex: 'https://google.com').
        script_js: Opcional. Código JavaScript a ser executado na página APÓS ela carregar. Você DEVE usar 'return' no JS se quiser capturar dados de volta. Exemplo: "document.querySelector('button').click(); return document.body.innerText;"
    """
    import time
    
    try:
        from selenium import webdriver
        from selenium.webdriver.edge.service import Service
        from selenium.webdriver.edge.options import Options
        from webdriver_manager.microsoft import EdgeChromiumDriverManager
        
        # Configura o navegador fantasma (invisível/headless)
        edge_options = Options()
        edge_options.add_argument("--headless")
        edge_options.add_argument("--disable-gpu")
        edge_options.add_argument("--window-size=1920,1080")
        edge_options.add_argument("--no-sandbox")
        edge_options.add_argument("--disable-dev-shm-usage")
        
        # Inicializa o Selenium com Edge (nativo do Windows)
        service = Service(EdgeChromiumDriverManager().install())
        driver = webdriver.Edge(service=service, options=edge_options)
        
        # Configura timeout
        driver.set_page_load_timeout(30)
        
        try:
            # Acessa a URL
            driver.get(url)
            time.sleep(2) # Aguarda o render inicial dinâmico
            
            resultado = f"Página '{url}' acessada com sucesso."
            
            # Se a IA enviou um script JS para rodar na página
            if script_js:
                resultado_js = driver.execute_script(script_js)
                if resultado_js:
                    resultado += f"\\n\\nResultado do Script JS:\\n{str(resultado_js)}"
                else:
                    resultado += "\n\nScript JS executado (sem retorno de dados)."
            else:
                # Se não mandou JS, apenas retorna o texto da página por padrão
                texto_pagina = driver.execute_script("return document.body.innerText;")
                resultado += f"\n\nConteúdo da página (truncado):\n{str(texto_pagina)[:2000]}..."
                
            return resultado
            
        finally:
            driver.quit() # Garante que o navegador fantasma será fechado
            
    except ImportError:
        return "Erro: Biblioteca 'selenium' ou 'webdriver-manager' não instalada."
    except Exception as e:
        return f"Erro no Navegador Fantasma: {str(e)}"


def notificar_usuario(titulo: str, mensagem: str) -> str:
    """Envia uma Notificação de Sistema (Toast Pop-up) diretamente na tela do Windows do usuário.
    Use isso para avisar o usuário sobre algo importante quando você estiver rodando em segundo plano ou quando quiser chamar a atenção dele fora do chat.
    
    Args:
        titulo: O título da notificação (ex: 'Alerta de Servidor' ou 'Lembrete').
        mensagem: O corpo da notificação.
    """
    try:
        from win11toast import toast
        toast(titulo, mensagem, app_id="Cromak Bridge")
        return f"Notificação '{titulo}' enviada com sucesso para a tela do usuário."
    except ImportError:
        return "Erro: Biblioteca 'win11toast' não instalada."
    except Exception as e:
        return f"Erro ao enviar notificação: {str(e)}"

def agendar_lembrete(minutos: float, mensagem_notificacao: str, titulo: str = "Lembrete do Jarvis") -> str:
    """Agenda uma notificação para o futuro. A IA cria uma tarefa em segundo plano que vai esperar a quantidade de minutos especificada e, em seguida, pular um Pop-up na tela do Windows do usuário.
    Use isso quando o usuário disser 'Me lembre de X em Y minutos'.
    
    Args:
        minutos: Tempo de espera em minutos (pode ser decimal, ex: 0.5 para 30 segundos).
        mensagem_notificacao: A mensagem que aparecerá no pop-up após o tempo acabar.
        titulo: O título do pop-up.
    """
    import threading
    import time
    
    def tarefa_background():
        time.sleep(minutos * 60)
        try:
            from win11toast import toast
            toast(titulo, mensagem_notificacao, app_id="Cromak Bridge", audio={"src": "ms-winsoundevent:Notification.Reminder"})
        except:
            pass
            
    try:
        # Inicia a thread em segundo plano sem bloquear a IA
        t = threading.Thread(target=tarefa_background, daemon=True)
        t.start()
        return f"Sucesso! Lembrete agendado. Uma notificação vai aparecer na tela do usuário em {minutos} minuto(s)."
    except Exception as e:
        return f"Erro ao agendar: {str(e)}"


def analisar_midia(caminho_arquivo: str, instrucao: str = "Descreva os detalhes importantes deste arquivo de mídia") -> str:
    """Analisa o conteúdo de arquivos de áudio (MP3, WAV, etc) ou vídeo (MP4, MOV, etc) locais e responde perguntas sobre eles.
    A IA atua como um assistente que 'assiste' ao vídeo ou 'escuta' o áudio, podendo extrair atas de reunião, descrever cenas, ou localizar momentos específicos.
    
    Args:
        caminho_arquivo: Caminho absoluto para o arquivo de áudio ou vídeo (ex: 'C:\\Videos\\reuniao.mp4').
        instrucao: O que você quer extrair ou analisar no arquivo.
    """
    import os
    import json
    from .seguranca import ler_config_seguro
    import time
    
    try:
        caminho_arquivo = os.path.expanduser(os.path.expandvars(caminho_arquivo))
        if not os.path.exists(caminho_arquivo):
            return f"Erro: Arquivo '{caminho_arquivo}' não encontrado."
            
        config_path = os.path.join(get_appdata_dir(), 'config.json')
        api_key = None
        cfg = ler_config_seguro(config_path)
        api_key = cfg.get("api_keys", {}).get("gemini", "")
                
        if not api_key:
            return "Erro: Chave de API do Gemini não configurada nas preferências. O motor multimodal requer Gemini."
            
        from google import genai
        from google.genai import types
        import httpx
        http_client = httpx.Client(verify=False)
        client = genai.Client(api_key=api_key, http_options={'client': http_client})
        
        # Faz o upload do arquivo para a API do Gemini
        arquivo_gemini = client.files.upload(file=caminho_arquivo)
        
        # Vídeos costumam precisar de um tempo de processamento no servidor do Google
        tentativas = 0
        while arquivo_gemini.state.name == 'PROCESSING' and tentativas < 60:
            time.sleep(2)
            arquivo_gemini = client.files.get(name=arquivo_gemini.name)
            tentativas += 1
            
        if arquivo_gemini.state.name == 'FAILED':
            return "Erro: O servidor do Gemini falhou ao processar a mídia."
            
        # Analisa o arquivo
        resposta = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[instrucao + '. DESCREVA DETALHADAMENTE O QUE VOCÊ VÊ PARA O USUÁRIO.', arquivo_gemini]
        )
        
        # Limpa o arquivo dos servidores do Google por segurança e privacidade
        try:
            client.files.delete(name=arquivo_gemini.name)
        except:
            pass
            
        return f"Resultado da Análise Multimodal:\n{resposta.text}"
        
    except Exception as e:
        return f"Erro ao analisar mídia: {str(e)}"


def fazer_requisicao_api(url: str, metodo: str = "GET", headers_json: str = None, body_json: str = None) -> str:
    """Realiza uma requisição HTTP/REST (GET, POST, PUT, DELETE) para qualquer API ou sistema externo.
    Use esta ferramenta para se comunicar com outras plataformas (como Trello, Discord, GitHub, APIs internas do usuário, etc).
    
    Args:
        url: O endpoint completo da API (ex: 'https://api.github.com/users/octocat').
        metodo: O método HTTP (GET, POST, PUT, DELETE). O padrão é GET.
        headers_json: Opcional. Um dicionário JSON em formato de string com os Headers (ex: '{"Authorization": "Bearer TOKEN"}').
        body_json: Opcional. Um dicionário JSON em formato de string com o corpo da requisição POST/PUT.
    """
    import requests
    import json
    from .seguranca import ler_config_seguro
    
    try:
        metodo = metodo.upper()
        
        headers = {}
        if headers_json:
            try:
                headers = json.loads(headers_json)
            except:
                pass
                
        body = None
        if body_json:
            try:
                body = json.loads(body_json)
            except:
                # Se não for JSON, envia como raw string
                body = body_json
                
        # Faz a requisição
        if metodo == "GET":
            response = requests.get(url, headers=headers, timeout=15)
        elif metodo == "POST":
            response = requests.post(url, headers=headers, json=body if isinstance(body, dict) else None, data=body if not isinstance(body, dict) else None, timeout=15)
        elif metodo == "PUT":
            response = requests.put(url, headers=headers, json=body if isinstance(body, dict) else None, data=body if not isinstance(body, dict) else None, timeout=15)
        elif metodo == "DELETE":
            response = requests.delete(url, headers=headers, timeout=15)
        else:
            return f"Erro: Método HTTP '{metodo}' não suportado."
            
        try:
            # Tenta retornar como JSON formatado se a resposta for JSON
            res_data = response.json()
            return f"Status Code: {response.status_code}\nResponse:\n{json.dumps(res_data, indent=2, ensure_ascii=False)}"
        except:
            # Retorna texto puro truncado para não explodir tokens se for um HTML gigante
            return f"Status Code: {response.status_code}\nResponse:\n{response.text[:2000]}"
            
    except Exception as e:
        return f"Erro ao realizar requisição API: {str(e)}"


def enviar_email(destinatario: str, assunto: str, corpo: str) -> str:
    """Envia um e-mail para o destinatario usando as credenciais do usuario."""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    import os
    from .seguranca import ler_config_seguro

    config_path = os.path.join(get_appdata_dir(), 'config.json')
    try:
        cfg = ler_config_seguro(config_path)
        cred = cfg.get("email_credentials", {})
        if not cred or not cred.get("email") or not cred.get("app_password"):
            # Fallback inteligente: como não há SMTP configurado, abre diretamente no cliente do Windows
            import urllib.parse
            import webbrowser
            dest_enc = destinatario.strip()
            assunto_enc = urllib.parse.quote(assunto)
            corpo_enc = urllib.parse.quote(corpo)
            mailto_url = f"mailto:{dest_enc}?subject={assunto_enc}&body={corpo_enc}"
            webbrowser.open(mailto_url)
            return (
                f"ℹ️ As credenciais de envio direto em segundo plano (SMTP) ainda não foram configuradas no aplicativo. "
                f"Porém, para sua comodidade, abri o seu cliente de e-mail padrão do Windows (ou navegador) com o destinatário '{destinatario}', "
                f"assunto '{assunto}' e corpo já preenchidos! Você só precisa clicar em Enviar. "
                f"Dica: Caso queira que eu envie 100% sozinho no futuro sem abrir janelas, configure seu e-mail e senha de app nas Configurações."
            )
        
        remetente = cred["email"]
        senha = cred["app_password"]

        msg = MIMEMultipart()
        msg['From'] = remetente
        msg['To'] = destinatario
        msg['Subject'] = assunto
        msg.attach(MIMEText(corpo, 'plain', 'utf-8'))

        # Detecta o servidor SMTP baseado no domínio do e-mail
        if '@hotmail.' in remetente or '@outlook.' in remetente or '@live.' in remetente:
            smtp_host = 'smtp-mail.outlook.com'
        elif '@yahoo.' in remetente:
            smtp_host = 'smtp.mail.yahoo.com'
        else:
            smtp_host = 'smtp.gmail.com'

        server = smtplib.SMTP(smtp_host, 587)
        server.starttls()
        server.login(remetente, senha)
        server.send_message(msg)
        server.quit()
        return f"E-mail enviado com sucesso para {destinatario}."
    except Exception as e:
        return f"Erro ao enviar email: {str(e)}"

def ler_emails(quantidade: int = 5, apenas_nao_lidos: bool = True) -> str:
    """Le a caixa de entrada do usuario para buscar novos e-mails."""
    import imaplib
    import email
    from email.header import decode_header
    import os
    from .seguranca import ler_config_seguro

    config_path = os.path.join(get_appdata_dir(), 'config.json')
    try:
        cfg = ler_config_seguro(config_path)
        cred = cfg.get("email_credentials", {})
        if not cred or not cred.get("email") or not cred.get("app_password"):
            return 'Erro de credencial. Peca ao usuario para editar config.json'
        
        usuario = cred["email"]
        senha = cred["app_password"]

        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(usuario, senha)
        mail.select("inbox")

        status, messages = mail.search(None, 'UNSEEN' if apenas_nao_lidos else 'ALL')
        email_ids = messages[0].split()
        if not email_ids:
            return "Nenhum e-mail encontrado."
            
        email_ids = email_ids[-quantidade:]
        resultado = []
        
        for eid in email_ids:
            res, msg_data = mail.fetch(eid, '(RFC822)')
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        try:
                            subject = subject.decode(encoding if encoding else 'utf-8', errors='ignore')
                        except:
                            subject = str(subject)
                    
                    de = msg.get("From")
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                try:
                                    body = part.get_payload(decode=True).decode(errors='ignore')
                                except: pass
                                break
                    else:
                        try:
                            body = msg.get_payload(decode=True).decode(errors='ignore')
                        except: pass
                    
                    resultado.append(f"De: {de}\nAssunto: {subject}\nConteudo: {body[:1000]}\n---")
                    
        mail.close()
        mail.logout()
        return "\n".join(resultado)
    except Exception as e:
        return f"Erro ao ler e-mails: {str(e)}"


def criar_pdf(nome_arquivo: str, conteudo_markdown: str = "", conteudo_html: str = "") -> str:
    """Cria um arquivo PDF rico.
    """
    try:
        import markdown
        import xhtml2pdf.pisa as pisa
        import os
        
        if conteudo_markdown:
            conteudo = markdown.markdown(conteudo_markdown)
        else:
            conteudo = conteudo_html

        if not nome_arquivo.lower().endswith('.pdf'):
            nome_arquivo += '.pdf'
            
        from .local_tools import get_real_windows_folder
        if not os.path.isabs(nome_arquivo) or not os.path.exists(os.path.dirname(nome_arquivo)):
            nome_arquivo = os.path.join(get_real_windows_folder('Desktop'), os.path.basename(nome_arquivo))
            
        html_template = f"""
        <html>
        <head>
            <style>
                @page {{ size: a4 portrait; margin: 2cm; }}
                body {{ font-family: Helvetica, Arial, sans-serif; font-size: 12pt; color: #333; }}
                h1 {{ color: #1a365d; text-align: center; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }}
                h2 {{ color: #2b6cb0; margin-top: 20px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
                th, td {{ border: 1px solid #cbd5e0; padding: 8px; text-align: left; }}
                th {{ background-color: #f3f4f6; }}
            </style>
        </head>
        <body>
            {conteudo}
        </body>
        </html>
        """
        
        with open(nome_arquivo, "w+b") as result_file:
            pisa_status = pisa.CreatePDF(
                html_template,
                dest=result_file,
                encoding='utf-8'
            )
            
        if pisa_status.err:
            return f"Aviso parcial ao gerar PDF: {pisa_status.err}. Mas o arquivo foi criado."
            
        try:
            os.startfile(os.path.abspath(nome_arquivo))
        except: pass
            
        return f"Sucesso! Arquivo PDF criado, salvo e aberto em: {nome_arquivo}"
    except Exception as e:
        return f"Erro ao criar arquivo PDF: {str(e)}"

def gerenciar_janelas(acao: str, nome_janela: str = "") -> str:
    """Gerencia as janelas do sistema operacional Windows (maximizar, minimizar, fechar, focar).
    
    Args:
        acao: O que fazer com a janela. Opcoes: 'minimizar_tudo', 'maximizar', 'minimizar', 'fechar', 'focar'.
        nome_janela: Parte do titulo da janela (ex: 'Chrome', 'Bloco de Notas'). Vazio se a acao for 'minimizar_tudo'.
    """
    try:
        import pygetwindow as gw
        
        if acao == 'minimizar_tudo':
            import ctypes
            ctypes.windll.user32.keybd_event(0x5B, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0x44, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0x44, 0, 2, 0)
            ctypes.windll.user32.keybd_event(0x5B, 0, 2, 0)
            return "Todas as janelas foram minimizadas (Area de Trabalho exibida)."
            
        janelas = gw.getWindowsWithTitle(nome_janela)
        if not janelas:
            return f"Nenhuma janela encontrada com o titulo parcial '{nome_janela}'."
            
        alvo = janelas[0]
        
        if acao == 'maximizar':
            if not alvo.isMaximized:
                alvo.maximize()
            return f"Janela '{alvo.title}' maximizada."
        elif acao == 'minimizar':
            if not alvo.isMinimized:
                alvo.minimize()
            return f"Janela '{alvo.title}' minimizada."
        elif acao == 'fechar':
            alvo.close()
            return f"Janela '{alvo.title}' fechada."
        elif acao == 'focar':
            try: alvo.activate()
            except: pass
            return f"Tentativa de colocar a janela '{alvo.title}' em foco."
        else:
            return f"Acao desconhecida: {acao}"
    except Exception as e:
        return f"Erro ao gerenciar janelas: {str(e)}"



def capturar_webcam(camera_index: int = 0) -> str:
    """Tira uma foto através da webcam do usuário para analisar rostos, objetos, ou o ambiente ao redor."""
    try:
        import cv2
        import os
        from datetime import datetime
        
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            return "Erro: Não foi possível acessar a webcam."
            
        for _ in range(10): cap.read()
        ret, frame = cap.read()
        cap.release()
        
        if not ret: return "Erro: O hardware ligou mas a tela ficou preta."
            
        pasta_dest = os.path.join(os.getcwd(), 'banco_de_dados', 'imagens_tela')
        os.makedirs(pasta_dest, exist_ok=True)
        
        caminho_completo = os.path.join(pasta_dest, f"webcam_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
        cv2.imwrite(caminho_completo, frame)
        
        from .seguranca import ler_config_seguro
        
        config_path = os.path.join(get_appdata_dir(), 'config.json')
        cfg = ler_config_seguro(config_path) or {}
        chaves = cfg.get("api_keys", {})
        groq_key = chaves.get("groq", "") or (cfg.get("api_key", "") if cfg.get("provider") == "groq" else "")
        gemini_key = chaves.get("gemini", "") or (cfg.get("api_key", "") if cfg.get("provider") == "gemini" else "")
        prompt_visao = "Você é os olhos do assistente Cromak Bridge Vox para uma pessoa com deficiência visual. Descreva exatamente o que você está vendo nesta foto da webcam do usuário (objetos na mão, embalagens, textos, expressão facial, ambiente). Seja direto, claro e natural em português."

        if groq_key:
            import base64
            from openai import OpenAI
            with open(caminho_completo, "rb") as img_f:
                b64_img = base64.b64encode(img_f.read()).decode("utf-8")
            client = OpenAI(api_key=groq_key, base_url="https://api.groq.com/openai/v1")
            resp = client.chat.completions.create(
                model="qwen/qwen3.8-27b",
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": prompt_visao},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
                ]}],
                max_tokens=1024
            )
            return f"[ANÁLISE DE CÂMERA (WEBCAM)]\n\n{resp.choices[0].message.content}"

        if not gemini_key:
            return f"Foto tirada com sucesso ({caminho_completo}), mas sem chave Groq ou Gemini configurada para enxergar."
            
        from google import genai
        import httpx
        client = genai.Client(api_key=gemini_key, http_options={'verify': False})
        
        from PIL import Image
        img = Image.open(caminho_completo)
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[img, prompt_visao]
        )
        return f"[ANÁLISE DE CÂMERA (WEBCAM)]\n\n{response.text}"
    except Exception as e:
        return f"Erro crasso ao acessar a webcam: {e}"

def obter_clima_e_hora(cidade: str = "") -> str:
    """Retorna o clima e a hora exata imediatamente."""
    try:
        import requests
        from datetime import datetime
        hora_atual = datetime.now().strftime('%d/%m/%Y às %H:%M')
        url = f"https://wttr.in/{cidade}?format=3" if cidade else "https://wttr.in/?format=3"
        try:
            resp = requests.get(url, timeout=5)
            clima = resp.text.strip()
        except:
            clima = "Não foi possível obter o clima no momento."
        return f"Data/Hora exata do sistema: {hora_atual}\nCondição climática: {clima}"
    except Exception as e:
        return f"Erro ao obter clima e hora: {e}"

def ler_documento_texto(caminho_arquivo: str) -> str:
    """Lê o texto completo de arquivos grandes (PDF, TXT, DOCX), resolvendo automaticamente nomes parciais ou sem extensão."""
    return ler_arquivo_local(caminho_arquivo)

def _ler_documento_texto_legado(caminho_arquivo: str) -> str:
    try:
        import os
        if not os.path.exists(caminho_arquivo):
            return f"Arquivo não encontrado: {caminho_arquivo}"
            
        ext = caminho_arquivo.lower().split('.')[-1]
        
        if ext == 'pdf':
            import PyPDF2
            texto = ""
            with open(caminho_arquivo, 'rb') as f:
                leitor = PyPDF2.PdfReader(f)
                limite = min(len(leitor.pages), 30)
                for i in range(limite):
                    texto += leitor.pages[i].extract_text() + "\n"
            return texto
        elif ext == 'docx':
            import docx
            doc = docx.Document(caminho_arquivo)
            texto = "\n".join([para.text for para in doc.paragraphs])
            return texto[:50000]
        else:
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                return f.read()[:50000]
    except Exception as e:
        return f"Erro ao ler documento: {e}"


def enviar_whatsapp(numero: str, mensagem: str) -> str:
    """Envia uma mensagem de WhatsApp pelo WhatsApp Web. 
    Abre o navegador e dispara (o usuário precisa já estar logado no WhatsApp Web).
    Args:
        numero: Número com código do país (ex: +5511999999999).
        mensagem: A mensagem a ser enviada.
    """
    try:
        import pywhatkit
        pywhatkit.sendwhatmsg_instantly(numero, mensagem, wait_time=15, tab_close=True, close_time=4)
        return f"Sucesso! Mensagem enviada no WhatsApp para {numero}."
    except Exception as e:
        return f"Erro ao enviar WhatsApp: {e}"

def criar_powerpoint(nome_arquivo: str, slides_json: str) -> str:
    """Cria uma apresentação PowerPoint (.pptx).
    Args:
        nome_arquivo: Caminho absoluto para salvar o .pptx.
        slides_json: String em formato JSON com os slides. Exemplo:
        [{"titulo": "Slide 1", "topicos": ["Ponto A", "Ponto B"]}, {"titulo": "Slide 2", "topicos": ["Ponto C"]}]
    """
    try:
        from pptx import Presentation
        import json
        import os
        
        if not nome_arquivo.lower().endswith('.pptx'):
            nome_arquivo += '.pptx'
            
        # Garante que vai salvar no Desktop real do usuario se ele passar só o nome
        if not os.path.isabs(nome_arquivo) or nome_arquivo.startswith("C:\\"):
            nome_arquivo = os.path.join(get_real_windows_folder('Desktop'), os.path.basename(nome_arquivo))
            
        dados = json.loads(slides_json)
        prs = Presentation()
        bullet_slide_layout = prs.slide_layouts[1]
        
        for slide_data in dados:
            slide = prs.slides.add_slide(bullet_slide_layout)
            shapes = slide.shapes
            title_shape = shapes.title
            body_shape = shapes.placeholders[1]
            
            title_shape.text = slide_data.get("titulo", "")
            tf = body_shape.text_frame
            
            topicos = slide_data.get("topicos", [])
            for i, topico in enumerate(topicos):
                if i == 0:
                    tf.text = str(topico)
                else:
                    p = tf.add_paragraph()
                    p.text = str(topico)
                    p.level = 0
                    
        prs.save(nome_arquivo)
        try:
            os.startfile(os.path.abspath(nome_arquivo))
        except:
            pass
        return f"PowerPoint gerado, salvo e aberto com sucesso em: {nome_arquivo}"
    except Exception as e:
        return f"Erro ao criar PowerPoint: {e}"

def baixar_youtube(url: str, apenas_audio: bool = True) -> str:
    """Baixa vídeo ou áudio do YouTube e salva na pasta Downloads.
    Se o usuário passar apenas o nome de uma música/vídeo (sem URL), você DEVE passar a string 'ytsearch:' seguida do nome. Ex: url='ytsearch:musica bad girl'"""
    try:
        import yt_dlp
        import os
        from .local_tools import get_real_windows_folder
        
        pasta_downloads = get_real_windows_folder('Downloads')
        ffmpeg_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'plugins', 'ffmpeg')
        
        ydl_opts = {
            'outtmpl': os.path.join(pasta_downloads, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'ffmpeg_location': ffmpeg_dir,
        }
        
        if apenas_audio:
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        else:
            ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            ydl_opts['merge_output_format'] = 'mp4'
            
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        return f"Sucesso! Mídia do Youtube baixada e salva na pasta: {pasta_downloads}"
    except Exception as e:
        return f"Erro ao baixar YouTube: {e}"

def controlar_hardware(acao: str, valor: int = 0) -> str:
    """Controla funções de hardware do sistema (volume, bloquear tela)."""
    try:
        import ctypes
        if acao in ['mutar', 'desmutar']:
            ctypes.windll.user32.keybd_event(0xAD, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0xAD, 0, 2, 0)
            return f"Comando de Volume (Toggle Mute) acionado."
        elif acao == 'aumentar_volume':
            for _ in range(valor or 5):
                ctypes.windll.user32.keybd_event(0xAF, 0, 0, 0)
                ctypes.windll.user32.keybd_event(0xAF, 0, 2, 0)
            return "Comando de aumentar volume acionado."
        elif acao == 'diminuir_volume':
            for _ in range(valor or 5):
                ctypes.windll.user32.keybd_event(0xAE, 0, 0, 0)
                ctypes.windll.user32.keybd_event(0xAE, 0, 2, 0)
            return "Comando de diminuir volume acionado."
        elif acao == 'bloquear_tela':
            ctypes.windll.user32.LockWorkStation()
            return "O computador foi bloqueado (Workstation Locked)."
        else:
            return f"Ação de hardware {acao} desconhecida. Tente mutar, desmutar, aumentar_volume ou diminuir_volume."
    except Exception as e:
        return f"Erro de hardware: {e}"


def tocar_audio_ou_radio(caminho_ou_url: str) -> str:
    """Inicia a reprodução de um arquivo de áudio local (MP3, WAV) ou rádio online (URL de stream).
    Equivalente ao RADIOVOX / TOCA / CDVOX.
    Usa o reprodutor nativo do usuário.
    """
    import os
    try:
        if not caminho_ou_url.startswith(("http://", "https://")):
            caminho_res = resolver_caminho_inteligente(caminho_ou_url)
            if os.path.exists(caminho_res):
                caminho_ou_url = caminho_res
        os.startfile(caminho_ou_url)
        return f"Mídia iniciada com sucesso: {caminho_ou_url}"
    except Exception as e:
        return f"Erro ao tentar reproduzir a mídia: {e}"

def imprimir_documento(caminho_arquivo: str) -> str:
    """Envia um documento (PDF, TXT, DOCX) diretamente para a impressora física padrão do Windows.
    Equivalente ao IMPRIVOX do Dosvox.
    
    Args:
        caminho_arquivo: Caminho absoluto do arquivo a ser impresso.
    """
    import os
    try:
        caminho_resolvido = resolver_caminho_inteligente(caminho_arquivo)
        if caminho_resolvido.startswith("AMBIGUO|"):
            _, pasta_amb, lista_amb = caminho_resolvido.split("|", 2)
            return f"Atenção: Foram encontrados múltiplos arquivos parecidos ({lista_amb}). Pergunte ao usuário qual deles imprimir."
        if os.path.exists(caminho_resolvido):
            caminho_arquivo = caminho_resolvido
        else:
            return f"Erro: Documento '{caminho_arquivo}' não encontrado para impressão."
                
        # Envia o comando de impressão nativo para o spooler do Windows
        os.startfile(caminho_arquivo, "print")
        return f"Documento '{os.path.basename(caminho_arquivo)}' enviado para a impressora padrão com sucesso!"
    except Exception as e:
        return f"Erro ao enviar para a impressora: {e}"



def mover_ou_renomear_arquivo(caminho_origem: str, caminho_destino: str) -> str:
    """Move ou renomeia um arquivo ou pasta do sistema.
    
    Args:
        caminho_origem: Caminho absoluto do arquivo atual.
        caminho_destino: Caminho absoluto para onde ele vai (incluindo o novo nome do arquivo).
    """
    import os
    import shutil
    try:
        origem_res = resolver_caminho_inteligente(caminho_origem)
        if origem_res.startswith("AMBIGUO|"):
            _, pasta_amb, lista_amb = origem_res.split("|", 2)
            return f"Atenção: Foram encontrados múltiplos arquivos parecidos ({lista_amb}). Pergunte ao usuário qual deles mover ou renomear."
        if os.path.exists(origem_res):
            caminho_origem = origem_res
        else:
            return f"Erro: O arquivo de origem {caminho_origem} não foi encontrado."
        shutil.move(caminho_origem, caminho_destino)
        return f"Sucesso! O arquivo foi movido/renomeado para {caminho_destino}"
    except Exception as e:
        return f"Erro ao mover arquivo: {e}"


def abrir_no_navegador(url: str) -> str:
    """Abre uma URL ou site da internet no navegador padrao do Windows.
    Use quando o usuario pedir para abrir um site, pagina de suporte ou link.
    """
    import webbrowser
    try:
        url_limpa = url.strip()
        if not url_limpa.startswith("http://") and not url_limpa.startswith("https://") and not url_limpa.startswith("mailto:"):
            url_limpa = "https://" + url_limpa
        webbrowser.open(url_limpa)
        return f"Pagina aberta com sucesso no navegador padrao: {url_limpa}"
    except Exception as e:
        return f"Erro ao abrir navegador: {e}"


def abrir_cliente_email(destinatario: str = "cromaksupport@gmail.com", assunto: str = "Suporte Cromak Bridge Vox", corpo: str = "") -> str:
    """Abre o aplicativo padrao de e-mail do Windows (Outlook, Mail, etc.) com destinatario, assunto e mensagem pre-preenchidos.
    Ideal para abrir canal direto com o suporte tecnico ou enviar e-mails locais sem precisar de senhas de SMTP.
    """
    import urllib.parse
    import webbrowser
    try:
        dest = destinatario.strip() if destinatario else "cromaksupport@gmail.com"
        assunto_enc = urllib.parse.quote(assunto)
        corpo_enc = urllib.parse.quote(corpo)
        mailto_url = f"mailto:{dest}?subject={assunto_enc}&body={corpo_enc}"
        webbrowser.open(mailto_url)
        return f"Cliente de e-mail do Windows aberto com destinatario {dest} e mensagem pronta para envio."
    except Exception as e:
        return f"Erro ao abrir cliente de e-mail: {e}"


def procurar_arquivo_usuario(termo_busca: str, pasta_especifica: str = "todas") -> str:
    """Procura arquivos pelo nome (ou parte do nome/extensão) de forma ultra-rápida e segura (sandboxed)
    exclusivamente dentro das 6 pastas do usuário (Área de Trabalho, Documentos, Downloads, Músicas, Imagens, Vídeos)
    e suas subpastas diretas, sem varrer pastas sensíveis do sistema operacional (como C:\\Windows).
    Use sempre que o usuário pedir: "encontre o arquivo X", "onde está o arquivo Y", "procure a música Z".
    """
    import os
    import difflib
    try:
        termo_limpo = termo_busca.strip('"\' ')
        termo_norm = _normalizar_nome_busca(os.path.splitext(termo_limpo)[0] or termo_limpo)
        termo_completo_norm = _normalizar_nome_busca(termo_limpo)
        ext_filtro = os.path.splitext(termo_limpo)[1].lower()
        palavras_busca = [p for p in termo_norm.split() if len(p) >= 2]
        prefixo_2 = termo_norm[:2] if len(termo_norm) >= 2 else ""

        todas_pastas = obter_todas_pastas_usuario()
        pasta_esp_norm = _normalizar_nome_busca(pasta_especifica)

        pastas_para_varrer = {}
        if pasta_esp_norm and pasta_esp_norm not in ("todas", "all", "qualquer", ""):
            for nome_p, cam_p in todas_pastas.items():
                if pasta_esp_norm in _normalizar_nome_busca(nome_p):
                    pastas_para_varrer[nome_p] = cam_p
        if not pastas_para_varrer:
            pastas_para_varrer = todas_pastas

        pastas_ignoradas = {
            ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
            "dist", "build", "_internal", "site-packages", "appdata",
            "$recycle.bin", "system volume information", "obj", "bin", "packages"
        }
        encontrados = []
        max_prof = 3 if len(pastas_para_varrer) == 1 else 2

        def _varrer_rapido(pasta_atual, nome_base, prof, contador):
            if prof > max_prof or contador[0] > 3500:
                return
            try:
                with os.scandir(pasta_atual) as it:
                    subdirs = []
                    for entry in it:
                        contador[0] += 1
                        if contador[0] > 3500:
                            break
                        nome = entry.name
                        if nome.startswith("."):
                            continue
                        try:
                            if entry.is_dir(follow_symlinks=False):
                                if prof < max_prof and nome.lower() not in pastas_ignoradas:
                                    subdirs.append(entry.path)
                                continue
                        except OSError:
                            continue

                        nome_sem_ext, ext_atual = os.path.splitext(nome)
                        ext_lower = ext_atual.lower()
                        if ext_lower == ".lnk":
                            continue
                        if ext_filtro and ext_lower != ext_filtro:
                            continue

                        nome_lower = nome_sem_ext.lower()
                        fn_norm = _normalizar_nome_busca(nome_sem_ext) if not nome_lower.isascii() else nome_lower
                        fn_completo_norm = fn_norm + ext_lower

                        score = 0.0
                        if termo_norm and (fn_norm == termo_norm or fn_completo_norm == termo_completo_norm):
                            score = 1.0
                        elif termo_norm and (fn_norm.startswith(termo_norm) or termo_norm in fn_norm):
                            score = 0.90
                        elif palavras_busca and all(p in fn_completo_norm for p in palavras_busca):
                            score = 0.85
                        elif prefixo_2 and fn_norm.startswith(prefixo_2) and abs(len(fn_norm) - len(termo_norm)) <= 5:
                            ratio = difflib.SequenceMatcher(None, termo_norm, fn_norm).ratio()
                            if ratio >= 0.72:
                                score = ratio

                        if score > 0:
                            encontrados.append((score, nome_base, entry.path))

                    for sd_path in subdirs:
                        _varrer_rapido(sd_path, nome_base, prof + 1, contador)
            except OSError:
                pass

        for nome_base, raiz in pastas_para_varrer.items():
            if raiz and os.path.exists(raiz):
                _varrer_rapido(raiz, nome_base, 0, [0])

        if not encontrados:
            pastas_nomes = ", ".join(pastas_para_varrer.keys())
            return f"Nenhum arquivo correspondente a '{termo_busca}' foi encontrado nas pastas do usuário ({pastas_nomes})."

        encontrados.sort(key=lambda x: x[0], reverse=True)
        top = encontrados[:15]
        linhas = [f"Encontrados {len(encontrados)} arquivo(s) para '{termo_busca}' (exibindo os principais):"]
        for _, pasta_origem, cam in top:
            linhas.append(f"- [{pasta_origem}] {cam}")
        return "\n".join(linhas)
    except Exception as e:
        return f"Erro ao procurar arquivo: {e}"


def _caminho_db_agenda() -> str:
    from .seguranca import get_appdata_dir
    pasta_vox = get_appdata_dir()
    pasta_db = os.path.join(pasta_vox, "banco_de_dados")
    os.makedirs(pasta_db, exist_ok=True)
    return os.path.join(pasta_db, "agenda_pessoal.db")

def _inicializar_db_agenda():
    import sqlite3
    db_path = _caminho_db_agenda()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agenda_itens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            titulo TEXT NOT NULL,
            data_evento TEXT DEFAULT '',
            hora_evento TEXT DEFAULT '',
            telefone_ou_valor TEXT DEFAULT '',
            detalhes TEXT DEFAULT '',
            notificado INTEGER DEFAULT 0,
            criado_em TEXT
        )
    """)
    conn.commit()
    conn.close()
    return db_path

import re, datetime

def gerenciar_agenda_pessoal(
    acao: str,
    titulo_ou_busca: str = "",
    data_evento: str = "",
    hora_evento: str = "",
    telefone_ou_numero: str = "",
    detalhes: str = ""
) -> str:
    """Agenda Pessoal Fixa e Permanente do usuário (salva em banco de dados local).
    Serve tanto para COMPROMISSOS (datas e horários) quanto para CONTATOS/TELEFONES e ANOTAÇÕES FIXAS.
    Use sempre que o usuário disser: "anote na minha agenda", "salve o número de fulano", "olhe minha agenda", "o que tem dia tal", "qual o telefone de X".

    Args:
        acao: Opções: 'salvar', 'consultar', 'listar_tudo', 'excluir'.
        titulo_ou_busca: Nome do compromisso, nome do contato/pessoa, data ou termo para buscar/excluir.
        data_evento: Data do compromisso no formato DD/MM/AAAA (ex: '05/11/2026'). Deixe vazio se for apenas um contato/telefone ou nota fixa.
        hora_evento: Horário do compromisso no formato HH:MM (ex: '14:30'). Opcional.
        telefone_ou_numero: Número de telefone, celular, chave Pix, documento ou código associado ao contato/registro.
        detalhes: Observações adicionais, endereço ou descrição completa.
    """
    import sqlite3
    from datetime import datetime
    try:
        db_path = _inicializar_db_agenda()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        acao_limpa = _normalizar_nome_busca(acao)

        # Resolução inteligente de datas (se a IA passou data_evento vazia ou com dia da semana / termos relativos)
        from datetime import date as _dt_d, timedelta as _dt_td
        _hoje_dt = _dt_d.today()
        _texto_analise_data = (data_evento + ' ' + titulo_ou_busca).strip().lower()
        
        # 1. Se data_evento não for DD/MM/AAAA válida, tenta resolver dia da semana ou data relativa
        if not re.search(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', data_evento):
            _dias_semana_map = {
                'segunda': 0, 'terca': 1, 'terça': 1, 'quarta': 2, 'quinta': 3, 'sexta': 4, 'sabado': 5, 'sábado': 5, 'domingo': 6
            }
            if 'amanha' in _texto_analise_data or 'amanhã' in _texto_analise_data:
                data_evento = (_hoje_dt + _dt_td(days=1)).strftime('%d/%m/%Y')
            elif 'hoje' in _texto_analise_data and ('salvar' in acao_limpa or 'adicionar' in acao_limpa):
                data_evento = _hoje_dt.strftime('%d/%m/%Y')
            else:
                for _nome_d, _idx_d in _dias_semana_map.items():
                    if _nome_d in _texto_analise_data:
                        _diff = (_idx_d - _hoje_dt.weekday()) % 7
                        if _diff == 0:
                            _diff = 7
                        data_evento = (_hoje_dt + _dt_td(days=_diff)).strftime('%d/%m/%Y')
                        break

        # 2. Se for consulta/busca e tiver dia X (ex: dia 3, dia 03)
        if acao_limpa not in ('salvar', 'adicionar', 'criar', 'agendar', 'inserir'):
            _m_dia_busca = re.search(r'\bdia\s+(\d{1,2})(?:/(\d{1,2}))?(?:/(\d{2,4}))?\b', _texto_analise_data)
            if _m_dia_busca:
                _num_d = int(_m_dia_busca.group(1))
                _num_m = int(_m_dia_busca.group(2)) if _m_dia_busca.group(2) else _hoje_dt.month
                _num_a = int(_m_dia_busca.group(3)) if _m_dia_busca.group(3) else _hoje_dt.year
                try:
                    _dt_cand = _dt_d(_num_a, _num_m, _num_d)
                    if _dt_cand < _hoje_dt and not _m_dia_busca.group(2):
                        _num_m = 1 if _num_m == 12 else _num_m + 1
                        _num_a = _num_a + 1 if _num_m == 1 else _num_a
                        _dt_cand = _dt_d(_num_a, _num_m, _num_d)
                    data_evento = _dt_cand.strftime('%d/%m/%Y')
                except: pass

        if acao_limpa in ("salvar", "adicionar", "criar", "agendar", "inserir"):
            if not titulo_ou_busca and not data_evento and not telefone_ou_numero:
                conn.close()
                return "Erro: Informe pelo menos um título/nome, data ou número para salvar na agenda."
            tipo = "compromisso" if data_evento.strip() else ("contato" if telefone_ou_numero.strip() else "nota")
            agora = datetime.now().strftime("%d/%m/%Y %H:%M")
            cursor.execute(
                """INSERT INTO agenda_itens (tipo, titulo, data_evento, hora_evento, telefone_ou_valor, detalhes, notificado, criado_em)
                   VALUES (?, ?, ?, ?, ?, ?, 0, ?)""",
                (tipo, titulo_ou_busca.strip(), data_evento.strip(), hora_evento.strip(), telefone_ou_numero.strip(), detalhes.strip(), agora)
            )
            conn.commit()
            novo_id = cursor.lastrowid
            conn.close()
            resumo = f"Registro #{novo_id} salvo com sucesso na sua Agenda Fixa: {titulo_ou_busca}"
            if data_evento:
                resumo += f" | Data: {data_evento}" + (f" às {hora_evento}" if hora_evento else "")
            if telefone_ou_numero:
                resumo += f" | Número/Contato: {telefone_ou_numero}"
            if detalhes:
                resumo += f" | Detalhes: {detalhes}"
            return resumo

        elif acao_limpa in ("excluir", "apagar", "remover", "deletar", "cancelar"):
            termo_norm = _normalizar_nome_busca(titulo_ou_busca or data_evento)
            cursor.execute("SELECT id, titulo, data_evento, hora_evento, telefone_ou_valor FROM agenda_itens")
            todos = cursor.fetchall()
            ids_para_remover = []
            nomes_removidos = []
            for r_id, r_tit, r_data, r_hora, r_tel in todos:
                bloco = _normalizar_nome_busca(f"{r_id} {r_tit} {r_data} {r_tel}")
                if termo_norm and (termo_norm == str(r_id) or termo_norm in bloco):
                    ids_para_remover.append(r_id)
                    nomes_removidos.append(f"#{r_id} {r_tit}" + (f" ({r_data})" if r_data else ""))
            if not ids_para_remover:
                conn.close()
                return f"Nenhum item encontrado na agenda correspondente a '{titulo_ou_busca or data_evento}' para excluir."
            for i_rem in ids_para_remover:
                cursor.execute("DELETE FROM agenda_itens WHERE id = ?", (i_rem,))
            conn.commit()
            conn.close()
            return "Removido(s) da agenda com sucesso: " + ", ".join(nomes_removidos)

        else:
            # consultar / listar_tudo
            cursor.execute("SELECT id, tipo, titulo, data_evento, hora_evento, telefone_ou_valor, detalhes FROM agenda_itens ORDER BY data_evento ASC, hora_evento ASC, id DESC")
            todos = cursor.fetchall()
            conn.close()

            if not todos:
                return "Sua agenda pessoal está vazia no momento."

            filtro_bruto = (titulo_ou_busca + " " + data_evento + " " + telefone_ou_numero).strip()
            filtro_norm = _normalizar_nome_busca(filtro_bruto)

            # Detecção de período temporal (semana que vem, este mês, intervalo DD/MM/AAAA a DD/MM/AAAA)
            dt_inicio_per, dt_fim_per = None, None
            texto_busca_temporal = (titulo_ou_busca + " " + data_evento).strip().lower()
            m_range = re.search(r"(\d{1,2}/\d{1,2}/\d{2,4})\s*(?:a|ate|até|-)\s*(\d{1,2}/\d{1,2}/\d{2,4})", texto_busca_temporal)
            if m_range:
                try:
                    d1_p = [int(p) for p in m_range.group(1).split("/")]
                    d2_p = [int(p) for p in m_range.group(2).split("/")]
                    ano1 = d1_p[2] if d1_p[2] > 100 else 2000 + d1_p[2]
                    ano2 = d2_p[2] if d2_p[2] > 100 else 2000 + d2_p[2]
                    from datetime import date as _dt_date
                    dt_inicio_per = min(_dt_date(ano1, d1_p[1], d1_p[0]), _dt_date(ano2, d2_p[1], d2_p[0]))
                    dt_fim_per = max(_dt_date(ano1, d1_p[1], d1_p[0]), _dt_date(ano2, d2_p[1], d2_p[0]))
                except: pass
            elif any(k in texto_busca_temporal for k in ("semana que vem", "proxima semana", "próxima semana")):
                from datetime import date as _dt_date, timedelta as _dt_td
                hoje = _dt_date.today()
                dias = 7 - hoje.weekday() if hoje.weekday() != 0 else 7
                dt_inicio_per = hoje + _dt_td(days=dias)
                dt_fim_per = dt_inicio_per + _dt_td(days=6)
            elif any(k in texto_busca_temporal for k in ("esta semana", "essa semana", "nesta semana")):
                from datetime import date as _dt_date, timedelta as _dt_td
                hoje = _dt_date.today()
                dt_inicio_per = hoje - _dt_td(days=hoje.weekday())
                dt_fim_per = dt_inicio_per + _dt_td(days=6)
            elif any(k in texto_busca_temporal for k in ("mes que vem", "mês que vem", "próximo mês", "proximo mes")):
                from datetime import date as _dt_date
                hoje = _dt_date.today()
                ano = hoje.year if hoje.month < 12 else hoje.year + 1
                mes = hoje.month + 1 if hoje.month < 12 else 1
                import calendar
                _, ult = calendar.monthrange(ano, mes)
                dt_inicio_per = _dt_date(ano, mes, 1)
                dt_fim_per = _dt_date(ano, mes, ult)
            elif any(k in texto_busca_temporal for k in ("este mês", "esse mês", "este mes", "neste mês")):
                from datetime import date as _dt_date
                hoje = _dt_date.today()
                import calendar
                _, ult = calendar.monthrange(hoje.year, hoje.month)
                dt_inicio_per = _dt_date(hoje.year, hoje.month, 1)
                dt_fim_per = _dt_date(hoje.year, hoje.month, ult)

            # Se o usuário pediu tudo ("olhe minha agenda", "tudo", "todos") ou não passou filtro
            palavras_genericas = {"tudo", "todos", "todas", "agenda", "minha agenda", "compromissos", "contatos", ""}
            mostrar_tudo = (acao_limpa == "listar_tudo") or (filtro_norm in palavras_genericas)

            filtrados = []
            palavras = [p for p in filtro_norm.split() if len(p) >= 2 and p not in ("dia", "data", "numero", "telefone", "agenda", "que", "tem", "semana", "vem", "proxima", "mes", "ano")]
            for item in todos:
                r_id, r_tipo, r_tit, r_data, r_hora, r_tel, r_det = item
                if mostrar_tudo:
                    filtrados.append(item)
                elif dt_inicio_per and dt_fim_per and r_data:
                    try:
                        from datetime import date as _dt_date
                        p_d = [int(x) for x in r_data.strip().split("/")]
                        ano_d = p_d[2] if p_d[2] > 100 else 2000 + p_d[2]
                        item_dt = _dt_date(ano_d, p_d[1], p_d[0])
                        if dt_inicio_per <= item_dt <= dt_fim_per:
                            filtrados.append(item)
                    except: pass
                else:
                    bloco_norm = _normalizar_nome_busca(f"{r_tit} {r_data} {r_hora} {r_tel} {r_det}")
                    if (data_evento and data_evento.strip() in r_data) or (filtro_norm in bloco_norm) or (palavras and all(p in bloco_norm for p in palavras)):
                        filtrados.append(item)

            if not filtrados:
                return f"Não encontrei nenhum compromisso ou número para '{filtro_bruto}' na sua agenda."

            compromissos = []
            contatos_notas = []
            for r_id, r_tipo, r_tit, r_data, r_hora, r_tel, r_det in filtrados:
                linha = f"• [#{r_id}] {r_tit}"
                if r_data:
                    linha += f" — Data: {r_data}" + (f" às {r_hora}" if r_hora else "")
                if r_tel:
                    linha += f" — Número: {r_tel}"
                if r_det:
                    linha += f" ({r_det})"
                if r_data:
                    compromissos.append(linha)
                else:
                    contatos_notas.append(linha)

            resposta = []
            if compromissos:
                resposta.append("Compromissos e Datas na Agenda:\n" + "\n".join(compromissos))
            if contatos_notas:
                resposta.append("Contatos, Números e Anotações Fixas:\n" + "\n".join(contatos_notas))
            return "\n\n".join(resposta)

    except Exception as e:
        return f"Erro ao acessar a agenda pessoal: {e}"

def alternar_preferencia_sistema(opcao: str, ativar: bool = True) -> str:
    """Ativa ou desativa opções de configuração do Cromak Bridge diretamente pela conversa com a IA.
    Opções: 'agent_mode' (Modo Agente / Auto-Coder), 'auto_tts' (Resposta por voz automática), 'start_fullscreen' (Iniciar em tela cheia), 'start_with_windows' (Iniciar com Windows), 'minimize_to_tray' (Minimizar para bandeja/tray), 'always_voice'.
    """
    import os
    from .seguranca import ler_config_seguro, salvar_config_seguro

    mapa_aliases = {
        'agente': 'agent_mode',
        'modo agente': 'agent_mode',
        'auto coder': 'agent_mode',
        'autocoder': 'agent_mode',
        'voz': 'auto_tts',
        'resposta por voz': 'auto_tts',
        'falar': 'auto_tts',
        'fala': 'auto_tts',
        'auto_tts': 'auto_tts',
        'always voice': 'always_voice',
        'always_voice': 'always_voice',
        'tela cheia': 'start_fullscreen',
        'fullscreen': 'start_fullscreen',
        'iniciar com windows': 'start_with_windows',
        'startup': 'start_with_windows',
        'bandeja': 'minimize_to_tray',
        'tray': 'minimize_to_tray',
        'minimizar para bandeja': 'minimize_to_tray'
    }

    op_norm = opcao.strip().lower()
    chave = mapa_aliases.get(op_norm, op_norm)

    nomes_amigaveis = {
        'agent_mode': 'Modo Agente (Auto-Coder)',
        'auto_tts': 'Resposta por Voz Automática',
        'always_voice': 'Modo Always-Voice',
        'start_fullscreen': 'Iniciar em Tela Cheia',
        'start_with_windows': 'Iniciar junto com o Windows',
        'minimize_to_tray': 'Minimizar para a Bandeja do Sistema'
    }

    if chave not in nomes_amigaveis:
        return f"Opção '{opcao}' não reconhecida. Opções disponíveis: Modo Agente, Resposta por Voz, Tela Cheia, Iniciar com o Windows, Bandeja."

    from .seguranca import get_appdata_dir, salvar_config_seguro, ler_config_seguro
    cfg_p = os.path.join(get_appdata_dir(), "config.json")
    if os.path.exists(cfg_p):
        cfg = ler_config_seguro(cfg_p) or {}
        cfg[chave] = bool(ativar)
        salvar_config_seguro(cfg_p, cfg)
        estado_txt = "ativada" if ativar else "desativada"
        msg = f"Sucesso: A opção '{nomes_amigaveis[chave]}' foi {estado_txt} nas Preferências do sistema."
        if chave in ("auto_tts", "always_voice", "agent_mode", "start_fullscreen"):
            msg += " (Importante: Para que a nova configuração de fala/voz/modo tenha efeito completo em todas as janelas e áudios, feche e abra o aplicativo novamente pelo atalho F4)."
        return msg

    return "Erro: Arquivo de configuração não encontrado."

def get_todas_ferramentas():





    return [ler_arquivo_local, listar_diretorio, obter_informacoes_sistema, executar_comando, pesquisar_na_web, ler_pagina_web, criar_planilha_excel, controlar_mouse_teclado, editar_arquivo_codigo, analisar_tela, consultar_banco_sqlite, memorizar_conhecimento, pesquisar_memoria_permanente, controlar_navegador_fantasma, notificar_usuario, agendar_lembrete, analisar_midia, fazer_requisicao_api, enviar_email, ler_emails, criar_pdf, gerenciar_janelas, enviar_whatsapp, criar_powerpoint, baixar_youtube, controlar_hardware, tocar_audio_ou_radio, imprimir_documento, mover_ou_renomear_arquivo, abrir_no_navegador, abrir_cliente_email, procurar_arquivo_usuario, gerenciar_agenda_pessoal, alternar_preferencia_sistema]













