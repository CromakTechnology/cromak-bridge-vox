# -*- coding: utf-8 -*-
"""
====================================================================================
CROMAK ONLINE SYNC & PROMO ENGINE - MOTOR PADRÃO DE ATUALIZAÇÃO E OFERTAS
====================================================================================
Módulo universal e reutilizável para todos os softwares da Cromak Technology.
Suporta verificação de versões semânticas (com build), ofertas promocionais em banner
e links dinâmicos de compra/checkout via repositório GitHub Pages da Cromak.

ESTRUTURA DAS PASTAS DO REPOSITÓRIO:
D:\\Users\\Marcos\\Documentos\\GitHub\\CromakTechnology.github.io\\projetos\\
├── software-update/   -> Linha 1: Versão online | Linha 2: URL de download/página
├── software-promo/    -> Linha 1: URL imagem banner | Linha 2: URL destino do banner
├── software-buy/      -> Linha 1: Preço (ex: 49.90) ou URL de checkout | Linha 2: URL checkout (opcional)
└── [slug].txt         -> Arquivo unificado com todas as 5 linhas acima (opcional)
====================================================================================
"""

import os
import sys
import re
import json
import urllib.request
import threading
from datetime import datetime
try:
    from core import i18n as core_i18n
except Exception:
    try:
        import core_i18n
    except Exception:
        core_i18n = None

# Import condicional do PyQt6 (permite rodar em scripts puros ou com interface Qt)
try:
    from PyQt6.QtCore import QObject, pyqtSignal, QUrl, Qt
    from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
    from PyQt6.QtGui import QPixmap, QCursor, QDesktopServices, QIcon
    HAS_PYQT6 = True
except ImportError:
    HAS_PYQT6 = False


# ==================================================================================
# FUNÇÕES UTILITÁRIAS E PARSER SEMÂNTICO
# ==================================================================================

def extrair_tupla_versao(texto):
    """
    Converte strings de versão como '1.6.0', '1.2.1 (Build 2026.10)' ou 'v2.0.1 build 45'
    em uma tupla de inteiros comparável numericamente.
    Exemplo: '1.2.1 (Build 2026.10)' -> (1, 2, 1, 2026, 10)
    """
    if not texto:
        return (0,)
    
    # Extrai a versão principal (ex: 1.2.1 ou 1.0)
    v_match = re.search(r'(\d+)\.(\d+)(?:\.(\d+))?', str(texto))
    # Extrai o build se existir (ex: Build 2026.10 ou build 450)
    b_match = re.search(r'build\s*(\d+(?:\.\d+)?)', str(texto), re.IGNORECASE)
    
    versao = [int(x) for x in v_match.groups() if x is not None] if v_match else [0]
    build = [int(x) for x in b_match.group(1).split('.')] if b_match else []
    return tuple(versao + build)


# ==================================================================================
# MOTOR PRINCIPAL DE COMUNICACAO ONLINE (UNIVERSAL)
# ==================================================================================

