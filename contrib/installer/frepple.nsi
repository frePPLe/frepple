;
; Nullsoft script for creating a windows installer for frePPLe
;
;  file     : $URL$
;  revision : $LastChangedRevision$  $LastChangedBy$
;  date     : $LastChangedDate$
;
; Copyright (C) 2007 by Johan De Taeye
;
; This library is free software; you can redistribute it and/or modify it
; under the terms of the GNU Lesser General Public License as published
; by the Free Software Foundation; either version 2.1 of the License, or
; (at your option) any later version.
;
; This library is distributed in the hope that it will be useful,
; but WITHOUT ANY WARRANTY; without even the implied warranty of
; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
; General Public License for more details.
;
; You should have received a copy of the GNU Lesser General Public
; License along with this library; if not, write to the Free Software
; Foundation Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA
;

; This installer script is building on the GNU auto-build scripts. We first
; create the distribution make target, and then unzip it. The windows installer
; then selects subdirectories of this distribution tree to be installed.
; To run this script successfully, you'll therefore need to have the cygwin
; system up and running on your machine.

; Make sure that this variable points to the windows version of Python, not
; the one that is part of cygwin.
!ifndef PYTHON
!define PYTHON "python.exe"
!endif

; Main definitions
!define PRODUCT_NAME "frePPLe"
!define PRODUCT_VERSION "0.6.1"
!define PRODUCT_PUBLISHER "frePPLe"
!define PRODUCT_WEB_SITE "http://www.frepple.com"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\frepple.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME} ${PRODUCT_VERSION}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

; Select compressor
SetCompressor /SOLID lzma

;Include for Modern UI and library installation
!include "MUI.nsh"
!include Library.nsh
!include WinMessages.nsh
!include "Sections.nsh"

; MUI Settings
!define MUI_ABORTWARNING
!define MUI_WELCOMEFINISHPAGE_BITMAP "frepple.bmp"
!define MUI_UNWELCOMEFINISHPAGE_BITMAP "frepple.bmp"
!define MUI_WELCOMEPAGE_TEXT "This wizard will guide you through the installation of frePPLe.\n\nIt is recommended to uninstall a previous version before this installing a new one.\n\nClick Next to continue"
!define MUI_HEADERIMAGE_BITMAP "..\..\doc\frepple.bmp"
!define MUI_ICON "frepple.ico"
!define MUI_UNICON "frepple.ico"

; Installer pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "../../COPYING"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
Page custom database database_leave
  ; Definition of the finish page
  !define MUI_FINISHPAGE_NOAUTOCLOSE
  !define MUI_FINISHPAGE_RUN_TEXT "Start the server right now"
  !define MUI_FINISHPAGE_RUN "$INSTDIR\bin\manage.exe"
  !define MUI_FINISHPAGE_SHOWREADME_NOTCHECKED
  !define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\doc\index.html"
  !define MUI_FINISHPAGE_SHOWREADME_TEXT "View documentation"
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Language files
!insertmacro MUI_LANGUAGE "English"

;Version Information
VIProductVersion "0.6.1.0"
VIAddVersionKey /LANG=${LANG_ENGLISH} FileVersion "0.6.1.0"
VIAddVersionKey /LANG=${LANG_ENGLISH} ProductName "frePPLe Installer"
VIAddVersionKey /LANG=${LANG_ENGLISH} Comments "frePPLe Installer - free Production Planning Library"
VIAddVersionKey /LANG=${LANG_ENGLISH} CompanyName "frePPLe"
VIAddVersionKey /LANG=${LANG_ENGLISH} LegalCopyright "Licenced under the GNU Lesser General Public License"
VIAddVersionKey /LANG=${LANG_ENGLISH} FileDescription "Install frePPLe - free Production Planning Library"


