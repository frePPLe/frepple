;
; Nullsoft script for creating a windows installer for frePPLe
;
; Copyright (C) 2007-2014 by frePPLe bvba
;
; This library is free software; you can redistribute it and/or modify it
; under the terms of the GNU Affero General Public License as published
; by the Free Software Foundation; either version 3 of the License, or
; (at your option) any later version.
;
; This library is distributed in the hope that it will be useful,
; but WITHOUT ANY WARRANTY; without even the implied warranty of
; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
; General Public License for more details.
;
; You should have received a copy of the GNU Affero General Public
; License along with this program.  If not, see <http://www.gnu.org/licenses/>.
;

; This installer script is building on the GNU auto-build scripts. We first
; create the distribution make target, and then unzip it. The windows installer
; then selects subdirectories of this distribution tree to be installed.
; To run this script successfully, you'll therefore need to have the cygwin
; system up and running on your machine.

; Make sure that this variable points to the windows version of Python, not
; the one that is part of cygwin.
!ifndef PYTHON
!define PYTHON "python3.exe"
!endif

; Main definitions
!define PRODUCT_NAME "frePPLe"
!define PRODUCT_VERSION "3.1.beta"
!define PRODUCT_PUBLISHER "frePPLe"
!define PRODUCT_WEB_SITE "http://frepple.com"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\frepple.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME} ${PRODUCT_VERSION}"

; Select compressor
SetCompressor /SOLID lzma

; Auxilary function to open a link in the browser
; Two versions of the function are defined: one for the installer and another for the uninstaller
!macro x un
Function ${un}openLinkNewWindow
  Push $3
  Exch
  Push $2
  Exch
  Push $1
  Exch
  Push $0
  Exch

  ReadRegStr $0 HKCR "http\shell\open\command" ""
  # Get browser path
  StrCpy $2 '"'
  StrCpy $1 $0 1
  StrCmp $1 $2 +2 # if path is not enclosed in " look for space as final char
    StrCpy $2 ' '
  StrCpy $3 1
  loop:
    StrCpy $1 $0 1 $3
    StrCmp $1 $2 found
    StrCmp $1 "" found
    IntOp $3 $3 + 1
    Goto loop

  found:
    StrCpy $1 $0 $3
    StrCmp $2 " " +2
      StrCpy $1 '$1"'

  Pop $0
  DetailPrint "Opening URL $0 in browser"
  Exec '$1 $0'
  Pop $0
  Pop $1
  Pop $2
  Pop $3
FunctionEnd
!macroend

!insertmacro x ""
!insertmacro x "un."

;Include for Modern UI and library installation
!define MULTIUSER_EXECUTIONLEVEL Highest
!define MULTIUSER_MUI
!define MULTIUSER_INSTALLMODE_COMMANDLINE
!define MULTIUSER_INSTALLMODE_INSTDIR "${PRODUCT_NAME} ${PRODUCT_VERSION}"
!include MultiUser.nsh
!include MUI2.nsh
!include Library.nsh
!include WinMessages.nsh
!include Sections.nsh
!include InstallOptions.nsh
!include LogicLib.nsh
!include FileFunc.nsh

; MUI Settings
!define MUI_ABORTWARNING
!define MUI_WELCOMEFINISHPAGE_BITMAP "frepple.bmp"
!define MUI_UNWELCOMEFINISHPAGE_BITMAP "frepple.bmp"
!define MUI_WELCOMEPAGE_TEXT "This wizard will guide you through the installation of frePPLe.$\r$\n$\r$\nIt is recommended to uninstall a previous version before this installing a new one."
!define MUI_HEADERIMAGE_BITMAP "..\..\doc\frepple.bmp"
!define MUI_ICON "..\..\src\frepple.ico"
!define MUI_UNICON "..\..\src\frepple.ico"

; Installer pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "../../COPYING"
!insertmacro MULTIUSER_PAGE_INSTALLMODE
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_COMPONENTS
Page custom DatabaseOpen DatabaseLeave
!insertmacro MUI_PAGE_INSTFILES
Page custom FinishOpen FinishLeave

