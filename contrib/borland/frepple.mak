#
# Directories to be configured by the user.
# Other than than the next two lines no additional changes should be required.
#
ROOT = C:\develop\frepple
XERCES = C:\develop\dll
XERCESVERSION = 2_7_0

#
# Convenience variables
#
TARGETPATH = $(ROOT)\contrib\borland\obj
PROJECTS = $(ROOT)\bin\frepple_bcc.exe \
           $(ROOT)\lib\frepple_bcc_static.lib \
           $(ROOT)\bin\frepple_bcc.dll \
           $(ROOT)\bin\module_forecast_bcc.dll

#
# Compiler and linker flags
#
USERDEFINES = HAVE_WINDOWS_H;HAVE_STRNICMP;HAVE_ATEXIT;NDEBUG
INCLUDEPATH = ..\..\include;$(XERCES)
LIBPATH = $(TARGETPATH);$(INCLUDEPATH)
# For production build:
CFLAG1 = -WC -WM -O2 -q -c -v- -b- -k-
LFLAGS_EXE = -Gl -q -I$(XERCES) -ap -x -Gn
LFLAGS_DLL = -Gl -Gi -q -I$(XERCES) -Tpd -x -Gn
# For debugging build:
#CFLAG1 = -WC -WM -O2 -q -c -v -b- -k
#LFLAGS_EXE = -Gl -q -I$(XERCES) -ap -x -Gn /v
#LFLAGS_DLL = -Gl -Gi -q -I$(XERCES) -Tpd -x -Gn /v
WARNINGS= -w-inl -w-par -w-hid -w-pia
ALLLIB = c0x32.obj import32.lib cw32mt.lib xerces-bor_$(XERCESVERSION).lib

#
# Object files to be compiled
#
OBJFILES = \
   $(TARGETPATH)\model\actions.obj \
   $(TARGETPATH)\model\actions.obj \
   $(TARGETPATH)\model\buffer.obj \
   $(TARGETPATH)\model\calendar.obj \
   $(TARGETPATH)\model\customer.obj \
   $(TARGETPATH)\model\demand.obj \
   $(TARGETPATH)\model\flow.obj \
   $(TARGETPATH)\model\flow_plan.obj \
   $(TARGETPATH)\model\item.obj \
   $(TARGETPATH)\model\leveled.obj \
   $(TARGETPATH)\model\library.obj \
   $(TARGETPATH)\model\load.obj \
   $(TARGETPATH)\model\load_plan.obj \
   $(TARGETPATH)\model\location.obj \
   $(TARGETPATH)\model\operation.obj \
   $(TARGETPATH)\model\operation_plan.obj \
   $(TARGETPATH)\model\plan.obj \
   $(TARGETPATH)\model\problem.obj \
   $(TARGETPATH)\model\problems_buffer.obj \
   $(TARGETPATH)\model\problems_demand.obj \
   $(TARGETPATH)\model\problems_operation_plan.obj \
   $(TARGETPATH)\model\problems_resource.obj \
   $(TARGETPATH)\model\resource.obj \
   $(TARGETPATH)\solver\solverbuffer.obj \
   $(TARGETPATH)\solver\solverdemand.obj \
   $(TARGETPATH)\solver\solveroperation.obj \
   $(TARGETPATH)\solver\solverplan.obj \
   $(TARGETPATH)\solver\solverresource.obj \
	 $(TARGETPATH)\utils\actions.obj \
   $(TARGETPATH)\utils\date.obj \
	 $(TARGETPATH)\utils\library.obj \
	 $(TARGETPATH)\utils\status.obj \
	 $(TARGETPATH)\utils\datainput.obj \
	 $(TARGETPATH)\utils\name.obj \
	 $(TARGETPATH)\utils\thread.obj \
   $(TARGETPATH)\main.obj \
   $(TARGETPATH)\dllmain.obj \
   $(TARGETPATH)\tags.obj

