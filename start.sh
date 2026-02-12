#!/bin/bash

# Definição das versões utilizadas
PYTHON_VERSION="3.12.10"
PYSIDE6_VERSION="6.10.1"
TENSORFLOW_VERSION="2.20.0"
NUMPY_VERSION="2.4.1"

echo "======================================================"
echo "  Gerador de Thumbnails - Configurando Ambiente"
echo "  Python: $PYTHON_VERSION"
echo "  PySide6: $PYSIDE6_VERSION"
echo "  TensorFlow: $TENSORFLOW_VERSION"
echo "  NumPy: $NUMPY_VERSION"
echo "======================================================"

echo "[1/4] Verificando instalacao do Python $PYTHON_VERSION..."
if ! python3 --version 2>&1 | grep -q "$PYTHON_VERSION"; then
    echo "Python $PYTHON_VERSION nao encontrado!"
    echo "Por favor, instale o Python $PYTHON_VERSION."
    exit 1
fi

echo "[2/4] Verificando ambiente virtual (venv)..."
if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Erro ao criar ambiente virtual."
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
