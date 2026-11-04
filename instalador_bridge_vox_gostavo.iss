; =====================================================================
; CROMAK BRIDGE VOX - INSTALADOR EXCLUSIVO GUSTAVO TORNIERO
; Versão: 1.3.7 | Matrix Core | Cromak Technology
; Pré-configurado: Chave Groq Ativa + Tela Cheia + Modo Agente + Zero Eco NVDA
; =====================================================================

[Setup]
AppName=Cromak Bridge Vox
AppVersion=1.3.7
AppPublisher=Cromak Technology
AppPublisherURL=https://cromaktechnology.github.io
AppSupportURL=https://cromaktechnology.github.io/pt/suporte.html
AppUpdatesURL=https://cromaktechnology.github.io/pt/bridge-vox.html

; Ícone oficial e imagens visuais
SetupIconFile=cromak-bridge.ico
UninstallDisplayName=Cromak Bridge Vox
UninstallDisplayIcon={app}\BridgeVox.exe

#if FileExists("wizard.bmp")
WizardImageFile=wizard.bmp
#endif

; Compatibilidade de 64 bits nativa no Windows
ArchitecturesInstallIn64BitMode=x64compatible

; Instalação oficial em Arquivos de Programas (requer privilégio de administrador)
PrivilegesRequired=admin
UsedUserAreasWarning=no
DefaultDirName={autopf}\Cromak Technology\Bridge Vox
DefaultGroupName=Bridge Vox

; Oculta telas desnecessárias para fluxo ágil e 100% acessível ao leitor de telas (NVDA / Narrador)
DisableDirPage=yes
DisableProgramGroupPage=yes
DisableReadyPage=yes
DisableFinishedPage=yes
DisableWelcomePage=no

; Nome do instalador gerado
OutputBaseFilename=Instalador_BridgeVox_Gustavo_v1.3.7
OutputDir=Output
Compression=lzma2/ultra64
SolidCompression=yes

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Messages]
brazilianportuguese.WelcomeLabel1=Bem-vindo ao instalador do Cromak Bridge Vox v1.3.7
brazilianportuguese.WelcomeLabel2=Esta instalação foi preparada especialmente para você, com sua chave de inteligência artificial pronta e configurada para uso imediato.%n%nO programa inicia automaticamente em tela cheia e é 100% operável por teclado e leitor de telas (NVDA e Narrador).%n%nClique no botão "Instalar" para iniciar o processo diretamente.
brazilianportuguese.ClickNext=
brazilianportuguese.ButtonNext=Instalar
brazilianportuguese.ButtonCancel=Cancelar

[Files]
; 1. Copia todos os arquivos da aplicação (excluindo scripts, instaladores e arquivos de config locais)
; ATENÇÃO: NÃO excluir *.zip pois o PyInstaller necessita do base_library.zip em _internal!
Source: "*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "*.iss,Output,Output\*,*.bmp,*.ico,config*.json,config*\*.*,*.tmp,*.log,*.rar,*roteiro*,*teste*,api-teste*.txt"

; 2. Envia a configuração pré-definida do Gustavo (Groq API + Tela Cheia + Modo Agente) direto para o AppData do usuário
#if FileExists("config_gustavo.json")
Source: "config_gustavo.json"; DestDir: "{userappdata}\Cromak Technology\Bridge"; DestName: "config.json"; Flags: ignoreversion
Source: "config_gustavo.json"; DestDir: "{userappdata}\Cromak Technology\Bridge Vox"; DestName: "config.json"; Flags: ignoreversion
#elif FileExists("config.json")
Source: "config.json"; DestDir: "{userappdata}\Cromak Technology\Bridge"; DestName: "config.json"; Flags: ignoreversion
Source: "config.json"; DestDir: "{userappdata}\Cromak Technology\Bridge Vox"; DestName: "config.json"; Flags: ignoreversion
#endif

[Icons]
Name: "{autodesktop}\Bridge Vox"; Filename: "{app}\BridgeVox.exe"; WorkingDir: "{app}"; IconFilename: "{app}\BridgeVox.exe"; IconIndex: 0; Comment: "Assistente de IA Acessível Cromak Bridge Vox"
Name: "{autoprograms}\Bridge Vox\Bridge Vox"; Filename: "{app}\BridgeVox.exe"; WorkingDir: "{app}"; IconFilename: "{app}\BridgeVox.exe"; IconIndex: 0; Comment: "Assistente de IA Acessível Cromak Bridge Vox"
Name: "{autoprograms}\Bridge Vox\Desinstalar Bridge Vox"; Filename: "{uninstallexe}"; IconFilename: "{app}\BridgeVox.exe"; IconIndex: 0; Comment: "Desinstalar Cromak Bridge Vox"

[Run]
Filename: "{app}\BridgeVox.exe"; WorkingDir: "{app}"; Description: "Iniciar Cromak Bridge Vox"; Flags: nowait postinstall skipifsilent runasoriginaluser

[Code]
procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpWelcome then
  begin
    WizardForm.NextButton.Caption := '&Instalar';
    WizardForm.CancelButton.Caption := '&Cancelar';
    WizardForm.WelcomeLabel1.Caption := 'Bem-vindo ao instalador do Cromak Bridge Vox v1.3.7';
    WizardForm.WelcomeLabel2.Caption :=
      'Esta instalação foi preparada especialmente para você, com sua chave de inteligência artificial pronta e configurada para uso imediato.' + #13#10#13#10 +
      'O programa inicia automaticamente em tela cheia e é 100% operável por teclado e leitor de telas (NVDA e Narrador).' + #13#10#13#10 +
      'Clique no botão "Instalar" para iniciar o processo diretamente.';
  end;
end;
