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

set /p choice="Deseja compilar para .exe agora? (s/n): "
if /I "%choice%"=="s" (
    echo Compilando com PyInstaller...
    :: --noconsole para apps GUI (PySide6)
    :: --add-data para incluir a pasta assets e ffmpeg
    pyinstaller --noconsole --onefile --add-data "assets;assets" --add-data "ffmpeg;ffmpeg" --name "ExtratorDeFrame" main.py
    
    if EXIST "dist\ExtratorDeFrame.exe" (
        echo Movendo executavel para a raiz e limpando arquivos temporarios...
        move /y "dist\ExtratorDeFrame.exe" "."
        rmdir /s /q "build"
        rmdir /s /q "dist"
        del /q "ExtratorDeFrame.spec"
        echo Compilacao concluida com sucesso! O 'ExtratorDeFrame.exe' esta na raiz.
    ) ELSE (
        echo Erro na compilacao. O executavel nao foi encontrado.
    )
)

echo Iniciando main.py...
python main.py

if %ERRORLEVEL% NEQ 0 (
    echo Ocorreu um erro durante a execucao.
    pause
)