; Uninstaller pages
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Language files, sorted alphabetically
!insertmacro MUI_LANGUAGE "English"   ; First option is the default language
!insertmacro MUI_LANGUAGE "Dutch"
!insertmacro MUI_LANGUAGE "French"
!insertmacro MUI_LANGUAGE "Italian"
!insertmacro MUI_LANGUAGE "Japanese"
!insertmacro MUI_LANGUAGE "Portuguese"
!insertmacro MUI_LANGUAGE "PortugueseBR"
!insertmacro MUI_LANGUAGE "SimpChinese"
!insertmacro MUI_LANGUAGE "Spanish"
!insertmacro MUI_LANGUAGE "TradChinese"

;Version Information
VIProductVersion "3.1.0.0"
VIAddVersionKey /LANG=${LANG_ENGLISH} FileVersion "3.1.0.0"
VIAddVersionKey /LANG=${LANG_ENGLISH} ProductName "frePPLe community edition installer"
VIAddVersionKey /LANG=${LANG_ENGLISH} Comments "frePPLe community edition installer"
VIAddVersionKey /LANG=${LANG_ENGLISH} CompanyName "frePPLe"
VIAddVersionKey /LANG=${LANG_ENGLISH} LegalCopyright "Dual licensed under the AGPL and commercial license"
VIAddVersionKey /LANG=${LANG_ENGLISH} FileDescription "frePPLe community edition installer"

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "${PRODUCT_NAME}_${PRODUCT_VERSION}_setup.exe"
BrandingText "${PRODUCT_NAME} ${PRODUCT_VERSION}"
CRCcheck on
ShowInstDetails show
ShowUnInstDetails show
Var day
Var month
Var year
Var day_name
Var hours
Var minutes
Var seconds

; Declare everything that needs to be extracted on startup.
; Only useful for BZIP2 compression
ReserveFile "parameters.ini"
ReserveFile "finish.ini"
ReserveFile '${NSISDIR}\Plugins\InstallOptions.dll'
ReserveFile "finish.bmp"


Function .onInit
  ;Extract some files used by the installer
  !insertmacro INSTALLOPTIONS_EXTRACT "parameters.ini"
  !insertmacro INSTALLOPTIONS_EXTRACT "finish.ini"
  !insertmacro INSTALLOPTIONS_EXTRACT "finish.bmp"

  ;Write image paths to the INI file
  WriteINIStr "$PLUGINSDIR\finish.ini" "Field 7" "Text" "$PLUGINSDIR\finish.bmp"

  !insertmacro MULTIUSER_INIT
FunctionEnd


Section -Start
  ; Create the python distribution and django server
  !system '${PYTHON} setup.py'

  ; Build the documentation if it doesn't exist yet
  !cd "../../doc"
  !system "bash -c 'if (test ! -f _build/html/index.html ); then pwd; fi'"

  ; Create a distribution if none exists yet
  !cd ".."
  !system "bash -c 'if (test ! -f frepple-${PRODUCT_VERSION}.tar.gz ); then make dist; fi'"

  ; Expand the distribution
  !system "bash -c 'rm -rf frepple-${PRODUCT_VERSION}'"
  !system "bash -c 'tar -xzf frepple-${PRODUCT_VERSION}.tar.gz'"
  !cd "frepple-${PRODUCT_VERSION}"
SectionEnd


