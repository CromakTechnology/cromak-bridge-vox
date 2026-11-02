
// --- GESTÃO DE ATALHOS ---
window.appShortcuts = {
    mic: 'F2', stop: 'Escape', config: 'F10', clear: 'F5',
    help: 'F1', exit: 'F4',
    txt: 'T', mail: 'R', web: 'I', files: 'A', calc: 'C', whats: 'Z'
};

function initShortcuts() {
    const inputs = document.querySelectorAll('.shortcut-input');
    inputs.forEach(input => {
        // Remove listener antigo se houver para não duplicar
        input.onkeydown = (e) => {
            // Ignora teclas modificadoras sozinhas
            if (['Control', 'Alt', 'Shift', 'Meta'].includes(e.key)) return;
            e.preventDefault();
            e.stopPropagation();
            let key = e.key;
            if (key === ' ') key = 'Space';
            if (key === 'Backspace' || key === 'Delete') {
                input.value = '';
            } else {
                input.value = key.length === 1 ? key.toUpperCase() : key;
            }
            // Feedback sonoro/acessível sutil
            try {
                if (typeof anunciarAoLeitor === 'function') {
                    anunciarAoLeitor("Tecla atribuída: " + input.value);
                }
            } catch(e) {}
        };
        input.onfocus = () => {
            input.select();
        };
    });
}

function resetShortcuts() {
    const defs = { shortMic: 'F2', shortStop: 'Escape', shortConfig: 'F10', shortClear: 'F5', shortHelp: 'F1', shortExit: 'F4', shortTxt: 'T', shortMail: 'R', shortWeb: 'I', shortFiles: 'A', shortCalc: 'C', shortWhats: 'Z' };
    for (let id in defs) {
        if(document.getElementById(id)) document.getElementById(id).value = defs[id];
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initShortcuts();
    // Foco inicial programático imediato (WAI-ARIA role="application" & WCAG 2.1.4)
    setTimeout(() => {
        const input = document.getElementById('userInput');
        if (input && !input.disabled) {
            input.focus();
        }
    }, 100);
});

// Ao retornar o foco para a janela do Bridge Vox, garante foco no campo de digitação
window.addEventListener('focus', () => {
    const activeModal = document.querySelector('.api-setup-overlay[style*="display: flex"], .settings-modal[style*="display: flex"], #customDialog[style*="display: flex"]');
    if (!activeModal && typeof focarCampoMensagem === 'function') {
        focarCampoMensagem();
    }
});




