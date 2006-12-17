;
; Nullsoft script for creating a windows installer for Frepple
;
;  file     : $HeadURL: https://svn.sourceforge.net/svnroot/frepple/trunk/contrib/installer/frepple.nsi $
;  revision : $LastChangedRevision$  $LastChangedBy$
;  date     : $LastChangedDate$
;  email    : jdetaeye@users.sourceforge.net
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

; Configuration section.
; UPDATE THIS SECTION ACCORDING TO YOUR SETUP!!!
!define XERCESPATH "c:\bin"
!define XERCESDLL "xerces-c_2_7.dll"

; Main definitions
!define PRODUCT_NAME "Frepple"
!define PRODUCT_VERSION "0.2.0"
!define PRODUCT_PUBLISHER "Frepple"
!define PRODUCT_WEB_SITE "http://frepple.sourceforge.net"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\frepple.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME} ${PRODUCT_VERSION}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

;Include for Modern UI and library installation
!include "MUI.nsh"
!include Library.nsh

; MUI Settings
!define MUI_ABORTWARNING
!define MUI_WELCOMEFINISHPAGE_BITMAP "frepple.bmp"
!define MUI_UNWELCOMEFINISHPAGE_BITMAP "frepple.bmp"
!define MUI_WELCOMEPAGE_TEXT "This wizard will guide you through the installation of Frepple.\n\nIt is recommended to uninstall a previous version before this installing a new one.\n\nClick Next to continue"
!define MUI_HEADERIMAGE_BITMAP "..\..\doc\frepple.bmp"
!define MUI_ICON "frepple.ico"
!define MUI_UNICON "frepple.ico"

; Installer pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "../../COPYING"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
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
VIProductVersion "0.2.0.0"
VIAddVersionKey /LANG=${LANG_ENGLISH} "FileVersion" "0.2.0"
VIAddVersionKey /LANG=${LANG_ENGLISH} "ProductName" "Frepple Installer"
VIAddVersionKey /LANG=${LANG_ENGLISH} "Comments" "Frepple Installer - Free Production Planning Library"
VIAddVersionKey /LANG=${LANG_ENGLISH} "CompanyName" "Frepple"
VIAddVersionKey /LANG=${LANG_ENGLISH} "LegalCopyright" "Licenced under the GNU Lesser General Public License"
VIAddVersionKey /LANG=${LANG_ENGLISH} "FileDescription" "Install Frepple - Free Production Planning Library"


; MUI end ------

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "${PRODUCT_NAME}_${PRODUCT_VERSION}_setup.exe"
InstallDir "$PROGRAMFILES\${PRODUCT_NAME} ${PRODUCT_VERSION}"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
BrandingText "${PRODUCT_NAME} ${PRODUCT_VERSION}"
CRCcheck on
ShowInstDetails show
ShowUnInstDetails show

Section -Start
  ; Create a distribution and expand it
  !cd "../.."
  !system "rm *.tar.gz"
  !system "make dist"
  !system "tar -xzf *.tar.gz"
  !cd "frepple-${PRODUCT_VERSION}"
  File "COPYING"
  File "README"
SectionEnd


Section "Application" SecAppl
	SectionIn RO     ; The app section can't be deselected
  SetOutPath "$INSTDIR\bin"
  SetOverwrite ifnewer

  ; Copy application, dll and libraries
  File "..\bin\frepple_vcc.exe"
  !insertmacro InstallLib DLL NOTSHARED NOREBOOT_NOTPROTECTED "..\bin\frepple_vcc.dll" "$INSTDIR\bin\frepple_vcc.dll" "$SYSDIR"
  File "..\bin\frepple_vcc.lib"
  File "..\bin\frepple_vcc.exp"

  ; Copy modules
  File "..\bin\mod_*.exp"
  File "..\bin\mod_*.lib"
  File "..\bin\mod_*.so"

  ; Copy configuration files
  File "bin\*.xsd"
  File "bin\*.xml"

  ; Add Xerces library
  !insertmacro InstallLib DLL NOTSHARED NOREBOOT_NOTPROTECTED "${XERCESPATH}\${XERCESDLL}" "$INSTDIR\bin\${XERCESDLL}" "$SYSDIR"

  ; Create menu
  CreateDirectory "$SMPROGRAMS\Frepple ${PRODUCT_VERSION}"
  CreateShortCut "$SMPROGRAMS\Frepple ${PRODUCT_VERSION}\Frepple.lnk" "$INSTDIR\bin\frepple.exe"

  ; Set an environment variable
  WriteRegExpandStr HKEY_CURRENT_USER "Environment" "FREPPLE_HOME" "$INSTDIR\bin"
