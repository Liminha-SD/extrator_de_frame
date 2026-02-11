#!/bin/bash

echo "[1/4] Verificando instalacao do Python..."
if ! command -v python3 &> /dev/null; then
    echo "Python3 nao encontrado!"
    echo "Por favor, instale o Python3 e o suporte a venv."
    echo "Exemplo (Ubuntu/Debian): sudo apt update && sudo apt install python3 python3-venv"
    exit 1
fi

echo "[2/4] Verificando ambiente virtual (venv)..."
if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Erro ao criar ambiente virtual."
        echo "Em sistemas Debian/Ubuntu, voce pode precisar instalar: sudo apt install python3-venv"
        exit 1
    fi
fi

echo "[3/4] Instalando/Atualizando dependencias..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Erro ao instalar dependencias."
    exit 1
fi

echo "[4/4] Iniciando o programa..."
python3 main.py
if [ $? -ne 0 ]; then
    echo "O programa encerrou com erro."
    exit 1
fi

deactivate
