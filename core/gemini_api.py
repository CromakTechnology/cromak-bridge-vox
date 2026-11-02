import time
from google import genai
from google.genai import types
from openai import OpenAI
import anthropic

# ==========================================
# 1. INTERFACE ADAPTER (Provider Manager)
# ==========================================
class AIProvider:
    """Classe base para padronizar qualquer IA."""
    def _chamar_api_com_retry(self, **kwargs):
        import time, re
        for tent in range(3):
            try:
                return self.client.chat.completions.create(**kwargs)
            except Exception as e:
                err_s = str(e)
                if ("429" in err_s or "rate_limit" in err_s.lower()) and tent < 2:
                    m_seg = re.search(r"try again in\s+(\d+(?:\.\d+)?)s", err_s, re.IGNORECASE)
                    m_ms = re.search(r"try again in\s+(\d+(?:\.\d+)?)ms", err_s, re.IGNORECASE)
                    if m_ms:
                        espera = max(1.0, float(m_ms.group(1)) / 1000.0 + 0.5)
                    elif m_seg:
                        espera = float(m_seg.group(1)) + 0.6
                    else:
                        espera = 3.0 * (tent + 1)
                    if espera <= 14.0:
                        print(f"[Smart Rate-Limit] Aguardando tempo exato da API ({espera:.1f}s) na etapa atual...")
                        try:
                            from .logger import log_api_call
                            log_api_call("Groq", str(kwargs.get("model", "qwen")), espera, 429, error=f"Rate Limit 429. Backoff de {espera:.1f}s")
                        except Exception:
                            pass
                        time.sleep(espera)
                        continue
                raise e

    def enviar_prompt(self, texto, caminho_arquivo=None):
        raise NotImplementedError("O provedor deve implementar este método.")

# ==========================================
# 2. MOTOR GOOGLE GEMINI
# ==========================================
class GeminiProvider(AIProvider):
    # ATENÇÃO AQUI: system_prompt="" adicionado nos parâmetros
    def __init__(self, api_key, model_name="gemini-1.5-flash", historico=None, system_prompt=""):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        
        formatted_history = []
        if historico:
            for msg in historico:
                role = msg.get("role")
                if role == "assistant": role = "model"
                
                parts = msg.get("parts", [""])
                text_parts = [types.Part.from_text(text=p) for p in parts if isinstance(p, str)]
                if text_parts:
                    formatted_history.append(types.Content(role=role, parts=text_parts))
        
        # Configura a temperatura e injeta a instrução de comportamento (se existir)
        config_args = {"temperature": 0.7}
        if system_prompt:
            config_args["system_instruction"] = system_prompt
            
        # Adiciona suporte a ferramentas (Function Calling)
        try:
            from .local_tools import get_todas_ferramentas
            config_args["tools"] = get_todas_ferramentas()
        except ImportError:
            print("Ferramentas locais não encontradas.")

        self.chat = self.client.chats.create(
            model=self.model_name,
            config=types.GenerateContentConfig(**config_args),
            history=formatted_history if formatted_history else None
        )

    def enviar_prompt(self, texto, caminho_arquivo=None):
        if caminho_arquivo:
            arquivo_enviado = self.client.files.upload(file=caminho_arquivo)
            return self.chat.send_message([texto, arquivo_enviado]).text
        return self.chat.send_message(texto).text

# ==========================================
# 3. MOTOR ALIBABA QWEN (Via OpenAI API)
# ==========================================
import json
from .seguranca import ler_config_seguro

