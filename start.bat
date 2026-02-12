@echo off
setlocal enabledelayedexpansion

echo [1/4] Verificando instalacao do Python 3.12.10...
python --version 2>nul | findstr /C:"3.12.10" >nul
if %errorlevel% neq 0 (
    echo Python 3.12.10 nao encontrado ou versao incorreta!
    echo Tentando instalar Python 3.12.10 via winget...
    winget install --id Python.Python.3.12 --version 3.12.10 --silent --accept-package-agreements --accept-source-agreements
    if !errorlevel! neq 0 (
        echo Nao foi possivel instalar o Python 3.12.10 automaticamente via winget.
        echo Por favor, instale o Python 3.12.10 manualmente em https://www.python.org/downloads/release/python-31210/
        pause
        exit /b 1
    )
    echo Python 3.12.10 instalado com sucesso. Por favor, reinicie este script.
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
) else (
    venv\Scripts\python.exe --version 2>nul | findstr /C:"3.12.10" >nul
    if !errorlevel! neq 0 (
        echo Ambiente virtual existente usa uma versao diferente do Python.
        echo Recomenda-se deletar a pasta 'venv' e rodar este script novamente.
        pause
    )
)

echo [3/4] Instalando/Atualizando dependencias...
call venv\Scripts\activate
python.exe -m pip install --upgrade pip
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