Section "Application" SecAppl
  SectionIn RO     ; The app section can't be deselected

  SetOutPath "$INSTDIR"
  SetOverwrite ifnewer
  File "COPYING"
  File "README"

  ; Copy application, dll and libraries
  SetOutPath "$INSTDIR\bin"
  File "..\bin\frepple.exe"
  !insertmacro InstallLib DLL NOTSHARED NOREBOOT_NOTPROTECTED "..\bin\frepple.dll" "$INSTDIR\bin\frepple.dll" "$SYSDIR"

  ; Copy modules
  File /nonfatal "..\bin\mod_*.so"

   ; Copy configuration files
  File "..\bin\*.xsd"
  File "..\bin\init.xml"

  ; Copy the license file the user specified
  File "..\bin\license.xml"

  ; Copy the django and python redistributables created by py2exe
  File /r "..\contrib\installer\dist\*.*"

  ; Copy djangosettings
  SetOutPath "$INSTDIR\bin\custom"
  File "..\contrib\django\djangosettings.py"

  ; Create menu
  CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME} ${PRODUCT_VERSION}"
  ; SetOutPath is used to set the working directory for the shortcut
  SetOutPath "$LOCALAPPDATA\${PRODUCT_NAME}\${PRODUCT_VERSION}"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME} ${PRODUCT_VERSION}\Start frePPLe server.lnk" "$INSTDIR\bin\freppleserver.exe"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME} ${PRODUCT_VERSION}\Open configuration folder.lnk" "$INSTDIR\bin\custom"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME} ${PRODUCT_VERSION}\Open log folder.lnk" "$LOCALAPPDATA\${PRODUCT_NAME}\${PRODUCT_VERSION}"

  ; Pick up the installation parameters
  ReadINIStr $6 "$PLUGINSDIR\parameters.ini" "Field 8" "State"  # Language
  StrCmp $6 "English" 0 +3
    StrCpy $6 "en-us"
    Goto ok2
  StrCmp $6 "Dutch" 0 +3
    StrCpy $6 "nl"
    Goto ok2
  StrCmp $6 "French" 0 +3
    StrCpy $6 "fr"
    Goto ok2
  StrCmp $6 "Italian" 0 +3
    StrCpy $6 "it"
    Goto ok2
  StrCmp $6 "Japanese" 0 +3
    StrCpy $6 "ja"
    Goto ok2
  StrCmp $6 "Portuguese" 0 +3
    StrCpy $6 "pt"
    Goto ok2
  StrCmp $6 "Brazilian Portuguese" 0 +3
    StrCpy $6 "pt-br"
    Goto ok2
  StrCmp $6 "Simplified Chinese" 0 +3
    StrCpy $6 "zh_cn"
    Goto ok2
  StrCmp $6 "Spanish" 0 +3
    StrCpy $6 "es"
    Goto ok2
  StrCmp $6 "Traditional Chinese" 0 +3
    StrCpy $6 "zh_tw"
    Goto ok2
  MessageBox MB_ICONEXCLAMATION|MB_OK "Invalid language selection $6!"
  ok2:
  ReadINIStr $1 "$PLUGINSDIR\parameters.ini" "Field 10" "State"  # DB name
  ReadINIStr $2 "$PLUGINSDIR\parameters.ini" "Field 11" "State"  # DB user
  ReadINIStr $3 "$PLUGINSDIR\parameters.ini" "Field 12" "State"  # DB password
  ReadINIStr $4 "$PLUGINSDIR\parameters.ini" "Field 13" "State"  # DB host
  ReadINIStr $5 "$PLUGINSDIR\parameters.ini" "Field 14" "State"  # DB port

  ; Update the settings.py file
  SetOutPath "$INSTDIR\bin\custom"
  FileOpen $R2 "djangosettings.py" "r"
  GetTempFileName $R3
  FileOpen $R4 $R3 "w"
  ; Read the first section in settings.py and write unmodified to the output file
  read1_loop:
    FileRead $R2 $R5
    IfErrors end_loop
    FileWrite $R4 "$R5"
    StrCmp "$R5" "# ================= START UPDATED BLOCK BY WINDOWS INSTALLER =================$\n" +3 0
    StrCmp "$R5" "# ================= START UPDATED BLOCK BY WINDOWS INSTALLER =================$\r$\n" +2 0
  Goto read1_loop
  ; Read the second section in settings.py and write a different text to the output file
  read2_loop:
    FileRead $R2 $R5
    IfErrors end_loop
    StrCmp "$R5" "# ================= END UPDATED BLOCK BY WINDOWS INSTALLER =================$\n" +3 0
    StrCmp "$R5" "# ================= END UPDATED BLOCK BY WINDOWS INSTALLER =================$\r$\n" +2 0
  Goto read2_loop
  ${GetTime} "" "L" $day $month $year $day_name $hours $minutes $seconds
  FileWrite $R4 "# Make this unique, and don't share it with anybody.$\r$\n"
  FileWrite $R4 "SECRET_KEY = '%@mzit!i8b*$zc&6oev96=$year$month$day$hours$minutes$seconds'$\r$\n"
  FileWrite $R4 "$\r$\n"
  FileWrite $R4 "# FrePPLe only supports the 'postgresql_psycopg2' database.$\r$\n"
  FileWrite $R4 "# Create additional entries in this dictionary to define scenario schemas.$\r$\n"
  FileWrite $R4 "DATABASES = {$\r$\n"
  FileWrite $R4 "  'default': {$\r$\n"
  FileWrite $R4 "    'ENGINE': 'django.db.backends.postgresql_psycopg2',$\r$\n"
  FileWrite $R4 "    'NAME': '$1',  # Database name $\r$\n"
  FileWrite $R4 "    'USER': '$2',  # Database user.$\r$\n"
  FileWrite $R4 "    'PASSWORD': '$3', # Password of the database user.$\r$\n"
  FileWrite $R4 "    'HOST': '$4',     # Set to empty string for localhost.$\r$\n"
  FileWrite $R4 "    'PORT': '$5',     # Set to empty string for default port number.$\r$\n"
  FileWrite $R4 "    'OPTIONS': {},  # Backend specific configuration parameters.$\r$\n"
  FileWrite $R4 "    'TEST': {$\r$\n"
  FileWrite $R4 "      'NAME': 'test_$1',  # Database used when running the test suite.$\r$\n"
  FileWrite $R4 "      },$\r$\n"
  FileWrite $R4 "    },$\r$\n"
  FileWrite $R4 "  }$\r$\n$\r$\n"
  FileWrite $R4 "FREPPLE_LOGDIR = r'$LOCALAPPDATA\${PRODUCT_NAME}\${PRODUCT_VERSION}'$\r$\n$\r$\n"
  FileWrite $R4 "LANGUAGE_CODE = '$6' # Language for the user interface$\r$\n"
  ; Read the third section in settings.py and write unmodified to the output file
  read3_loop:
    FileWrite $R4 "$R5"
    FileRead $R2 $R5
    IfErrors end_loop
  Goto read3_loop
  end_loop:
    FileClose $R2
    FileClose $R4
    Rename "djangosettings.py" "djangosettings.py.old"
    Rename "$R3" "djangosettings.py"
    ClearErrors