def get_openai_tools():
    return [
        {
            "type": "function",
            "function": {
                "name": "ler_arquivo_local",
                "description": "Lê o conteúdo de um arquivo (TXT, PDF, DOCX, CSV, MD, código) no computador do usuário. Aceita nome parcial ou SEM extensão (ex: Desktop\\potifolio), pois descobre sozinho a extensão e o nome completo na pasta. NUNCA pergunte a extensão ao usuário, chame esta ferramenta direto!",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "caminho_absoluto": {"type": "string", "description": "Caminho para o arquivo (pode ser sem extensão ou apenas parte do nome)."}
                    },
                    "required": ["caminho_absoluto"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "listar_diretorio",
                "description": "Lista todos os arquivos e pastas dentro de um diretório.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "caminho_diretorio": {"type": "string", "description": "Caminho absoluto para a pasta."}
                    },
                    "required": ["caminho_diretorio"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "obter_informacoes_sistema",
                "description": "Retorna informações básicas do sistema operacional e hora atual.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "executar_comando",
                "description": "Executa um comando no terminal do Windows (CMD/PowerShell) e retorna a saida. Use para abrir programas ou verificar sistema.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "comando": {"type": "string", "description": "Comando exato a ser executado."}
                    },
                    "required": ["comando"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "pesquisar_na_web",
                "description": "Pesquisa informações na internet usando o buscador DuckDuckGo e retorna os principais resultados. Use sempre que precisar de informações recentes ou notícias.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "termo_de_busca": {"type": "string", "description": "A frase ou palavra-chave para buscar na web."}
                    },
                    "required": ["termo_de_busca"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "ler_pagina_web",
                "description": "Lê o conteúdo de uma página web específica (URL) e extrai todo o texto limpo dela.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "O link completo da página web (HTTP/HTTPS)."}
                    },
                    "required": ["url"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "criar_planilha_excel",
                "description": "Gera e salva um arquivo de planilha do Excel (.xlsx) na área de trabalho do usuário.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "nome_arquivo": {"type": "string", "description": "O nome do arquivo sem a extensão, ex: Relatorio"},
                        "dados_json": {"type": "string", "description": "Uma string contendo um array de dicionarios em JSON. Ex: '[{\"Produto\": \"Mouse\", \"Preco\": 50}]'"}
                    },
                    "required": ["nome_arquivo", "dados_json"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "controlar_mouse_teclado",
                "description": "Simula interações físicas do usuário com o mouse e teclado usando RPA. Pode digitar textos sozinho, clicar ou mover o mouse.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "acao": {"type": "string", "description": "O tipo de ação. Pode ser: 'digitar', 'pressionar_tecla', 'clicar', 'mover_mouse', 'scroll'."},
                        "parametro": {"type": "string", "description": "O valor da ação. Ex: o texto a digitar, a tecla, ou 'X,Y' para coordenadas."}
                    },
                    "required": ["acao"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "editar_arquivo_codigo",
                "description": "Cria ou sobrescreve um arquivo com um conteúdo fornecido.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "caminho_absoluto": {"type": "string", "description": "Caminho absoluto do arquivo"},
                        "conteudo_completo": {"type": "string", "description": "O código ou texto completo a ser salvo"}
                    },
                    "required": ["caminho_absoluto", "conteudo_completo"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "analisar_tela",
                "description": "Tira uma captura de tela invisível do usuário e usa visão para ler textos, achar erros visuais ou analisar gráficos.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "instrucao": {"type": "string", "description": "O que a IA deve procurar ou analisar na imagem capturada."}
                    },
                    "required": ["instrucao"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "consultar_banco_sqlite",
                "description": "Conecta em um banco SQLite (.db/.sqlite) e roda uma Query SQL (apenas SELECT) para ler dados e gerar relatórios.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "caminho_db": {"type": "string", "description": "O caminho absoluto para o banco SQLite."},
                        "query_sql": {"type": "string", "description": "A instrução SELECT do SQL a ser rodada."}
                    },
                    "required": ["caminho_db", "query_sql"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "memorizar_conhecimento",
                "description": "Salva uma informação, preferência do usuário ou regra importante na Memória de Longo Prazo. Use para coisas que você não quer esquecer quando o usuário iniciar uma Nova Conversa.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "assunto": {"type": "string", "description": "Categoria da memória (ex: Preferência, Servidor)"},
                        "detalhes": {"type": "string", "description": "O conhecimento a ser salvo"}
                    },
                    "required": ["assunto", "detalhes"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "pesquisar_memoria_permanente",
                "description": "Pesquisa a Memória de Longo Prazo em busca de coisas salvas em sessões/dias anteriores.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "termo_busca": {"type": "string", "description": "Palavra-chave para pesquisar na memória."}
                    },
                    "required": ["termo_busca"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "controlar_navegador_fantasma",
                "description": "Abre um navegador invisível, acessa uma URL dinâmica e executa JavaScript na página para clicar, logar ou extrair dados. Útil para sites complexos que o scraper simples não lê.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL para acessar."},
                        "script_js": {"type": "string", "description": "Opcional. Código JavaScript a ser executado para manipular a página e extrair dados usando return (ex: return document.body.innerText)."}
                    },
                    "required": ["url"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "notificar_usuario",
                "description": "Envia um Pop-up (Toast Notification) nativo do Windows na tela do usuário. Use para chamar a atenção fora do chat.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "titulo": {"type": "string", "description": "Título principal do Pop-up."},
                        "mensagem": {"type": "string", "description": "O aviso a ser dado."}
                    },
                    "required": ["titulo", "mensagem"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "agendar_lembrete",
                "description": "Agenda uma tarefa em segundo plano. Após os minutos especificados, um pop-up nativo saltará na tela do usuário lembrando-o de algo.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "minutos": {"type": "number", "description": "Quantos minutos esperar (ex: 5 para 5 min, 0.5 para 30 segundos)."},
                        "mensagem_notificacao": {"type": "string", "description": "O que dizer no lembrete."},
                        "titulo": {"type": "string", "description": "Título opcional."}
                    },
                    "required": ["minutos", "mensagem_notificacao"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "analisar_midia",
                "description": "Analisa arquivos de vídeo (MP4, AVI) ou áudio (MP3, WAV) respondendo perguntas precisas sobre eles. A IA literalmente assiste ao vídeo/áudio.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "caminho_arquivo": {"type": "string", "description": "Caminho absoluto do arquivo no PC."},
                        "instrucao": {"type": "string", "description": "O que extrair do arquivo (ex: 'Faça a ata da reunião', 'Descreva quem entra na sala')."}
                    },
                    "required": ["caminho_arquivo", "instrucao"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "fazer_requisicao_api",
                "description": "Faz uma requisição HTTP (GET, POST, PUT) para interagir com APIs de outros sistemas (Trello, GitHub, sistemas locais, etc).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "A URL ou Endpoint."},
                        "metodo": {"type": "string", "description": "GET, POST, PUT ou DELETE. Padrão é GET."},
                        "headers_json": {"type": "string", "description": "Dicionário JSON em string com Headers (ex: Bearer tokens)."},
                        "body_json": {"type": "string", "description": "Dicionário JSON em string com o Payload (para POST/PUT)."}
                    },
                    "required": ["url"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "enviar_email",
                "description": "Envia um e-mail para o destinatário usando a conta do usuário.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "destinatario": {"type": "string", "description": "Endereço de e-mail de destino (ex: teste@gmail.com)."},
                        "assunto": {"type": "string", "description": "O assunto principal."},
                        "corpo": {"type": "string", "description": "O corpo do e-mail."}
                    },
                    "required": ["destinatario", "assunto", "corpo"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "ler_emails",
                "description": "Lê a caixa de entrada do usuário para processar e-mails recebidos.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "quantidade": {"type": "number", "description": "Máximo de e-mails para ler. Padrão 5."},
                        "apenas_nao_lidos": {"type": "boolean", "description": "Se True, lê apenas e-mails não lidos. Padrão True."}
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "criar_pdf",
                "description": "Gera um arquivo PDF formatado e bem desenhado a partir de um texto Markdown (Títulos, tabelas, negritos). A ferramenta salva o PDF e já abre na tela do usuário.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "nome_arquivo": {"type": "string", "description": "Caminho absoluto para salvar o arquivo (deve terminar com .pdf)."},
                        "conteudo_markdown": {"type": "string", "description": "Conteúdo do documento em sintaxe Markdown (use #, **, tabelas, etc)."}
                    },
                    "required": ["nome_arquivo", "conteudo_markdown"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "gerenciar_janelas",
                "description": "Gerencia as janelas abertas no sistema operacional (minimizar, maximizar, focar ou fechar janelas de outros aplicativos).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "acao": {"type": "string", "description": "A ação a ser feita. Opções exatas: 'minimizar_tudo', 'maximizar', 'minimizar', 'fechar', 'focar'."},
                        "nome_janela": {"type": "string", "description": "Parte do título da janela (ex: 'Chrome', 'Bloco de Notas'). Deixe vazio se a ação for minimizar_tudo."}
                    },
                    "required": ["acao"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "enviar_whatsapp",
                "description": "Envia uma mensagem no WhatsApp Web. O navegador será aberto e o envio será automático.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "numero": {"type": "string", "description": "Número do WhatsApp com código do país (ex: +5511999999999)."},
                        "mensagem": {"type": "string", "description": "O corpo da mensagem."}
                    },
                    "required": ["numero", "mensagem"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "criar_powerpoint",
                "description": "Cria um arquivo de apresentação do PowerPoint (.pptx).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "nome_arquivo": {"type": "string", "description": "Caminho absoluto do arquivo a salvar (deve terminar com .pptx)."},
                        "slides_json": {"type": "string", "description": "Uma string em formato JSON exato. Exemplo: [{\"titulo\": \"Slide 1\", \"topicos\": [\"Ponto A\", \"Ponto B\"]}, {\"titulo\": \"Slide 2\", \"topicos\": [\"Ponto C\"]}]"}
                    },
                    "required": ["nome_arquivo", "slides_json"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "baixar_youtube",
                "description": "Faz o download de um vídeo ou áudio do YouTube.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "Link completo do YouTube."},
                        "apenas_audio": {"type": "boolean", "description": "Se True, baixa apenas o MP3/áudio. Padrão: True."}
                    },
                    "required": ["url"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "controlar_hardware",
                "description": "Controla hardwares/funções físicas do computador.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "acao": {"type": "string", "description": "Opções exatas: 'mutar', 'desmutar', 'aumentar_volume', 'diminuir_volume', 'bloquear_tela'."},
                        "valor": {"type": "integer", "description": "Quantos cliques de volume aumentar/diminuir. Ex: 10."}
                    },
                    "required": ["acao"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "capturar_webcam",
                "description": "Liga a webcam do usuário, tira uma foto instantânea em segundo plano e retorna a análise visual do rosto do usuário ou do ambiente ao redor. Perfeito para responder 'como eu estou?', 'o que estou segurando?'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "camera_index": {"type": "integer", "description": "Índice da webcam (padrão é 0)."}
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "obter_clima_e_hora",
                "description": "Retorna o clima e a hora exata imediatamente, para respostas espaciais/temporais rápidas.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "cidade": {"type": "string", "description": "Cidade para buscar o clima. Vazio para automático."}
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "ler_documento_texto",
                "description": "Lê o texto bruto de um PDF ou TXT (Modo Leitura de Acessibilidade) para a IA resumir ou ler em voz alta.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "caminho_arquivo": {"type": "string", "description": "Caminho absoluto do arquivo a ser lido."}
                    },
                    "required": ["caminho_arquivo"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "mover_ou_renomear_arquivo",
                "description": "Move ou renomeia um arquivo ou pasta do sistema. Use caminhos absolutos.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "caminho_origem": {"type": "string", "description": "Caminho absoluto do arquivo atual."},
                        "caminho_destino": {"type": "string", "description": "Caminho absoluto para onde ele vai (incluindo o nome final)."}
                    },
                    "required": ["caminho_origem", "caminho_destino"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "tocar_audio_ou_radio",
                "description": "Inicia a reprodução de um arquivo de áudio local (MP3, WAV) ou rádio online.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "caminho_ou_url": {"type": "string", "description": "Caminho absoluto do arquivo de áudio local ou URL."}
                    },
                    "required": ["caminho_ou_url"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "imprimir_documento",
                "description": "Envia um documento (PDF, Imagem, Texto) para a Impressora padrão do Windows.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "caminho_arquivo": {"type": "string", "description": "Caminho absoluto do arquivo a ser impresso."}
                    },
                    "required": ["caminho_arquivo"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "abrir_no_navegador",
                "description": "Abre um endereço web ou site no navegador de internet padrão do Windows. Use quando o usuário pedir para abrir um site ou página de suporte.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL completa do site a ser aberto (ex: https://cromaktechnology.github.io/pt/suporte.html)"}
                    },
                    "required": ["url"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "abrir_cliente_email",
                "description": "Abre o cliente padrão de e-mail do Windows com destinatário, assunto e corpo já preenchidos. Use para abrir mensagem de suporte ou e-mail sem precisar de senha.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "destinatario": {"type": "string", "description": "E-mail de destino (padrão: cromaksupport@gmail.com)"},
                        "assunto": {"type": "string", "description": "Assunto do e-mail"},
                        "corpo": {"type": "string", "description": "Texto da mensagem ou descrição do problema"}
                    },
                    "required": ["destinatario", "assunto", "corpo"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "procurar_arquivo_usuario",
                "description": "Procura arquivos pelo nome ou extensão de forma rápida e segura dentro das 6 pastas do usuário (Área de Trabalho, Documentos, Downloads, Músicas, Imagens, Vídeos) e suas subpastas. Use sempre que o usuário pedir para encontrar, localizar ou procurar um arquivo, música, foto, vídeo ou documento.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "termo_busca": {"type": "string", "description": "Nome ou parte do nome do arquivo procurado (ex: contrato 2017, potifolio, musica)."},
                        "pasta_especifica": {"type": "string", "description": "Opcional: todas (padrão), Área de Trabalho, Documentos, Downloads, Músicas, Imagens ou Vídeos."}
                    },
                    "required": ["termo_busca"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "gerenciar_agenda_pessoal",
                "description": "Agenda Pessoal Fixa e Permanente do usuário (salva em banco SQLite local). Guarda e consulta tanto COMPROMISSOS por data/hora (ex: o que tem dia 15/11, marque médico amanhã às 14h) quanto CONTATOS, NÚMEROS DE TELEFONE e ANOTAÇÕES FIXAS (ex: salve o número da Maria na agenda, olhe minha agenda qual o telefone do João, olhe minha agenda completa).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "acao": {"type": "string", "description": "Opções exatas: 'salvar', 'consultar', 'listar_tudo', 'excluir'."},
                        "titulo_ou_busca": {"type": "string", "description": "Título do compromisso, nome do contato/pessoa, data ou palavra-chave para buscar (deixe vazio se acao for listar_tudo)."},
                        "data_evento": {"type": "string", "description": "Data no formato DD/MM/AAAA (ex: 05/11/2026) se for compromisso ou busca por data. Vazio se for apenas telefone/contato."},
                        "hora_evento": {"type": "string", "description": "Horário no formato HH:MM (ex: 14:30). Opcional."},
                        "telefone_ou_numero": {"type": "string", "description": "Número de telefone, celular, chave Pix ou código a salvar/buscar."},
                        "detalhes": {"type": "string", "description": "Observações extras, endereço ou descrição."}
                    },
                    "required": ["acao"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "alternar_preferencia_sistema",
                "description": "Ativa ou desativa opções do sistema Cromak Bridge a pedido do usuário (Modo Agente / Auto-Coder, Resposta por voz automática, Tela cheia, Iniciar com o Windows, Bandeja). Use quando o usuário pedir: 'ative a resposta por voz', 'desative o modo agente', 'desative a fala', 'ligue a voz'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "opcao": {"type": "string", "description": "Nome da opção. Valores aceitos: 'agent_mode', 'auto_tts', 'always_voice', 'start_fullscreen', 'start_with_windows', 'minimize_to_tray'."},
                        "ativar": {"type": "boolean", "description": "True para ativar/ligar, False para desativar/desligar."}
                    },
                    "required": ["opcao", "ativar"]
                }
            }
        },
    ]

