#!/bin/bash



clear

# Verifica se o python3 está instalado
if ! command -v python3 &> /dev/null
then
    echo "O Python não está instalado. Por favor, instale antes de continuar."
    exit
fi

python3 -u fascinante.py
