// --- GESTÃO DE ATALHOS ---
window.appShortcuts = {
    mic: 'F2', stop: 'Escape', config: 'F10', clear: 'F5',
    help: 'F1', exit: 'F4',
    txt: 'T', mail: 'R', web: 'I', files: 'A', calc: 'C', whats: 'Z'
};

function initShortcuts() {
    const inputs = document.querySelectorAll('.shortcut-input');
    inputs.forEach(input => {
        input.addEventListener('keydown', (e) => {
            e.preventDefault();
            e.stopPropagation();
            let key = e.key;
            if (key === ' ') key = 'Space';
            if (key === 'Backspace') {
                input.value = '';
            } else {
                input.value = key.length === 1 ? key.toUpperCase() : key;
            }
        });
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
});

// vox-mode.js
let gravando = false;


let cromakAudioAtual = null;

// Ao carregar a pagina, vamos puxar as configuracoes para popular o modal (caso ele seja aberto)
window.addEventListener('pywebviewready', () => {
    pywebview.api.obter_configuracoes().then(config => {
        if(config.language) document.getElementById('configLanguage').value = config.language;
        if(document.getElementById('configInterfaceMode')) document.getElementById('configInterfaceMode').value = config.interface_mode || 'vox';
        if(config.start_with_windows !== undefined) document.getElementById('configStartup').checked = config.start_with_windows;
        if(config.minimize_to_tray !== undefined) document.getElementById('configTray').checked = config.minimize_to_tray;
        if(config.agent_mode !== undefined) document.getElementById('configAgente').checked = config.agent_mode;
        if(config.auto_tts !== undefined) document.getElementById('configAutoVoz').checked = config.auto_tts;
        if(config.always_voice !== undefined) document.getElementById('configBridgeVox').checked = config.always_voice;
    });

    // Boas vindas em audio
    document.getElementById('voxStatus').innerText = "Pressione ESPAÇO e fale (6 segundos)";
    tocarFala("Sistema de acessibilidade iniciado. Pressione espaço e faça sua pergunta.");
});

// Listener Global para a barra de espaco
window.addEventListener('keydown', (e) => {
    if (document.activeElement && document.activeElement.classList.contains('shortcut-input')) return;
    if (e.ctrlKey || e.altKey) return;
    
    let keyName = e.key;
    if (keyName === ' ') keyName = 'Space';
    if (keyName.length === 1) keyName = keyName.toUpperCase();
    
    const sc = window.appShortcuts;
    const match = (val) => val && (keyName === val.toUpperCase() || keyName === val);

    if (match(sc.mic)) {
        e.preventDefault();
        if (typeof toggleMicrofone === 'function') toggleMicrofone();
        return;
    }
    
    if (match(sc.stop) || e.key === 'Escape') {
        e.preventDefault();
        if (gravando) {
            cancelarGravacao();
            return;
        }
        pywebview.api.parar_audio();
        return;
    }
    
    if (match(sc.config)) {
        e.preventDefault();
        if(typeof abrirConfiguracoes !== 'undefined') abrirConfiguracoes();
        return;
    }

    if (match(sc.exit)) {
        e.preventDefault();
        if (typeof window.confirmarEncerramento === 'function') {
            window.confirmarEncerramento();
        } else if (typeof confirmarEncerramento === 'function') {
            confirmarEncerramento();
        } else if (window.pywebview && pywebview.api && pywebview.api.encerrar_sistema) {
            pywebview.api.encerrar_sistema();
        }
        return;
    }
    
    if (match(sc.help)) {
        e.preventDefault();
        pywebview.api.abrir_janela_ajuda();
        return;
    }

    let comando = "";
    if (match(sc.txt)) comando = "Abra o editor de texto (Editor de Texto).";
    else if (match(sc.mail)) comando = "Leia meus e-mails (Leitor de E-mails).";
    else if (match(sc.web)) comando = "Pesquise na internet (Navegador Web).";
    else if (match(sc.files)) comando = "Liste os arquivos do diretório atual (Gerenciador de Arquivos).";
    else if (match(sc.calc)) comando = "Vamos fazer uma conta matemática.";
    else if (match(sc.whats)) comando = "Mande uma mensagem no WhatsApp.";
    
    if (comando !== "") {
        e.preventDefault();
        pywebview.api.enviar_comando_texto(comando);
        return;
    }
});

function cancelarGravacao() {
    if (!gravando) return;
    gravando = false;
    const micCircle = document.getElementById('micCircle');
    const statusTxt = document.getElementById('voxStatus');
    const outTxt = document.getElementById('voxTextOutput');
    if (micCircle) micCircle.className = 'vox-mic-circle';
    if (statusTxt) statusTxt.innerText = "Gravação cancelada. Pressione ESPAÇO para falar.";
    if (window.pywebview && pywebview.api) {
        if (typeof pywebview.api.cancelar_audio === 'function') pywebview.api.cancelar_audio();
        else if (typeof pywebview.api.parar_audio === 'function') pywebview.api.parar_audio();
    }
}

function toggleMicrofone() {
    if (gravando) {
        cancelarGravacao();
        return;
    }

    // Se a IA estiver falando algo, a barra de espaco corta a fala dela
    if (cromakAudioAtual && !cromakAudioAtual.paused) {
        cromakAudioAtual.pause();
        cromakAudioAtual = null;
        document.getElementById('voxStatus').innerText = "Pressione ESPAÇO e fale (6 segundos)";
        return;
    }

    iniciarGravacao();
}

function iniciarGravacao() {
    gravando = true;
    const micCircle = document.getElementById('micCircle');
    const statusTxt = document.getElementById('voxStatus');
    const outTxt = document.getElementById('voxTextOutput');

    micCircle.className = 'vox-mic-circle listening';
    statusTxt.innerText = "Ouvindo... (Fale agora)";
    outTxt.innerText = "...";

    pywebview.api.ouvir_e_responder_nativo().then(resp => {
        gravando = false;
        micCircle.className = 'vox-mic-circle';
        
        if(resp && resp.startsWith("Erro")) {
            statusTxt.innerText = "Erro ao processar";
            outTxt.innerText = resp;
            tocarFala("Ocorreu um erro de conexão. Verifique sua chave da API nas configurações.");
        } else if (resp) {
            statusTxt.innerText = "Resposta recebida. Pressione ESPAÇO para falar novamente.";
            outTxt.innerHTML = marked.parse(resp); // Converte markdown se houver
            tocarFala(resp);
        } else {
            statusTxt.innerText = "Pressione ESPAÇO e fale";
            outTxt.innerText = "Não entendi. Pode repetir?";
            tocarFala("Não consegui ouvir. Pode repetir?");
        }
    }).catch(err => {
        gravando = false;
        micCircle.className = 'vox-mic-circle';
        statusTxt.innerText = "Erro no sistema";
    });

    // Simulador visual de transicao para "pensando" apos 6 segundos
    setTimeout(() => {
        if(gravando) {
            micCircle.className = 'vox-mic-circle thinking';
            statusTxt.innerText = "Pensando...";
        }
    }, 6000);
}

function tocarFala(texto) {
    if (cromakAudioAtual && !cromakAudioAtual.paused) {
        cromakAudioAtual.pause();
    }
    
    // Removemos markdown para ler limpo
    let textoLimpo = texto.replace(/[*#_]/g, '');
    
    pywebview.api.gerar_voz_neural(textoLimpo).then(b64 => {
        if (!b64) return;
        cromakAudioAtual = new Audio("data:audio/mp3;base64," + b64);
        cromakAudioAtual.play();
    });
}

// ---- METODOS DO MODAL DE CONFIGURACOES ----
function abrirConfiguracoes() {
    const modal = document.getElementById('settingsModal');
    modal.style.display = 'flex';
    setTimeout(() => modal.style.opacity = '1', 10);
}

function fecharModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.style.opacity = '0';
    setTimeout(() => modal.style.display = 'none', 300);
}

function fecharConfiguracoes() {
    fecharModal('settingsModal');
}

function switchSettingsTab(event, tabId) {
    document.querySelectorAll('.settings-tab').forEach(tab => tab.style.display = 'none');
    document.getElementById('tab-' + tabId).style.display = 'block';
    
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    event.currentTarget.classList.add('active');
}

function mostrarAba(abaId, element) {
    document.querySelectorAll('.settings-tab').forEach(tab => tab.style.display = 'none');
    document.getElementById(abaId).style.display = 'block';
    
    document.querySelectorAll('.settings-sidebar li').forEach(li => li.classList.remove('active'));
    element.classList.add('active');
}

function salvarConfiguracoes() {
    const payload = {
        language: document.getElementById('configLanguage').value,
        interface_mode: document.getElementById('configInterfaceMode') ? document.getElementById('configInterfaceMode').value : 'vox',
        start_with_windows: document.getElementById('configStartup').checked,
        minimize_to_tray: document.getElementById('configTray').checked,
        agent_mode: document.getElementById('configAgente').checked,
        auto_tts: document.getElementById('configAutoVoz').checked,
        always_voice: document.getElementById('configBridgeVox').checked
    };

    pywebview.api.salvar_preferencias(payload).then(() => {
        fecharModal('settingsModal');
        if (payload.interface_mode === 'normal' || payload.interface_mode === 'high_contrast') {
            window.location.href = 'index.html';
        } else {
            window.location.reload();
        }
    });
}
window.addEventListener('keydown', (e) => {
    if (document.activeElement && document.activeElement.classList.contains('shortcut-input')) return;

    const input = document.getElementById('userInput');
    const isTyping = document.activeElement === input || document.activeElement.tagName === 'TEXTAREA' || document.activeElement.tagName === 'INPUT';
    if (e.ctrlKey || e.altKey) return;
    
    let keyName = e.key;
    if (keyName === ' ') keyName = 'Space';
    if (keyName.length === 1) keyName = keyName.toUpperCase();
    
    const sc = window.appShortcuts;
    const match = (val) => val && (keyName === val.toUpperCase() || keyName === val);

    if (match(sc.mic)) {
        if (isTyping && keyName === 'Space') return;
        e.preventDefault();
        const btnVoz = document.getElementById('voiceBtn') || document.getElementById('mainMicBtn') || document.getElementById('micBtn');
        if(!btnVoz) return;
        const oldHtml = btnVoz.innerHTML;
        btnVoz.innerHTML = `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="red" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="3"></circle></svg>`;
        pywebview.api.ouvir_e_responder_nativo().then(resp => {
            btnVoz.innerHTML = oldHtml;
            if(resp && resp.startsWith("Erro")) {
                if(typeof mostrarToast !== 'undefined') mostrarToast(resp, true);
            } else if (resp) {
                if(typeof adicionarMensagem !== 'undefined') adicionarMensagem(resp, 'ai');
            }
        });
        return;
    }
    
    if (match(sc.stop)) {
        e.preventDefault();
        if(typeof stopBtn !== 'undefined' && stopBtn) stopBtn.click();
        pywebview.api.parar_audio();
        return;
    }
    
    if (match(sc.config)) {
        if (isTyping && keyName.length === 1) return;
        e.preventDefault();
        if(typeof abrirConfiguracoes !== 'undefined') abrirConfiguracoes();
        return;
    }

    if (match(sc.clear)) {
        if (isTyping && keyName.length === 1) return;
        e.preventDefault();
        if(typeof novaConversa !== 'undefined') novaConversa();
        else pywebview.api.reiniciar_conversa();
        return;
    }
    
    if (match(sc.help)) {
        if (isTyping && keyName.length === 1) return;
        e.preventDefault();
        pywebview.api.abrir_janela_ajuda();
        return;
    }
    
    if (match(sc.exit)) {
        if (isTyping && keyName.length === 1) return;
        e.preventDefault();
        if (typeof window.confirmarEncerramento === 'function') {
            window.confirmarEncerramento();
        } else if (typeof confirmarEncerramento === 'function') {
            confirmarEncerramento();
        } else if (window.pywebview && pywebview.api && pywebview.api.encerrar_sistema) {
            pywebview.api.encerrar_sistema();
        }
        return;
    }

    let comando = "";
    const checkboxBridgeVox = document.getElementById('configBridgeVox');
    // Só funciona se não estiver digitando, e se o modo Vox estiver ativado (ou no próprio vox-mode onde sempre é ativado se configurado, mas vamos simplificar).
    if (!isTyping) {
        if (match(sc.txt)) comando = "Abra o editor de texto (Editor de Texto).";
        else if (match(sc.mail)) comando = "Leia meus e-mails (Leitor de E-mails).";
        else if (match(sc.web)) comando = "Pesquise na internet (Navegador Web).";
        else if (match(sc.files)) comando = "Liste os arquivos do diretório atual (Gerenciador de Arquivos).";
        else if (match(sc.calc)) comando = "Vamos fazer uma conta matemática.";
        else if (match(sc.whats)) comando = "Mande uma mensagem no WhatsApp.";
    }
    
    if (comando !== "") {
        e.preventDefault();
        if (input) { input.value = comando; document.getElementById('sendBtn').click(); }
        else { 
            pywebview.api.enviar_comando_texto(comando);
        }
        return;
    }
});

// =========================================================================
// LEITOR DE TELA NATIVO (TAB NAVIGATION)
// =========================================================================
let navegandoPorTeclado = false;

window.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') navegandoPorTeclado = true;
});