class CromakOnlineSync:
    """
    Gerenciador unificado de sincronização remota para produtos da Cromak Technology.
    
    Sincroniza automaticamente a partir das pastas oficiais do repositório:
      - software-update: versão atualizada e link de download
      - software-promo: banner promocional e link de destino
      - software-buy: preço dinâmico e link de compra
    """

    RAW_GITHUB_BASE = "https://raw.githubusercontent.com/CromakTechnology/CromakTechnology.github.io/main/projetos"
    PAGES_GITHUB_BASE = "https://cromaktechnology.github.io/projetos"
    LOCAL_REPO_DIR = r"D:\Users\Marcos\Documentos\GitHub\CromakTechnology.github.io\projetos"

    def __init__(self, nome_programa="Cromak Software", url_config="", url_update="", url_promo="", url_buy="", site_fallback="https://cromaktechnology.github.io"):
        self.nome_programa = nome_programa
        self.url_config = url_config
        self.url_update = url_update
        self.url_promo = url_promo
        self.url_buy = url_buy
        self.site_fallback = site_fallback
        self.user_agent = f"CromakSyncClient/{nome_programa.replace(' ', '')}"
        self._parsed_config = None

    def _obter_slugs_candidatos(self):
        """Gera slugs padronizados a partir do nome do programa."""
        base = self.nome_programa.lower().strip()
        slug_hifen = re.sub(r'[^a-z0-9]+', '-', base).strip('-')
        slug_underline = slug_hifen.replace('-', '_')
        slug_sem_espaco = slug_hifen.replace('-', '')
        
        candidatos = [slug_hifen, slug_underline, slug_sem_espaco]
        if "suite" in slug_hifen:
            candidatos.append(slug_hifen.replace("-suite", ""))
        return list(dict.fromkeys(candidatos))

    def _obter_caminho_cache(self):
        """Retorna o caminho permanente em %APPDATA%/Cromak Technology/<Programa>/online_sync.json"""
        appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
        pasta = os.path.join(appdata, "Cromak Technology", self.nome_programa)
        os.makedirs(pasta, exist_ok=True)
        return os.path.join(pasta, "online_sync.json")

    def carregar_dados_cache(self):
        """Carrega configurações salvas localmente."""
        arq = self._obter_caminho_cache()
        if os.path.exists(arq):
            try:
                with open(arq, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "aberturas": 0,
            "aberturas_desde_promo": 0,
            "ultima_promo": "",
            "buy_url": self.site_fallback,
            "preco": "",
            "versao_online": "",
            "url_download": self.site_fallback
        }

    def salvar_dados_cache(self, dados):
        """Persiste alterações no arquivo JSON de sincronização."""
        try:
            arq = self._obter_caminho_cache()
            with open(arq, "w", encoding="utf-8") as f:
                json.dump(dados, f, indent=4)
        except Exception:
            pass

    # --- LEITURA MULTI-FONTE (LOCAL REPO -> RAW GITHUB -> GITHUB PAGES) ---
    def _ler_arquivo_texto_multi_fonte(self, subpasta, sufixos_especificos=None):
        """
        Lê conteúdo de arquivo .txt em software-update, software-promo ou software-buy,
        tentando o repositório local (se disponível), depois Raw GitHub e GitHub Pages.
        """
        slugs = self._obter_slugs_candidatos()
        nomes_arquivos = []
        for s in slugs:
            nomes_arquivos.append(f"{s}.txt")
            if sufixos_especificos:
                for suf in sufixos_especificos:
                    nomes_arquivos.append(f"{s}{suf}.txt")

        # 1. Tentativa via disco local (desenvolvimento / offline)
        if os.path.isdir(self.LOCAL_REPO_DIR):
            pasta_local = os.path.join(self.LOCAL_REPO_DIR, subpasta) if subpasta else self.LOCAL_REPO_DIR
            if os.path.isdir(pasta_local):
                for nome_arq in nomes_arquivos:
                    caminho = os.path.join(pasta_local, nome_arq)
                    if os.path.isfile(caminho):
                        try:
                            with open(caminho, "r", encoding="utf-8", errors="ignore") as f:
                                conteudo = f.read().strip()
                                if conteudo:
                                    return [l.strip() for l in conteudo.splitlines() if l.strip()]
                        except Exception:
                            pass

        # 2. Tentativa via rede (Raw GitHub e GitHub Pages)
        bases_remotas = [self.RAW_GITHUB_BASE, self.PAGES_GITHUB_BASE]
        for base_url in bases_remotas:
            url_dir = f"{base_url}/{subpasta}" if subpasta else base_url
            for nome_arq in nomes_arquivos:
                url_completa = f"{url_dir}/{nome_arq}"
                try:
                    req = urllib.request.Request(url_completa, headers={'User-Agent': self.user_agent})
                    with urllib.request.urlopen(req, timeout=4) as resp:
                        if resp.status == 200:
                            conteudo = resp.read().decode('utf-8', 'ignore').strip()
                            linhas = [l.strip() for l in conteudo.splitlines() if l.strip()]
                            if linhas:
                                return linhas
                except Exception:
                    continue

        return []

    def _buscar_config_unificada(self):
        """Busca o arquivo .txt unificado do software na raiz de projetos (ex: connection-blackout.txt)."""
        if self._parsed_config is not None:
            return self._parsed_config

        # 1. Se URL explícita foi fornecida
        if self.url_config:
            try:
                req = urllib.request.Request(self.url_config, headers={'User-Agent': self.user_agent})
                with urllib.request.urlopen(req, timeout=4) as resp:
                    if resp.status == 200:
                        conteudo = resp.read().decode('utf-8', 'ignore').strip()
                        linhas = [l.strip() for l in conteudo.splitlines() if l.strip()]
                        if linhas:
                            self._parsed_config = self._processar_linhas_unificadas(linhas)
                            return self._parsed_config
            except Exception:
                pass

        # 2. Busca na raiz de projetos (sem subpasta)
        linhas = self._ler_arquivo_texto_multi_fonte(subpasta="")
        if linhas:
            self._parsed_config = self._processar_linhas_unificadas(linhas)
            return self._parsed_config

        self._parsed_config = {}
        return self._parsed_config

    def _processar_linhas_unificadas(self, linhas):
        return {
            'versao': linhas[0] if len(linhas) > 0 else '',
            'url_download': linhas[1] if len(linhas) > 1 else self.site_fallback,
            'banner_img': linhas[2] if len(linhas) > 2 else '',
            'banner_link': linhas[3] if len(linhas) > 3 else self.site_fallback,
            'buy_url': linhas[4] if len(linhas) > 4 else self.site_fallback,
            'preco': linhas[4] if (len(linhas) > 4 and not linhas[4].startswith("http")) else ""
        }

    # --- COOLDOWN INTELIGENTE DE PROMOÇÕES ---
    def registrar_abertura_e_verificar_promo(self, horas_cooldown=4.0, aberturas_intervalo=3):
        """
        Regra Inteligente de Exibição:
        - Incrementa os contadores de abertura do software.
        - Exibe na 1ª abertura absoluta.
        - Nas aberturas subsequentes, exibe se passaram mais de `horas_cooldown` (padrão 4h)
          OU se o usuário já abriu o programa `aberturas_intervalo` vezes (padrão 3 vezes).
        """
        dados = self.carregar_dados_cache()
        dados["aberturas"] = dados.get("aberturas", 0) + 1
        aberturas_desde = dados.get("aberturas_desde_promo", 0) + 1
        dados["aberturas_desde_promo"] = aberturas_desde
        self.salvar_dados_cache(dados)

        ultima_promo_str = dados.get("ultima_promo", "")
        if not ultima_promo_str:
            return True

        try:
            ultima_data = datetime.fromisoformat(ultima_promo_str)
            agora = datetime.now()
            horas = (agora - ultima_data).total_seconds() / 3600.0
            if horas >= horas_cooldown or aberturas_desde >= aberturas_intervalo:
                return True
        except Exception:
            return True

        return False

    def marcar_promo_exibida(self):
        """Registra o timestamp exato de exibição e zera o contador de aberturas desde a promo."""
        dados = self.carregar_dados_cache()
        dados["ultima_promo"] = datetime.now().isoformat()
        dados["aberturas_desde_promo"] = 0
        self.salvar_dados_cache(dados)

    def obter_url_compra(self):
        """Retorna a URL dinâmica de compra armazenada no cache ou o fallback."""
        dados = self.carregar_dados_cache()
        return dados.get("buy_url", self.site_fallback)

    def obter_preco(self):
        """Retorna o valor/preço atual do produto armazenado em cache (ex: '49.90')."""
        dados = self.carregar_dados_cache()
        return dados.get("preco", "")

    def obter_info_completa(self):
        """Retorna todas as informações locais e remotas agregadas."""
        return self.carregar_dados_cache()

    # --- CONSULTAS DE REDE (BACKGROUND) ---
    def checar_atualizacao(self, versao_atual, callback=None):
        """
        Verifica a versão online de forma assíncrona (em thread separada).
        Consulta `software-update/<slug>.txt` ou a configuração unificada.
        callback(tem_update: bool, nova_versao: str, url_download: str)
        """
        def _tarefa():
            tem_update = False
            nova_versao = str(versao_atual)
            url_down = self.site_fallback

            # 1. Tenta a pasta software-update
            linhas_update = self._ler_arquivo_texto_multi_fonte("software-update", sufixos_especificos=["-update", "_update"])
            if linhas_update:
                nova_versao = linhas_update[0].strip()
                if len(linhas_update) > 1 and linhas_update[1].startswith("http"):
                    url_down = linhas_update[1].strip()
                t_online = extrair_tupla_versao(nova_versao)
                t_atual = extrair_tupla_versao(versao_atual)
                tem_update = t_online > t_atual
            else:
                # 2. Fallback para arquivo unificado
                cfg = self._buscar_config_unificada()
                if cfg and cfg.get('versao'):
                    nova_versao = cfg['versao']
                    url_down = cfg.get('url_download') or self.site_fallback
                    t_online = extrair_tupla_versao(nova_versao)
                    t_atual = extrair_tupla_versao(versao_atual)
                    tem_update = t_online > t_atual
                elif self.url_update:
                    try:
                        req = urllib.request.Request(self.url_update, headers={'User-Agent': self.user_agent})
                        with urllib.request.urlopen(req, timeout=4) as resp:
                            if resp.status == 200:
                                conteudo = resp.read().decode('utf-8', 'ignore').strip()
                                linhas = conteudo.splitlines()
                                if linhas:
                                    nova_versao = linhas[0].strip()
                                    url_down = linhas[1].strip() if len(linhas) > 1 else self.site_fallback
                                    t_online = extrair_tupla_versao(nova_versao)
                                    t_atual = extrair_tupla_versao(versao_atual)
                                    tem_update = t_online > t_atual
                    except Exception:
                        pass

            # Salva versão e link encontrados em cache
            dados = self.carregar_dados_cache()
            dados["versao_online"] = nova_versao
            dados["url_download"] = url_down
            self.salvar_dados_cache(dados)

            if callback:
                callback(tem_update, nova_versao, url_down)

        threading.Thread(target=_tarefa, daemon=True).start()

    def sincronizar_background(self, deve_verificar_promo=True, callback_promo=None, callback_concluido=None):
        """
        Sincroniza preço, URL de compra e faz o download seguro da imagem da promoção.
        - Lê de `software-buy` (preço ou link)
        - Lê de `software-promo` (banner e link de destino)
        callback_promo(imagem_path: str, link_destino: str)
        """
        def _tarefa():
            dados = self.carregar_dados_cache()
            cfg = self._buscar_config_unificada()

            # -------------------------------------------------------------
            # 1. Sincronizar Preço e Compra a partir de 'software-buy'
            # -------------------------------------------------------------
            linhas_buy = self._ler_arquivo_texto_multi_fonte("software-buy", sufixos_especificos=["-buy", "_buy"])
            if linhas_buy:
                item1 = linhas_buy[0].strip()
                if item1.startswith("http"):
                    dados["buy_url"] = item1
                else:
                    dados["preco"] = item1
                    if len(linhas_buy) > 1 and linhas_buy[1].startswith("http"):
                        dados["buy_url"] = linhas_buy[1].strip()
            elif cfg.get('buy_url'):
                if cfg.get('preco'):
                    dados["preco"] = cfg['preco']
                if str(cfg['buy_url']).startswith("http"):
                    dados["buy_url"] = cfg['buy_url']
            elif self.url_buy:
                try:
                    req_buy = urllib.request.Request(self.url_buy, headers={'User-Agent': self.user_agent})
                    with urllib.request.urlopen(req_buy, timeout=4) as resp:
                        if resp.status == 200:
                            conteudo_buy = resp.read().decode('utf-8', 'ignore').strip()
                            if conteudo_buy.startswith("http"):
                                dados["buy_url"] = conteudo_buy
                            else:
                                dados["preco"] = conteudo_buy
                except Exception:
                    pass

            # -------------------------------------------------------------
            # 2. Sincronizar Banner de Promoção a partir de 'software-promo'
            # -------------------------------------------------------------
            if deve_verificar_promo:
                temp_dir = os.path.join(os.environ.get("TEMP", "C:\\Temp"), "CromakUI")
                os.makedirs(temp_dir, exist_ok=True)
                nome_safe = self.nome_programa.lower().replace(" ", "_")
                promo_img_path = os.path.join(temp_dir, f"promo_{nome_safe}.jpg")
                link_url = dados.get("buy_url", self.site_fallback)
                img_url = ""

                linhas_promo = self._ler_arquivo_texto_multi_fonte("software-promo", sufixos_especificos=["-promo", "_promo"])
                if linhas_promo:
                    img_url = linhas_promo[0].strip()
                    if len(linhas_promo) > 1 and linhas_promo[1].startswith("http"):
                        link_url = linhas_promo[1].strip()
                elif cfg.get('banner_img'):
                    img_url = cfg['banner_img']
                    link_url = cfg.get('banner_link') or link_url
                elif self.url_promo:
                    try:
                        req_promo = urllib.request.Request(self.url_promo, headers={'User-Agent': self.user_agent})
                        with urllib.request.urlopen(req_promo, timeout=4) as resp:
                            if resp.status == 200:
                                conteudo = resp.read().decode('utf-8', 'ignore').strip()
                                l_p = conteudo.splitlines()
                                img_url = l_p[0].strip() if len(l_p) > 0 else ""
                                link_url = l_p[1].strip() if len(l_p) > 1 else link_url
                    except Exception:
                        pass

                dados["banner_img"] = img_url
                dados["banner_link"] = link_url

                sucesso = False
                if img_url.startswith("http"):
                    try:
                        req_img = urllib.request.Request(img_url, headers={'User-Agent': self.user_agent})
                        with urllib.request.urlopen(req_img, timeout=6) as resp_img:
                            if resp_img.status == 200:
                                img_bytes = resp_img.read()
                                with open(promo_img_path, "wb") as f_img:
                                    f_img.write(img_bytes)
                                sucesso = True
                                if callback_promo:
                                    callback_promo(promo_img_path, link_url)
                    except Exception:
                        pass

                # Se falhar o download mas já tiver cópia em disco, reaproveita
                if not sucesso and os.path.exists(promo_img_path):
                    if callback_promo:
                        callback_promo(promo_img_path, link_url)

            self.salvar_dados_cache(dados)
            if callback_concluido:
                callback_concluido(dados)

        threading.Thread(target=_tarefa, daemon=True).start()