// --- SISTEMA DE PARTÍCULAS ---
        (function () {
            const canvas = document.getElementById('particleCanvas');
            const ctx = canvas.getContext('2d');
            let particles = [];
            let mouse = { x: null, y: null, radius: 150 };

            function resize() { canvas.width = window.innerWidth; canvas.height = window.innerHeight; }
            class Particle {
                constructor() {
                    this.x = Math.random() * canvas.width; this.y = Math.random() * canvas.height;
                    this.size = Math.random() * 1.5 + 1; this.speedX = (Math.random() - 0.5) * 0.8; this.speedY = (Math.random() - 0.5) * 0.8;
                }
                update() {
                    this.x += this.speedX; this.y += this.speedY;
                    if (this.x < -10) this.x = canvas.width + 10; if (this.x > canvas.width + 10) this.x = -10;
                    if (this.y < -10) this.y = canvas.height + 10; if (this.y > canvas.height + 10) this.y = -10;
                }
                draw() { ctx.beginPath(); ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2); ctx.fillStyle = `rgba(99, 102, 241, 0.4)`; ctx.fill(); }
            }
            function init() { particles = []; for (let i = 0; i < 60; i++) particles.push(new Particle()); }
            function animate() { ctx.clearRect(0, 0, canvas.width, canvas.height); particles.forEach(p => { p.update(); p.draw(); }); requestAnimationFrame(animate); }
            window.addEventListener('resize', () => { resize(); init(); });
            resize(); init(); animate();
        })();

        // --- SISTEMA DE INTERNACIONALIZAÇÃO (i18n) ---
        window.appIdiomaAtual = 'pt_BR';
        window.i18nDict = {};

        function t(chave, fallback = '') {
            if (window.i18nDict && window.i18nDict[chave]) return window.i18nDict[chave];
            return fallback || chave;
        }

        function aplicarIdiomaNaTela(dict) {
            if (!dict) return;
            window.i18nDict = dict;

            document.querySelectorAll('[data-i18n]').forEach(el => {
                const k = el.getAttribute('data-i18n');
                if (dict[k]) el.innerText = dict[k];
            });
            document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
                const k = el.getAttribute('data-i18n-placeholder');
                if (dict[k]) el.placeholder = dict[k];
            });
            document.querySelectorAll('[data-i18n-title]').forEach(el => {
                const k = el.getAttribute('data-i18n-title');
                if (dict[k]) el.title = dict[k];
            });
            document.querySelectorAll('[data-i18n-aria]').forEach(el => {
                const k = el.getAttribute('data-i18n-aria');
                if (dict[k]) el.setAttribute('aria-label', dict[k]);
            });
        }

        function carregarIdioma(codigo = 'pt_BR') {
            window.appIdiomaAtual = codigo;
            if (window.pywebview && pywebview.api && pywebview.api.carregar_idioma) {
                pywebview.api.carregar_idioma(codigo).then(dict => {
                    aplicarIdiomaNaTela(dict);
                }).catch(() => {});
            } else {
                fetch(`locale/${codigo}.json`).then(r => r.json()).then(dict => {
                    aplicarIdiomaNaTela(dict);
                }).catch(() => {});
            }
        }

        function carregarListaIdiomas(idiomaSelecionado) {
            if (window.pywebview && pywebview.api && pywebview.api.listar_idiomas) {
                pywebview.api.listar_idiomas().then(lista => {
                    const select = document.getElementById('configLanguage');
                    if (select && lista && lista.length > 0) {
                        const atual = idiomaSelecionado || select.value || window.appIdiomaAtual || 'pt_BR';
                        select.innerHTML = '';
                        lista.forEach(item => {
                            const opt = document.createElement('option');
                            opt.value = item.code;
                            opt.innerText = item.name;
                            if (item.code === atual) opt.selected = true;
                            select.appendChild(opt);
                        });
                    }
                }).catch(() => {});
            }
        }

        // --- INTEGRAÇÃO PYTHON E LÓGICA ---
        let currentSessionId = null;
        let currentRequestToken = 0;
        let isEnviandoMensagem = false;

        window.addEventListener('pywebviewready', function() {
            initCustomSelects();

            if (window.pywebview && pywebview.api && pywebview.api.obter_versao_app) {
                pywebview.api.obter_versao_app().then(info => {
                    const el = document.getElementById('aboutAppVersion');
                    if (el && info && info.full) {
                        el.innerText = info.full;
                    }
                }).catch(() => {});
            }

            pywebview.api.verificar_api_key().then(function(tem_chave) {
                if (tem_chave) {
                    document.getElementById('apiSetupOverlay').style.display = 'none';
                    carregarSessoesIniciais();
                    focarCampoMensagem();
                } else {
                    const appContainer = document.querySelector('.app-container');
                    if (appContainer) {
                        appContainer.setAttribute('aria-hidden', 'true');
                        appContainer.setAttribute('inert', '');
                    }
                    setTimeout(() => {
                        const setupInput = document.getElementById('setupProvider') || document.querySelector('#apiSetupOverlay input');
                        if (setupInput) setupInput.focus();
                    }, 100);
                }
            });
            
            pywebview.api.obter_configuracoes().then(config => {
                const lang = (config && config.language) ? config.language : 'pt_BR';
                carregarIdioma(lang);
                carregarListaIdiomas(lang);
                if (config && config.interface_mode === 'high_contrast') {
                    document.body.classList.add('high-contrast-theme');
                    const sidebarLogo = document.querySelector('.logo-icon-img');
                    if (sidebarLogo) {
                        sidebarLogo.src = 'lib/bridge-vox.png';
                        // Modifica o texto mantendo a imagem e adicionando o "Vox"
                        sidebarLogo.parentElement.innerHTML = sidebarLogo.outerHTML + ' Cromak Bridge Vox';
                    }
                }
                const quickProv = document.getElementById('quickProviderSelector');
                if (quickProv && config.provider) { 
                    quickProv.value = config.provider; 
                    forceUpdateCustomUI('quickProviderSelector'); 
                }
                
                // Restaura o model atual no top bar
                if (config.model) {
                    setTimeout(() => {
                        const modelSel = document.getElementById('modelSelector');
                        if (modelSel) { 
                            modelSel.value = config.model; 
                            forceUpdateCustomUI('modelSelector');
                        }
                    }, 500);
                }
                
                // Restaura estado do duelo, se salvo
                if (config.duel) {
                    const {prov1, mod1, prov2, mod2} = config.duel;
                    document.getElementById('duelProv1').value = prov1 || 'gemini';
                    document.getElementById('duelProv2').value = prov2 || 'claude';
                    
                    Promise.all([
                        pywebview.api.obter_modelos_por_provedor(prov1 || 'gemini'),
                        pywebview.api.obter_modelos_por_provedor(prov2 || 'claude')
                    ]).then(([modelos1, modelos2]) => {
                        const sel1 = document.getElementById('duelMod1');
                        sel1.innerHTML = '';
                        modelos1.forEach(m => { sel1.appendChild(new Option(m.replace('models/', ''), m)); });
                        if(mod1) sel1.value = mod1;

                        const sel2 = document.getElementById('duelMod2');
                        sel2.innerHTML = '';
                        modelos2.forEach(m => { sel2.appendChild(new Option(m.replace('models/', ''), m)); });
                        if(mod2) sel2.value = mod2;
                    });
                }
            });

            // Intercepta todos os links clicados dentro do chat
            document.getElementById('messagesContainer').addEventListener('click', function(e) {
                const link = e.target.closest('a');
                if (link) {
                    e.preventDefault(); // Impede o aplicativo de sair da tela
                    pywebview.api.abrir_link(link.href); // Manda o Python abrir no Chrome/Edge
                }
            });
        });

        function salvarApiKey() {
            const key = document.getElementById('apiKeyInput').value.trim();
            if (!key) return;
            pywebview.api.salvar_api_key(key).then(function() {
                document.getElementById('apiSetupOverlay').style.opacity = '0';
                setTimeout(() => { document.getElementById('apiSetupOverlay').style.display = 'none'; carregarSessoesIniciais(); }, 400);
            });
        }

        // ==========================================
        // SISTEMA DE DROPDOWNS CUSTOMIZADOS
        // ==========================================
        function initCustomSelects() {
            const selects = document.querySelectorAll('select.model-dropdown, select.settings-input');
            selects.forEach(select => {
                if (select.dataset.customized) return;
                select.dataset.customized = "true";
                select.style.display = 'none';

                const isSettings = select.classList.contains('settings-input');

                const container = document.createElement('div');
                container.className = 'custom-select-container';
                if (isSettings) {
                    container.style.display = 'block';
                    container.style.width = '100%';
                    container.style.marginBottom = '16px';
                }
                select.parentNode.insertBefore(container, select.nextSibling);

                const trigger = document.createElement('div');
                trigger.className = 'custom-select-trigger';
                trigger.tabIndex = 0; // Permite receber foco do teclado (Tab)
                trigger.setAttribute('role', 'combobox');
                trigger.setAttribute('aria-haspopup', 'listbox');
                trigger.setAttribute('aria-expanded', 'false');

                // Define rótulo acessível para o NVDA
                let rotuloAcessivel = "Seletor de opções";
                if (select.id === 'quickProviderSelector') rotuloAcessivel = "Provedor de inteligência artificial";
                else if (select.id === 'modelSelector') rotuloAcessivel = "Modelo de inteligência artificial";
                else if (select.previousElementSibling && select.previousElementSibling.classList.contains('settings-label')) {
                    rotuloAcessivel = select.previousElementSibling.innerText;
                }
                trigger.setAttribute('aria-label', rotuloAcessivel);

                if (isSettings) {
                    trigger.style.width = '100%';
                    trigger.style.padding = '14px 20px';
                    trigger.style.backgroundColor = 'rgba(0,0,0,0.2)';
                    trigger.style.color = 'white';
                }
                
                trigger.innerHTML = `<span class="custom-select-text"></span> <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-left: 8px;" aria-hidden="true"><polyline points="6 9 12 15 18 9"></polyline></svg>`;
                
                const dropdown = document.createElement('div');
                dropdown.className = 'custom-select-dropdown';
                dropdown.setAttribute('role', 'listbox');

                container.appendChild(trigger);
                container.appendChild(dropdown);

                const updateTriggerText = () => {
                    const selectedOpt = select.options[select.selectedIndex];
                    const textoOpcao = selectedOpt ? selectedOpt.innerText : 'Selecione...';
                    trigger.querySelector('.custom-select-text').innerText = textoOpcao;
                    trigger.setAttribute('aria-label', `${rotuloAcessivel}: ${textoOpcao}`);
                };

                const renderOptions = () => {
                    dropdown.innerHTML = '';
                    Array.from(select.options).forEach((opt, idx) => {
                        const btn = document.createElement('button');
                        btn.innerText = opt.innerText;
                        btn.setAttribute('role', 'option');
                        btn.setAttribute('aria-selected', opt.selected ? 'true' : 'false');
                        btn.onclick = (e) => {
                            e.stopPropagation();
                            select.value = opt.value;
                            updateTriggerText();
                            dropdown.classList.remove('active');
                            trigger.setAttribute('aria-expanded', 'false');
                            setTimeout(() => dropdown.style.display = 'none', 200);
                            select.dispatchEvent(new Event('change'));
                            trigger.focus();
                        };
                        dropdown.appendChild(btn);
                    });
                    updateTriggerText();
                };

                const toggleDropdown = (e) => {
                    if (e) e.stopPropagation();
                    const isActive = dropdown.classList.contains('active');
                    document.querySelectorAll('.custom-select-dropdown').forEach(d => {
                        d.classList.remove('active');
                        d.style.display = 'none';
                    });
                    document.querySelectorAll('.custom-select-trigger').forEach(t => t.setAttribute('aria-expanded', 'false'));

                    if (!isActive) {
                        dropdown.style.display = 'flex';
                        trigger.setAttribute('aria-expanded', 'true');
                        setTimeout(() => {
                            dropdown.classList.add('active');
                            const primeiroBtn = dropdown.querySelector('button');
                            if (primeiroBtn) primeiroBtn.focus();
                        }, 10);
                    }
                };

                trigger.onclick = toggleDropdown;
                trigger.onkeydown = (e) => {
                    if (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowDown') {
                        e.preventDefault();
                        toggleDropdown(e);
                    }
                };

                dropdown.onkeydown = (e) => {
                    const botoes = Array.from(dropdown.querySelectorAll('button'));
                    const indexAtual = botoes.indexOf(document.activeElement);

                    if (e.key === 'ArrowDown') {
                        e.preventDefault();
                        const prox = (indexAtual + 1) % botoes.length;
                        botoes[prox].focus();
                    } else if (e.key === 'ArrowUp') {
                        e.preventDefault();
                        const ant = (indexAtual - 1 + botoes.length) % botoes.length;
                        botoes[ant].focus();
                    } else if (e.key === 'Escape') {
                        e.preventDefault();
                        dropdown.classList.remove('active');
                        trigger.setAttribute('aria-expanded', 'false');
                        setTimeout(() => dropdown.style.display = 'none', 200);
                        trigger.focus();
                    }
                };

                // Observa quando o innerHTML do select muda (ex: carregando novos modelos)
                const observer = new MutationObserver(renderOptions);
                observer.observe(select, { childList: true });
                
                // Allow programmatic value changes to update the custom UI
                select.addEventListener('change', updateTriggerText);
                select.refreshCustomUI = updateTriggerText;

                renderOptions();
            });
        }
        
        function forceUpdateCustomUI(selectId) {
            const el = document.getElementById(selectId);
            if(el && el.refreshCustomUI) el.refreshCustomUI();
        }

                // ==========================================
        // ACESSIBILIDADE E ANÚNCIOS PARA LEITOR DE TELA (NVDA / NARRADOR)
        // ==========================================
        function limparTextoParaLeitor(texto) {
            if (!texto) return '';
            return String(texto)
                .replace(/!\[.*?\]\(.*?\)/g, '')
                .replace(/<[^>]*>/g, '')
                .replace(/[*_#`~\[\]]/g, '')
                .replace(/\n{2,}/g, '. ')
                .replace(/\n/g, ' ')
                .replace(/\s+/g, ' ')
                .trim();
        }

        function anunciarAoLeitor(mensagem, urgente = false) {
            const announcer = document.getElementById('a11yLiveAnnouncer');
            if (!announcer) return;
            if (urgente) {
                announcer.setAttribute('aria-live', 'assertive');
            } else {
                announcer.setAttribute('aria-live', 'polite');
            }
            announcer.textContent = '';
            setTimeout(() => {
                announcer.textContent = mensagem;
            }, 60);
        }
        window.anunciarAoLeitor = anunciarAoLeitor;
        window.anunciarParaLeitorDeTela = anunciarAoLeitor;

        function focarCampoMensagem() {
            setTimeout(() => {
                const input = document.getElementById('userInput');
                if (input && !input.disabled) {
                    input.focus();
                }
            }, 120);
        }

        function focarUltimaRespostaIA() {
            const wrappers = document.querySelectorAll('.messages-container .message-wrapper.wrapper-ia');
            if (wrappers.length > 0) {
                const last = wrappers[wrappers.length - 1];
                last.focus();
            } else {
                if (typeof mostrarToast !== 'undefined') mostrarToast("Nenhuma resposta da IA para ler ainda.", true);
            }
        }

        
        function abrirLinkGerarApi(provider) {
            const urls = {
                gemini: 'https://aistudio.google.com/app/apikey',
                groq: 'https://console.groq.com/keys',
                openai: 'https://platform.openai.com/api-keys',
                claude: 'https://console.anthropic.com/settings/keys',
                qwen: 'https://bailian.console.aliyun.com/'
            };
            const url = urls[provider] || urls['gemini'];
            if (window.pywebview && pywebview.api && pywebview.api.abrir_link) {
                pywebview.api.abrir_link(url);
            } else {
                window.open(url, '_blank');
            }
        }

        function atualizarProvedorSetup() {
            const selectEl = document.getElementById('setupProvider');
            if (!selectEl) return;
            const provider = selectEl.value;
            const nomes = {
                gemini: 'Google Gemini',
                groq: 'Groq Ultra-Rápido',
                openai: 'OpenAI ChatGPT',
                claude: 'Anthropic Claude',
                qwen: 'Alibaba Qwen Cloud'
            };
            const boxes = ['gemini', 'groq', 'openai', 'claude', 'qwen'];
            boxes.forEach(b => {
                const box = document.getElementById('setupBox_' + b);
                if (box) box.style.display = (b === provider) ? 'block' : 'none';
            });
            
            if (typeof anunciarAoLeitor === 'function') {
                anunciarAoLeitor("Provedor alterado para " + (nomes[provider] || provider) + ". Digite sua chave abaixo ou use o botão para gerar nova API.");
            }
        }

        function carregarSessoesIniciais() {
            pywebview.api.obter_modelos().then(function(modelos) {
                const selector = document.getElementById('modelSelector');
                if (selector && modelos.length > 0) {
                    selector.innerHTML = '';
                    modelos.forEach(m => {
                        const opt = document.createElement('option');
                        opt.value = m; opt.innerText = m.replace('models/', '').toUpperCase();
                        selector.appendChild(opt);
                    });
                    
                    pywebview.api.obter_configuracoes().then(cfg => {
                        if (cfg && cfg.model) { 
                            selector.value = cfg.model; 
                            forceUpdateCustomUI('modelSelector');
                        }
                    });
                }
            });

            pywebview.api.obter_sessoes().then(function(sessoes) {
                // CORREÇÃO: Só cria nova conversa se o banco de dados estiver completamente vazio
                if (sessoes.length === 0) {
                    criarSessao();
                } else {
                    renderizarSessoes(sessoes);
                    abrirSessao(sessoes[0][0]);
                }
            });
        }

        function renderizarSessoes(sessoes) {
            const list = document.getElementById('sessionList');
            list.innerHTML = '';
            
            const svgPin = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="17" x2="12" y2="22"></line><path d="M5 17h14v-1.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.76V6h1a2 2 0 0 0 0-4H8a2 2 0 0 0 0 4h1v4.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24Z"></path></svg>`;
            const svgRename = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>`;
            const svgTrash = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>`;
            
            sessoes.forEach(s => {
                const id = s[0]; const title = s[1]; const isPinned = s[2];
                const item = document.createElement('div');
                item.className = 'session-item'; item.dataset.id = id;
                
                const titleSpan = document.createElement('span');
                titleSpan.className = 'session-title'; 
                // Ícone de pino ativo diretamente no nome da sessão se estiver fixada
                titleSpan.innerHTML = (isPinned ? `<span style="color:var(--accent-1); margin-right:6px;">${svgPin}</span>` : '') + title;
                titleSpan.onclick = () => abrirSessao(id);
                
                const actionsDiv = document.createElement('div');
                actionsDiv.className = 'session-actions';
                
                const pinBtn = document.createElement('button'); pinBtn.className = 's-action-btn'; pinBtn.innerHTML = svgPin; pinBtn.title = "Fixar";
                pinBtn.onclick = (e) => { e.stopPropagation(); pywebview.api.fixar_sessao(id, isPinned ? 0 : 1).then(() => pywebview.api.obter_sessoes().then(s => renderizarSessoes(s))); };
                
                const renameBtn = document.createElement('button'); renameBtn.className = 's-action-btn'; renameBtn.innerHTML = svgRename; renameBtn.title = "Renomear";
                renameBtn.onclick = async (e) => { 
                    e.stopPropagation(); 
                    const novo = await showCustomDialog('prompt', 'Renomear Conversa', '', title);
                    if (novo && novo !== title) {
                        pywebview.api.renomear_sessao_manual(id, novo).then(() => pywebview.api.obter_sessoes().then(s => renderizarSessoes(s)));
                    }
                };
                
                const delBtn = document.createElement('button'); delBtn.className = 's-action-btn'; delBtn.innerHTML = svgTrash; delBtn.title = "Apagar";
                delBtn.onclick = async (e) => { 
                    e.stopPropagation(); 
                    const isConfirmed = await showCustomDialog('confirm-danger', 'Excluir conversa', 'Tem certeza que deseja apagar esta conversa permanentemente? Esta ação não pode ser desfeita.');
                    if (isConfirmed) {
                        pywebview.api.excluir_sessao(id).then(() => {
                            pywebview.api.obter_sessoes().then(s => {
                                if(s.length === 0) criarSessao();
                                else { renderizarSessoes(s); abrirSessao(s[0][0]); }
                            });
                        });
                    }
                };
                
                actionsDiv.append(pinBtn, renameBtn, delBtn); item.append(titleSpan, actionsDiv); list.appendChild(item);
            });
            destacarSessaoAtiva();
        }

        function recarregarSessoes() { pywebview.api.obter_sessoes().then(sessoes => renderizarSessoes(sessoes)); }
        function criarSessao() { pywebview.api.criar_sessao().then(nova_id => { recarregarSessoes(); abrirSessao(nova_id); }); }
        function novaConversa() { criarSessao(); }
        
        function abrirSessao(id) {
            currentSessionId = id; destacarSessaoAtiva();
            if (window.innerWidth <= 768) toggleSidebar();
            
            pywebview.api.abrir_sessao(id).then(function(historico) {
                const container = document.getElementById('messagesContainer'); 
                container.innerHTML = '';
                
                if (historico.length === 0) {
                    // Renderiza o novo template caso a conversa esteja vazia
                    container.innerHTML = `
                        <div class="empty-state" id="emptyState" role="region" aria-label="Início de nova conversa. Escolha um comando rápido abaixo ou digite sua mensagem no campo de texto">
                            <div class="empty-icon-glow">
                                <img src="${document.body.classList.contains('high-contrast-theme') ? 'lib/bridge-vox.png' : 'lib/cromak-bridge.ico'}" alt="Logo do Cromak Bridge" class="empty-icon" onerror="this.style.display='none'">
                            </div>
                            <h2>${t('welcome_title', 'Como posso ajudar você hoje no seu computador?')}</h2>
                            <p>${t('welcome_subtitle', 'Escolha um comando rápido abaixo ou digite sua pergunta para começar.')}</p>
                            <div class="suggestions-grid" role="group" aria-label="Sugestões de comandos rápidos">
                                <button class="suggestion-btn" onclick="usarSugestao('O que você pode fazer no meu computador? Me explique suas funções e ferramentas.')">${t('suggestion_pc', 'O que você pode fazer no meu PC?')}</button>
                                <button class="suggestion-btn" onclick="usarSugestao('Como você pode ler meus arquivos, PDFs e documentos de texto?')">${t('suggestion_docs', 'Como ler documentos e PDFs')}</button>
                                <button class="suggestion-btn" onclick="usarSugestao('Quais são os principais atalhos de teclado e de voz para usar o Bridge?')">${t('suggestion_shortcuts', 'Atalhos de teclado e voz')}</button>
                            </div>
                        </div>
                    `;
                }
                else {
                    historico.forEach(msg => appendMessage(msg[1], msg[0], false));
                }
                focarCampoMensagem();
            });
        }

        function usarSugestao(texto) {
            const input = document.getElementById('userInput');
            input.value = texto;
            sendMessage(); // Envia automaticamente a mensagem clicada
        }

        function destacarSessaoAtiva() { document.querySelectorAll('.session-item').forEach(item => { item.classList.remove('active'); if (parseInt(item.dataset.id) === currentSessionId) item.classList.add('active'); }); }
        function filtrarSessoes() { const termo = document.getElementById('searchSession').value.toLowerCase(); document.querySelectorAll('.session-item').forEach(item => { item.style.display = item.innerText.toLowerCase().includes(termo) ? 'flex' : 'none'; }); }
        function mudarModelo() { pywebview.api.mudar_modelo(document.getElementById('modelSelector').value); }
        
        function mudarProvedorRapido() {
            const provider = document.getElementById('quickProviderSelector').value;
            pywebview.api.obter_configuracoes().then(config => {
                config.provider = provider;
                pywebview.api.salvar_preferencias(config).then(() => {
                    pywebview.api.obter_modelos().then(function(modelos) {
                        const selector = document.getElementById('modelSelector');
                        selector.innerHTML = '';
                        modelos.forEach(m => {
                            const opt = document.createElement('option');
                            opt.value = m; opt.innerText = m.replace('models/', '').toUpperCase();
                            selector.appendChild(opt);
                        });
                        const configProv = document.getElementById('configProvider');
                        if (configProv) configProv.value = provider;
                    });
                });
            });
        }

        function toggleSidebar() { document.getElementById('sidebar').classList.toggle('active'); }

        
        function formatCodeBlocks(container) {
            container.querySelectorAll('pre').forEach((pre) => {
                if (pre.dataset.formatted) return;
                pre.dataset.formatted = "true";
                pre.style.position = 'relative';
                
                const copyBtn = document.createElement('button');
                copyBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg> Copiar';
                copyBtn.style.position = 'absolute';
                copyBtn.style.top = '8px';
                copyBtn.style.right = '8px';
                copyBtn.style.padding = '4px 8px';
                copyBtn.style.background = 'rgba(255, 255, 255, 0.1)';
                copyBtn.style.border = 'none';
                copyBtn.style.borderRadius = '4px';
                copyBtn.style.color = 'var(--text-secondary)';
                copyBtn.style.cursor = 'pointer';
                copyBtn.style.display = 'flex';
                copyBtn.style.alignItems = 'center';
                copyBtn.style.gap = '6px';
                copyBtn.style.fontSize = '0.75rem';
                copyBtn.style.transition = 'all 0.2s ease';
                copyBtn.style.backdropFilter = 'blur(4px)';
                
                copyBtn.onmouseover = () => { copyBtn.style.background = 'rgba(255,255,255,0.2)'; copyBtn.style.color = 'white'; };
                copyBtn.onmouseout = () => { copyBtn.style.background = 'rgba(255,255,255,0.1)'; copyBtn.style.color = 'var(--text-secondary)'; };
                
                copyBtn.onclick = () => {
                    const code = pre.querySelector('code');
                    if (code) {
                        navigator.clipboard.writeText(code.innerText);
                        copyBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--success)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg> Copiado!';
                        copyBtn.style.color = 'var(--success)';
                        setTimeout(() => {
                            copyBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg> Copiar';
                            copyBtn.style.color = 'var(--text-secondary)';
                        }, 2000);
                    }
                };
                pre.appendChild(copyBtn);
                
                const block = pre.querySelector('code');
                if (block) hljs.highlightElement(block);
            });
        }

        function appendMessage(text, sender, isNewResponse = false) {
            if (text === null || text === undefined) { text = "❌ Erro: IA retornou resposta vazia."; }
            const container = document.getElementById('messagesContainer');
            const emptyState = document.getElementById('emptyState');
            if (emptyState) emptyState.remove();

            const wrapperDiv = document.createElement('div');
            wrapperDiv.className = `message-wrapper wrapper-${sender}`;
            wrapperDiv.tabIndex = 0;
            wrapperDiv.setAttribute('role', 'region');
            const autorLabel = (sender === 'user' ? 'Sua Pergunta' : 'Resposta da IA');
            wrapperDiv.setAttribute('aria-label', autorLabel);

            // Indicador para o leitor de telas
            const srIntro = document.createElement('span');
            srIntro.className = 'sr-only';
            srIntro.innerText = sender === 'user' ? 'Início da sua pergunta: ' : 'Início da resposta da IA: ';
            wrapperDiv.appendChild(srIntro);

            // Navegação e leitura de histórico de mensagens por teclado
            wrapperDiv.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' || e.key === 'Enter') {
                    e.preventDefault();
                    focarCampoMensagem();
                    return;
                }
                if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    let prev = wrapperDiv.previousElementSibling;
                    while (prev && !prev.classList.contains('message-wrapper')) {
                        prev = prev.previousElementSibling;
                    }
                    if (prev) {
                        prev.focus();
                    }
                } else if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    let next = wrapperDiv.nextElementSibling;
                    while (next && !next.classList.contains('message-wrapper')) {
                        next = next.nextElementSibling;
                    }
                    if (next) {
                        next.focus();
                    } else {
                        focarCampoMensagem();
                    }
                }
            });

            const msgDiv = document.createElement('div');
            msgDiv.className = `message ${sender}`;
            msgDiv.dataset.rawText = text;

            msgDiv.innerHTML = marked.parse(String(text));
            
            const actionBar = document.createElement('div');
            actionBar.className = 'message-actions';

            const svgCopy = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>`;
            const svgCheck = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--success)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>`;
            const svgEdit = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>`;
            
            const svgSpeaker = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>`;
            const svgSpeakerOff = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><line x1="23" y1="9" x2="17" y2="15"></line><line x1="17" y1="9" x2="23" y2="15"></line></svg>`;

            if (sender === 'ia') {
                const ttsBtn = document.createElement('button');
                ttsBtn.className = 'action-btn';
                ttsBtn.innerHTML = svgSpeaker;
                ttsBtn.title = "Ouvir resposta (Text-to-Speech)";
                ttsBtn.onclick = () => lerEmVozAlta(msgDiv, ttsBtn, svgSpeaker, svgSpeakerOff);
                actionBar.appendChild(ttsBtn);

                formatCodeBlocks(msgDiv);
            }
            
            // Adiciona clique nas imagens para visualizar em tela cheia
            msgDiv.querySelectorAll('img').forEach(img => {
                img.style.cursor = 'zoom-in';
                img.onclick = () => {
                    const modal = document.getElementById('imageModal');
                    document.getElementById('imageModalSrc').src = img.src;
                    modal.style.display = 'flex';
                    setTimeout(() => modal.classList.add('active'), 10);
                };
            });

            const svgRefresh = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><path d="M3 3v5h5"></path></svg>`;

            // Regex atualizado para limpar o SVG na hora de editar
            const cleanRegex = /<svg.*?>.*?<\/svg> \*\*\[.*?\]\*\*/g;

            const copyBtn = document.createElement('button');
            copyBtn.className = 'action-btn';
            copyBtn.innerHTML = svgCopy;
            copyBtn.title = "Copiar texto";
            copyBtn.onclick = () => {
                let cleanText = msgDiv.dataset.rawText.replace(/!\[.*?\]\(data:image.*?\)/g, '[Imagem Anexada]');
                cleanText = cleanText.replace(/<div class='attachment-chip'[^>]*>/g, '').replace(/<\/div>/g, '');
                navigator.clipboard.writeText(cleanText.trim());
                copyBtn.innerHTML = svgCheck;
                setTimeout(() => { copyBtn.innerHTML = svgCopy; }, 2000);
            };
            actionBar.appendChild(copyBtn);

            if (sender === 'user') {
                const editBtn = document.createElement('button');
                editBtn.className = 'action-btn';
                editBtn.innerHTML = svgEdit;
                editBtn.title = "Editar e reenviar";
                editBtn.onclick = () => {
                    document.getElementById('userInput').value = msgDiv.dataset.rawText.replace(/!\[.*?\]\(data:image.*?\)/g, '').replace(cleanRegex, '').trim();
                    document.getElementById('userInput').focus();
                };
                actionBar.appendChild(editBtn);
                
                const refreshBtn = document.createElement('button');
                refreshBtn.className = 'action-btn';
                refreshBtn.innerHTML = svgRefresh;
                refreshBtn.title = "Refazer esta pergunta";
                refreshBtn.onclick = () => {
                    document.getElementById('userInput').value = msgDiv.dataset.rawText.replace(/!\[.*?\]\(data:image.*?\)/g, '').replace(cleanRegex, '').trim();
                    sendMessage();
                };
                actionBar.appendChild(refreshBtn);
            } else {
                const refreshBtn = document.createElement('button');
                refreshBtn.className = 'action-btn';
                refreshBtn.innerHTML = svgRefresh;
                refreshBtn.title = "Refazer resposta";
                refreshBtn.onclick = () => {
                    let prevNode = wrapperDiv.previousElementSibling;
                    while (prevNode && !prevNode.classList.contains('wrapper-user')) { prevNode = prevNode.previousElementSibling; }
                    if (prevNode) {
                        document.getElementById('userInput').value = prevNode.querySelector('.message').dataset.rawText.replace(/!\[.*?\]\(data:image.*?\)/g, '').replace(cleanRegex, '').trim();
                        sendMessage();
                    }
                };
                actionBar.appendChild(refreshBtn);
            }

            wrapperDiv.appendChild(msgDiv);
            wrapperDiv.appendChild(actionBar);
            container.appendChild(wrapperDiv);
            container.scrollTop = container.scrollHeight;
            return wrapperDiv;
        }

        function handleEnter(e) { if (e.key === 'Enter') sendMessage(); }

        function showTypingIndicator() {
            const container = document.getElementById('messagesContainer');
            const wrapperDiv = document.createElement('div');
            wrapperDiv.className = `message-wrapper wrapper-ia`;
            wrapperDiv.id = 'typingIndicator';

            const msgDiv = document.createElement('div');
            msgDiv.className = `message ia`;
            msgDiv.innerHTML = `<div class="typing-indicator"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>`;
            
            wrapperDiv.appendChild(msgDiv);
            container.appendChild(wrapperDiv);
            container.scrollTop = container.scrollHeight;
        }

        function removeTypingIndicator() {
            const el = document.getElementById('typingIndicator');
            if (el) el.remove();
        }

        
        function interromperIA() {
            if (document.getElementById('stopBtn').style.display === 'none') return;
            
            currentRequestToken++; // Invalida a requisição ativa no frontend
            
            removeTypingIndicator();
            appendMessage("<em>[Geração interrompida pelo usuário]</em>", "ia", true);
            
            document.getElementById('sendBtn').style.display = 'flex';
            document.getElementById('stopBtn').style.display = 'none';
            
            const input = document.getElementById('userInput');
            const sendBtn = document.getElementById('sendBtn');
            isEnviandoMensagem = false;
            input.readOnly = false;
            input.disabled = false;
            sendBtn.disabled = false;
            focarCampoMensagem();
        }
        
        function sendMessage() {
            const input = document.getElementById('userInput');
            const sendBtn = document.getElementById('sendBtn');
            const text = input.value.trim();
            
            const hasFile = document.getElementById('imagePreview').style.display === 'block';
            const fileName = document.getElementById('imageName').innerText;
            
            if ((!text && !hasFile) || currentSessionId === null || isEnviandoMensagem) return;

            isEnviandoMensagem = true;
            input.readOnly = true;
            sendBtn.disabled = true;

            currentRequestToken++;
            const myToken = currentRequestToken;
            
            document.getElementById('sendBtn').style.display = 'none';
            document.getElementById('stopBtn').style.display = 'flex';
            
            pywebview.api.obter_imagem_base64().then(b64 => {
                let msgText = text;
                const clipSvg = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent-1)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 4px; margin-top: -2px;"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path></svg>`;

                if (b64) { msgText = `![Anexo](${b64})\n\n${text}`; } 
                else if (hasFile) { msgText = `${clipSvg} **[Arquivo Anexado: ${fileName}]**\n\n${text}`; }
                
                appendMessage(msgText, 'user', false);
                input.value = '';
                
                showTypingIndicator();
                
                // Anuncia claramente ao leitor de telas sem desativar o campo
                anunciarAoLeitor("Mensagem enviada. Aguarde, a IA está pensando...");

                // Feedback no NVDA se a IA demorar mais de 3.5 segundos
                const timerFeedbackDemora = setTimeout(() => {
                    if (isEnviandoMensagem) {
                        anunciarAoLeitor("Aguarde, processando...");
                    }
                }, 3500);
                
                // Fala "Processando" via TTS nativo do navegador
                pywebview.api.obter_configuracoes().then(cfg => {
                    if (cfg && cfg.auto_tts === true) {
                        try {
                            const u = new SpeechSynthesisUtterance("Processando...");
                            u.lang = 'pt-BR';
                            u.rate = 1.2;
                            window.speechSynthesis.speak(u);
                        } catch(e) {}
                    }
                });
                
                pywebview.api.processar_prompt(currentSessionId, text).then(function(resposta) {
                    if (myToken !== currentRequestToken) return; // Requisicao cancelada
                    
                    clearTimeout(timerFeedbackDemora);
                    document.getElementById('sendBtn').style.display = 'flex';
                    document.getElementById('stopBtn').style.display = 'none';
                    removeTypingIndicator();
                    const novaMsgEl = appendMessage(resposta, 'ia', true);
                    isEnviandoMensagem = false;
                    input.readOnly = false;
                    sendBtn.disabled = false;
                    removerImagem();
                    
                    // FOCO IMEDIATO NA RESPOSTA: O NVDA começa a ler a resposta completa sem interrupção
                    if (novaMsgEl) {
                        setTimeout(() => novaMsgEl.focus(), 100);
                    }
                    setTimeout(() => recarregarSessoes(), 2000);
                    
                    // Auto-TTS Check
                    pywebview.api.obter_configuracoes().then(cfg => {
                        if (cfg && cfg.auto_tts === true) {
                            setTimeout(() => {
                                const msgs = document.querySelectorAll('.message-wrapper.wrapper-ia');
                                if (msgs.length > 0) {
                                    const lastWrapper = msgs[msgs.length - 1];
                                    const ttsBtn = lastWrapper.querySelector('.action-btn[title*="Voz"], .action-btn[title*="Ouvir"]');
                                    if (ttsBtn) ttsBtn.click();
                                }
                            }, 300);
                        }
                    });
                }).catch(function() {
                    if (typeof timerFeedbackDemora !== 'undefined') clearTimeout(timerFeedbackDemora);
                    removeTypingIndicator();
                    isEnviandoMensagem = false;
                    input.readOnly = false;
                    sendBtn.disabled = false;
                    const erroEl = appendMessage("⚠️ Erro Fatal de Conexão.", 'ia', true);
                    if (erroEl) {
                        setTimeout(() => erroEl.focus(), 100);
                    }
                });
            });
        }

        // ==========================================
        // UTILITÁRIOS DA UI
        // ==========================================
        function fecharImageModal() {
            const modal = document.getElementById('imageModal');
            modal.classList.remove('active');
            setTimeout(() => { modal.style.display = 'none'; document.getElementById('imageModalSrc').src = ''; }, 300);
        }

        // ==========================================
        // CONTROLE DO MENU DE ANEXOS
        // ==========================================
        function toggleAttachmentMenu(e) {
            if (e) e.stopPropagation();
            const menu = document.getElementById('attachmentMenu');
            const btnAttachment = document.getElementById('btnAttachment');

            if (menu.classList.contains('active')) {
                menu.classList.remove('active');
                setTimeout(() => { menu.style.display = 'none'; }, 200);
                if (btnAttachment) btnAttachment.focus();
            } else {
                menu.style.display = 'flex';
                setTimeout(() => { 
                    menu.classList.add('active'); 
                    // Move foco para o primeiro botão de anexo
                    const primeiroBtn = menu.querySelector('button');
                    if (primeiroBtn) primeiroBtn.focus();
                }, 50);
            }
        }

        // Navegação por teclado no menu de anexos (Setas Cima / Baixo / Esc)
        document.addEventListener('keydown', (e) => {
            const menu = document.getElementById('attachmentMenu');
            if (!menu || !menu.classList.contains('active')) return;

            const botoes = Array.from(menu.querySelectorAll('button'));
            const indexAtual = botoes.indexOf(document.activeElement);

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                const prox = (indexAtual + 1) % botoes.length;
                botoes[prox].focus();
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                const ant = (indexAtual - 1 + botoes.length) % botoes.length;
                botoes[ant].focus();
            } else if (e.key === 'Escape') {
                e.preventDefault();
                toggleAttachmentMenu(null);
            }
        });

        function capturarTela() {
            toggleAttachmentMenu(new Event('click'));
            document.body.style.opacity = '0.5'; // Feedback visual de captura
            pywebview.api.capturar_tela().then(nome => { 
                document.body.style.opacity = '1';
                if (nome) { 
                    document.getElementById('imagePreview').style.display = 'block'; 
                    document.getElementById('imageName').innerText = nome; 
                } 
            }); 
        }

        function selecionarProjeto() {
            toggleAttachmentMenu(new Event('click'));
            
            pywebview.api.selecionar_projeto().then(caminho => {
                if(caminho) {
                    document.getElementById('imagePreview').style.display = 'block';
                    document.getElementById('imageName').innerText = "Projeto Anexado (Contexto Extraído)";
                    const svgContainer = document.querySelector('#imagePreview svg');
                    if(svgContainer) {
                        svgContainer.innerHTML = '<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>';
                    }
                }
            });
        }
        
        function anexarArquivo(tipo) {
            toggleAttachmentMenu(new Event('click'));
            pywebview.api.escolher_arquivo(tipo).then(nome => { 
                if (nome) { 
                    document.getElementById('imagePreview').style.display = 'block'; 
                    document.getElementById('imageName').innerText = nome; 
                } 
            }); 
        }

        function removerImagem() { 
            document.getElementById('imagePreview').style.display = 'none'; 
            document.getElementById('imageName').innerText = ''; 
            pywebview.api.limpar_arquivo(); 
        }

        // --- FUNÇÕES DE ANEXO DO MODO DUELO ---
        function toggleAttachmentMenuDuel(e) {
            if (e) e.stopPropagation();
            const menu = document.getElementById('attachmentMenuDuel');
            if (menu.classList.contains('active')) {
                menu.classList.remove('active');
                setTimeout(() => { menu.style.display = 'none'; }, 200);
            } else {
                menu.style.display = 'flex';
                setTimeout(() => { menu.classList.add('active'); }, 10);
            }
        }

        function capturarTelaDuelo() {
            toggleAttachmentMenuDuel(new Event('click'));
            document.body.style.opacity = '0.5';
            pywebview.api.capturar_tela().then(nome => { 
                document.body.style.opacity = '1';
                if (nome) { 
                    document.getElementById('imagePreviewDuel').style.display = 'block'; 
                    document.getElementById('imageNameDuel').innerText = nome; 
                } 
            });
        }

        function anexarArquivoDuelo(tipo) {
            toggleAttachmentMenuDuel(new Event('click'));
            pywebview.api.escolher_arquivo(tipo).then(nome => { 
                if (nome) { 
                    document.getElementById('imagePreviewDuel').style.display = 'block'; 
                    document.getElementById('imageNameDuel').innerText = nome; 
                } 
            });
        }

        function removerImagemDuelo() {
            const preview = document.getElementById('imagePreviewDuel');
            if (preview) preview.style.display = 'none'; 
            const name = document.getElementById('imageNameDuel');
            if (name) name.innerText = ''; 
            pywebview.api.limpar_arquivo(); 
        }
        
        
        let gravandoAudio = false;

        function cancelarAudio() {
            if (!gravandoAudio) return;
            gravandoAudio = false;
            esconderOverlayVoz();
            if (window.pywebview && pywebview.api) {
                if (typeof pywebview.api.cancelar_audio === 'function') {
                    pywebview.api.cancelar_audio();
                } else if (typeof pywebview.api.parar_audio === 'function') {
                    pywebview.api.parar_audio();
                }
            }
            anunciarParaLeitorDeTela("Gravação cancelada.");
            focarCampoMensagem();
        }

        function toggleAudio(autoEnviar = true) { 
            if (gravandoAudio) {
                // Se já estiver ouvindo, pressionar F2 cancela imediatamente
                cancelarAudio();
                return;
            }

            gravandoAudio = true;
            mostrarOverlayVoz();
            anunciarParaLeitorDeTela("Microfone ativado. Fale após o bipe. Pressione F2 para cancelar.");
            
            pywebview.api.gravar_audio().then(texto => { 
                if (!gravandoAudio) return; // Foi cancelado durante a captura
                gravandoAudio = false;
                esconderOverlayVoz();

                if (!texto || texto.startsWith("[Erro]")) {
                    mostrarToastErro(texto || "[Erro] Não consegui ouvir.");
                    anunciarParaLeitorDeTela(texto || "Não consegui ouvir. Tente novamente com F2.");
                    focarCampoMensagem();
                } else if (texto.startsWith("[Cancelado]")) {
                    anunciarParaLeitorDeTela("Gravação cancelada.");
                    focarCampoMensagem();
                } else {
                    const inp = document.getElementById('userInput');
                    if (inp) inp.value = texto;
                    focarCampoMensagem();
                    if (autoEnviar && typeof sendMessage === 'function') {
                        sendMessage();
                    }
                }
            }).catch(e => {
                if (!gravandoAudio) return;
                gravandoAudio = false;
                esconderOverlayVoz();
                mostrarToastErro("[Erro] Falha no microfone.");
                focarCampoMensagem();
            }); 
        }

        function toggleAudioDuel() { 
            if (gravandoAudio) {
                cancelarAudio();
                return;
            }

            gravandoAudio = true;
            mostrarOverlayVoz();
            pywebview.api.gravar_audio().then(texto => { 
                if (!gravandoAudio) return;
                gravandoAudio = false;
                esconderOverlayVoz();

                if (texto && !texto.startsWith("[Erro]") && !texto.startsWith("[Cancelado]")) {
                    const dInp = document.getElementById('duelInput');
                    if (dInp) dInp.value = texto;
                } else if (texto && texto.startsWith("[Erro]")) {
                    mostrarToastErro(texto);
                }
            }).catch(e => {
                if (!gravandoAudio) return;
                gravandoAudio = false;
                esconderOverlayVoz();
                mostrarToastErro("[Erro] Falha no microfone.");
            }); 
        }

        // --- FUNÇÕES DE UI DE VOZ ---
        function mostrarOverlayVoz() {
            let overlay = document.getElementById('vozOverlay');
            if (!overlay) {
                overlay = document.createElement('div');
                overlay.id = 'vozOverlay';
                overlay.style.position = 'fixed';
                overlay.style.top = '0';
                overlay.style.left = '0';
                overlay.style.width = '100vw';
                overlay.style.height = '100vh';
                overlay.style.background = 'rgba(0, 0, 0, 0.7)';
                overlay.style.backdropFilter = 'blur(5px)';
                overlay.style.zIndex = '999999';
                overlay.style.display = 'flex';
                overlay.style.alignItems = 'center';
                overlay.style.justifyContent = 'center';
                overlay.style.flexDirection = 'column';
                overlay.style.userSelect = 'none';
                
                overlay.innerHTML = `
                    <div id="vozOverlayCircle" style="background: rgba(15, 15, 20, 0.9); border: 1px solid var(--accent-1); border-radius: 50%; width: 120px; height: 120px; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 30px var(--accent-1); animation: pulsar 1.5s infinite; cursor: pointer;" title="Clique para cancelar (F2 / Esc)">
                        <svg width="50" height="50" viewBox="0 0 24 24" fill="none" stroke="var(--accent-1)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg>
                    </div>
                    <h2 style="color: white; margin-top: 30px; font-family: 'Inter', sans-serif; font-weight: 500;">Ouvindo...</h2>
                    <p style="color: #a1a1aa; font-family: 'Inter', sans-serif; font-size: 0.9rem;">Fale claramente no microfone (5 segundos)</p>
                    <button type="button" id="vozBtnCancelar" style="margin-top: 18px; background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.2); color: #e4e4e7; padding: 8px 22px; border-radius: 20px; font-size: 0.85rem; cursor: pointer; transition: all 0.2s; font-family: 'Inter', sans-serif; display: flex; align-items: center; gap: 8px;">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                        Cancelar (F2 ou Esc)
                    </button>
                    <style>
                        @keyframes pulsar {
                            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(124, 58, 237, 0.7); }
                            70% { transform: scale(1); box-shadow: 0 0 0 30px rgba(124, 58, 237, 0); }
                            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(124, 58, 237, 0); }
                        }
                        #vozBtnCancelar:hover {
                            background: rgba(239, 68, 68, 0.2) !important;
                            border-color: #ef4444 !important;
                            color: #fca5a5 !important;
                        }
                    </style>
                `;
                
                overlay.addEventListener('click', () => {
                    cancelarAudio();
                });
                
                document.body.appendChild(overlay);
            }
            overlay.style.display = 'flex';
        }

        function esconderOverlayVoz() {
            const overlay = document.getElementById('vozOverlay');
            if (overlay) overlay.style.display = 'none';
        }

        function mostrarToastErro(mensagem) {
            let toast = document.createElement('div');
            toast.style.position = 'fixed';
            toast.style.bottom = '30px';
            toast.style.left = '50%';
            toast.style.transform = 'translateX(-50%)';
            toast.style.background = '#ef4444'; // red-500
            toast.style.color = 'white';
            toast.style.padding = '12px 24px';
            toast.style.borderRadius = '8px';
            toast.style.boxShadow = '0 4px 12px rgba(0,0,0,0.5)';
            toast.style.fontFamily = 'Inter, sans-serif';
            toast.style.zIndex = '9999999';
            toast.innerText = mensagem;
            document.body.appendChild(toast);
            
            setTimeout(() => {
                toast.style.opacity = '0';
                toast.style.transition = 'opacity 0.5s';
                setTimeout(() => toast.remove(), 500);
            }, 4000);
        }

        function abrirConfiguracoes() {
            const modal = document.getElementById('settingsModal');
            
            // Tenta buscar os dados do Python. Se falhar, abre em branco.
            try {
                pywebview.api.obter_configuracoes().then(config => {
                    if (config) {
                        document.getElementById('configProvider').value = config.provider || 'gemini';
                        document.getElementById('configLanguage').value = config.language || 'pt_BR';
                        carregarListaIdiomas(config.language || 'pt_BR');
                        // Atalhos
                        if(config.shortcuts) {
                            window.appShortcuts = Object.assign(window.appShortcuts, config.shortcuts);
                            const map = { shortMic: 'mic', shortStop: 'stop', shortConfig: 'config', shortClear: 'clear', shortHelp: 'help', shortExit: 'exit', shortTxt: 'txt', shortMail: 'mail', shortWeb: 'web', shortFiles: 'files', shortCalc: 'calc', shortWhats: 'whats' };
                            for(let id in map) {
                                if(document.getElementById(id)) document.getElementById(id).value = config.shortcuts[map[id]] || window.appShortcuts[map[id]];
                            }
                        }

                        if (document.getElementById('configInterfaceMode')) {
                            document.getElementById('configInterfaceMode').value = config.interface_mode || 'normal';
                        }
                        document.getElementById('configSystemPrompt').value = config.system_prompt || '';
                        
                        if (document.getElementById('configFullscreen')) {
                            document.getElementById('configFullscreen').checked = (config.start_fullscreen !== undefined) ? config.start_fullscreen : true;
                        }
                        document.getElementById('configStartup').checked = config.start_with_windows || false;
                        document.getElementById('configTray').checked = config.minimize_to_tray || false;
                        
                        document.getElementById('configAgente').checked = config.agent_mode || false;
                        document.getElementById('configAutoVoz').checked = config.auto_tts || false;
                        if (document.getElementById('configBridgeVox')) {
                            document.getElementById('configBridgeVox').checked = config.always_voice || false;
                        }
                        
                        const chaves = config.api_keys || {};
                        document.getElementById('keyGemini').value = chaves['gemini'] || '';
                        if (document.getElementById('keyGroq')) document.getElementById('keyGroq').value = chaves['groq'] || '';
                        document.getElementById('keyQwen').value = chaves['qwen'] || '';
                        document.getElementById('keyOpenai').value = chaves['openai'] || '';
                        document.getElementById('keyClaude').value = chaves['claude'] || '';
                        if(document.getElementById('pathDesktop')) document.getElementById('pathDesktop').value = config.pathDesktop || '';
                        if(document.getElementById('pathDocuments')) document.getElementById('pathDocuments').value = config.pathDocuments || '';
                        if(document.getElementById('pathDownloads')) document.getElementById('pathDownloads').value = config.pathDownloads || '';
                        if(document.getElementById('pathMusic')) document.getElementById('pathMusic').value = config.pathMusic || '';
                        if(document.getElementById('pathPictures')) document.getElementById('pathPictures').value = config.pathPictures || '';
                        if(document.getElementById('pathVideos')) document.getElementById('pathVideos').value = config.pathVideos || '';
                        const cred = config.email_credentials || {};
                        document.getElementById('keyEmail').value = cred.email || '';
                        document.getElementById('keyEmailPass').value = cred.app_password || '';
                    }
                    
                    // Reseta para a aba 'Geral' e exibe o modal
                    switchSettingsTab({target: document.querySelector('.tab-btn')}, 'geral');
                    mostrarPainel(modal);

                }).catch(err => {
                    console.error("Erro ao obter configurações do Python:", err);
                    mostrarPainel(modal); // Abre mesmo com erro
                });
            } catch (error) {
                console.error("Falha de conexão com backend:", error);
                mostrarPainel(modal); // Abre mesmo com erro
            }
        }

        function salvarConfiguracaoInicial() {
            const btn = document.querySelector('.api-setup-box .btn-new-chat');
            btn.innerText = "Conectando...";
            btn.disabled = true;

            const provider = document.getElementById('setupProvider').value;
            const payload = {
                provider: provider,
                language: 'pt_BR',
                system_prompt: '',
                start_with_windows: false,
                minimize_to_tray: false,
                interface_mode: document.getElementById('setupInterfaceMode').value,
                api_keys: {
                    gemini: document.getElementById('setupKeyGemini').value.trim(),
                    groq: document.getElementById('setupKeyGroq') ? document.getElementById('setupKeyGroq').value.trim() : '',
                    openai: document.getElementById('setupKeyOpenai').value.trim(),
                    claude: document.getElementById('setupKeyClaude').value.trim(),
                    qwen: document.getElementById('setupKeyQwen').value.trim()
                }
            };
            
            // Só exige que o provedor principal tenha chave
            if (!payload.api_keys[provider]) {
                mostrarToast(`Por favor, insira a chave da API para o provedor selecionado (${provider.toUpperCase()}).`, true);
                btn.innerText = "Conectar e Iniciar";
                btn.disabled = false;
                return;
            }

            carregarIdioma(payload.language);
            pywebview.api.salvar_preferencias(payload).then(() => {
                document.getElementById('apiSetupOverlay').style.display = 'none';
                
                // RESTAURA O CONTAINER PRINCIPAL PARA O NVDA
                const appContainer = document.querySelector('.app-container');
                if (appContainer) {
                    appContainer.removeAttribute('aria-hidden');
                    appContainer.removeAttribute('inert');
                }
                const userInput = document.getElementById('userInput');
                if (userInput) userInput.focus();

                // Repassa os valores preenchidos para a aba de configurações (para caso ele abra depois)
                document.getElementById('configProvider').value = provider;
                if (document.getElementById('configInterfaceMode')) document.getElementById('configInterfaceMode').value = payload.interface_mode;
                document.getElementById('keyGemini').value = payload.api_keys.gemini;
                if (document.getElementById('keyGroq')) document.getElementById('keyGroq').value = payload.api_keys.groq;
                document.getElementById('keyOpenai').value = payload.api_keys.openai;
                document.getElementById('keyClaude').value = payload.api_keys.claude;
                document.getElementById('keyQwen').value = payload.api_keys.qwen;

                // Força o trigger do onchange para o dropdown customizado atualizar
                document.getElementById('configProvider').dispatchEvent(new Event('change'));
                
                carregarSessoesIniciais();
                focarCampoMensagem();
            }).catch(err => {
                mostrarToast("Erro ao salvar configuração: " + err, true);
                btn.innerText = "Conectar e Iniciar";
                btn.disabled = false;
            });
        }

        // Função auxiliar para exibir o painel de configurações com acessibilidade nativa
        function mostrarPainel(modal) {
            modal.style.display = 'flex';
            setTimeout(() => modal.style.opacity = '1', 10);
            if (window.innerWidth <= 768) toggleSidebar();

            // ISOLAMENTO DE ACESSIBILIDADE PARA LEITORES DE TELA (NVDA / NARRADOR)
            const appContainer = document.querySelector('.app-container');
            if (appContainer) {
                appContainer.setAttribute('aria-hidden', 'true');
                appContainer.setAttribute('inert', '');
            }

            // Move o foco para a primeira aba ativa ou primeiro botão do modal
            setTimeout(() => {
                const focoInicial = modal.querySelector('.tab-btn.active, .settings-header .close-btn, button');
                if (focoInicial) focoInicial.focus();
            }, 50);
        }

        function fecharConfiguracoes() {
            const modal = document.getElementById('settingsModal');
            if (modal) {
                modal.style.opacity = '0';
                setTimeout(() => { modal.style.display = 'none'; }, 300);
            }

            // RESTAURA ACESSIBILIDADE DO CONTAINER PRINCIPAL
            const appContainer = document.querySelector('.app-container');
            if (appContainer) {
                appContainer.removeAttribute('aria-hidden');
                appContainer.removeAttribute('inert');
            }

            // Devolve sempre o foco prioritário para o campo de mensagem
            focarCampoMensagem();
        }

        function salvarConfiguracoes() {
            // Pega especificamente o botão de confirmar do modal de configurações
            const btnSalvar = document.querySelector('#settingsModal .dialog-btn.confirm');
            if(btnSalvar) {
                btnSalvar.disabled = true;
                btnSalvar.innerText = "Salvando...";
            }

            const payload = {
                provider: document.getElementById('configProvider').value,
                language: document.getElementById('configLanguage').value,
                    interface_mode: document.getElementById('configInterfaceMode').value,
                system_prompt: document.getElementById('configSystemPrompt').value,
                start_fullscreen: document.getElementById('configFullscreen') ? document.getElementById('configFullscreen').checked : true,
                start_with_windows: document.getElementById('configStartup').checked,
                minimize_to_tray: document.getElementById('configTray').checked,
                agent_mode: document.getElementById('configAgente').checked,
                auto_tts: document.getElementById('configAutoVoz').checked,
                always_voice: document.getElementById('configBridgeVox') ? document.getElementById('configBridgeVox').checked : false,
                shortcuts: {
                    mic: document.getElementById('shortMic') ? document.getElementById('shortMic').value : 'F2',
                    stop: document.getElementById('shortStop') ? document.getElementById('shortStop').value : 'Escape',
                    config: document.getElementById('shortConfig') ? document.getElementById('shortConfig').value : 'F10',
                    clear: document.getElementById('shortClear') ? document.getElementById('shortClear').value : 'F5',
                    help: document.getElementById('shortHelp') ? document.getElementById('shortHelp').value : 'F1',
                    exit: document.getElementById('shortExit') ? document.getElementById('shortExit').value : 'F4',
                    txt: document.getElementById('shortTxt') ? document.getElementById('shortTxt').value : 'T',
                    mail: document.getElementById('shortMail') ? document.getElementById('shortMail').value : 'R',
                    web: document.getElementById('shortWeb') ? document.getElementById('shortWeb').value : 'I',
                    files: document.getElementById('shortFiles') ? document.getElementById('shortFiles').value : 'A',
                    calc: document.getElementById('shortCalc') ? document.getElementById('shortCalc').value : 'C',
                    whats: document.getElementById('shortWhats') ? document.getElementById('shortWhats').value : 'Z'
                },
                pathDesktop: document.getElementById('pathDesktop') ? document.getElementById('pathDesktop').value.trim() : "",
                pathDocuments: document.getElementById('pathDocuments') ? document.getElementById('pathDocuments').value.trim() : "",
                pathDownloads: document.getElementById('pathDownloads') ? document.getElementById('pathDownloads').value.trim() : "",
                pathMusic: document.getElementById('pathMusic') ? document.getElementById('pathMusic').value.trim() : "",
                pathPictures: document.getElementById('pathPictures') ? document.getElementById('pathPictures').value.trim() : "",
                pathVideos: document.getElementById('pathVideos') ? document.getElementById('pathVideos').value.trim() : "",
                api_keys: {
                    gemini: document.getElementById('keyGemini').value,
                    groq: document.getElementById('keyGroq') ? document.getElementById('keyGroq').value : '',
                    qwen: document.getElementById('keyQwen').value,
                    openai: document.getElementById('keyOpenai').value,
                    claude: document.getElementById('keyClaude').value
                },
                email_credentials: {
                    email: document.getElementById('keyEmail').value,
                    app_password: document.getElementById('keyEmailPass').value
                }
            };
            
            pywebview.api.salvar_preferencias(payload).then(() => {
                fecharConfiguracoes(); // Garante o fechamento
                
                // Aplica o idioma escolhido imediatamente na tela
                if (payload.language) {
                    carregarIdioma(payload.language);
                }
                
                const mode = payload.interface_mode;
                const isHighContrast = document.body.classList.contains('high-contrast-theme');
                if ((mode === 'high_contrast' && !isHighContrast) || (mode === 'normal' && isHighContrast)) {
                    window.location.reload();
                    return;
                }
                
                pywebview.api.obter_modelos().then(modelos => {
                    const selector = document.getElementById('modelSelector');
                    if (selector) {
                        selector.innerHTML = '';
                        modelos.forEach(m => {
                            const opt = document.createElement('option');
                            opt.value = m; 
                            opt.innerText = m.replace('models/', '').toUpperCase();
                            selector.appendChild(opt);
                        });
                        
                        // Garante que o dropdown de provedor rápido acompanhe a mudança das configurações globais!
                        const quickProv = document.getElementById('quickProviderSelector');
                        if (quickProv) { 
                            quickProv.value = payload.provider; 
                            forceUpdateCustomUI('quickProviderSelector');
                        }
                    }
                });
                
                appendMessage(`⚙️ **Configurações:** O motor de IA atual foi alterado para **${payload.provider.toUpperCase()}**.`, 'ia');
                
                // Restaura o botão
                if(btnSalvar) {
                    btnSalvar.disabled = false;
                    btnSalvar.innerText = "Salvar Alterações";
                }
            }).catch(err => {
                appendMessage(`⚠️ Erro ao salvar preferências: ${err}`, 'ia');
                fecharConfiguracoes(); // Fecha o modal mesmo se der erro no Python
                if(btnSalvar) {
                    btnSalvar.disabled = false;
                    btnSalvar.innerText = "Salvar Alterações";
                }
            });
        }

        // ==========================================
        // MENU DE CONTEXTO CUSTOMIZADO (BOTÃO DIREITO)
        // ==========================================
        document.addEventListener('contextmenu', function(e) {
            const selectedText = window.getSelection().toString().trim();
            // Só mostra o menu se tiver texto selecionado
            if (selectedText.length > 0) {
                e.preventDefault();
                const menu = document.getElementById('customContextMenu');
                menu.style.display = 'block';
                menu.style.left = e.pageX + 'px';
                menu.style.top = e.pageY + 'px';
            }
        });

        // Esconde o menu se clicar em qualquer lugar
        document.addEventListener('click', function(e) {
            const menu = document.getElementById('customContextMenu');
            if (menu) menu.style.display = 'none';
        });

        function copiarTextoSelecionado() {
            const texto = window.getSelection().toString();
            if (texto) {
                navigator.clipboard.writeText(texto);
                document.getElementById('customContextMenu').style.display = 'none';
            }
        }

        // ==========================================
        // SISTEMA DE DIALOGS CUSTOMIZADOS
        // ==========================================
        let dialogResolve = null;

        function showCustomDialog(type, title, message, defaultValue = "") {
            return new Promise((resolve) => {
                dialogResolve = resolve;
                const overlay = document.getElementById('customDialog');
                const box = overlay.querySelector('.custom-dialog-box');
                const titleEl = document.getElementById('dialogTitle');
                const msgEl = document.getElementById('dialogMessage');
                const inputEl = document.getElementById('dialogInput');
                const confirmBtn = document.getElementById('dialogConfirmBtn');
                const cancelBtn = overlay.querySelector('.dialog-btn.cancel');

                titleEl.innerText = title;
                msgEl.innerText = message;
                msgEl.style.display = message ? 'block' : 'none';
                cancelBtn.style.display = 'block'; // Padrão: mostra o cancelar

                if (type === 'prompt') {
                    inputEl.style.display = 'block';
                    inputEl.value = defaultValue;
                    confirmBtn.className = 'dialog-btn confirm';
                    confirmBtn.innerText = t('btn_save', 'Salvar');
                    cancelBtn.innerText = t('btn_cancel', 'Cancelar');
                } else if (type === 'confirm-danger') {
                    inputEl.style.display = 'none';
                    confirmBtn.className = 'dialog-btn danger';
                    confirmBtn.innerText = t('btn_delete', 'Excluir');
                    cancelBtn.innerText = t('btn_cancel', 'Cancelar');
                } else if (type === 'confirm-exit') {
                    inputEl.style.display = 'none';
                    confirmBtn.className = 'dialog-btn danger';
                    confirmBtn.innerText = t('dialog_exit_btn_confirm', 'Fechar Programa (Enter)');
                    cancelBtn.innerText = t('dialog_exit_btn_cancel', 'Cancelar (Esc)');
                } else if (type === 'info') {
                    inputEl.style.display = 'none';
                    confirmBtn.className = 'dialog-btn confirm';
                    confirmBtn.innerText = 'OK';
                    cancelBtn.style.display = 'none'; // Esconde Cancelar no Info
                }

                overlay.style.display = 'flex';
                setTimeout(() => {
                    overlay.style.opacity = '1';
                    box.style.transform = 'scale(1)';
                    if (type === 'prompt') {
                        inputEl.focus();
                    } else if (type === 'confirm-exit') {
                        confirmBtn.focus();
                    } else {
                        confirmBtn.focus();
                    }
                }, 10);
            });
        }

        window.confirmarEncerramento = async function() {
            const overlay = document.getElementById('customDialog');
            if (overlay && overlay.style.display === 'flex') {
                return;
            }

            const titulo = t('dialog_exit_title', 'Encerrar Assistente');
            const mensagem = t('dialog_exit_msg', 'O Assistente Cromak Bridge Vox será encerrado. Deseja realmente fechar o programa? Pressione Enter para fechar ou Esc para cancelar.');

            anunciarAoLeitor(`${titulo}. ${mensagem}`, true);

            const confirmado = await showCustomDialog('confirm-exit', titulo, mensagem);
            if (confirmado) {
                anunciarAoLeitor(t('dialog_exit_confirming', 'Encerrando o Cromak Bridge Vox. Até logo!'), true);
                setTimeout(() => {
                    if (window.pywebview && pywebview.api && pywebview.api.encerrar_sistema) {
                        pywebview.api.encerrar_sistema();
                    } else {
                        window.close();
                    }
                }, 180);
            } else {
                anunciarAoLeitor(t('dialog_exit_cancelled', 'Encerramento cancelado. Continuando no assistente.'));
                focarCampoMensagem();
            }
        };

        function closeCustomDialog(isConfirm) {
            const overlay = document.getElementById('customDialog');
            const box = overlay.querySelector('.custom-dialog-box');
            const inputEl = document.getElementById('dialogInput');

            overlay.style.opacity = '0';
            box.style.transform = 'scale(0.95)';
            
            setTimeout(() => {
                overlay.style.display = 'none';
                if (dialogResolve) {
                    if (isConfirm) {
                        dialogResolve(inputEl.style.display === 'block' ? inputEl.value.trim() : true);
                    } else {
                        dialogResolve(false);
                    }
                    dialogResolve = null;
                }
            }, 200);
        }

        function aplicarPresetComportamento() {
            const select = document.getElementById('presetComportamento');
            const textarea = document.getElementById('configSystemPrompt');
            
            if (select.value === 'assistente') {
                textarea.value = "Você é um assistente virtual extremamente eficiente. Vá direto ao ponto, evite jargões desnecessários e estruture suas respostas da forma mais clara e objetiva possível.";
            } else if (select.value === 'programador') {
                textarea.value = "Você é um Engenheiro de Software Sênior. Forneça códigos limpos, otimizados, e sempre com comentários explicativos nas partes complexas. Utilize as melhores práticas de Clean Code, SOLID e evite gambiarras.";
            } else if (select.value === 'escritor') {
                textarea.value = "Você é um Copywriter e Escritor Criativo de alto nível. Use um tom persuasivo, humano e envolvente. Utilize técnicas de storytelling e formate o texto (negritos, itálicos e parágrafos curtos) para prender a atenção do leitor do início ao fim.";
            } else if (select.value === '') {
                textarea.value = ""; // Limpa se escolher personalizado
            }
        }

        // ==========================================
        // CONTROLES DO POP-UP MENU (CONFIGURAÇÕES)
        // ==========================================
        function toggleSettingsMenu(e) {
            if (e) e.stopPropagation();
            const popup = document.getElementById('settingsPopup');
            const btnConfig = document.getElementById('btnMainConfig');
            
            if (popup.classList.contains('active')) {
                popup.classList.remove('active');
                setTimeout(() => { popup.style.display = 'none'; }, 200);
                if (btnConfig) btnConfig.focus();
            } else {
                popup.style.display = 'flex';
                setTimeout(() => { 
                    popup.classList.add('active'); 
                    // Move foco imediatamente para a primeira opção (Preferências)
                    const primeiroItem = popup.querySelector('button');
                    if (primeiroItem) primeiroItem.focus();
                }, 50);
            }
        }

        // Navegação por Teclado dentro do Menu Pop-up (Setas Cima / Baixo / Esc)
        document.addEventListener('keydown', (e) => {
            const popup = document.getElementById('settingsPopup');
            if (!popup || !popup.classList.contains('active')) return;

            const itens = Array.from(popup.querySelectorAll('button'));
            const indexAtual = itens.indexOf(document.activeElement);

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                const proximoIndex = (indexAtual + 1) % itens.length;
                itens[proximoIndex].focus();
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                const anteriorIndex = (indexAtual - 1 + itens.length) % itens.length;
                itens[anteriorIndex].focus();
            } else if (e.key === 'Escape') {
                e.preventDefault();
                toggleSettingsMenu(null);
            }
        });

        function abrirPreferencias() {
            const popup = document.getElementById('settingsPopup');
            if (popup) { popup.classList.remove('active'); popup.style.display = 'none'; }
            abrirConfiguracoes(); // Chama a janela principal de APIs original
        }

        async function abrirSobre() {
            const popup = document.getElementById('settingsPopup');
            if (popup) { popup.classList.remove('active'); popup.style.display = 'none'; }
            if (window.pywebview && pywebview.api && pywebview.api.obter_versao_app) {
                try {
                    const info = await pywebview.api.obter_versao_app();
                    const el = document.getElementById('aboutAppVersion');
                    if (el && info && info.full) el.innerText = info.full;
                } catch (e) {}
            }
            document.getElementById('aboutModal').style.display = 'flex';
        }
        
        function fecharSobre() {
            document.getElementById('aboutModal').style.display = 'none';
        }

        async function abrirAjuda() {
            const popup = document.getElementById('settingsPopup');
            if (popup) { popup.classList.remove('active'); popup.style.display = 'none'; }
            pywebview.api.abrir_janela_ajuda();
        }

        // ==========================================
        // SISTEMA DE ABAS (CONFIGURAÇÕES)
        // ==========================================
        function switchSettingsTab(event, tabName) {
            // 1. Esconde todas as abas
            document.querySelectorAll('.settings-tab').forEach(el => {
                el.style.display = 'none';
            });
            
            // 2. Remove o visual "ativo" de todos os botões e atualiza ARIA
            document.querySelectorAll('.tab-btn').forEach(el => {
                el.classList.remove('active');
                el.setAttribute('aria-selected', 'false');
            });
            
            // 3. Mostra a aba clicada e marca o botão como ativo
            const tabConteudo = document.getElementById(`tab-${tabName}`);
            if (tabConteudo) {
                tabConteudo.style.display = 'block';
                if (tabName === 'atalhos') {
                    setTimeout(() => { if (typeof initShortcuts === 'function') initShortcuts(); }, 50);
                }
            }

            if (event && event.target) {
                event.target.classList.add('active');
                event.target.setAttribute('aria-selected', 'true');
            }
        }

        // ==========================================
        // CLIQUE GLOBAL (ESCONDE MENUS SE CLICAR FORA)
        // ==========================================
        document.addEventListener('click', function(e) {
            const contextMenu = document.getElementById('customContextMenu');
            if (contextMenu) contextMenu.style.display = 'none';
            
            const popup = document.getElementById('settingsPopup');
            const btnMainConfig = document.getElementById('btnMainConfig');
            if (popup && popup.classList.contains('active') && !popup.contains(e.target) && !btnMainConfig.contains(e.target)) {
                popup.classList.remove('active');
                setTimeout(() => { popup.style.display = 'none'; }, 200);
            }

            const attachMenu = document.getElementById('attachmentMenu');
            const btnAttach = document.getElementById('btnAttachment');
            if (attachMenu && attachMenu.classList.contains('active') && !attachMenu.contains(e.target) && !btnAttach.contains(e.target)) {
                attachMenu.classList.remove('active');
                setTimeout(() => { attachMenu.style.display = 'none'; }, 200);
            }
            
            const attachMenuDuel = document.getElementById('attachmentMenuDuel');
            const btnAttachDuel = document.getElementById('btnAttachmentDuel');
            if (attachMenuDuel && attachMenuDuel.classList.contains('active') && !attachMenuDuel.contains(e.target) && (!btnAttachDuel || !btnAttachDuel.contains(e.target))) {
                attachMenuDuel.classList.remove('active');
                setTimeout(() => { attachMenuDuel.style.display = 'none'; }, 200);
            }
            
            // Fecha os selects customizados
            document.querySelectorAll('.custom-select-dropdown').forEach(d => {
                if (d.classList.contains('active') && !d.parentNode.contains(e.target)) {
                    d.classList.remove('active');
                    setTimeout(() => { d.style.display = 'none'; }, 200);
                }
            });
        });

        // ==========================================
        // FUNÇÕES DA ABA DE CONFIGURAÇÕES
        // ==========================================
        function alternarVisibilidade(inputId) {
            const input = document.getElementById(inputId);
            if (input.type === 'password') {
                input.type = 'text';
            } else {
                input.type = 'password';
            }
        }

        async function colarTexto(inputId) {
            try {
                const text = await navigator.clipboard.readText();
                document.getElementById(inputId).value = text;
            } catch (err) {
                console.error("Falha ao colar: ", err);
            }
        }

        // ==========================================
        // BLOQUEIO GLOBAL DEFINITIVO E DRAG & DROP
        // ==========================================
        const areaDeChat = document.getElementById('mainConversa');

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            window.addEventListener(eventName, function(e) {
                e.preventDefault();
                e.stopPropagation();

                if (eventName === 'dragover') {
                    areaDeChat.classList.add('drag-active');
                } 
                else if (eventName === 'dragleave') {
                    if (e.clientX === 0 || e.clientY === 0) {
                        areaDeChat.classList.remove('drag-active');
                    }
                } 
                else if (eventName === 'drop') {
                    areaDeChat.classList.remove('drag-active');
                    
                    if (e.dataTransfer && e.dataTransfer.files.length > 0) {
                        const file = e.dataTransfer.files[0];
                        const reader = new FileReader();
                        
                        reader.onload = function(evt) {
                            const base64Data = evt.target.result;
                            pywebview.api.receber_arquivo_drop(file.name, base64Data).then(nome => {
                                if (nome) {
                                    document.getElementById('imagePreview').style.display = 'block';
                                    document.getElementById('imageName').innerText = nome;
                                }
                            });
                        };
                        
                        reader.onerror = function() {
                            mostrarToast("Erro ao ler o arquivo selecionado.", true);
                        };
                        
                        reader.readAsDataURL(file);
                    }
                }
            }, false);
        });

        // ==========================================
        // ALTERNÂNCIA DE MODOS (CONVERSA VS DUELO)
        // ==========================================
        function salvarDueloLocal() {
            const prov1 = document.getElementById('duelProv1').value;
            const prov2 = document.getElementById('duelProv2').value;
            const mod1 = document.getElementById('duelMod1').value;
            const mod2 = document.getElementById('duelMod2').value;
            pywebview.api.salvar_preferencias_duelo(prov1, mod1, prov2, mod2);
        }

        function alternarModo(modo) {
            const btnConversa = document.getElementById('btnConversa');
            const btnDuelo = document.getElementById('btnDuelo');
            const mainConversa = document.getElementById('mainConversa');
            const mainDuelo = document.getElementById('mainDuelo');

            // Reseta visual dos botões e esconde as telas
            btnConversa.classList.remove('active');
            btnDuelo.classList.remove('active');
            mainConversa.style.display = 'none';
            mainDuelo.style.display = 'none';

            if (modo === 'conversa') {
                btnConversa.classList.add('active');
                mainConversa.style.display = 'flex';
                // Recarrega o estado atual das sessões para garantir que a UI volte perfeita
                recarregarSessoes();
            } else if (modo === 'duelo') {
                btnDuelo.classList.add('active');
                mainDuelo.style.display = 'flex';
                // Foca automaticamente no input do modo duelo
                document.getElementById('duelInput').focus();
            }
        }
        // --- MODO DUELO ---
        function carregarModelosDuelo(col) {
            const provider = document.getElementById(`duelProv${col}`).value;
            pywebview.api.obter_modelos_por_provedor(provider).then(modelos => {
                const selector = document.getElementById(`duelMod${col}`);
                selector.innerHTML = '';
                if(modelos.length > 0) {
                    modelos.forEach(m => {
                        const opt = document.createElement('option');
                        opt.value = m; 
                        opt.innerText = m.replace('models/', '');
                        selector.appendChild(opt);
                    });
                }
                salvarDueloLocal();
            });
        }
        
        function salvarDueloLocal() {
            const prov1 = document.getElementById('duelProv1').value;
            const prov2 = document.getElementById('duelProv2').value;
            const mod1 = document.getElementById('duelMod1').value;
            const mod2 = document.getElementById('duelMod2').value;
            pywebview.api.salvar_preferencias_duelo(prov1, mod1, prov2, mod2);
        }

        function alternarModo(modo) {
            const btnConversa = document.getElementById('btnConversa');
            const btnDuelo = document.getElementById('btnDuelo');
            const mainConversa = document.getElementById('mainConversa');
            const mainDuelo = document.getElementById('mainDuelo');
            
            if (modo === 'conversa') {
                btnConversa.classList.add('active');
                btnDuelo.classList.remove('active');
                mainConversa.style.display = 'flex';
                mainDuelo.style.display = 'none';
            } else {
                btnDuelo.classList.add('active');
                btnConversa.classList.remove('active');
                mainDuelo.style.display = 'flex';
                mainConversa.style.display = 'none';
                
                // Carrega pela primeira vez se estiverem vazios
                if(document.getElementById('duelMod1').options.length <= 1) {
                    carregarModelosDuelo(1);
                    carregarModelosDuelo(2);
                }
            }
        }
        
        function enviarDuelo() {
            const input = document.getElementById('duelInput');
            const prov1 = document.getElementById('duelProv1').value;
            const prov2 = document.getElementById('duelProv2').value;
            const mod1 = document.getElementById('duelMod1').value;
            const mod2 = document.getElementById('duelMod2').value;
            
            // Salva a configuração de duelo no JSON
            pywebview.api.salvar_preferencias_duelo(prov1, mod1, prov2, mod2);
            
            const hasFile = document.getElementById('imagePreviewDuel').style.display === 'block';
            const fileName = document.getElementById('imageNameDuel').innerText;
            
            const text = input.value.trim();
            if (!text && !hasFile) return;
            
            let userPromptDisplay = text;
            const clipSvg = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent-1)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 4px; margin-top: -2px;"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path></svg>`;
            if (hasFile) {
                userPromptDisplay = `${clipSvg} <b>[Arquivo: ${fileName}]</b><br><br>${text}`;
            }
            
            input.value = '';
            input.disabled = true;
            
            const cols = document.querySelectorAll('.duel-column > div:nth-child(2)');
            // Renderiza estado de loading
            const loadingHTML = `<div class="typing-indicator" style="margin-top: 20px;"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>`;
            cols[0].innerHTML = `<div style="width: 100%; text-align: left;"><div style="background: rgba(255,255,255,0.05); padding: 12px; border-radius: 8px; margin-bottom: 12px; color: var(--text-primary);"><b>Você:</b> ${userPromptDisplay}</div>${loadingHTML}</div>`;
            cols[1].innerHTML = `<div style="width: 100%; text-align: left;"><div style="background: rgba(255,255,255,0.05); padding: 12px; border-radius: 8px; margin-bottom: 12px; color: var(--text-primary);"><b>Você:</b> ${userPromptDisplay}</div>${loadingHTML}</div>`;
            
            // Chama o motor Python
            pywebview.api.processar_duelo(text, prov1, mod1, prov2, mod2).then(resultado => {
                input.disabled = false;
                removerImagemDuelo();
                input.focus();
                
                const renderCol = (colNode, resp) => {
                    colNode.innerHTML = `<div style="width: 100%; text-align: left;">
                        <div style="background: rgba(255,255,255,0.05); padding: 12px; border-radius: 8px; margin-bottom: 16px; color: var(--text-primary); font-size: 0.95rem;"><b>Você:</b> ${userPromptDisplay}</div>
                        <div class="message-wrapper wrapper-ia" style="align-items: flex-start; width: 100%;">
                            <div class="message ia" style="margin: 0; width: 100%; max-width: 100%; padding: 16px;" data-raw-text="${encodeURIComponent(resp)}">${marked.parse(resp)}</div>
                            <div class="message-actions">
                                <button class="action-btn" title="Copiar texto" onclick="copiarDuelo(this)">
                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                                </button>
                                                                <button class="action-btn" title="Refazer pergunta" onclick="document.getElementById('duelInput').value='${text.replace(/'/g, "\'")}'; enviarDuelo();">
                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><path d="M3 3v5h5"></path></svg>
                                </button>
                                <button class="action-btn" title="Ouvir Resposta" onclick="this.dataset.rawText = decodeURIComponent(this.closest('.message-wrapper').querySelector('.message').dataset.rawText); lerEmVozAlta(this, this, '<svg width=18 height=18 viewBox=\'0 0 24 24\' fill=none stroke=currentColor stroke-width=2 stroke-linecap=round stroke-linejoin=round><polygon points=\'11 5 6 9 2 9 2 15 6 15 11 19 11 5\'></polygon><path d=\'M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07\'></path></svg>', '<svg width=18 height=18 viewBox=\'0 0 24 24\' fill=none stroke=currentColor stroke-width=2 stroke-linecap=round stroke-linejoin=round><polygon points=\'11 5 6 9 2 9 2 15 6 15 11 19 11 5\'></polygon><line x1=\'23\' y1=\'9\' x2=\'17\' y2=\'15\'></line><line x1=\'17\' y1=\'9\' x2=\'23\' y2=\'15\'></line></svg>')">
                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>
                                </button>
                            </div>
                        </div>
                    </div>`;
                    formatCodeBlocks(colNode);
                };

                renderCol(cols[0], resultado["col1"]);
                renderCol(cols[1], resultado["col2"]);
                
                // Força o final do scroll no duelo também
                document.querySelectorAll('.duel-column > div:nth-child(2)').forEach(e => e.scrollTop = e.scrollHeight);
            }).catch(err => {
                input.disabled = false;
                cols[0].innerHTML = "Erro ao conectar.";
                cols[1].innerHTML = "Erro ao conectar.";
            });
        }
        
        function copiarDuelo(btn) {
            const wrapper = btn.closest('.message-wrapper');
            const msgDiv = wrapper.querySelector('.message');
            const rawText = decodeURIComponent(msgDiv.dataset.rawText);
            navigator.clipboard.writeText(rawText.trim());
            const svgCheck = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--success)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>`;
            const svgCopy = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>`;
            btn.innerHTML = svgCheck;
            setTimeout(() => { btn.innerHTML = svgCopy; }, 2000);
        }