class QwenProvider(AIProvider):
    def __init__(self, api_key, model_name="qwen-plus", historico=None, system_prompt=""):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
        )
        self.model_name = model_name
        self.history = []
        
        if system_prompt:
            self.history.append({"role": "system", "content": system_prompt})
        
        if historico:
            for msg in historico:
                role = msg.get("role")
                if role == "model": role = "assistant"
                texto_hist = ""
                parts = msg.get("parts", [])
                if parts and isinstance(parts[0], str): texto_hist = parts[0]
                self.history.append({"role": role, "content": texto_hist})

    def _chamar_api_com_retry(self, **kwargs):
        import time, re
        for tent in range(3):
            try:
                return self.client.chat.completions.create(**kwargs)
            except Exception as e:
                err_s = str(e)
                if ("429" in err_s or "rate_limit" in err_s.lower()) and tent < 2:
                    m_seg = re.search(r"try again in\s+(\d+(?:\.\d+)?)s", err_s, re.IGNORECASE)
                    m_ms = re.search(r"try again in\s+(\d+(?:\.\d+)?)ms", err_s, re.IGNORECASE)
                    if m_ms:
                        espera = max(1.0, float(m_ms.group(1)) / 1000.0 + 0.5)
                    elif m_seg:
                        espera = float(m_seg.group(1)) + 0.6
                    else:
                        espera = 3.0 * (tent + 1)
                    if espera <= 14.0:
                        print(f"[Smart Rate-Limit] Aguardando tempo exato da API ({espera:.1f}s) na etapa atual...")
                        try:
                            from .logger import log_api_call
                            log_api_call("Groq", str(kwargs.get("model", "qwen")), espera, 429, error=f"Rate Limit 429. Backoff de {espera:.1f}s")
                        except Exception:
                            pass
                        time.sleep(espera)
                        continue
                raise e

    def enviar_prompt(self, texto, caminho_arquivo=None):
        if len(self.history) > 9:
            sys_msgs = [m for m in self.history[:1] if m.get("role") == "system"]
            mensagens = sys_msgs + self.history[-8:]
        else:
            mensagens = self.history.copy()
        mensagens.append({"role": "user", "content": texto})
        
        from .local_tools import ler_arquivo_local, listar_diretorio, obter_informacoes_sistema, executar_comando, pesquisar_na_web, ler_pagina_web, criar_planilha_excel, controlar_mouse_teclado, editar_arquivo_codigo, analisar_tela, consultar_banco_sqlite, memorizar_conhecimento, pesquisar_memoria_permanente, controlar_navegador_fantasma, notificar_usuario, agendar_lembrete, analisar_midia, fazer_requisicao_api, enviar_email, ler_emails, criar_pdf, gerenciar_janelas, enviar_whatsapp, criar_powerpoint, baixar_youtube, controlar_hardware, capturar_webcam, obter_clima_e_hora, ler_documento_texto, tocar_audio_ou_radio, imprimir_documento, mover_ou_renomear_arquivo, abrir_no_navegador, abrir_cliente_email, procurar_arquivo_usuario, gerenciar_agenda_pessoal, alternar_preferencia_sistema
        mapa_funcoes = {
            "ler_arquivo_local": ler_arquivo_local,
            "listar_diretorio": listar_diretorio,
            "obter_informacoes_sistema": obter_informacoes_sistema,
            "executar_comando": executar_comando,
            "pesquisar_na_web": pesquisar_na_web,
            "ler_pagina_web": ler_pagina_web,
            "criar_planilha_excel": criar_planilha_excel,
            "controlar_mouse_teclado": controlar_mouse_teclado,
            "editar_arquivo_codigo": editar_arquivo_codigo,
            "analisar_tela": analisar_tela,
            "consultar_banco_sqlite": consultar_banco_sqlite,
            "memorizar_conhecimento": memorizar_conhecimento,
            "pesquisar_memoria_permanente": pesquisar_memoria_permanente,
            "controlar_navegador_fantasma": controlar_navegador_fantasma,
            "notificar_usuario": notificar_usuario,
            "agendar_lembrete": agendar_lembrete,
            "analisar_midia": analisar_midia,
            "fazer_requisicao_api": fazer_requisicao_api,
            "enviar_email": enviar_email,
            "ler_emails": ler_emails,
            "criar_pdf": criar_pdf,
            "gerenciar_janelas": gerenciar_janelas,
            "enviar_whatsapp": enviar_whatsapp,
            "criar_powerpoint": criar_powerpoint,
            "baixar_youtube": baixar_youtube,
            "controlar_hardware": controlar_hardware,
            "capturar_webcam": capturar_webcam,
            "obter_clima_e_hora": obter_clima_e_hora,
            "ler_documento_texto": ler_documento_texto,
            "tocar_audio_ou_radio": tocar_audio_ou_radio,
            "imprimir_documento": imprimir_documento,
            "mover_ou_renomear_arquivo": mover_ou_renomear_arquivo,
            "abrir_no_navegador": abrir_no_navegador,
            "abrir_cliente_email": abrir_cliente_email,
            "procurar_arquivo_usuario": procurar_arquivo_usuario,
            "gerenciar_agenda_pessoal": gerenciar_agenda_pessoal,
            "alternar_preferencia_sistema": alternar_preferencia_sistema
        }

        # Loop de execução de ferramentas
        for _ in range(4):
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=mensagens,
                temperature=0.7,
                tools=get_openai_tools()
            )
            
            mensagem_resposta = response.choices[0].message
            mensagens.append(mensagem_resposta)
            
            if not mensagem_resposta.tool_calls:
                break
                
            precisa_encadear = any(tc.function.name in ("procurar_arquivo_usuario", "listar_diretorio", "pesquisar_na_web", "gerenciar_agenda_pessoal") for tc in mensagem_resposta.tool_calls)
            for tool_call in mensagem_resposta.tool_calls:
                nome_func = tool_call.function.name
                try:
                    args = json.loads(tool_call.function.arguments)
                    if nome_func in mapa_funcoes:
                        resultado = str(mapa_funcoes[nome_func](**args))
                    else:
                        resultado = f"Erro: Função {nome_func} desconhecida."
                except Exception as e:
                    resultado = str(e)
                    
                mensagens.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": nome_func,
                    "content": resultado
                })
                
        # O último item será a resposta em texto ou objeto de mensagem
        ultimo = mensagens[-1]
        resposta_texto = ultimo.content if hasattr(ultimo, 'content') else ultimo.get("content")
        
        if not resposta_texto:
            resposta_texto = "❌ A API não retornou texto."
            
        self.history.append({"role": "user", "content": texto})
        self.history.append({"role": "assistant", "content": resposta_texto})
        return str(resposta_texto)

