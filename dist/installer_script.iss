; Script para Inno Setup (CORRIGIDO)
#define MyAppName "Direct Label Printer"
#define MyAppVersion "1.1"
#define MyAppPublisher "Sua Empresa"
#define MyAppExeName "DirectLabelPrinter.exe"
#define MyServiceName "DirectLabelPrinterService"

[Setup]
; ... (seção Setup continua a mesma) ...
AppId={{AUTO}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
OutputDir=.\installers
OutputBaseFilename=DirectLabelPrinter-{#MyAppVersion}-setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Files]
; Copia tudo da pasta 'dist' do PyInstaller
Source: "C:\Users\Usuario\VSCode\directlabelprinter\dist\DirectLabelPrinter.exe"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Copia o utilitário de serviço NSSM
Source: "D:\nssm.exe"; DestDir: "{app}"; Flags: ignoreversion

[Run]
; CORREÇÃO AQUI: Removemos a flag 'runhidden'. 
; O Inno Setup agora irá mostrar uma janela de progresso com a saída do comando.
Filename: "{app}\{#MyAppExeName}"; Parameters: "postinstall"; WorkingDir: "{app}"; Flags: waituntilterminated

; A instalação do serviço continua escondida, o que está correto.
Filename: "{app}\nssm.exe"; Parameters: "install {#MyServiceName} ""{app}\{#MyAppExeName}"""; Flags: runhidden waituntilterminated
Filename: "{app}\nssm.exe"; Parameters: "set {#MyServiceName} AppDirectory ""{app}"""; Flags: runhidden waituntilterminated
Filename: "{app}\nssm.exe"; Parameters: "set {#MyServiceName} DisplayName ""{#MyAppName}"""; Flags: runhidden waituntilterminated
Filename: "{app}\nssm.exe"; Parameters: "set {#MyServiceName} Description ""Serviço para a API de impressão de etiquetas."""; Flags: runhidden waituntilterminated

; Inicia o serviço (também escondido)
Filename: "net.exe"; Parameters: "start {#MyServiceName}"; Flags: runhidden

[UninstallRun]
; ... (seção de desinstalação continua a mesma) ...
Filename: "net.exe"; Parameters: "stop {#MyServiceName}"; Flags: runhidden waituntilterminated
Filename: "{app}\nssm.exe"; Parameters: "remove {#MyServiceName} confirm"; Flags: runhidden waituntilterminated