SectionEnd


Function DatabaseOpen
  !insertmacro MUI_HEADER_TEXT "Language selection and database configuration" "Specify the installation parameters."
  !insertmacro INSTALLOPTIONS_DISPLAY "parameters.ini"
FunctionEnd


Function Databaseleave
  ; Verify the connection to the database
  ReadINIStr $2 "$PLUGINSDIR\parameters.ini" "Field 10" "State"  # DB name
  ReadINIStr $3 "$PLUGINSDIR\parameters.ini" "Field 11" "State"  # DB user
  ReadINIStr $4 "$PLUGINSDIR\parameters.ini" "Field 12" "State"  # DB password
  ReadINIStr $5 "$PLUGINSDIR\parameters.ini" "Field 13" "State"  # DB host
  ReadINIStr $6 "$PLUGINSDIR\parameters.ini" "Field 14" "State"  # DB port
  ${if} $2 == ""
  ${OrIf} $3 == ""
  ${OrIf} $4 == ""
    MessageBox MB_OK "Missing a mandatory field"
    ; Return to the page
    Abort
  ${endif}
  ClearErrors
  System::Call 'Kernel32::SetEnvironmentVariable(t, t)i ("PGPASSWORD", "$4").r0'
  ExecWait 'psql -d $2 -U $3 -h $5 -p $6 -c "select version();"'
  IfErrors 0 ok
     StrCpy $1 'A test connection to the database failed...$\r$\n$\r$\n'
     StrCpy $1 '$1Update the parameters or:$\r$\n'
     StrCpy $1 '$1  1) Install PostgreSQL 9.4$\r$\n'
     StrCpy $1 '$1  2) Configure it to till you can successfully connect from the commands:$\r$\n'
     StrCpy $1 '$1        set PGPASSWORD=$4$\r$\n'
     StrCpy $1 '$1        psql -d $2 -U $3 -h $5 -p $6 -c "select version();"$\r$\n'
     StrCpy $1 '$1  3) Assure psql is on the PATH environment variable'
     MessageBox MB_OK $1
     ; Return to the page
     Abort
  ok:
FunctionEnd


Function FinishOpen
  ; Display the page
  ${If} $MultiUser.InstallMode == "CurrentUser"
    WriteIniStr "$PLUGINSDIR\finish.ini" "Field 6" "Flags" "DISABLED"
  ${EndIf}
  !insertmacro MUI_HEADER_TEXT "Completing the installation" "frePPLe has been installed on your computer"
  !insertmacro INSTALLOPTIONS_DISPLAY "finish.ini"
FunctionEnd


Function FinishLeave
  ; Check how we left the screen: toggle "install service", toggle "run in console", or "next" button
  ReadINIStr $0 "$PLUGINSDIR\finish.ini" "Settings" "State"
  ${If} $0 == 5
     ; Toggling the "run in system tray" checkbox
     ReadINIStr $0 "$PLUGINSDIR\finish.ini" "Field 5" "State"
     ${If} $0 == 1
       ; Deactivate the "install service" checkbox
       WriteIniStr "$PLUGINSDIR\finish.ini" "Field 6" "State" "0"
       readinistr $2 "$PLUGINSDIR\finish.ini" "Field 6" "HWND"
       SendMessage $2 ${BM_SETCHECK} 0 0
     ${EndIf}
     Abort  ; Return to the page
  ${ElseIf} $0 == 6
     ; Toggling the "install service" checkbox
     ReadINIStr $0 "$PLUGINSDIR\finish.ini" "Field 6" "State"
     ${If} $0 == 1
       ; Deactivate the "run in system tray" checkbox
       WriteIniStr "$PLUGINSDIR\finish.ini" "Field 5" "State" "0"
       readinistr $2 "$PLUGINSDIR\finish.ini" "Field 5" "HWND"
       SendMessage $2 ${BM_SETCHECK} 0 0
     ${EndIf}
     Abort  ; Return to the page
  ${EndIf}

  ; Start the server in system tray
  ReadINIStr $0 "$PLUGINSDIR\finish.ini" "Field 5" "State"
  ${If} $0 == 1
    Exec '"$INSTDIR\bin\freppleserver.exe"'
  ${EndIf}

  ; Install the service
  ReadINIStr $0 "$PLUGINSDIR\finish.ini" "Field 6" "State"
  ${If} $0 == 1
    nsExec::Exec '"$INSTDIR\bin\freppleservice.exe" --startup auto install'
    sleep 2
    nsExec::Exec '"$INSTDIR\bin\freppleservice.exe" start'
    CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME} ${PRODUCT_VERSION}\Start service.lnk" "$INSTDIR\bin\freppleservice.exe" "start"
    CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME} ${PRODUCT_VERSION}\Stop service.lnk" "$INSTDIR\bin\freppleservice.exe" "stop"
  ${EndIf}
FunctionEnd


Section "Documentation" SecDoc
  SetOutPath "$INSTDIR"
  SetOverwrite ifnewer
  CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME} ${PRODUCT_VERSION}"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME} ${PRODUCT_VERSION}\Documentation.lnk" "$INSTDIR\html\index.html"
  File /r "..\doc\_build\html"   ; Pick up doc from build folder, not dist folder