window.addEventListener('mousedown', () => {
    navegandoPorTeclado = false;
});

window.addEventListener('focusin', (e) => {
    // Só fala se o usuário estiver usando o teclado (Tab) e se a opção de Leitor Nativo fizer sentido,
    // Mas como é um recurso de acessibilidade, vamos falar sempre que vier do teclado.
    if (!navegandoPorTeclado) return;
    
    let el = e.target;
    // Ignora elementos invisíveis ou que não deveriam ter foco
    if (el.style.display === 'none' || el.style.visibility === 'hidden') return;
    
    // Tenta pegar a descrição mais fiel do elemento
    let texto = el.getAttribute('aria-label') || el.title || el.placeholder || el.innerText;
    
    // Se for um input sem placeholder, falar "Campo de texto"
    if (!texto && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA')) {
        texto = "Campo de texto";
    }
    
    if (texto && typeof texto === 'string') {
        texto = texto.trim().substring(0, 80); // Limita tamanho
        if (texto.length > 0) {
            window.speechSynthesis.cancel();
            let fala = new SpeechSynthesisUtterance(texto);
            fala.lang = 'pt-BR';
            fala.rate = 1.3; // Um pouco mais rápido para navegação ágil
            window.speechSynthesis.speak(fala);
        }
    }
});
// =========================================================================