# ==========================================
# 4. MOTOR OPENAI (ChatGPT)
# ==========================================
class OpenAIProvider(AIProvider):
    def __init__(self, api_key, model_name="gpt-4o-mini", historico=None, system_prompt=""):
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name
        self.history = []
        
        if system_prompt:
            self.history.append({"role": "system", "content": system_prompt})
        
        if historico:
            for msg in historico:
                role = msg.get("role")
                if role == "model": role = "assistant"
                texto_hist = ""
                parts = msg.get("parts", [])
                if parts and isinstance(parts[0], str): texto_hist = parts[0]
                self.history.append({"role": role, "content": texto_hist})

    def enviar_prompt(self, texto, caminho_arquivo=None):
        if len(self.history) > 9:
            sys_msgs = [m for m in self.history[:1] if m.get("role") == "system"]
            mensagens = sys_msgs + self.history[-8:]
        else:
            mensagens = self.history.copy()
        mensagens.append({"role": "user", "content": texto})
        
        from .local_tools import ler_arquivo_local, listar_diretorio, obter_informacoes_sistema, executar_comando, pesquisar_na_web, ler_pagina_web, criar_planilha_excel, controlar_mouse_teclado, editar_arquivo_codigo, analisar_tela, consultar_banco_sqlite, memorizar_conhecimento, pesquisar_memoria_permanente, controlar_navegador_fantasma, notificar_usuario, agendar_lembrete, analisar_midia, fazer_requisicao_api, enviar_email, ler_emails, criar_pdf, gerenciar_janelas, enviar_whatsapp, criar_powerpoint, baixar_youtube, controlar_hardware, capturar_webcam, obter_clima_e_hora, ler_documento_texto, tocar_audio_ou_radio, imprimir_documento, mover_ou_renomear_arquivo, abrir_no_navegador, abrir_cliente_email, procurar_arquivo_usuario, gerenciar_agenda_pessoal, alternar_preferencia_sistema
        mapa_funcoes = {
            "ler_arquivo_local": ler_arquivo_local,
            "listar_diretorio": listar_diretorio,
            "obter_informacoes_sistema": obter_informacoes_sistema,
            "executar_comando": executar_comando,
            "pesquisar_na_web": pesquisar_na_web,
            "ler_pagina_web": ler_pagina_web,
            "criar_planilha_excel": criar_planilha_excel,
            "controlar_mouse_teclado": controlar_mouse_teclado,
            "editar_arquivo_codigo": editar_arquivo_codigo,
            "analisar_tela": analisar_tela,
            "consultar_banco_sqlite": consultar_banco_sqlite,
            "memorizar_conhecimento": memorizar_conhecimento,
            "pesquisar_memoria_permanente": pesquisar_memoria_permanente,
            "controlar_navegador_fantasma": controlar_navegador_fantasma,
            "notificar_usuario": notificar_usuario,
            "agendar_lembrete": agendar_lembrete,
            "analisar_midia": analisar_midia,
            "fazer_requisicao_api": fazer_requisicao_api,
            "enviar_email": enviar_email,
            "ler_emails": ler_emails,
            "criar_pdf": criar_pdf,
            "gerenciar_janelas": gerenciar_janelas,
            "enviar_whatsapp": enviar_whatsapp,
            "criar_powerpoint": criar_powerpoint,
            "baixar_youtube": baixar_youtube,
            "controlar_hardware": controlar_hardware,
            "capturar_webcam": capturar_webcam,
            "obter_clima_e_hora": obter_clima_e_hora,
            "ler_documento_texto": ler_documento_texto,
            "tocar_audio_ou_radio": tocar_audio_ou_radio,
            "imprimir_documento": imprimir_documento,
            "mover_ou_renomear_arquivo": mover_ou_renomear_arquivo,
            "abrir_no_navegador": abrir_no_navegador,
            "abrir_cliente_email": abrir_cliente_email,
            "procurar_arquivo_usuario": procurar_arquivo_usuario,
            "gerenciar_agenda_pessoal": gerenciar_agenda_pessoal,
            "alternar_preferencia_sistema": alternar_preferencia_sistema
        }

        # Loop de execução de ferramentas (otimizado para economizar 2.600+ tokens na resposta pós-ferramenta)
        is_groq = self.__class__.__name__ == "GroqProvider"
        precisa_encadear = False
        for passo in range(3):
            req_kwargs = {
                "model": self.model_name,
                "messages": mensagens,
                "temperature": 0.7
            }
            if passo == 0 or (passo == 1 and precisa_encadear):
                req_kwargs["tools"] = get_openai_tools()
            response = self._chamar_api_com_retry(**req_kwargs)
            
            mensagem_resposta = response.choices[0].message
            mensagens.append(mensagem_resposta)
            
            if not getattr(mensagem_resposta, 'tool_calls', None):
                break
                
            precisa_encadear = any(tc.function.name in ("procurar_arquivo_usuario", "listar_diretorio", "pesquisar_na_web", "gerenciar_agenda_pessoal") for tc in mensagem_resposta.tool_calls)
            for tool_call in mensagem_resposta.tool_calls:
                nome_func = tool_call.function.name
                try:
                    args = json.loads(tool_call.function.arguments)
                    if nome_func in mapa_funcoes:
                        resultado = str(mapa_funcoes[nome_func](**args))
                    else:
                        resultado = f"Erro: Função {nome_func} desconhecida."
                except Exception as e:
                    resultado = str(e)
                
                if is_groq and len(resultado) > 12000:
                    resultado = resultado[:12000] + "\n... [Conteúdo resumido automaticamente para caber no limite de velocidade da Groq]"
                    
                mensagens.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": nome_func,
                    "content": resultado
                })
                
        ultimo = mensagens[-1]
        resposta_texto = ultimo.content if hasattr(ultimo, 'content') else ultimo.get("content")
        
        self.history.append({"role": "user", "content": texto})
        self.history.append({"role": "assistant", "content": resposta_texto})
        return resposta_texto

