@echo off
setlocal enabledelayedexpansion

:: Definição das versões utilizadas
set PYTHON_VERSION=3.12.10
set PYSIDE6_VERSION=6.10.1
set TENSORFLOW_VERSION=2.20.0
set NUMPY_VERSION=2.4.1

echo ======================================================
echo   Gerador de Thumbnails - Configurando Ambiente
echo   Python: %PYTHON_VERSION%
echo   PySide6: %PYSIDE6_VERSION%
echo   TensorFlow: %TENSORFLOW_VERSION%
echo   NumPy: %NUMPY_VERSION%
echo ======================================================

echo [1/5] Verificando instalacao do Python %PYTHON_VERSION%...
python --version 2>nul | findstr /C:"%PYTHON_VERSION%" >nul
if %errorlevel% neq 0 (
    echo Python %PYTHON_VERSION% nao encontrado ou versao incorreta!
    echo Tentando instalar Python %PYTHON_VERSION% via winget...
    winget install --id Python.Python.3.12 --version %PYTHON_VERSION% --silent --accept-package-agreements --accept-source-agreements
    if !errorlevel! neq 0 (
        echo Nao foi possivel instalar o Python %PYTHON_VERSION% automaticamente via winget.
        echo Por favor, instale o Python %PYTHON_VERSION% manualmente em https://www.python.org/downloads/release/python-31210/
        pause
        exit /b 1
    )
    echo Python %PYTHON_VERSION% instalado com sucesso. Por favor, reinicie este script.
    pause
    exit /b 0
)

echo [2/5] Verificando instalacao do FFmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    if not exist "ffmpeg\bin\ffmpeg.exe" (
        echo FFmpeg nao encontrado no sistema nem na pasta local!
        echo Tentando instalar FFmpeg via winget...
        winget install --id Gyan.FFmpeg --silent --accept-package-agreements --accept-source-agreements
        if !errorlevel! neq 0 (
            echo Nao foi possivel instalar o FFmpeg automaticamente via winget.
            echo O programa pode nao funcionar corretamente sem o FFmpeg.
            pause
        ) else (
            echo FFmpeg instalado com sucesso.
        )
    ) else (
        echo FFmpeg encontrado na pasta local do projeto.
    )
) else (
    echo FFmpeg encontrado no sistema.
)

echo [3/5] Verificando ambiente virtual (venv)...
if not exist "venv" (
    echo Criando ambiente virtual...
    python -m venv venv
    if !errorlevel! neq 0 (
        echo Erro ao criar ambiente virtual.
        pause
        exit /b 1
    )
) else (
    venv\Scripts\python.exe --version 2>nul | findstr /C:"%PYTHON_VERSION%" >nul
    if !errorlevel! neq 0 (
        echo Ambiente virtual existente usa uma versao diferente do Python.
        echo Recomenda-se deletar a pasta 'venv' e rodar este script novamente.
        pause
    )
)

echo [4/5] Instalando/Atualizando dependencias...
call venv\Scripts\activate
python.exe -m pip install --upgrade pip
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
