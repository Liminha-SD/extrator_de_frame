@echo off
setlocal enabledelayedexpansion

:: ======================================================
:: Gerador de Thumbnails - Instalador e Executor
:: ======================================================
set APP_NAME=Gerador de Thumbnails
set PYTHON_VERSION=3.12.1
set PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-amd64.exe
set VENV_DIR=venv
set REQS_FILE=requirements.txt

title %APP_NAME% - Inicializando...

echo ======================================================
echo           %APP_NAME%
echo ======================================================
echo.

:: 1. Verificar Conexão com Internet (opcional mas útil)
ping -n 1 google.com >nul 2>&1
if %errorlevel% neq 0 (
    echo [AVISO] Nao foi possivel detectar conexao com a internet. 
    echo         Se for a primeira vez rodando, a instalacao pode falhar.
    echo.
)

:: 2. Verificar Python
echo [1/5] Verificando instalacao do Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python nao encontrado. Iniciando processo de instalacao...
    
    if not exist "python_installer.exe" (
        echo Baixando instalador oficial do Python %PYTHON_VERSION%...
        curl -L "%PYTHON_URL%" -o python_installer.exe
        if !errorlevel! neq 0 (
            echo.
            echo [ERRO] Falha ao baixar o instalador do Python.
            echo Por favor, instale manualmente em: https://www.python.org/
            pause
            exit /b 1
        )
    )
    
    echo Instalando Python... Por favor, aguarde.
    start /wait python_installer.exe /quiet InstallAllUsers=0 Include_launcher=1 PrependPath=1
    del python_installer.exe
    
    echo.
    echo [SUCESSO] Python instalado! 
    echo IMPORTANTE: Voce precisa REINICIAR este script (fechar e abrir o .bat)
    echo para que o Windows reconheca o Python instalado.
    echo.
    pause
    exit /b 0
)

:: 3. Verificar FFmpeg
echo [2/5] Verificando FFmpeg...
set FFMPEG_PATH=%~dp0ffmpeg\bin
if not exist "%FFMPEG_PATH%\ffmpeg.exe" (
    echo FFmpeg nao encontrado em %FFMPEG_PATH%. Baixando...
    mkdir temp_ffmpeg >nul 2>&1
    curl -L "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" -o temp_ffmpeg\ffmpeg.zip
    
    if !errorlevel! equ 0 (
        echo Extraindo FFmpeg...
        tar -xf temp_ffmpeg\ffmpeg.zip -C temp_ffmpeg
        if not exist "ffmpeg\bin" mkdir "ffmpeg\bin"
        for /d %%i in (temp_ffmpeg\ffmpeg-*) do (
            move /y "%%i\bin\*" "ffmpeg\bin\" >nul
        )
        rmdir /s /q temp_ffmpeg >nul 2>&1
        echo [SUCESSO] FFmpeg configurado.
    ) else (
        echo [AVISO] Falha ao baixar FFmpeg. O programa pode nao funcionar corretamente.
    )
) else (
    echo FFmpeg ja esta presente.
)

:: 4. Configurar Ambiente Virtual (venv)
echo [3/5] Configurando ambiente virtual...
if not exist "%VENV_DIR%" (
    echo Criando novo ambiente virtual (venv)...
    python -m venv %VENV_DIR%
    if !errorlevel! neq 0 (
        echo [ERRO] Falha ao criar ambiente virtual.
        pause
        exit /b 1
    )
)

:: 5. Instalar Dependencias
echo [4/5] Instalando dependencias (isso pode demorar na primeira vez)...
call %VENV_DIR%\Scripts\activate.bat

:: Verificar se o pip precisa de upgrade
python -m pip install --upgrade pip >nul 2>&1

:: Instalar requisitos
pip install -r %REQS_FILE%
if %errorlevel% neq 0 (
    echo.
    echo [ERRO] Falha ao instalar dependencias. Verifique sua conexao.
    pause
    exit /b 1
)

:: 6. Executar Programa
echo [5/5] Iniciando %APP_NAME%...
echo.
title %APP_NAME% - Rodando
python main.py

if %errorlevel% neq 0 (
    echo.
    echo [AVISO] O programa encerrou com um codigo de erro (%errorlevel%).
    pause
)

deactivate
echo.
echo Obrigado por usar o %APP_NAME%!
pause
