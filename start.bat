@echo off
setlocal enabledelayedexpansion

echo [1/4] Verificando instalacao do Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python nao encontrado! Tentando abrir o instalador via winget...
    winget install Python.Python.3.10 --silent --accept-package-agreements --accept-source-agreements
    if !errorlevel! neq 0 (
        echo Nao foi possivel instalar o Python automaticamente.
        echo Por favor, instale o Python manualmente em https://www.python.org/
        pause
        exit /b 1
    )
    echo Python instalado com sucesso. Por favor, reinicie este script.
    pause
    exit /b 0
)

echo [2/4] Verificando ambiente virtual (venv)...
if not exist "venv" (
    echo Criando ambiente virtual...
    python -m venv venv
    if !errorlevel! neq 0 (
        echo Erro ao criar ambiente virtual.
        pause
        exit /b 1
    )
)

echo [3/4] Instalando/Atualizando dependencias...
call venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
if !errorlevel! neq 0 (
    echo Erro ao instalar dependencias.
    pause
    exit /b 1
)

echo [4/4] Iniciando o programa...
python main.py
if !errorlevel! neq 0 (
    echo O programa encerrou com erro.
    pause
    exit /b 1
)

deactivate
pause
