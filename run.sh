#!/bin/bash

echo "Verificando ambiente virtual..."
if [ -d "venv" ]; then
    echo "Ativando ambiente virtual..."
    # Tenta ativar no formato Windows (Git Bash) ou Linux
    if [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
    elif [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    fi
else
    echo "Ambiente virtual nao encontrado em ./venv. Usando Python do sistema."
fi

echo "Atualizando o pip..."
python -m pip install --upgrade pip

echo "Verificando e instalando dependencias..."
pip install -r requirements.txt

echo "Iniciando main.py..."
python main.py
