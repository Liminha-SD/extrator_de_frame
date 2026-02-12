@echo off
setlocal enabledelayedexpansion

:: Configuração de Versões
set PYTHON_VERSION=3.12.10
set PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-amd64.exe
set PYSIDE6_VERSION=6.10.1
set TENSORFLOW_VERSION=2.20.0
set NUMPY_VERSION=2.4.1

echo ======================================================
echo   Gerador de Thumbnails - Configurando Ambiente
echo   Versao Desejada do Python: %PYTHON_VERSION%
echo ======================================================

echo [1/5] Verificando versao do Python...
python --version 2>nul | findstr /C:"%PYTHON_VERSION%" >nul
if %errorlevel% neq 0 (
    echo Python %PYTHON_VERSION% nao encontrado ou versao diferente.
    echo Baixando instalador oficial da versao %PYTHON_VERSION%...
    
    curl -L "%PYTHON_URL%" -o python_installer.exe
    
    if !errorlevel! equ 0 (
        echo Instalando Python %PYTHON_VERSION%...
        echo Isso pode levar um minuto. Nao feche esta janela.
        
        :: /quiet: instalação silenciosa
        :: InstallAllUsers=0: instala apenas para o usuário (evita pedir admin)
        :: PrependPath=1: adiciona ao PATH automaticamente
        python_installer.exe /quiet InstallAllUsers=0 Include_launcher=1 PrependPath=1
        
        del python_installer.exe
        echo.
        echo Python %PYTHON_VERSION% instalado com sucesso!
        echo.
        echo IMPORTANTE: Por favor, FECHE ESTA JANELA e abra o start.bat novamente
        echo para que o Windows reconheça a nova versão no seu terminal.
        pause
        exit /b 0
    ) else (
        echo.
        echo ERRO: Falha ao baixar o Python %PYTHON_VERSION%.
        echo Verifique sua conexao ou instale manualmente em:
        echo https://www.python.org/downloads/release/python-31210/
        pause
        exit /b 1
    )
) else (
    echo Python %PYTHON_VERSION% ja esta pronto para uso.
)

echo [2/5] Verificando FFmpeg...
set FFMPEG_READY=0
if exist "ffmpeg\bin\ffmpeg.exe" (
    set FFMPEG_READY=1
) else (
    ffmpeg -version >nul 2>&1
    if !errorlevel! equ 0 set FFMPEG_READY=1
)

if %FFMPEG_READY% equ 0 (
    echo FFmpeg nao encontrado. Baixando via curl...
    mkdir temp_ffmpeg >nul 2>&1
    curl -L "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" -o temp_ffmpeg\ffmpeg.zip
    
    if !errorlevel! equ 0 (
        echo Extraindo FFmpeg...
        tar -xf temp_ffmpeg\ffmpeg.zip -C temp_ffmpeg
        for /d %%i in (temp_ffmpeg\ffmpeg-*) do (
            if not exist "ffmpeg\bin" mkdir "ffmpeg\bin"
            move /y "%%i\bin\*" "ffmpeg\bin\" >nul
        )
        rmdir /s /q temp_ffmpeg >nul 2>&1
        echo FFmpeg configurado em ffmpeg\bin\
    )
)

echo [3/5] Verificando ambiente virtual (venv)...
if not exist "venv" (
    echo Criando ambiente virtual com Python %PYTHON_VERSION%...
    python -m venv venv
)

echo [4/5] Instalando/Atualizando bibliotecas...
call venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

echo [5/5] Iniciando o programa...
python main.py
if !errorlevel! neq 0 (
    echo O programa encerrou com erro.
    pause
)

deactivate