#
# Implicit make rules
#
.autodepend
{..\..\src}.cpp{$(TARGETPATH)}.obj:
    $(MAKEDIR)\bcc32 $(CFLAG1) $(WARNINGS) -I$(INCLUDEPATH) -D$(USERDEFINES);$(SYSDEFINES) -n$(@D) {$< }
{..\..\src\solver}.cpp{$(TARGETPATH)\solver}.obj:
    $(MAKEDIR)\bcc32 $(CFLAG1) $(WARNINGS) -I$(INCLUDEPATH) -D$(USERDEFINES);$(SYSDEFINES) -n$(@D) {$< }
{..\..\src\model}.cpp{$(TARGETPATH)\model}.obj:
    $(MAKEDIR)\bcc32 $(CFLAG1) $(WARNINGS) -I$(INCLUDEPATH) -D$(USERDEFINES);$(SYSDEFINES) -n$(@D) {$< }
{..\..\src\modules\forecast}.cpp{$(TARGETPATH)\forecast}.obj:
    $(MAKEDIR)\bcc32 $(CFLAG1) $(WARNINGS) -I$(INCLUDEPATH) -D$(USERDEFINES);$(SYSDEFINES) -n$(@D) {$< }
{..\..\src\utils}.cpp{$(TARGETPATH)\utils}.obj:
    $(MAKEDIR)\bcc32 $(CFLAG1) $(WARNINGS) -I$(INCLUDEPATH) -D$(USERDEFINES);$(SYSDEFINES) -n$(@D) {$< }

#
# Make targets
#

# First and default make target
all: MakeBuildDirs $(PROJECTS)

# Build main executable
$(ROOT)\bin\frepple_bcc.exe: $(OBJFILES)
  $(MAKEDIR)\BRCC32 -i $(MAKEDIR)\..\include -fo obj\exe.res -32 ..\..\src\exe.rc  
	$(MAKEDIR)\ilink32 $(LFLAGS_EXE) -L$(LIBPATH) $(OBJFILES),$@,,$(ALLLIB),,obj\exe.res

# Build static library
# @todo this is currently not complete: source files with identical names
# existing multiple directories, and the library tool doesn't appreciate
# that... Only one of the files is added in the library.
$(ROOT)\lib\frepple_bcc_static.lib: $(OBJFILES)
	$(MAKEDIR)\tlib /P64 /C $@ /u $(OBJFILES), $(TARGETPATH)\frepple.lst

$(ROOT)\bin\frepple_bcc.dll: $(OBJFILES)
  $(MAKEDIR)\BRCC32 -i $(MAKEDIR)\..\include -fo obj\dll.res -32 ..\..\src\dll.rc  
	$(MAKEDIR)\ilink32 $(LFLAGS_DLL) -L$(LIBPATH) $(OBJFILES),$@,,$(ALLLIB),..\..\src\frepple.def,obj\dll.res
	move $(ROOT)\bin\frepple_bcc.lib $(ROOT)\lib\frepple_bcc.lib

$(ROOT)\bin\module_forecast_bcc.dll: $(TARGETPATH)\forecast\forecast.obj
	$(MAKEDIR)\ilink32 $(LFLAGS_DLL) -L$(LIBPATH) $(TARGETPATH)\forecast\forecast.obj,$@,,$(ALLLIB),,
	move $(ROOT)\bin\module_forecast_bcc.lib $(ROOT)\lib\module_forecast_bcc.lib

# Make build directories
MakeBuildDirs:
  -mkdir $(TARGETPATH)
  -mkdir $(TARGETPATH)\forecast
  -mkdir $(TARGETPATH)\solver
  -mkdir $(TARGETPATH)\model
  -mkdir $(TARGETPATH)\utils

# Cleanup make target
clean:
  -del /q /s $(TARGETPATH)
  -del $(ROOT)\bin\frepple_bcc.exe $(ROOT)\bin\frepple_bcc.dll $(ROOT)\lib\frepple_bcc_static.lib $(ROOT)\bin\*.tds


