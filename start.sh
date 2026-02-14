#!/bin/bash

# ======================================================
# Gerador de Thumbnails - Instalador e Executor (Linux/Mac)
# ======================================================
APP_NAME="Gerador de Thumbnails"
VENV_DIR="venv"
REQS_FILE="requirements.txt"

echo "======================================================"
echo "          $APP_NAME"
echo "======================================================"
echo ""

# 1. Verificar Python
echo "[1/4] Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "[ERRO] Python 3 nao encontrado. Por favor, instale o Python 3."
    exit 1
fi

# 2. Configurar Ambiente Virtual (venv)
echo "[2/4] Configurando ambiente virtual..."
if [ ! -d "$VENV_DIR" ]; then
    echo "Criando novo ambiente virtual (venv)..."
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "[ERRO] Falha ao criar ambiente virtual. Voce pode precisar instalar o pacote 'python3-venv'."
        exit 1
    fi
fi

# 3. Instalar Dependencias
echo "[3/4] Instalando dependencias..."
source "$VENV_DIR/bin/activate"
python3 -m pip install --upgrade pip
pip install -r "$REQS_FILE"
if [ $? -ne 0 ]; then
    echo "[ERRO] Falha ao instalar dependencias."
    exit 1
fi

# 4. Executar Programa
echo "[4/4] Iniciando $APP_NAME..."
python3 main.py
if [ $? -ne 0 ]; then
    echo ""
    echo "[AVISO] O programa encerrou com um codigo de erro ($?)."
fi

deactivate
