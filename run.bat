@echo off
SETLOCAL EnableExtensions

echo Verificando ambiente virtual...
IF EXIST "venv\Scripts\activate.bat" (
    echo Ativando ambiente virtual...
    call venv\Scripts\activate.bat
) ELSE (
    echo Ambiente virtual nao encontrado em .\venv. Usando Python do sistema.
)

echo Atualizando o pip...
python -m pip install --upgrade pip

echo Verificando e instalando dependencias...
pip install -r requirements.txt

echo Iniciando main.py...
python main.py

if %ERRORLEVEL% NEQ 0 (
    echo Ocorreu um erro durante a execucao.
    pause
)