SectionEnd

Section "Examples" SecEx
  SetOutPath "$INSTDIR"
  SetOverwrite ifnewer
  File /r "test"
  SetOutPath "$INSTDIR\test"
SectionEnd

SubSection /E "Development" SecDev

Section /O "Header files" SecLib
  SetOutPath "$INSTDIR"
  SetOverwrite ifnewer
  File /r "include"
SectionEnd

Section /O "Source code" SecSrc
  SetOutPath "$INSTDIR"
  File /r "src"
SectionEnd

Section /O "Modules code" SecMod
  SetOutPath "$INSTDIR"
  File /r "modules"
SectionEnd

Section /O "Add-ons" SecContrib
  SetOutPath "$INSTDIR"
  File /r "contrib"
SectionEnd

SubSectionEnd


Section -AdditionalIcons
  WriteIniStr "$INSTDIR\${PRODUCT_NAME} web site.url" "InternetShortcut" "URL" "${PRODUCT_WEB_SITE}"
  CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME} ${PRODUCT_VERSION}"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME} ${PRODUCT_VERSION}\frePPLe web site.lnk" "${PRODUCT_WEB_SITE}"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME} ${PRODUCT_VERSION}\Uninstall.lnk" "$INSTDIR\uninst.exe" "/$MultiUser.InstallMode"
SectionEnd


Section -Post
  ; Clean up the distribution directory
  !cd ".."
  !system "sh -c 'rm -rf frepple-${PRODUCT_VERSION}'"

  ; Create the log directory
  CreateDirectory "$LOCALAPPDATA\${PRODUCT_NAME}\${PRODUCT_VERSION}"

  ; Create the database schema
  DetailPrint "Creating database schema"
  nsExec::ExecToLog /OEM /TIMEOUT=90000 '"$INSTDIR\bin\frepplectl.exe" migrate --noinput'
  Pop $0
  ${If} $0 == "0"
    DetailPrint "Loading demo data"
    nsExec::ExecToLog /OEM /TIMEOUT=90000 '"$INSTDIR\bin\frepplectl.exe" loaddata demo'
    DetailPrint "Generating initial plan"
    nsExec::ExecToLog /OEM /TIMEOUT=90000 '"$INSTDIR\bin\frepplectl.exe" frepple_run'
  ${else}
    DetailPrint "x $0 x"
    DetailPrint "ERROR CREATING DATABASE SCHEMA!!!"
    DetailPrint " "
    DetailPrint "Review the file 'bin\\custom\\djangosettings.py' and run 'frepplectl migrate'"
    DetailPrint " "
  ${EndIf}

  ; Create uninstaller
  WriteUninstaller "$INSTDIR\uninst.exe"
  WriteRegStr SHCTX "${PRODUCT_DIR_REGKEY}" "" "$\"$INSTDIR\bin\frepple.exe$\""
  WriteRegStr SHCTX "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr SHCTX "${PRODUCT_UNINST_KEY}" "UninstallString" "$\"$INSTDIR\uninst.exe$\" /$MultiUser.InstallMode"
  WriteRegStr SHCTX "${PRODUCT_UNINST_KEY}" "QuietUninstallString" "$\"$INSTDIR\uninst.exe$\" /$MultiUser.InstallMode /S"
  WriteRegStr SHCTX "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$\"$INSTDIR\bin\frepplectl.exe$\""
  WriteRegStr SHCTX "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr SHCTX "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr SHCTX "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
  WriteRegStr SHCTX "${PRODUCT_UNINST_KEY}" "NoModify" "1"
  WriteRegStr SHCTX "${PRODUCT_UNINST_KEY}" "NoRepair" "1"
  ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
  IntFmt $0 "0x%08X" $0
  WriteRegDWORD SHCTX "${PRODUCT_UNINST_KEY}" "EstimatedSize" "$0"

  ; Open the post-installation page
  Push "http://www.frepple.com/post-install/?version=${PRODUCT_VERSION}"
  Call openLinkNewWindow