; MUI end ------

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "${PRODUCT_NAME}_${PRODUCT_VERSION}_setup.exe"
InstallDir "$PROGRAMFILES\${PRODUCT_NAME} ${PRODUCT_VERSION}"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
BrandingText "${PRODUCT_NAME} ${PRODUCT_VERSION}"
CRCcheck on
ShowInstDetails show
ShowUnInstDetails show

ReserveFile "parameters.ini"
!insertmacro MUI_RESERVEFILE_INSTALLOPTIONS

Function .onInit
  ;Extract InstallOptions INI file
  !insertmacro MUI_INSTALLOPTIONS_EXTRACT "parameters.ini"
FunctionEnd

Section -Start
  ; Create the python distribution and django server
  !system "${PYTHON} setup.py"

  ; Create a distribution if none exists yet
  !cd "../.."
  !system "bash -c 'if (test ! -f frepple-${PRODUCT_VERSION}.tar.gz ); then make dist; fi'"

  ; Expand the distribution
  !system "bash -c 'rm -rf frepple-${PRODUCT_VERSION}'"
  !system "bash -c 'tar -xzf frepple-${PRODUCT_VERSION}.tar.gz'"

  ; Default content that is always installed
  !cd "frepple-${PRODUCT_VERSION}"
  SetOutPath "$INSTDIR"
  File "COPYING"
  File "README"
SectionEnd


Section "Application" SecAppl
  SectionIn RO     ; The app section can't be deselected
  SetOutPath "$INSTDIR\bin"
  SetOverwrite ifnewer

  ; Copy application, dll and libraries
  File "..\bin\frepple.exe"
  !insertmacro InstallLib DLL NOTSHARED NOREBOOT_NOTPROTECTED "..\bin\frepple.dll" "$INSTDIR\bin\frepple.dll" "$SYSDIR"
  File "..\bin\frepple.lib"
  File "..\bin\frepple.exp"

  ; Copy modules
  File "..\bin\mod_*.so"

  ; Copy configuration files
  File "..\bin\*.xsd"
  File "..\bin\init.xml"

  ; Copy sqlite database if there is one
  File /nonfatal "..\bin\frepple.sqlite"

  ; Copy the django and python redistributables created by py2exe
  SetOutPath "$INSTDIR\bin"
  File /r "..\contrib\installer\dist\*.*"

  ; Create menu
  CreateDirectory "$SMPROGRAMS\frePPLe ${PRODUCT_VERSION}"
  CreateShortCut "$SMPROGRAMS\frePPLe ${PRODUCT_VERSION}\Run server.lnk" "$INSTDIR\bin\manage.exe"

  ; Set an environment variable (and propagate immediately to other processes)
  System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("FREPPLE_HOME", "$INSTDIR\bin").r0'
  WriteRegExpandStr HKEY_CURRENT_USER "Environment" "FREPPLE_HOME" "$INSTDIR\bin"
  SendMessage ${HWND_BROADCAST} ${WM_WININICHANGE} 0 "STR:Environment" /TIMEOUT=5000

  ; Pick up the installation parameters
  ReadINIStr $6 "$PLUGINSDIR\parameters.ini" "Field 8" "State"  # Language
  StrCmp $6 "English" 0 +3
    StrCpy $6 "en-us"
    Goto ok2
  StrCmp $6 "Dutch" 0 +3
    StrCpy $6 "nl"
    Goto ok2
  MessageBox MB_ICONEXCLAMATION|MB_OK "Invalid language selection $6!"
  ok2:
  ReadINIStr $0 "$PLUGINSDIR\parameters.ini" "Field 9" "State"   # DB engine
  StrCmp $0 "SQLite" 0 +3
    StrCpy $0 "sqlite3"
    Goto ok
  StrCmp $0 "PostgreSQL 8.2" 0 +3
    StrCpy $0 "postgresql_psycopg2"
    Goto ok
  StrCmp $0 "MySQL" 0 +3
    StrCpy $0 "mysql"
    Goto ok
  StrCmp $0 "Oracle 10g" 0 +3
    StrCpy $0 "oracle"
    Goto ok
  MessageBox MB_ICONEXCLAMATION|MB_OK "Invalid database type $0!"
  ok:
  ReadINIStr $1 "$PLUGINSDIR\parameters.ini" "Field 10" "State"   # DB name
  ReadINIStr $2 "$PLUGINSDIR\parameters.ini" "Field 11" "State"   # DB user
  ReadINIStr $3 "$PLUGINSDIR\parameters.ini" "Field 12" "State"  # DB password
  ReadINIStr $4 "$PLUGINSDIR\parameters.ini" "Field 13" "State"  # DB host
  ReadINIStr $5 "$PLUGINSDIR\parameters.ini" "Field 14" "State"  # DB port

  ; Create a settings file for the server
  StrCpy $9 "$INSTDIR\bin\settings.py"
  FileOpen $9 $9 w
  FileWrite $9 "# Django supports the following database engines: 'oracle', 'postgresql_psycopg2',$\r$\n"
  FileWrite $9 "# 'postgresql', 'mysql', 'sqlite3' 'oracle' or 'ado_mssql'.$\r$\n"
  FileWrite $9 "# FrePPLe supports only 'postgresql_psycopg2', 'mysql' and 'sqlite3'$\r$\n"
  FileWrite $9 "DATABASE_ENGINE = '$0'$\r$\n"
  FileWrite $9 "DATABASE_NAME = '$1'  # Database name$\r$\n"
  FileWrite $9 "DATABASE_USER = '$2'  # Not used with sqlite3.$\r$\n"
  FileWrite $9 "DATABASE_PASSWORD = '$3' # Not used with sqlite3.$\r$\n"
  FileWrite $9 "DATABASE_HOST = '$4' # Set to empty string for localhost. Not used with sqlite3.$\r$\n"
  FileWrite $9 "DATABASE_PORT = '$5' # Set to empty string for default. Not used with sqlite3.$\r$\n"
  FileWrite $9 "LANGUAGE_CODE = '$6' # Language for the user interface$\r$\n"
  FileClose $9
