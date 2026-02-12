@echo off
setlocal enabledelayedexpansion

:: Definição das versões das bibliotecas
set PYSIDE6_VERSION=6.10.1
set TENSORFLOW_VERSION=2.20.0
set NUMPY_VERSION=2.4.1

echo ======================================================
echo   Gerador de Thumbnails - Configurando Ambiente
echo   Bibliotecas: PySide6, TensorFlow, NumPy
echo ======================================================

echo [1/5] Verificando instalacao do Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python nao encontrado no PATH.
    
    where winget >nul 2>nul
    if !errorlevel! neq 0 (
        echo Winget nao encontrado. Por favor, instale o Python 3 manualmente em python.org
        pause
        exit /b 1
    )

    echo Tentando instalar Python 3.12 via winget...
    winget install --id Python.Python.3.12 --source winget --silent --accept-package-agreements --accept-source-agreements
    
    if !errorlevel! neq 0 (
        echo Falha na instalacao silenciosa. Tentando interativa...
        winget install --id Python.Python.3.12 --source winget
    )

    if !errorlevel! neq 0 (
        echo Nao foi possivel instalar o Python automaticamente.
        echo Por favor, instale manualmente: https://www.python.org/
        pause
        exit /b 1
    )
    
    echo Python instalado. Reinicie este script para atualizar o PATH.
    pause
    exit /b 0
)

echo [2/5] Verificando instalacao do FFmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    if not exist "ffmpeg\bin\ffmpeg.exe" (
        echo FFmpeg nao encontrado. Tentando instalar via winget...
        winget install --id Gyan.FFmpeg --silent --accept-package-agreements --accept-source-agreements
    ) else (
        echo FFmpeg encontrado na pasta local.
    )
) else (
    echo FFmpeg encontrado no sistema.
)

echo [3/5] Verificando ambiente virtual (venv)...
if not exist "venv" (
    echo Criando ambiente virtual...
    python -m venv venv
    if !errorlevel! neq 0 (
        echo Erro ao criar ambiente virtual. Verifique se o modulo 'venv' esta instalado.
        pause
        exit /b 1
    )
)

echo [4/5] Instalando/Atualizando dependencias...
call venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if !errorlevel! neq 0 (
    echo Erro ao instalar dependencias.
    pause
    exit /b 1
)

echo [5/5] Iniciando o programa...
python main.py
if !errorlevel! neq 0 (
    echo O programa encerrou com erro.
    pause
    exit /b 1
)

deactivate
pause
