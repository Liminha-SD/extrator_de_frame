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

:: 1. Verificar Conexão
echo [1/5] Verificando conexao...
ping -n 1 google.com >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Aviso: Sem internet. A instalacao pode falhar se for o primeiro uso.
) else (
    echo [OK] Conectado a internet.
)
echo.

:: 2. Verificar Python
echo [2/5] Configurando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [>] Python nao encontrado. Baixando instalador...
    
    if not exist "python_installer.exe" (
        :: curl -# mostra uma barra de progresso simples
        curl -L -# "%PYTHON_URL%" -o python_installer.exe
        if !errorlevel! neq 0 (
            echo.
            echo [ERRO] Falha ao baixar o Python. Instale em: https://www.python.org/
            pause
            exit /b 1
        )
    )
    
    echo [>] Instalando Python (isso pode levar alguns instantes)...
    echo     [....................] Instalando...
    start /wait python_installer.exe /quiet InstallAllUsers=0 Include_launcher=1 PrependPath=1
    del python_installer.exe
    
    echo [OK] Python instalado com sucesso.
    echo.
    echo [!] IMPORTANTE: REINICIE ESTE SCRIPT (feche e abra o .bat)
    echo     para o Windows reconhecer o novo caminho do Python.
    echo.
    pause
    exit /b 0
) else (
    for /f "tokens=2" %%v in ('python --version') do set CURRENT_PY=%%v
    echo [OK] Python !CURRENT_PY! detectado.
)
echo.

:: 3. Verificar FFmpeg
echo [3/5] Configurando FFmpeg...
set FFMPEG_PATH=%~dp0ffmpeg\bin
if not exist "%FFMPEG_PATH%\ffmpeg.exe" (
    echo [>] FFmpeg ausente. Baixando componentes necessarios...
    mkdir temp_ffmpeg >nul 2>&1
    curl -L -# "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" -o temp_ffmpeg\ffmpeg.zip
    
    if !errorlevel! equ 0 (
        echo [>] Extraindo arquivos...
        tar -xf temp_ffmpeg\ffmpeg.zip -C temp_ffmpeg
        if not exist "ffmpeg\bin" mkdir "ffmpeg\bin"
        for /d %%i in (temp_ffmpeg\ffmpeg-*) do (
            move /y "%%i\bin\*" "ffmpeg\bin\" >nul
        )
        rmdir /s /q temp_ffmpeg >nul 2>&1
        echo [OK] FFmpeg configurado localmente.
    ) else (
        echo [!] Falha ao baixar FFmpeg. Algumas funcoes podem nao funcionar.
    )
) else (
    echo [OK] FFmpeg detectado na pasta do projeto.
)
echo.

:: 4. Configurar Ambiente Virtual (venv)
echo [4/5] Configurando Ambiente Virtual...
if not exist "%VENV_DIR%" (
    echo [>] Criando novo ambiente isolado (venv)...
    python -m venv %VENV_DIR%
    if !errorlevel! neq 0 (
        echo [ERRO] Nao foi possivel criar o ambiente virtual.
        pause
        exit /b 1
    )
    echo [OK] Ambiente venv criado.
) else (
    echo [OK] Ambiente venv ja existe.
)
echo.

:: 5. Instalar Dependencias
echo [5/5] Sincronizando Bibliotecas...
call %VENV_DIR%\Scripts\activate.bat

echo [>] Atualizando gerenciador de pacotes (pip)...
python -m pip install --upgrade pip >nul 2>&1

echo [>] Verificando dependencias em %REQS_FILE%...
echo     (Isso pode demorar alguns minutos na primeira vez)
pip install -r %REQS_FILE% --quiet
if %errorlevel% neq 0 (
    echo.
    echo [ERRO] Falha ao instalar as bibliotecas. Verifique sua conexao.
    pause
    exit /b 1
)
echo [OK] Tudo pronto para iniciar!
echo.

:: Executar
title %APP_NAME% - Ativo
echo ------------------------------------------------------
echo           INICIANDO APLICATIVO
echo ------------------------------------------------------
python main.py

if %errorlevel% neq 0 (
    echo.
    echo [!] O programa parou inesperadamente (Codigo: %errorlevel%).
    pause
)

deactivate