// ==========================================
// SPOTLIGHT (BARRA DE COMANDO GLOBAL)
// ==========================================
function abrirSpotlight() {
    const overlay = document.getElementById('spotlightOverlay');
    const input = document.getElementById('spotlightInput');
    const result = document.getElementById('spotlightResult');
    
    overlay.style.display = 'flex';
    input.value = '';
    result.style.display = 'none';
    result.innerHTML = '';
    
    setTimeout(() => {
        input.focus();
    }, 50);
}

function fecharSpotlight() {
    document.getElementById('spotlightOverlay').style.display = 'none';
}

function handleSpotlightKey(e) {
    if (e.key === 'Escape') {
        fecharSpotlight();
    } else if (e.key === 'Enter') {
        enviarSpotlight();
    }
}

function enviarSpotlight() {
    const input = document.getElementById('spotlightInput');
    const result = document.getElementById('spotlightResult');
    const text = input.value.trim();
    
    if (!text) return;
    
    input.disabled = true;
    result.style.display = 'block';
    result.style.padding = '24px';
    result.innerHTML = '<div class="typing-indicator" style="justify-content: flex-start;"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>';
    
    pywebview.api.processar_comando_spotlight(text).then(resposta => {
        input.disabled = false;
        result.innerHTML = marked.parse(resposta);
        formatCodeBlocks(result);
        input.focus();
    }).catch(err => {
        input.disabled = false;
        result.innerHTML = '<span style="color: #ef4444;">Erro ao processar o comando. Tente novamente.</span>';
        input.focus();
    });
}


