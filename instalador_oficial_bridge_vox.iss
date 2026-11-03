; =====================================================================

; CROMAK BRIDGE VOX - INSTALADOR OFICIAL DE DISTRIBUIÇÃO PÚBLICA

; Versão: 1.3.7 | Matrix Core | Cromak Technology

; =====================================================================



[Setup]

AppName=Cromak Bridge Vox

AppVersion=1.3.7

AppPublisher=Cromak Technology

AppPublisherURL=https://cromaktechnology.github.io

AppSupportURL=https://cromaktechnology.github.io/pt/suporte.html

AppUpdatesURL=https://cromaktechnology.github.io/pt/bridge-vox.html

AppUserModelID=Cromak Bridge Vox



; Pasta padrão de instalação oficial (Arquivos de Programas do Windows)

DefaultDirName={autopf}\Cromak Technology\Bridge Vox

DefaultGroupName=Bridge Vox



; Ícone oficial do instalador e desinstalador

SetupIconFile=cromak-bridge.ico

UninstallDisplayName=Cromak Bridge Vox

UninstallDisplayIcon={app}\cromak-bridge.ico



; Suporte opcional a imagens customizadas do assistente (quando você criar wizard.bmp)

#if FileExists("wizard.bmp")

WizardImageFile=wizard.bmp

#endif

#if FileExists("wizard-small.bmp")

WizardSmallImageFile=wizard-small.bmp

#endif



; 64 bits nativo (compatível com x64 e ARM64)

ArchitecturesInstallIn64BitMode=x64compatible



; Fluxo limpo e acessível para quem usa leitores de tela (NVDA / Narrador)

DisableDirPage=yes

DisableProgramGroupPage=yes

DisableReadyPage=yes

DisableFinishedPage=yes

DisableWelcomePage=no



; Nome do instalador oficial gerado

OutputBaseFilename=Instalador_Cromak_Bridge_Vox_v1.3.7

OutputDir=Output

Compression=lzma2/ultra64

SolidCompression=yes

PrivilegesRequired=admin

UsedUserAreasWarning=no



[Languages]

Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"



[Messages]

brazilianportuguese.WelcomeLabel1=Bem-vindo ao instalador oficial do Cromak Bridge Vox v1.3.7

brazilianportuguese.WelcomeLabel2=Esta instalação foi otimizada para ser rápida, segura e 100% acessível com leitores de tela (NVDA e Narrador).%n%nO Cromak Bridge Vox é o seu assistente de inteligência artificial multimodal operado por voz e teclado.%n%nO programa será instalado na pasta padrão de Arquivos de Programas e INICIARÁ AUTOMATICAMENTE ao término da instalação.%n%nClique no botão "Instalar" para concluir o processo diretamente.

brazilianportuguese.ClickNext=

brazilianportuguese.ExitSetupTitle=Sair da Instalação

brazilianportuguese.ExitSetupMessage=A instalação ainda não foi concluída. Se você sair agora, o Cromak Bridge Vox não será instalado no seu computador.%n%nVocê poderá executar o instalador novamente a qualquer momento para concluir a instalação.%n%nDeseja realmente fechar o instalador?

brazilianportuguese.ButtonCancel=Cancelar

brazilianportuguese.ButtonNext=Instalar

brazilianportuguese.ButtonFinish=Concluir



[Files]

; Copia todos os arquivos da pasta atual compilada (executável BridgeVox.exe, pasta _internal, docs, etc.)

; NÃO copia arquivos de configuração pré-definidos (o usuário novo configurará sua API ou manterá as que já possui)

; ATENÇÃO: NÃO excluir *.zip pois o PyInstaller necessita do base_library.zip em _internal!

Source: "*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "*.iss,Output\*,config*.json,config*\*.*,*.tmp,*.log,*.rar"

Source: "cromak-bridge.ico"; DestDir: "{app}"; Flags: ignoreversion



[Icons]

; Atalhos na Área de Trabalho e no Menu Iniciar

Name: "{autodesktop}\Bridge Vox"; Filename: "{app}\BridgeVox.exe"; WorkingDir: "{app}"; IconFilename: "{app}\cromak-bridge.ico"; Comment: "Assistente de IA Acessível Cromak Bridge Vox"; AppUserModelID: "Cromak Bridge Vox"

