!include WinMessages.nsh

!define COPYYEAR 2025

Var VersionNumber


Section
  SetDetailsPrint both
  InitPluginsDir
  StrCpy $VersionNumber "v2.0.0"
  ExpandEnvStrings $0 %COMSPEC%
  MessageBox MB_OK "RescueBox $VersionNumber $INSTDIR"
  MessageBox MB_OK|MB_ICONINFORMATION "Copyright (R) ${COPYYEAR}"
SectionEnd

!macro customHeader
    RequestExecutionLevel admin
!macroend


Function .onInstSuccess
    Var /GLOBAL INSTDIR_DAT
    Strcpy "$INSTDIR_DAT" "$INSTDIR\resources\assets\rb_server"
    ExpandEnvStrings $0 %COMSPEC%
    ExecWait '"$0" /C "msiexec /i $INSTDIR_DAT\winfsp-2.0.23075.msi   INSTALLLEVEL=1000 /passive"'
    Var /GLOBAL O_LOG
    Strcpy "$O_LOG" "$AppData\RescueBox-Desktop\logs\o.log"
    ExecWait '"$0" /C "$INSTDIR_DAT\OllamaSetup.exe /verysilent /SP /SUPPRESSMSGBOXES /log=$O_LOG"'

FunctionEnd


Section "Uninstall"
  Var /GLOBAL INSTDIR_LOG
  Strcpy "$INSTDIR_LOG" "$AppData\RescueBox-Desktop\logs"

  FindWindow $0 "RescueBox-Desktop"
  SendMessage $0 ${WM_CLOSE} 0 0
  ExecWait '"$0" /k "del/f /q $INSTDIR_LOG\*.log"'
  ExecWait '"$0" /K "rmdir /S /Q $INSTDIR"'

SectionEnd