// ==========================================
// TEXT-TO-SPEECH NEURAL (EDGE TTS via Python)
// ==========================================
let cromakAudioAtual = null;
let cromakFalando = false;

function lerEmVozAlta(msgDiv, btnElement, svgOn, svgOff) {
    if (cromakFalando && cromakAudioAtual) {
        cromakAudioAtual.pause();
        cromakAudioAtual.currentTime = 0;
        cromakFalando = false;
        btnElement.innerHTML = svgOn;
        btnElement.style.color = '';
        return;
    }
    
    let texto = msgDiv.dataset.rawText || msgDiv.innerText;
    
    // Mostra feedback visual de carregamento (porque a API demora 1~2 segundos pra gerar)
    btnElement.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--accent-1)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="animation: spin 1s linear infinite;"><line x1="12" y1="2" x2="12" y2="6"></line><line x1="12" y1="18" x2="12" y2="22"></line><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line><line x1="2" y1="12" x2="6" y2="12"></line><line x1="18" y1="12" x2="22" y2="12"></line><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line><line x1="16.24" y1="4.93" x2="19.07" y2="7.76"></line></svg>`;
    
    pywebview.api.gerar_voz_neural(texto).then(b64 => {
        if (!b64) {
            btnElement.innerHTML = svgOn;
            return;
        }
        
        cromakAudioAtual = new Audio("data:audio/mp3;base64," + b64);
        
        cromakAudioAtual.onplay = () => {
            cromakFalando = true;
            btnElement.innerHTML = svgOff;
            btnElement.style.color = 'var(--success)';
        };
        
        cromakAudioAtual.onended = () => {
            cromakFalando = false;
            btnElement.innerHTML = svgOn;
            btnElement.style.color = '';
        };
        
        cromakAudioAtual.onerror = () => {
            cromakFalando = false;
            btnElement.innerHTML = svgOn;
            btnElement.style.color = '';
        };
        
        cromakAudioAtual.play();
    }).catch(err => {
        console.error("Erro no TTS Neural:", err);
        btnElement.innerHTML = svgOn;
    });
}


// Menu de Contexto Customizado para a Caixa de Digitação
document.addEventListener("DOMContentLoaded", () => {
    // 1. Injeta o CSS do menu
    document.head.insertAdjacentHTML('beforeend', `<style>
    .custom-context-menu {
      position: absolute;
      background: #1a1a1c;
      border: 1px solid #3f3f46;
      border-radius: 8px;
      box-shadow: 0 4px 15px rgba(0,0,0,0.8);
      padding: 5px 0;
      z-index: 10000;
      display: none;
      min-width: 150px;
    }
    .custom-context-menu div {
      padding: 10px 15px;
      cursor: pointer;
      color: #e4e4e7;
      font-family: 'Inter', sans-serif;
      font-size: 14px;
      transition: background 0.2s;
    }
    .custom-context-menu div:hover {
      background: #7c3aed; /* accent-1 */
      color: white;
    }
    </style>`);

    // 2. Injeta o HTML do menu
    document.body.insertAdjacentHTML('beforeend', `
    <div id="customContextMenu" class="custom-context-menu">
      <div id="menuCopiar">📋 Copiar</div>
      <div id="menuColar">📥 Colar</div>
      <div id="menuRecortar">✂️ Recortar</div>
    </div>
    `);

    const userInput = document.getElementById('userInput');
    const menu = document.getElementById('customContextMenu');

    // Abre o menu apenas ao clicar com o botão direito na caixa de texto
    userInput.addEventListener('contextmenu', (e) => {
        // Bloqueia o preventDefault original do pywebview para esse elemento específico parando a propagação,
        // mas na verdade o pywebview injeta na window. Vamos cancelar a bolha:
        e.stopPropagation();
        e.preventDefault();
        
        menu.style.left = e.pageX + 'px';
        menu.style.top = (e.pageY - 120) + 'px'; // Sobe um pouco para não vazar da tela
        menu.style.display = 'block';
    });

    // Fecha o menu se clicar em qualquer lugar
    document.addEventListener('click', () => {
        menu.style.display = 'none';
    });

    // Ações do menu
    document.getElementById('menuCopiar').addEventListener('click', () => {
        const selected = userInput.value.substring(userInput.selectionStart, userInput.selectionEnd);
        navigator.clipboard.writeText(selected);
    });

    document.getElementById('menuColar').addEventListener('click', async () => {
        try {
            const text = await navigator.clipboard.readText();
            const start = userInput.selectionStart;
            const end = userInput.selectionEnd;
            userInput.value = userInput.value.substring(0, start) + text + userInput.value.substring(end);
            userInput.selectionStart = userInput.selectionEnd = start + text.length;
            userInput.focus();
        } catch (err) {
            console.error("Erro ao colar:", err);
            // Fallback se o navegador bloquear o readText sem HTTPS
            userInput.value += "[Falha de Permissão: Use Ctrl+V no teclado local para colar]";
        }
    });

    document.getElementById('menuRecortar').addEventListener('click', () => {
        const selected = userInput.value.substring(userInput.selectionStart, userInput.selectionEnd);
        navigator.clipboard.writeText(selected);
        const start = userInput.selectionStart;
        const end = userInput.selectionEnd;
        userInput.value = userInput.value.substring(0, start) + userInput.value.substring(end);
        userInput.selectionStart = userInput.selectionEnd = start;
        userInput.focus();
    });
});


// ==========================================
// MODO BRIDGE VOX (ATALHOS DE ACESSIBILIDADE FRONTEND - CONFORME WCAG 2.1.4)
// ==========================================
window.addEventListener('keydown', (e) => {
    // Se estiver interagindo com campo de gravação de atalho no modal de preferências, não intercepta
    if (document.activeElement && document.activeElement.classList.contains('shortcut-input')) return;

    // 1. F4 ou Alt+F4 ou Ctrl+Q / Alt+Q: Encerramento com Confirmação e Acessibilidade (NVDA)
    const isExitKey = e.key === 'F4' || 
                      (e.altKey && (e.key === 'F4' || e.key.toLowerCase() === 'q')) || 
                      (e.ctrlKey && e.key.toLowerCase() === 'q') ||
                      (window.appShortcuts && window.appShortcuts.exit && e.key.toUpperCase() === window.appShortcuts.exit.toUpperCase());
    if (isExitKey) {
        e.preventDefault();
        e.stopPropagation();
        if (typeof window.confirmarEncerramento === 'function') {
            window.confirmarEncerramento();
        } else if (window.pywebview && pywebview.api && pywebview.api.encerrar_sistema) {
            pywebview.api.encerrar_sistema();
        }
        return;
    }

    // 2. F3 ou Ctrl+L ou Alt+L: Ler / Focar na última resposta da IA (Acessibilidade NVDA)
    if (e.key === 'F3' || ((e.ctrlKey || e.altKey) && (e.key.toLowerCase() === 'l'))) {
        e.preventDefault();
        focarUltimaRespostaIA();
        return;
    }

    // 3. F11 ou Alt+Enter: Alternar Tela Cheia (Fullscreen)
    if (e.key === 'F11' || (e.altKey && e.key === 'Enter')) {
        e.preventDefault();
        if (window.pywebview && pywebview.api && pywebview.api.alternar_tela_cheia) {
            pywebview.api.alternar_tela_cheia();
        }
        return;
    }

    // 4. Tecla ESCAPE: Interromper áudio / síntese de voz e fechar modais
    if (e.key === 'Escape') {
        if (typeof gravandoAudio !== 'undefined' && gravandoAudio) {
            e.preventDefault();
            cancelarAudio();
            return;
        }
        if (typeof stopBtn !== 'undefined' && stopBtn) stopBtn.click();
        if (typeof fecharSobre === 'function') fecharSobre();
        if (typeof window.speechSynthesis !== 'undefined' && window.speechSynthesis) {
            window.speechSynthesis.cancel();
        }
        if (typeof window.currentAudio !== 'undefined' && window.currentAudio) {
            window.currentAudio.pause();
            window.currentAudio.currentTime = 0;
        }
        if (window.pywebview && pywebview.api && pywebview.api.parar_audio) {
            pywebview.api.parar_audio();
        }
        // Deixa propagar para fechar modais caso haja algum aberto
    }

    const activeEl = document.activeElement;
    const isTyping = activeEl && (
        activeEl.id === 'userInput' || 
        activeEl.tagName === 'TEXTAREA' || 
        activeEl.tagName === 'INPUT' || 
        activeEl.isContentEditable || 
        activeEl.classList.contains('shortcut-input')
    );

    // 5. Atalhos Funcionais com suporte a modificadores (WCAG 2.1.4):
    //    F1 ou Alt+H / Ctrl+H (Ajuda)
    //    F2 ou Alt+M / Ctrl+M (Microfone / Walkie-talkie)
    //    F5 ou Ctrl+N / Alt+N (Nova Conversa)
    //    F10 ou Ctrl+, / Alt+S (Configurações)
    const sc = window.appShortcuts || {};
    let keyName = e.key;
    if (keyName === ' ') keyName = 'Space';
    if (keyName.length === 1) keyName = keyName.toUpperCase();
    const match = (val) => val && (keyName === val.toUpperCase() || keyName === val);

    // F1 / Alt+H / Ctrl+H -> Ajuda
    const isHelp = e.key === 'F1' || match(sc.help) || ((e.altKey || e.ctrlKey) && e.key.toLowerCase() === 'h');
    if (isHelp) {
        if (isTyping && !e.altKey && !e.ctrlKey) return;
        e.preventDefault();
        if (window.pywebview && pywebview.api && pywebview.api.abrir_janela_ajuda) {
            pywebview.api.abrir_janela_ajuda();
        }
        return;
    }

    // F2 / Alt+M / Ctrl+M -> Microfone (Walkie-Talkie)
    const isMic = e.key === 'F2' || match(sc.mic) || ((e.altKey || e.ctrlKey) && e.key.toLowerCase() === 'm');
    if (isMic) {
        if (isTyping && !e.altKey && !e.ctrlKey) return;
        e.preventDefault();
        toggleAudio(true);
        return;
    }

    // F5 / Ctrl+N / Alt+N -> Nova Conversa
    const isNewChat = e.key === 'F5' || match(sc.clear) || ((e.altKey || e.ctrlKey) && e.key.toLowerCase() === 'n');
    if (isNewChat) {
        if (isTyping && !e.altKey && !e.ctrlKey) return;
        e.preventDefault();
        criarSessao();
        anunciarAoLeitor("Nova conversa iniciada.");
        focarCampoMensagem();
        return;
    }

    // F10 / Ctrl+, / Alt+S -> Configurações
    const isConfig = e.key === 'F10' || match(sc.config) || (e.ctrlKey && e.key === ',') || (e.altKey && e.key.toLowerCase() === 's');
    if (isConfig) {
        if (isTyping && !e.altKey && !e.ctrlKey) return;
        e.preventDefault();
        if (typeof abrirConfiguracoes !== 'undefined') abrirConfiguracoes();
        return;
    }

    // WCAG 2.1.4: Se o usuário estiver digitando em campo de texto, atalhos de tecla única NUNCA disparam!
    if (isTyping && !e.altKey && !e.ctrlKey) {
        return; // Usuário digitando normalmente
    }

    // Ferramentas Rápidas com suporte a Tecla Única (quando NÃO estiver digitando) OU Alt+Letra (a qualquer momento)
    let comando = "";
    const isTool = (letter) => (!isTyping && match(letter) && !e.ctrlKey && !e.altKey) || (e.altKey && e.key.toUpperCase() === letter);

    if (isTool(sc.txt || 'T')) comando = "Abra o editor de texto (Editor de Texto).";
    else if (isTool(sc.mail || 'R')) comando = "Leia meus e-mails (Leitor de E-mails).";
    else if (isTool(sc.web || 'I')) comando = "Pesquise na internet (Navegador Web).";
    else if (isTool(sc.files || 'A')) comando = "Liste os arquivos do diretório atual (Gerenciador de Arquivos).";
    else if (isTool(sc.calc || 'C')) comando = "Vamos fazer uma conta matemática.";
    else if (isTool(sc.whats || 'Z')) comando = "Mande uma mensagem no WhatsApp.";

    if (comando !== "") {
        e.preventDefault();
        const inputEl = document.getElementById('userInput');
        if (inputEl) { inputEl.value = comando; document.getElementById('sendBtn').click(); }
        else if (window.pywebview && pywebview.api && pywebview.api.enviar_comando_texto) {
            pywebview.api.enviar_comando_texto(comando);
        }
        return;
    }
});

function atualizarCamposApiSetup() {
    const provedor = document.getElementById('setupProvider');
    if (!provedor) return;
    const pVal = provedor.value;
    
    const divKeyGemini = document.getElementById('divKeyGemini');
    const divKeyOpenai = document.getElementById('divKeyOpenai');
    const divKeyClaude = document.getElementById('divKeyClaude');
    const divKeyQwen = document.getElementById('divKeyQwen');
    
    if (divKeyGemini) divKeyGemini.style.display = 'none';
    if (divKeyOpenai) divKeyOpenai.style.display = 'none';
    if (divKeyClaude) divKeyClaude.style.display = 'none';
    if (divKeyQwen) divKeyQwen.style.display = 'none';
    
    if(pVal === 'gemini' && divKeyGemini) divKeyGemini.style.display = 'block';
    if(pVal === 'openai' && divKeyOpenai) divKeyOpenai.style.display = 'block';
    if(pVal === 'claude' && divKeyClaude) divKeyClaude.style.display = 'block';
    if(pVal === 'qwen' && divKeyQwen) divKeyQwen.style.display = 'block';
}

function toggleSidebarDesktop() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) {
        sidebar.classList.toggle('desktop-hidden');
    }
}


// =========================================================================
// ACESSIBILIDADE NATIVA (FOCUS TRAP PARA MODAIS & ISOLAMENTO PARA NVDA)
// =========================================================================
window.addEventListener('keydown', (e) => {
    // 0. Tratamento para Dialog Customizado (Confirmação de Encerramento, etc.)
    const customDialog = document.getElementById('customDialog');
    if (customDialog && customDialog.style.display === 'flex') {
        if (e.key === 'Escape') {
            e.preventDefault();
            e.stopPropagation();
            closeCustomDialog(false);
            return;
        }
        if (e.key === 'Enter') {
            e.preventDefault();
            e.stopPropagation();
            if (document.activeElement && document.activeElement.id === 'dialogCancelBtn') {
                closeCustomDialog(false);
            } else {
                closeCustomDialog(true);
            }
            return;
        }
    }

    // 1. Fechar modal com tecla ESC
    if (e.key === 'Escape') {
        const settingsModal = document.getElementById('settingsModal');
        if (settingsModal && settingsModal.style.display === 'flex') {
            e.preventDefault();
            fecharConfiguracoes();
            return;
        }
        const aboutModal = document.getElementById('aboutModal');
        if (aboutModal && aboutModal.style.display === 'flex') {
            e.preventDefault();
            fecharSobre();
            return;
        }
    }

    // 2. Confinamento de foco (Focus Trap) dentro de modais abertos
    if (e.key === 'Tab') {
        const modalAberto = document.querySelector('.custom-dialog-overlay[style*="display: flex"], .settings-modal[style*="display: flex"], .modal-overlay[style*="display: flex"]');
        if (!modalAberto) return;

        // Pega todos os elementos focáveis visíveis dentro do modal
        const elementosFocaveis = Array.from(modalAberto.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        )).filter(el => {
            return el.offsetParent !== null && !el.disabled && el.style.display !== 'none' && el.style.visibility !== 'hidden';
        });

        if (elementosFocaveis.length === 0) return;

        const primeiroElemento = elementosFocaveis[0];
        const ultimoElemento = elementosFocaveis[elementosFocaveis.length - 1];

        if (e.shiftKey) {
            // Shift + Tab voltando: se estiver no primeiro, pula pro último
            if (document.activeElement === primeiroElemento || !modalAberto.contains(document.activeElement)) {
                e.preventDefault();
                ultimoElemento.focus();
            }
        } else {
            // Tab avançando: se estiver no último, pula pro primeiro
            if (document.activeElement === ultimoElemento || !modalAberto.contains(document.activeElement)) {
                e.preventDefault();
                primeiroElemento.focus();
            }
        }
    }
});

    // ==========================================
    // NAVEGAÇÃO DE ACESSIBILIDADE TECLADO NO CHAT (USER INPUT -> MENSAGENS)
    // ==========================================
    const userInputField = document.getElementById('userInput');
    if (userInputField) {
        userInputField.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowUp') {
                if (userInputField.selectionStart === 0 && userInputField.selectionEnd === 0) {
                    const wrappers = document.querySelectorAll('.messages-container .message-wrapper');
                    if (wrappers.length > 0) {
                        e.preventDefault();
                        wrappers[wrappers.length - 1].focus();
                    }
                }
            }
        });
    }

// ==========================================
// CROMAK ONLINE SYNC - VERIFICAÇÃO DE ATUALIZAÇÕES
// ==========================================
function verificarAtualizacaoOnline() {
    const btn = document.getElementById('btnVerificarUpdate');
    const textoOriginal = btn ? btn.innerText : 'Verificar Atualizações';
    if (btn) {
        btn.disabled = true;
        btn.innerText = 'Verificando...';
    }
    anunciarAoLeitor("Verificando atualizações online no repositório da Cromak Technology. Aguarde...");

    if (!window.pywebview || !pywebview.api || !pywebview.api.verificar_atualizacoes) {
        if (btn) {
            btn.disabled = false;
            btn.innerText = textoOriginal;
        }
        return;
    }

    pywebview.api.verificar_atualizacoes().then(res => {
        if (btn) {
            btn.disabled = false;
            btn.innerText = textoOriginal;
        }
        if (res && res.tem_update) {
            const msg = `🎉 Nova versão encontrada: ${res.versao_online}! Abrindo página oficial...`;
            mostrarToast(msg, false);
            anunciarAoLeitor(msg);
            setTimeout(() => {
                if (pywebview.api.abrir_link && res.url_download) {
                    pywebview.api.abrir_link(res.url_download);
                }
            }, 1200);
        } else {
            const vAtual = (res && res.versao_atual) ? res.versao_atual : '1.3.5';
            const msg = `✅ Você já está utilizando a versão mais recente do Cromak Bridge (${vAtual}).`;
            mostrarToast(msg, false);
            anunciarAoLeitor(msg);
        }
    }).catch(err => {
        if (btn) {
            btn.disabled = false;
            btn.innerText = textoOriginal;
        }
        const msgErro = "Não foi possível verificar atualizações no momento. Tente novamente mais tarde.";
        mostrarToast(msgErro, true);
        anunciarAoLeitor(msgErro);
    });
}