SectionEnd


; Section descriptions
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SecAppl} "Installation of the compiled executables"
  !insertmacro MUI_DESCRIPTION_TEXT ${SecDoc} "Installation of the documentation"
  !insertmacro MUI_DESCRIPTION_TEXT ${SecEx} "Installation of example datasets and tests"
  !insertmacro MUI_DESCRIPTION_TEXT ${SecDev} "Installation for development purposes"
  !insertmacro MUI_DESCRIPTION_TEXT ${SecLib} "Header files and libraries"
  !insertmacro MUI_DESCRIPTION_TEXT ${SecSrc} "Installation of the core source code"
  !insertmacro MUI_DESCRIPTION_TEXT ${SecMod} "Installation of the source code of optional modules"
  !insertmacro MUI_DESCRIPTION_TEXT ${SecContrib} "Installation of a number of optional add-ons and utilities"
!insertmacro MUI_FUNCTION_DESCRIPTION_END


Function un.onUninstSuccess
  HideWindow
  MessageBox MB_ICONINFORMATION|MB_OK "$(^Name) was successfully removed from your computer."
FunctionEnd


Function un.onInit
  !insertmacro MULTIUSER_UNINIT
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "Are you sure you want to remove $(^Name) and all of its components?" IDYES +2
    Abort
FunctionEnd


Section Uninstall
  ; Remove the service
  nsExec::Exec '"$INSTDIR\bin\freppleservice.exe" stop'
  sleep 3
  nsExec::Exec '"$INSTDIR\bin\freppleservice.exe" remove'

  ; Remove the entries from the start menu
  Delete "$SMPROGRAMS\${PRODUCT_NAME} ${PRODUCT_VERSION}\Uninstall.lnk"
  Delete "$SMPROGRAMS\${PRODUCT_NAME} ${PRODUCT_VERSION}\Documentation.lnk"
  Delete "$SMPROGRAMS\${PRODUCT_NAME} ${PRODUCT_VERSION}\Start frePPLe server.lnk"
  Delete "$SMPROGRAMS\${PRODUCT_NAME} ${PRODUCT_VERSION}\frePPLe web site.lnk"
  Delete "$SMPROGRAMS\${PRODUCT_NAME} ${PRODUCT_VERSION}\Start service.lnk"
  Delete "$SMPROGRAMS\${PRODUCT_NAME} ${PRODUCT_VERSION}\Stop service.lnk"
  Delete "$SMPROGRAMS\${PRODUCT_NAME} ${PRODUCT_VERSION}\Open configuration folder.lnk"
  Delete "$SMPROGRAMS\${PRODUCT_NAME} ${PRODUCT_VERSION}\Open log folder.lnk"

  ; Remove the folder in start menu
  RMDir "$SMPROGRAMS\${PRODUCT_NAME} ${PRODUCT_VERSION}"

  ; Remove the log directory
  ; Version subdirectory is always removed.
  ; FrePPLe subdirectory is removed if it is empty.
  RMDir /r "$LOCALAPPDATA\${PRODUCT_NAME}\${PRODUCT_VERSION}"
  RMDir "$LOCALAPPDATA\${PRODUCT_NAME}"

  ; Remove the installation directory
  RMDir /r "$INSTDIR"
  Sleep 500
  IfFileExists "$INSTDIR" 0 Finished
  MessageBox MB_OK|MB_ICONEXCLAMATION "Alert: $INSTDIR could not be removed."
  Finished:

  ; Remove installation registration key
  DeleteRegKey SHCTX "${PRODUCT_UNINST_KEY}"
  DeleteRegKey SHCTX "${PRODUCT_DIR_REGKEY}"

  ; Do not automatically close the window
  SetAutoClose false

  ; Open the post-uninstallation page
  Push "http://www.frepple.com/post-uninstall/?version=${PRODUCT_VERSION}"
  Call un.openLinkNewWindow
SectionEnd