SectionEnd


Function database
  StrCpy $1 "SQLite"

  ; Detect MySQL installation
  EnumRegKey $0 HKLM "software\MySQL AB" 0
  StrCmp $0 "" +2 0
  StrCpy $1 "$1|MySQL"

  ; Detect PostgreSQL installation
  EnumRegKey $0 HKLM "software\PostgreSQL" 0
  StrCmp $0 "" +2 0
  StrCpy $1 "$1|PostgreSQL 8.2"

  ; Detect Oracle installation
  EnumRegKey $0 HKLM "software\ORACLE" 0
  StrCmp $0 "" +2 0
  StrCpy $1 "$1|Oracle 10g"

  ; Update the dropdown with available databases
  WriteIniStr "$PLUGINSDIR\parameters.ini" "Field 9" "ListItems" "$1"

  ; Display the page
  !insertmacro MUI_HEADER_TEXT "Language selection and database configuration" "Specify the installation parameters."
  !insertmacro MUI_INSTALLOPTIONS_DISPLAY "parameters.ini"
FunctionEnd


Function database_leave
  ReadINIStr $0 "$PLUGINSDIR\parameters.ini" "Settings" "State"
  IntCmp $0 7 0 done
    ; Disable user name, user password, host and port when the
    ; SQLite database engine is selected.
    ReadINIStr $1 "$PLUGINSDIR\parameters.ini" "Field 9" "State"
    StrCpy $2 ""
    StrCpy $3 1
    StrCmp $1 "SQLite" 0 +3
      StrCpy $2 "DISABLED"
      StrCpy $3 0
    WriteIniStr "$PLUGINSDIR\parameters.ini" "Field 11" "Flags" "$2"
    ReadINIStr $4 "$PLUGINSDIR\parameters.ini" "Field 11" "HWND"
    EnableWindow $4 $3
    ReadINIStr $4 "$PLUGINSDIR\parameters.ini" "Field 11" "HWND2"
    EnableWindow $4 $3
    WriteIniStr "$PLUGINSDIR\parameters.ini" "Field 12" "Flags" "$2"
    ReadINIStr $4 "$PLUGINSDIR\parameters.ini" "Field 12" "HWND"
    EnableWindow $4 $3
    ReadINIStr $4 "$PLUGINSDIR\parameters.ini" "Field 12" "HWND2"
    EnableWindow $4 $3
    WriteIniStr "$PLUGINSDIR\parameters.ini" "Field 13" "Flags" "$2"
    ReadINIStr $4 "$PLUGINSDIR\parameters.ini" "Field 13" "HWND"
    EnableWindow $4 $3
    ReadINIStr $4 "$PLUGINSDIR\parameters.ini" "Field 13" "HWND2"
    EnableWindow $4 $3
    WriteIniStr "$PLUGINSDIR\parameters.ini" "Field 14" "Flags" "$2"
    ReadINIStr $4 "$PLUGINSDIR\parameters.ini" "Field 14" "HWND"
    EnableWindow $4 $3
    ReadINIStr $4 "$PLUGINSDIR\parameters.ini" "Field 14" "HWND2"
    EnableWindow $4 $3
    ; Return to the page
    Abort
  done:
FunctionEnd


Section "Documentation" SecDoc
  SetOutPath "$INSTDIR"
  SetOverwrite ifnewer
  CreateDirectory "$SMPROGRAMS\Frepple ${PRODUCT_VERSION}"
  CreateShortCut "$SMPROGRAMS\Frepple ${PRODUCT_VERSION}\Documentation.lnk" "$INSTDIR\doc\index.html"
  File /r "doc"
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
  CreateDirectory "$SMPROGRAMS\frePPLe ${PRODUCT_VERSION}"
  CreateShortCut "$SMPROGRAMS\frePPLe ${PRODUCT_VERSION}\frePPLe web site.lnk" "${PRODUCT_WEB_SITE}"
  CreateShortCut "$SMPROGRAMS\frePPLe ${PRODUCT_VERSION}\Uninstall.lnk" "$INSTDIR\uninst.exe"
SectionEnd


Section -Post
  ; Clean up the distribution directory
  !cd ".."
  !system "sh -c 'rm -rf frepple-${PRODUCT_VERSION}'"

  ; Create uninstaller
  WriteUninstaller "$INSTDIR\uninst.exe"
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\bin\frepple.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\bin\frepple.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
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
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "Are you sure you want to remove $(^Name) and all of its components?" IDYES +2
  Abort
FunctionEnd


Section Uninstall
  ; Remove the entries from the start menu
  Delete "$SMPROGRAMS\frePPLe ${PRODUCT_VERSION}\Uninstall.lnk"
  Delete "$SMPROGRAMS\frePPLe ${PRODUCT_VERSION}\Documentation.lnk"
  Delete "$SMPROGRAMS\frePPLe ${PRODUCT_VERSION}\Run server.lnk"
  Delete "$SMPROGRAMS\frePPLe ${PRODUCT_VERSION}\frePPLe web site.lnk"

  ; Remove the folder in start menu
  RMDir "$SMPROGRAMS\frePPLe ${PRODUCT_VERSION}"

  ; Removed the installation directory
  RMDir /r "$INSTDIR"
  Sleep 500
  IfFileExists "$INSTDIR" 0 Finished
  MessageBox MB_OK|MB_ICONEXCLAMATION "Alert: $INSTDIR could not be removed."
  Finished:

  ; Delete environment variable
  DeleteRegValue HKEY_CURRENT_USER "Environment" "FREPPLE_HOME"
  SendMessage ${HWND_BROADCAST} ${WM_WININICHANGE} 0 "STR:Environment" /TIMEOUT=5000

  ; Remove installation registration key
  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"

  ; Do not automatically close the window
  SetAutoClose false
SectionEnd