# ==================================================================================
# INTEGRAÇÃO COM TKINTER (MODAL DE PROMO BANNER)
# ==================================================================================

def exibir_modal_promo_tk(parent, imagem_path, link_destino, titulo="Cromak Special Offer", icone_path=None):
    """
    Exibe modal promocional nativo em Tkinter com banner clicável e design Dark moderno.
    Compatível com Connection Blackout e Install Protector.
    """
    try:
        import tkinter as tk
        from PIL import Image, ImageTk
        import webbrowser

        if not imagem_path or not os.path.exists(imagem_path):
            return None

        pop = tk.Toplevel(parent)
        pop.withdraw()
        pop.title(titulo)

        # Configura o ícone na barra de título da janela
        if icone_path and os.path.exists(icone_path):
            try:
                pop.iconbitmap(icone_path)
            except Exception:
                try:
                    _ico_img = ImageTk.PhotoImage(Image.open(icone_path))
                    pop.iconphoto(False, _ico_img)
                except Exception:
                    pass
        else:
            for candidato in ["InstallProtector.ico", "ConnectionBlackout.ico", "icon.ico", "app.ico"]:
                if os.path.exists(candidato):
                    try:
                        pop.iconbitmap(candidato)
                        break
                    except Exception:
                        pass

        pop.configure(bg="#121212", highlightthickness=1, highlightbackground="#2D2D2D")
        pop.transient(parent)
        pop.grab_set()

        # Carrega e redimensiona o banner
        img_pil = Image.open(imagem_path)
        largura_max = 560
        if img_pil.width > largura_max:
            ratio = largura_max / float(img_pil.width)
            nova_altura = int(float(img_pil.height) * float(ratio))
            img_pil = img_pil.resize((largura_max, nova_altura), Image.Resampling.LANCZOS)

        foto = ImageTk.PhotoImage(img_pil)

        def _ao_clicar_banner(e=None):
            if link_destino:
                webbrowser.open(link_destino)
            pop.destroy()

        lbl_banner = tk.Label(pop, image=foto, bg="#121212", cursor="hand2", bd=0)
        lbl_banner.image = foto  # Mantém referência viva
        lbl_banner.pack(fill="both", expand=True)
        lbl_banner.bind("<Button-1>", _ao_clicar_banner)

        rodape = tk.Frame(pop, bg="#121212", padx=15, pady=8)
        rodape.pack(fill="x")

        lbl_dica = tk.Label(rodape, text=core_i18n.t("dialogs.promo_limited_offer", "Oferta por tempo limitado. Clique na imagem para abrir.") if core_i18n else "Oferta por tempo limitado. Clique na imagem para abrir.", 
                            bg="#121212", fg="#777777", font=("Segoe UI", 9))
        lbl_dica.pack(side="left")

        btn_fechar = tk.Button(rodape, text=core_i18n.t("dialogs.promo_later", "Mais tarde") if core_i18n else "Mais tarde", bg="#242424", fg="#aaaaaa", 
                               activebackground="#2e2e2e", activeforeground="#ffffff", 
                               font=("Segoe UI", 9), relief="flat", padx=16, pady=3, 
                               cursor="hand2", command=pop.destroy)
        btn_fechar.pack(side="right")

        pop.update_idletasks()
        larg = pop.winfo_reqwidth()
        alt = pop.winfo_reqheight()
        x = (pop.winfo_screenwidth() // 2) - (larg // 2)
        y = (pop.winfo_screenheight() // 2) - (alt // 2)
        pop.geometry(f"{larg}x{alt}+{x}+{y}")
        pop.deiconify()
        pop.focus_force()
        return pop
    except Exception:
        return None


# ==================================================================================
# INTEGRAÇÃO NATIVA COM PYQT6 (WORKER E DIALOG DE PROMO)
# ==================================================================================

if HAS_PYQT6:
    class CromakQtSyncWorker(QObject):
        """Worker assíncrono pronto para acoplar em interfaces PyQt6 via Signals."""
        update_resultado = pyqtSignal(bool, str, str)  # tem_update, versao, url
        promo_pronta = pyqtSignal(str, str)            # img_path, link_destino

        def __init__(self, sync_engine: CromakOnlineSync):
            super().__init__()
            self.engine = sync_engine

        def verificar_atualizacao(self, versao_atual):
            self.engine.checar_atualizacao(
                versao_atual,
                callback=lambda tem, ver, url: self.update_resultado.emit(tem, ver, url)
            )

        def sincronizar(self, deve_promo=True):
            self.engine.sincronizar_background(
                deve_verificar_promo=deve_promo,
                callback_promo=lambda path, link: self.promo_pronta.emit(path, link)
            )


    class DialogPromoPadrao(QDialog):
        """Modal visual moderno de promoção com banner clicável de borda a borda."""
        def __init__(self, imagem_path, link_destino, titulo="Cromak Special Offer", icone_res=None, parent=None):
            super().__init__(parent)
            self.link_destino = link_destino or "https://cromaktechnology.github.io"
            self.setWindowTitle(titulo)

            if icone_res is not None:
                try:
                    from resource_loader import CromakResourceLoader
                    self.setWindowIcon(CromakResourceLoader.icon(icone_res))
                except Exception:
                    pass

            self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowCloseButtonHint)
            self.setStyleSheet("""
                QDialog {
                    background-color: #121212;
                    border: 1px solid #2D2D2D;
                }
            """)

            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)

            self.lbl_banner = QLabel()
            self.lbl_banner.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self.lbl_banner.setToolTip(core_i18n.t("dialogs.promo_tooltip", "Clique na imagem para aproveitar esta oferta especial") if core_i18n else "Clique na imagem para aproveitar esta oferta especial")
            self.lbl_banner.setStyleSheet("border: none; background: transparent;")

            pixmap = QPixmap(imagem_path)
            if not pixmap.isNull():
                largura_max = 560
                if pixmap.width() > largura_max:
                    pixmap = pixmap.scaledToWidth(largura_max, Qt.TransformationMode.SmoothTransformation)
                self.lbl_banner.setPixmap(pixmap)
                self.setFixedSize(pixmap.width(), pixmap.height() + 45)
            else:
                self.lbl_banner.setText(core_i18n.t("dialogs.promo_special_offer", "Oferta Especial Disponível\nClique para Conferir") if core_i18n else "Oferta Especial Disponível\nClique para Conferir")
                self.lbl_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.lbl_banner.setStyleSheet("color: white; font-size: 14px; padding: 40px;")
                self.setFixedSize(480, 260)

            self.lbl_banner.mousePressEvent = self._ao_clicar_banner
            layout.addWidget(self.lbl_banner)

            rodape = QHBoxLayout()
            rodape.setContentsMargins(15, 6, 15, 8)

            lbl_dica = QLabel(core_i18n.t("dialogs.promo_limited_offer", "Oferta por tempo limitado. Clique na imagem para abrir.") if core_i18n else "Oferta por tempo limitado. Clique na imagem para abrir.")
            lbl_dica.setStyleSheet("color: #777777; font-size: 11px; font-family: 'Segoe UI';")
            rodape.addWidget(lbl_dica)
            rodape.addStretch()

            btn_fechar = QPushButton(core_i18n.t("dialogs.promo_later", "Mais tarde") if core_i18n else "Mais tarde")
            btn_fechar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_fechar.setFixedHeight(28)
            btn_fechar.setStyleSheet("""
                QPushButton {
                    background-color: #242424;
                    color: #AAAAAA;
                    border: 1px solid #333333;
                    border-radius: 4px;
                    padding: 0 16px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #2E2E2E;
                    color: white;
                    border-color: #555555;
                }
            """)
            btn_fechar.clicked.connect(self.close)
            rodape.addWidget(btn_fechar)

            layout.addLayout(rodape)

        def _ao_clicar_banner(self, event):
            if event.button() == Qt.MouseButton.LeftButton:
                QDesktopServices.openUrl(QUrl(self.link_destino))
                self.accept()