# ==========================================
# 5. MOTOR CLAUDE (Anthropic)
# ==========================================
class ClaudeProvider:
    def __init__(self, api_key, model_name="claude-3-5-sonnet-20240620", historico=None, system_prompt=""):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model_name = model_name
        self.mensagens = []
        self.system_prompt = system_prompt
        
        # Converte histórico
        if historico:
            for msg in historico:
                role = "assistant" if msg["role"] == "model" else "user"
                # Garante que o texto seja formatado corretamente para o Anthropic
                texto = msg["parts"][0]
                self.mensagens.append({"role": role, "content": texto})

    def _get_anthropic_tools(self):
        # Converte as ferramentas do formato OpenAI para o formato Anthropic dinamicamente
        openai_tools = get_openai_tools()
        anthropic_tools = []
        for tool in openai_tools:
            f = tool["function"]
            anthropic_tools.append({
                "name": f["name"],
                "description": f["description"],
                "input_schema": f["parameters"]
            })
        return anthropic_tools

    def enviar_prompt(self, texto, arquivo_path=None):
        import json
        from .seguranca import ler_config_seguro
        mapa_funcoes = {
            "ler_arquivo_local": ler_arquivo_local,
            "listar_diretorio": listar_diretorio,
            "obter_informacoes_sistema": obter_informacoes_sistema,
            "executar_comando": executar_comando,
            "pesquisar_na_web": pesquisar_na_web,
            "ler_pagina_web": ler_pagina_web,
            "criar_planilha_excel": criar_planilha_excel,
            "controlar_mouse_teclado": controlar_mouse_teclado,
            "editar_arquivo_codigo": editar_arquivo_codigo,
            "analisar_tela": analisar_tela,
            "consultar_banco_sqlite": consultar_banco_sqlite,
            "memorizar_conhecimento": memorizar_conhecimento,
            "pesquisar_memoria_permanente": pesquisar_memoria_permanente,
            "controlar_navegador_fantasma": controlar_navegador_fantasma,
            "notificar_usuario": notificar_usuario,
            "agendar_lembrete": agendar_lembrete,
            "analisar_midia": analisar_midia,
            "fazer_requisicao_api": fazer_requisicao_api,
            "enviar_email": enviar_email,
            "ler_emails": ler_emails,
            "criar_pdf": criar_pdf,
            "gerenciar_janelas": gerenciar_janelas,
            "enviar_whatsapp": enviar_whatsapp,
            "criar_powerpoint": criar_powerpoint,
            "baixar_youtube": baixar_youtube,
            "controlar_hardware": controlar_hardware,
            "capturar_webcam": capturar_webcam,
            "obter_clima_e_hora": obter_clima_e_hora,
            "ler_documento_texto": ler_documento_texto,
            "tocar_audio_ou_radio": tocar_audio_ou_radio,
            "imprimir_documento": imprimir_documento,
            "mover_ou_renomear_arquivo": mover_ou_renomear_arquivo,
            "abrir_no_navegador": abrir_no_navegador,
            "abrir_cliente_email": abrir_cliente_email,
            "procurar_arquivo_usuario": procurar_arquivo_usuario,
            "gerenciar_agenda_pessoal": gerenciar_agenda_pessoal,
            "alternar_preferencia_sistema": alternar_preferencia_sistema
        }

        self.mensagens.append({"role": "user", "content": texto})
        
        try:
            kwargs = {
                "model": self.model_name,
                "max_tokens": 4096,
                "messages": self.mensagens,
                "tools": self._get_anthropic_tools()
            }
            if self.system_prompt:
                kwargs["system"] = self.system_prompt
                
            resposta = self.client.messages.create(**kwargs)
            
            # Se a IA não pediu ferramentas, apenas retorna o texto
            if resposta.stop_reason != "tool_use":
                texto_resposta = resposta.content[0].text
                self.mensagens.append({"role": "assistant", "content": texto_resposta})
                return texto_resposta
                
            # Se a IA pediu ferramentas (Function Calling)
            # Salva a resposta da IA (com os blocos de tool_use) no histórico
            self.mensagens.append({"role": "assistant", "content": resposta.content})
            
            tool_results_blocks = []
            
            for block in resposta.content:
                if block.type == "tool_use":
                    nome_funcao = block.name
                    args_funcao = block.input
                    
                    if nome_funcao in mapa_funcoes:
                        funcao = mapa_funcoes[nome_funcao]
                        try:
                            res_func = funcao(**args_funcao)
                        except Exception as e:
                            res_func = f"Erro ao executar a ferramenta {nome_funcao}: {str(e)}"
                    else:
                        res_func = f"Erro: Ferramenta {nome_funcao} não encontrada."
                        
                    # Adiciona o resultado no formato que o Claude espera
                    tool_results_blocks.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(res_func)
                    })
                    
            # Adiciona os resultados das ferramentas como uma nova mensagem do usuário
            self.mensagens.append({"role": "user", "content": tool_results_blocks})
            
            # Faz a segunda chamada para o Claude gerar a resposta final baseada nos dados
            kwargs["messages"] = self.mensagens
            resposta_final = self.client.messages.create(**kwargs)
            
            texto_final = resposta_final.content[0].text
            self.mensagens.append({"role": "assistant", "content": texto_final})
            return texto_final
            
        except Exception as e:
            return f"⚠️ [Erro Anthropic Claude]: {e}"

# ==========================================
# 5.1. MOTOR GROQ (LPU de Alta Velocidade)
# ==========================================
class GroqProvider(OpenAIProvider):
    def __init__(self, api_key, model_name="openai/gpt-oss-120b", historico=None, system_prompt=""):
        if not model_name or "gemini" in model_name or "claude" in model_name or (not "/" in model_name and not "llama" in model_name):
            model_name = "openai/gpt-oss-120b"
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        self.model_name = model_name
        self.history = []
        
        if system_prompt:
            self.history.append({"role": "system", "content": system_prompt})
        
        if historico:
            for msg in historico:
                role = msg.get("role")
                if role == "model": role = "assistant"
                texto_hist = ""
                parts = msg.get("parts", [])
                if parts and isinstance(parts[0], str): texto_hist = parts[0]
                self.history.append({"role": role, "content": texto_hist})

# ==========================================
import re