SectionEnd


Section "Documentation" SecDoc
  SetOutPath "$INSTDIR"
  SetOverwrite ifnewer
  CreateDirectory "$SMPROGRAMS\Frepple ${PRODUCT_VERSION}"
  CreateShortCut "$SMPROGRAMS\Frepple ${PRODUCT_VERSION}\Frepple documentation.lnk" "$INSTDIR\doc\index.html"
  File /r "doc"
SectionEnd


Section "Examples" SecEx
  SetOutPath "$INSTDIR"
  SetOverwrite ifnewer
  File /r "test"
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

SubSectionEnd


Section "Add-ons" SecContrib
  SetOutPath "$INSTDIR"
  File /r "contrib"

	; A link to the excel sheet
  CreateDirectory "$SMPROGRAMS\Frepple ${PRODUCT_VERSION}"
  CreateShortCut "$SMPROGRAMS\Frepple ${PRODUCT_VERSION}\Frepple on Excel.lnk" "$INSTDIR\contrib\excel\frepple.xls"
SectionEnd


Section -AdditionalIcons
  WriteIniStr "$INSTDIR\${PRODUCT_NAME} web site.url" "InternetShortcut" "URL" "${PRODUCT_WEB_SITE}"
  CreateDirectory "$SMPROGRAMS\Frepple ${PRODUCT_VERSION}"
  CreateShortCut "$SMPROGRAMS\Frepple ${PRODUCT_VERSION}\Frepple web site.lnk" "${PRODUCT_WEB_SITE}"
  CreateShortCut "$SMPROGRAMS\Frepple ${PRODUCT_VERSION}\Uninstall.lnk" "$INSTDIR\uninst.exe"
SectionEnd


Section -Post
  ; Clean up the distribution files
  !cd ".."
  !system "rm -rf frepple-*"
  ; Create uninstaller
  WriteUninstaller "$INSTDIR\uninst.exe"
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\bin\frepple_vcc.exe"
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
  !insertmacro MUI_DESCRIPTION_TEXT ${SecSrc} "Installation of the complete source code"
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
  Delete "$SMPROGRAMS\Frepple ${PRODUCT_VERSION}\Uninstall.lnk"
  Delete "$SMPROGRAMS\Frepple ${PRODUCT_VERSION}\Frepple documentation.lnk"
  Delete "$SMPROGRAMS\Frepple ${PRODUCT_VERSION}\Frepple web site.lnk"
  Delete "$SMPROGRAMS\Frepple ${PRODUCT_VERSION}\Frepple.lnk"
  Delete "$SMPROGRAMS\Frepple ${PRODUCT_VERSION}\Frepple on Excel.lnk"

  ; Remove the folder in start menu
  RMDir "$SMPROGRAMS\Frepple ${PRODUCT_VERSION}"

  ; Removed the installation directory
  RMDir /r "$INSTDIR"
  Sleep 500
  IfFileExists "$INSTDIR" 0 Finished
  MessageBox MB_OK|MB_ICONEXCLAMATION "Alert: $INSTDIR could not be removed."
  Finished:

  ; Delete environment variable
  DeleteRegValue HKEY_CURRENT_USER "Environment" "FREPPLE_HOME"

  ; Remove installation registration key
  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"

  SetAutoClose true
SectionEnd