Name: "{autoprograms}\Bridge Vox\Bridge Vox"; Filename: "{app}\BridgeVox.exe"; WorkingDir: "{app}"; IconFilename: "{app}\cromak-bridge.ico"; Comment: "Assistente de IA Acessível Cromak Bridge Vox"; AppUserModelID: "Cromak Bridge Vox"

Name: "{autoprograms}\Bridge Vox\Desinstalar Bridge Vox"; Filename: "{uninstallexe}"; IconFilename: "{app}\cromak-bridge.ico"; Comment: "Desinstalar Cromak Bridge Vox"



[Registry]

Root: HKCU; Subkey: "Software\Classes\AppUserModelId\Cromak Bridge Vox"; ValueType: string; ValueName: "DisplayName"; ValueData: "Cromak Bridge Vox"; Flags: uninsdeletekey

Root: HKCU; Subkey: "Software\Classes\AppUserModelId\Cromak Bridge Vox"; ValueType: string; ValueName: "IconUri"; ValueData: "{app}\cromak-bridge.ico"; Flags: uninsdeletekey

Root: HKCU; Subkey: "Software\Classes\AppUserModelId\Cromak Bridge Vox"; ValueType: dword; ValueName: "ShowInSettings"; ValueData: 1; Flags: uninsdeletekey



[Run]

; Inicia o aplicativo automaticamente ao término da instalação

Filename: "{app}\BridgeVox.exe"; WorkingDir: "{app}"; Description: "Iniciar Cromak Bridge Vox"; Flags: nowait postinstall skipifsilent runasoriginaluser



[Code]

procedure CurPageChanged(CurPageID: Integer);

begin

  if CurPageID = wpWelcome then

  begin

    WizardForm.NextButton.Caption := '&Instalar';

    WizardForm.CancelButton.Caption := '&Cancelar';

    WizardForm.WelcomeLabel1.Caption := 'Bem-vindo ao instalador oficial do Cromak Bridge Vox v1.3.7';

    WizardForm.WelcomeLabel2.Caption :=

      'Esta instalação foi otimizada para ser rápida, segura e 100% acessível com leitores de tela (NVDA e Narrador).' + #13#10#13#10 +

      'O Cromak Bridge Vox é o seu assistente de inteligência artificial multimodal operado por voz e teclado.' + #13#10#13#10 +

      'O programa será instalado na pasta padrão de Arquivos de Programas e INICIARÁ AUTOMATICAMENTE ao término da instalação.' + #13#10#13#10 +

      'Clique no botão "Instalar" para concluir o processo diretamente.';

  end;

end;



// =====================================================================

// CUIDADO E PROTEÇÃO DOS DADOS DO USUÁRIO NA DESINSTALAÇÃO

// =====================================================================

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);

var

  AppDataPath, AppDataVoxPath: String;

  Resposta: Integer;

begin

  if CurUninstallStep = usUninstall then

  begin

    AppDataPath := ExpandConstant('{userappdata}\Cromak Technology\Bridge');

    AppDataVoxPath := ExpandConstant('{userappdata}\Cromak Technology\Bridge Vox');



    // Pergunta com total respeito ao usuário e sua acessibilidade

    Resposta := MsgBox(

      'Deseja também excluir os seus dados pessoais, como a sua Agenda Fixa, contatos salvos e histórico de conversas?' + #13#10#13#10 +

      '• Clique em NÃO para MANTER sua agenda, contatos e configurações protegidos no computador caso queira reinstalar no futuro.' + #13#10 +

      '• Clique em SIM para APAGAR completamente todos os dados do Cromak Bridge Vox deste computador.',

      mbConfirmation, MB_YESNO or MB_DEFBUTTON2

    );



    if Resposta = IDYES then

    begin

      // O usuário confirmou que deseja remover tudo

      if DirExists(AppDataPath) then

        DelTree(AppDataPath, True, True, True);

      if DirExists(AppDataVoxPath) then

        DelTree(AppDataVoxPath, True, True, True);

    end;

  end;

end;