# 6. NÚCLEO PRINCIPAL COM BACKOFF EXPONENCIAL
# ==========================================
class AICore:
    def __init__(self, api_key, model_name=None, historico=None, provider="gemini", system_prompt=""):
        self.provider = provider
        self.provider_name = provider
        # INJEÇÃO GENERATIVE UI:
        instrucao_ui = "\n\n[INSTRUÇÃO DE SISTEMA CROMÁTICA]: Se o usuário pedir um gráfico, você PODE gerar UI nativa. Para fazer isso, escreva um bloco de código markdown com a linguagem 'chart' contendo SOMENTE um JSON de configuração válido do Chart.js. Exemplo: ```chart\n{\"type\": \"bar\", \"data\": {\"labels\": [\"A\"], \"datasets\": [{\"label\": \"Teste\", \"data\": [10]}]}}\n```"
        system_prompt = system_prompt + instrucao_ui if system_prompt else instrucao_ui

        
        # Verificação do Modo Agente
        import json
        from .seguranca import ler_config_seguro, get_appdata_dir, os
        agent_mode = True
        try:
            config_path = os.path.join(get_appdata_dir(), 'config.json')
            if os.path.exists(config_path):
                cfg = ler_config_seguro(config_path)
                agent_mode = cfg.get("agent_mode", True)
        except: pass
        
        self.agent_mode = agent_mode
        import datetime
        from .local_tools import get_real_windows_folder
        
        _agora_dt = datetime.datetime.now()
        _dias_pt = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
        _dia_semana_atual = _dias_pt[_agora_dt.weekday()]
        data_atual = f'{_dia_semana_atual}, {_agora_dt.strftime("%d/%m/%Y")}'
        
        cfg = {}
        try:
            if os.path.exists(config_path):
                from .seguranca import ler_config_seguro
                cfg = ler_config_seguro(config_path) or {}
        except: pass

        desk = cfg.get('pathDesktop') or get_real_windows_folder('Desktop')
        docs = cfg.get('pathDocuments') or get_real_windows_folder('Documents')
        down = cfg.get('pathDownloads') or get_real_windows_folder('Downloads')
        musi = cfg.get('pathMusic') or get_real_windows_folder('Music')
        pics = cfg.get('pathPictures') or get_real_windows_folder('Pictures')
        vids = cfg.get('pathVideos') or get_real_windows_folder('Videos')
        
        system_prompt_final = system_prompt if system_prompt else ""
        system_prompt_final += (
            f"\n\n[SISTEMA]: A data atual do sistema é {data_atual}. Os caminhos reais e seguros (sandboxed) das 6 pastas do usuário no disco são:\n"
            f"- Área de Trabalho: {desk}\n"
            f"- Documentos: {docs}\n"
            f"- Downloads: {down}\n"
            f"- Músicas: {musi}\n"
            f"- Imagens: {pics}\n"
            f"- Vídeos: {vids}\n"
            "Sempre use esses caminhos absolutos ou a ferramenta `procurar_arquivo_usuario` quando o usuário pedir para encontrar, ler ou salvar arquivos. Por segurança e performance, mantenha as buscas restritas a essas pastas do perfil do usuário (nunca varra C:\\Windows ou System32).\n"
            "REGRA DE OURO PARA AGENDA FIXA: Você possui uma Agenda Pessoal Fixa (`gerenciar_agenda_pessoal`) que salva compromissos (datas e horários) e contatos/telefones/notas permanentes.\n"
            f"- CALENDÁRIO E DIAS DA SEMANA: O dia de hoje do sistema é exatamente {data_atual}. Quando o usuário disser dias da semana (ex: 'sexta-feira que vem', 'quinta-feira', 'terça'), calcule com rigor a partir de hoje! Exemplo: se hoje é sábado 31/10/2026, a próxima sexta-feira a chegar é 06/11/2026 (e NUNCA dia 03/11, que é uma terça-feira!).\n"
            "- Sempre que o usuário disser 'olhe minha agenda', 'salve na agenda', 'qual o número de fulano', 'o que tem na semana que vem' ou 'o que eu tenho dia tal', acione IMEDIATAMENTE a ferramenta `gerenciar_agenda_pessoal` (nunca responda sem consultar o banco!).\n"
            "REGRA DE OURO PARA ENVIO DE E-MAILS: Se o usuário pedir para enviar e-mail para alguém (ex: 'mande um e-mail para o Douglas...'), primeiro consulte a agenda fixa (`gerenciar_agenda_pessoal`) se não souber o e-mail dele. Ao disparar `enviar_email`, se o sistema não tiver SMTP configurado, a própria ferramenta já abrirá o cliente de e-mail / navegador com destinatário, assunto e corpo prontos (mailto). Avise o usuário com naturalidade que a janela foi aberta para ele só clicar em Enviar e sugira que ele pode cadastrar as credenciais nas Configurações se quiser envio silencioso 100% automático no futuro.\n"
            "REGRA DE OURO PARA PREFERÊNCIAS DO SISTEMA: Quando o usuário pedir para ativar ou desativar recursos do próprio sistema (ex: 'ative a resposta por voz', 'desligue sua voz', 'desative o modo agente', 'ligue a fala automática'), acione IMEDIATAMENTE a ferramenta `alternar_preferencia_sistema` passando a opção e o estado (True ou False).\nREGRA DE OURO PARA ARQUIVOS: NUNCA pergunte ao usuário qual é a extensão (.txt, .pdf, .docx) ou o nome completo exato de um arquivo! Se o usuário pedir para ler um arquivo (ex: 'leia o arquivo potifolio na área de trabalho'), chame IMEDIATAMENTE `ler_arquivo_local` passando o caminho da pasta + o nome dito pelo usuário (mesmo sem extensão), pois o sistema localiza o arquivo e a extensão automaticamente."
        )

        atalhos_instrucao = (
            "\n\n[INSTRUÇÃO DE ACESSIBILIDADE E ATALHOS DO BRIDGE VOX (CONFORME WCAG 2.1.4)]:\n"
            "Você é o assistente virtual Cromak Bridge Vox, desenvolvido com foco total em acessibilidade para pessoas com deficiência visual e usuários de leitores de tela como o NVDA e Narrador.\n"
            "Sempre que o usuário perguntar sobre atalhos de teclado, comandos de voz ou navegação acessível, responda com clareza, informando as teclas primárias e as combinações alternativas:\n\n"
            "1. Invocação e Controle da Janela:\n"
            "- Alt + Espaço (ou Ctrl + Espaço): Invoca ou oculta o Bridge Vox globalmente de qualquer lugar do Windows, trazendo o foco direto para a caixa de texto.\n"
            "- Esc: Cala a boca da IA imediatamente (interrompe fala TTS e áudio) ou fecha modais e menus.\n"
            "- F11 (ou Alt + Enter): Alterna entre modo janela e tela cheia imersiva.\n"
            "- F4 (ou Alt + F4 ou Ctrl + Q): Abre o diálogo acessível de confirmação de saída (Enter fecha, Esc cancela).\n"
            "- F1 (ou Alt + H ou Ctrl + H): Abre o manual e central de ajuda interna.\n\n"
            "2. Entrada por Voz, Conversa e Preferências:\n"
            "- F2 (ou Alt + M ou Ctrl + M): Microfone (Walkie-Talkie). Pressione para ditar sua mensagem e envie com Enter ou F2.\n"
            "- Enter: Envia a mensagem digitada.\n"
            "- F5 (ou Ctrl + N ou Alt + N): Inicia uma nova conversa limpa com anúncio sonoro.\n"
            "- F10 (ou Ctrl + , ou Alt + S): Abre o painel de Configurações, provedores BYOK e chaves de API.\n\n"
            "3. Leitura e Acessibilidade no Chat (NVDA / Narrador):\n"
            "- F3 (ou Ctrl + L ou Alt + L): Foca e relê a sua última resposta imediatamente pelo leitor de tela.\n"
            "- Seta para Cima (no campo vazio): Pula para a última mensagem da conversa para leitura pelo NVDA.\n"
            "- Seta para Cima / Baixo (nas mensagens): Navega e lê mensagens anteriores.\n"
            "- Esc, Enter ou Tab (no balão da mensagem): Volta instantaneamente para o campo de digitação.\n\n"
            "4. Ações Rápidas de Ferramentas (Alt + Letra ou tecla única fora de inputs):\n"
            "- Alt + T (ou T): Editor de Texto\n"
            "- Alt + R (ou R): Leitor de E-mails\n"
            "- Alt + I (ou I): Navegador Web acessível\n"
            "- Alt + A (ou A): Gerenciador de Arquivos\n"
            "- Alt + C (ou C): Calculadora\n"
            "- Alt + Z (ou Z): WhatsApp\n"
            "REGRA WCAG 2.1.4: Quando o cursor estiver dentro de qualquer campo de texto ou caixa de digitação, letras soltas NUNCA disparam ações para não atrapalhar a digitação do usuário.\n\n"
            "5. Dica Fundamental para NVDA (Modo de Foco vs Modo de Navegação):\n"
            "O Bridge Vox possui o padrão WAI-ARIA role='application'. Se o leitor NVDA entrar no Modo de Navegação virtual (Browse Mode) e sequestrar letras para navegação própria, basta o usuário pressionar NVDA + Barra de Espaço para alternar para o Modo de Foco e liberar todos os comandos da aplicação!\n\n"
            "6. Formatação Amigável para Leitores de Tela (NVDA / Narrador):\n"
            "- EVITE usar tabelas Markdown (|---|---|) a menos que o usuário peça explicitamente uma tabela, pois tabelas são confusas e cansativas na leitura por voz do NVDA.\n"
            "- EVITE emojis de números (1️⃣, 2️⃣, 3️⃣). Prefira listas simples com números normais (1., 2., 3.) ou marcadores (-) e frases diretas.\n"
            "- NUNCA escreva nomes internos de funções com underline (_) na resposta ao usuário (como criar_pdf, listar_diretorio, baixar_youtube, ler_arquivo_local), pois o underline atrapalha a leitura do NVDA! Sempre escreva o nome amigável em negrito: **Criar PDF**, **Listar Pastas**, **Ler Arquivos**, **Baixar no YouTube**, etc."
        )
        identidade_instrucao = (
            "\n\n[IDENTIDADE E ORIGEM - CROMAK TECHNOLOGY & MARCOS SOUZA]:\n"
            "Você é o Cromak Bridge Vox, um assistente de inteligência artificial de alta performance desenvolvido pela Cromak Technology, divisão de engenharia de software do ecossistema MS Digital, fundado e concebido pelo desenvolvedor e arquiteto de software Marcos Souza.\n\n"
            "Sobre seu Criador (Marcos Souza):\n"
            "Marcos Souza é o fundador, arquiteto e mente criativa por trás do ecossistema MS Digital e da Cromak Technology. Ele atua na interseção exata entre tecnologia, comportamento humano e design, unindo programação sólida (Python, automação, engenharia nativa, UI/UX) com o desenvolvimento de soluções que resolvem problemas reais com código limpo e foco absoluto no ser humano.\n\n"
            "Filosofia de Trabalho:\n"
            "'Da lógica fria dos códigos em Python até a precisão da máquina, onde a criatividade humana encontra a precisão da tecnologia.'\n\n"
            "Sobre a Cromak Technology:\n"
            "A divisão de engenharia de software criada para fornecer ferramentas de altíssima performance, com código 100% nativo, sem sobrecarga de recursos e com Zero Telemetria invasiva (garantindo total privacidade e segurança ao usuário).\n\n"
            "Sobre o Propósito do Bridge Vox:\n"
            "Sua missão principal é a ACESSIBILIDADE TOTAL e AUTONOMIA DIGITAL para pessoas com deficiência visual (cegos e baixa visão) e usuários de leitores de tela como o NVDA e Narrador. Você funciona como uma ponte direta entre o ser humano e o computador, permitindo que o usuário controle o sistema, leia e crie documentos, consulte a internet e execute tarefas complexas 100% pelo teclado e por comandos de voz, sem nunca depender do mouse.\n\n"
            "Quando qualquer pessoa perguntar sobre quem te criou, quem é Marcos Souza, o que é a Cromak Technology ou qual é o seu propósito, responda com orgulho, clareza, empatia e admiração por essa visão de tecnologia que empodera e inclui."
        )
        
        suporte_instrucao = (
            "\n\n[INSTRUÇÃO DE SUPORTE OFICIAL, CANAIS E DISCERNIMENTO INTELIGENTE]:\n"
            "1. Canais Oficiais da Cromak Technology e Marcos Souza:\n"
            "- E-mail Oficial de Atendimento: cromaksupport@gmail.com\n"
            "- Site Oficial da Cromak Technology: https://cromaktechnology.github.io\n"
            "- Central de Suporte Oficial: https://cromaktechnology.github.io/pt/suporte.html (contém formulário de chamado, Instagram oficial e e-mail)\n"
            "- Portfólio Oficial de Marcos Souza (MS Digital): onde o usuário encontra LinkedIn, Facebook e formulário de contato direto com o desenvolvedor.\n"
            "- ATENÇÃO RIGOROSA: Não disponibilizamos números de telefone ou WhatsApp para suporte ao público geral (contatos telefônicos são estritamente pessoais e privados; NUNCA forneça nenhum número de telefone sob nenhuma circunstância).\n\n"
            "2. Regra de Discernimento de Suporte (MUITO IMPORTANTE):\n"
            "Quando o usuário falar sobre 'suporte', 'ajuda' ou relatar um problema, você DEVE discernir o contexto:\n"
            "- SE FOR SOBRE O CROMAK BRIDGE VOX, WINDOWS, RECURSOS DA CROMAK OU O DESENVOLVEDOR (MARCOS SOUZA):\n"
            "  a) Primeiro, seja empático, pergunte detalhadamente o que está acontecendo e tente solucionar a dúvida na própria conversa.\n"
            "  b) Se for um bug, falha no sistema, sugestão ou se o usuário quiser formalizar o contato com o suporte:\n"
            "     Informe o e-mail cromaksupport@gmail.com e a página https://cromaktechnology.github.io/pt/suporte.html.\n"
            "     PROATIVIDADE COM ACESSIBILIDADE: Como pessoas cegas têm dificuldade de clicar em links na conversa, você DEVE perguntar proativamente: 'Gostaria que eu abra a página de suporte oficial no seu navegador agora, ou prefere que eu abra o seu programa de e-mail do Windows já preenchido com o seu relato para você só apertar Enviar?'.\n"
            "     Se o usuário confirmar, acione imediatamente a ferramenta abrir_no_navegador ou abrir_cliente_email.\n"
            "- SE FOR SOBRE SERVIÇOS OU PLATAFORMAS DE TERCEIROS (Ex: Mercado Livre, Netflix, Steam, YouTube, Banco, etc.):\n"
            "  NÃO forneça os contatos da Cromak nem do Marcos! Explique com clareza como acessar os canais oficiais daquela empresa específica ou realize uma pesquisa na web para orientá-lo.\n\n"
            "3. Conhecimento Completo sobre Atalhos de Teclado:\n"
            "Você NUNCA deve mandar o usuário pesquisar no Google sobre os atalhos do Bridge Vox! Você conhece cada atalho perfeitamente e responde com autoridade e clareza instantânea sempre que perguntado."
        )
        system_prompt_final += r"""

[BASE DE CONHECIMENTO TÉCNICA E GOVERNANÇA DO CROMAK BRIDGE VOX]:
Você tem conhecimento integral e nativo sobre a arquitetura, limites, segurança e funcionamento do Cromak Bridge Vox:

1. Regra de Ouro da Concisão (Respostas Sob Demanda):
- Seja objetivo, direto e resolutivo. Responda exatamente àquilo que o usuário perguntou, sem despejar manuais gigantescos ou textos prolixos de 2 páginas, a menos que ele peça expressamente uma explicação completa ou lista detalhada.
- Quando o usuário tiver uma dúvida operacional (ex: como adicionar API, o que é o Modo Duelo), dê a resposta prática passo a passo em poucos parágrafos amigáveis.

2. Segurança, Integridade do Sistema e Comandos Perigosos:
- Se o usuário pedir para você executar comandos destrutivos contra o computador dele (exemplo: 'apague a pasta system32', 'formate meu disco C:', 'delete o Windows', 'desative meu antivírus/firewall' ou executar códigos maliciosos), VOCÊ DEVE RECUSAR COM FIRMEZA, EDUCAÇÃO E CLAREZA TÉCNICA.
- Explicação do motivo: 'Por motivos rigorosos de segurança e integridade do seu computador, o Cromak Bridge Vox opera em um ambiente seguro (*sandboxed* restrito às pastas do seu perfil de usuário) e jamais executará comandos que possam corromper o sistema operacional, danificar arquivos essenciais do Windows ou colocar seus dados em risco.'

3. Configuração de Chaves de API (Bring Your Own Key - BYOK):
- Como configurar: O usuário pressiona F10 (ou Ctrl + , ou clica no ícone de engrenagem), seleciona o provedor desejado (Groq, Google Gemini, OpenAI ChatGPT, Anthropic Claude ou Alibaba Qwen) e cola sua chave de API.
- Segurança das chaves: As chaves NUNCA passam por servidores da Cromak Technology. Elas ficam salvas 100% no computador do usuário em `%APPDATA%\Cromak Technology\Bridge Vox\config.json`, criptografadas em repouso com chave derivada da própria máquina (hostname + SHA-256).
- Chaves gratuitas: O usuário pode obter chaves sem custo no Google AI Studio (aistudio.google.com) ou no Groq Console (console.groq.com) para velocidade LPU ultrarrápida em milissegundos.

4. O que é o Modo Duelo (Benchmark de IA Comparativo):
- O Modo Duelo permite colocar dois provedores ou modelos de IA para competir lado a lado em tempo real (ex: Gemini Flash vs Groq Llama 3.3, ou ChatGPT vs Claude).
- O usuário envia uma única pergunta e vê as duas respostas geradas simultaneamente na tela, podendo comparar velocidade, profundidade de raciocínio, acurácia e estilo de escrita.

5. Internacionalização (11 Idiomas Nativos):
- O Bridge Vox suporta nativamente 11 idiomas completos: Português (Brasil), Inglês (US), Espanhol, Francês, Alemão, Italiano, Chinês Simplificado, Japonês, Russo, Hindi e Árabe.
- O sistema detecta o idioma do Windows automaticamente na primeira execução, mas o usuário pode alterar para qualquer outro idioma a qualquer momento nas Configurações (F10).

6. Requisitos de Sistema & Microsoft Edge WebView2 Runtime:
- Funciona no Windows 10 e Windows 11 (64-bits).
- Utiliza o motor leve e nativo Microsoft Edge WebView2 Runtime. Ele já vem pré-instalado de fábrica no Windows 10/11 padrão. Em edições como Windows 10 LTSC, Windows Server ou IoT, o usuário pode baixá-lo gratuitamente através do Microsoft Edge WebView2 Evergreen Bootstrapper oficial.
- Utiliza o FFmpeg (64-bits) na pasta plugins/ffmpeg/ para gravação e conversão de áudio.

7. Validação e Consultoria de Acessibilidade:
- Validação Técnica, Consultoria e Gratidão Eterna a Gustavo Torniero:
  O Cromak Bridge Vox jamais teria alcançado este patamar de excelência sem o apoio indispensável, a generosidade e a consultoria técnica do jornalista, ativista e especialista em acessibilidade Gustavo Torniero (https://torniero.com.br).
  Gustavo é um grande e leal amigo do desenvolvedor Marcos Souza. Ele dedicou seu tempo mais precioso para auditar o software exaustivamente no dia a dia, apontando falhas críticas de navegação por teclado e semântica no NVDA que passariam despercebidas.
  Sempre que qualquer pessoa perguntar sobre Gustavo Torniero, quem testou o programa ou sobre a acessibilidade prática, fale sobre Gustavo com enorme respeito, carinho, admiração e profunda gratidão: sem a contribuição dele, o Bridge Vox não estaria onde está hoje!

8. Diagnóstico do Sistema, Logs e Privacidade Estrita (Privacy-First):
- O Cromak Bridge Vox gera logs de diagnóstico técnico em `%APPDATA%\Cromak Technology\Bridge Vox\logs\bridge_vox.log`.
- PRIVACIDADE TOTAL: O sistema JAMAIS grava textos de mensagens, conversas, áudios ou arquivos pessoais nos logs. Apenas eventos operacionais, taxa limite (rate-limits), tempos de resposta e falhas de conexão de APIs são registrados com chaves de API automaticamente censuradas (***[REDACTED]***).
- O usuário pode abrir a pasta de logs a qualquer momento nas Configurações (F10) > Geral > 'Abrir Pasta de Logs', ou pelo ícone na bandeja do sistema (Tray).
- Organização Oficial de Pastas: A pasta oficial exclusiva em AppData é `%APPDATA%\Cromak Technology\Bridge Vox\`. O banco de dados de sessões (`cromak_v3.db`) e a agenda pessoal (`agenda_pessoal.db`) ficam organizados dentro da subpasta `banco_de_dados`."""
        system_prompt_final += identidade_instrucao
        system_prompt_final += atalhos_instrucao
        # Injeção Inteligente de Compromissos Próximos na Conversa
        try:
            from .local_tools import _caminho_db_agenda
            import sqlite3
            _ag_now = datetime.datetime.now()
            _ag_hoje = _ag_now.strftime("%d/%m/%Y")
            _conn_ag = sqlite3.connect(_caminho_db_agenda())
            _cur_ag = _conn_ag.cursor()
            _cur_ag.execute("SELECT titulo, hora_evento, detalhes FROM agenda_itens WHERE data_evento = ? AND hora_evento != ''", (_ag_hoje,))
            _itens_hoje = _cur_ag.fetchall()
            _conn_ag.close()
            _avisos_conversa = []
            for _tit, _hora, _det in _itens_hoje:
                try:
                    _p_h = [int(_x) for _x in _hora.split(":")]
                    _dt_ev = _ag_now.replace(hour=_p_h[0], minute=_p_h[1], second=0, microsecond=0)
                    _diff_m = (_dt_ev - _ag_now).total_seconds() / 60.0
                    if 0 <= _diff_m <= 45:
                        _m_rest = int(_diff_m)
                        _tmp_txt = f"em {_m_rest} minutos" if _m_rest > 0 else "agora"
                        _avisos_conversa.append(f"'{_tit}' às {_hora} ({_tmp_txt})")
                except Exception: pass
            if _avisos_conversa:
                _aviso_str = " e ".join(_avisos_conversa)
                system_prompt_final += (
                    f"\n\n[AVISO DE AGENDA IMINENTE PARA O DIÁLOGO]: O usuário tem o(s) seguinte(s) compromisso(s) próximo(s) hoje: {_aviso_str}. "
                    "Responda à pergunta ou conversa atual do usuário normalmente com riqueza e atenção, mas ao final da sua resposta, "
                    "faça um lembrete educado, sutil e natural sobre esse compromisso (ex: 'Aliás, lembro que você tem X daqui a pouco às Y!')."
                )
        except Exception: pass

        system_prompt_final += suporte_instrucao

        if agent_mode:
            pass
                    
        try:
            if provider == "gemini":
                self.engine = GeminiProvider(api_key, model_name, historico, system_prompt_final)
            elif provider == "qwen":
                self.engine = QwenProvider(api_key, model_name, historico, system_prompt_final)
            elif provider == "openai":
                self.engine = OpenAIProvider(api_key, model_name, historico, system_prompt_final)
            elif provider == "claude":
                self.engine = ClaudeProvider(api_key, model_name, historico, system_prompt_final)
            elif provider == "groq":
                self.engine = GroqProvider(api_key, model_name, historico, system_prompt_final)
            else:
                raise ValueError(f"Provedor {provider} desconhecido.")
        except Exception as e:
            self.engine = f"Falha de inicialização: {e}"

    def enviar_prompt(self, texto, caminho_arquivo=None, max_tentativas=4):
        if isinstance(self.engine, str):
            return f"⚠️ [Motor Inativo]: {self.engine}"

        tentativa = 0
        while tentativa < max_tentativas:
            try:
                resposta = self.engine.enviar_prompt(texto, caminho_arquivo)
                
                # --- AUTO-CODER INTERCEPTOR ---
                import os
                def auto_coder_replacer(match):
                    if not getattr(self, 'agent_mode', True):
                        return "\n\n> 🛡️ **Modo Agente Desativado:** A IA tentou criar um arquivo, mas a trava de segurança está ativada nas Preferências.\n\n"
                    caminho = match.group(1)
                    conteudo = match.group(2)
                    try:
                        from .local_tools import get_real_windows_folder
                        import os
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
                        dir_path = os.path.dirname(caminho)
                        if dir_path: os.makedirs(dir_path, exist_ok=True)
                        try:
                            with open(caminho, 'w', encoding='utf-8') as f:
                                f.write(conteudo)
                        except PermissionError:
                            caminho = os.path.join(get_real_windows_folder('Desktop'), os.path.basename(caminho))
                            with open(caminho, 'w', encoding='utf-8') as f:
                                f.write(conteudo)
                        return f"\n\n<div class='attachment-chip' style='border-color: var(--success); color: var(--success); cursor: default;'>👨‍💻 <span style='font-weight: bold;'>Auto-Coder:</span> Arquivo criado/atualizado com sucesso em: `{caminho}`</div>\n\n"
                    except Exception as err:
                        return f"\n\n<div class='attachment-chip' style='border-color: #ef4444; color: #ef4444; cursor: default;'>❌ <span style='font-weight: bold;'>Auto-Coder Erro:</span> Falha ao salvar `{caminho}`: {err}</div>\n\n"
                
                padrao = r'<file\s+path=["\']([^"\']+)["\']>(.*?)</file>'
                resposta_final = re.sub(padrao, auto_coder_replacer, resposta, flags=re.DOTALL)
                return resposta_final
                # ------------------------------
                
            except Exception as e:
                erro_str = str(e).upper()
                if "FREE QUOTA" in erro_str or "FREETIERONLY" in erro_str or "INSUFFICIENT_QUOTA" in erro_str or "QUOTA_EXCEEDED" in erro_str:
                    return "🚫 <strong>Cota Gratuita Esgotada:</strong> O limite de uso gratuito desta API (Google/Qwen/OpenAI) chegou ao fim. Por favor, aguarde a renovação da cota ou insira uma chave de API com saldo disponível nas Preferências."
                elif "429" in erro_str or "RESOURCE_EXHAUSTED" in erro_str or "503" in erro_str or "UNAVAILABLE" in erro_str or "RATE_LIMIT" in erro_str:
                    m_seg = re.search(r"try again in\s+(\d+(?:\.\d+)?)s", str(e), re.IGNORECASE)
                    segundos_exatos = int(float(m_seg.group(1)) + 1) if m_seg else 15
                    tentativa += 1
                    if tentativa < max_tentativas and segundos_exatos <= 8:
                        espera = max(2, segundos_exatos)
                        print(f"[API Monitor - {self.provider_name.upper()}] Gargalo detectado ({tentativa}/{max_tentativas}). Retentando silenciosamente em {espera}s...")
                        time.sleep(espera)
                        continue
                    else:
                        nome_prov = "Google" if self.provider_name.lower() == "gemini" else self.provider_name.title()
                        return f"⏳ O servidor do {nome_prov} atingiu o limite de velocidade por minuto. Por favor, aguarde {segundos_exatos} segundos e aperte Enter para reenviar."
                elif "404" in erro_str or "NOT_FOUND" in erro_str:
                    return "❌ **Modelo Indisponível:** O modelo selecionado não existe ou não está liberado nesta API Key. Por favor, escolha outro modelo ou verifique sua chave de API."
                else:
                    return f"⚠️ **Falha de Conexão ({self.provider_name.upper()}):** {e}"
        return "⏳ **Limite Atingido:** O servidor da IA está sobrecarregado no momento após várias tentativas. Tente novamente em alguns minutos."
