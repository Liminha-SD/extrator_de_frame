# Extrator de Frames (AI-Powered)

Este projeto é uma ferramenta robusta com interface gráfica (GUI) desenvolvida em Python para extração inteligente de frames de vídeos. Ele utiliza **FFmpeg** para o processamento de vídeo e um modelo de **Deep Learning (TensorFlow/Keras)** para validar a qualidade dos frames extraídos, garantindo que apenas os "melhores" momentos (conforme treinado no modelo) sejam salvos.

## 🚀 Funcionalidades

- **Extração Inteligente**: Valida automaticamente se um frame é "bom" ou "ruim" usando Inteligência Artificial.
- **Fila de Processamento**: Adicione múltiplos vídeos para serem processados sequencialmente.
- **Interface Gráfica Moderna**: Desenvolvida com PySide6 (Qt) com tema escuro.
- **Configuração Flexível**: 
  - Ajuste a quantidade de frames desejada por vídeo.
  - Escolha se deseja usar a validação por IA ou extração pura.
  - Seleção personalizada de diretórios de saída e modelos Keras.
- **Logs em Tempo Real**: Acompanhe todo o processo de extração e predição da IA diretamente na interface.

## 🛠️ Pré-requisitos

Antes de começar, você precisará ter instalado:

1. **Python 3.10+**
2. **FFmpeg**: O projeto inclui um arquivo `ffmpeg.zip`. 
   - **Importante**: Extraia o conteúdo de `ffmpeg.zip` na raiz do projeto. Isso criará uma pasta `ffmpeg/bin` contendo os executáveis necessários. O programa está configurado para priorizar essa pasta local.

## 📦 Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/extrator_de_frame.git
   cd extrator_de_frame
   ```

2. Extraia o arquivo `ffmpeg.zip` para que a estrutura `ffmpeg/bin/ffmpeg.exe` exista.

3. (Opcional) Crie um ambiente virtual:
   ```bash
   python -m venv venv
   ```

4. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Como Usar

### Windows (Automático)
O script `run.bat` facilita o uso no Windows:
1. Execute o `run.bat`.
2. Ele tentará ativar o ambiente virtual na pasta `venv` (se existir). Caso contrário, usará o Python do sistema.
3. O script atualizará automaticamente as dependências do `requirements.txt` e abrirá a interface.
4. Ao final, ele oferece a opção de compilar o projeto para um executável `.exe`.

### Linux/macOS
1. Dê permissão de execução: `chmod +x run.sh`
2. Execute o script: `./run.sh`

### Manual (Qualquer SO)
1. Execute o aplicativo:
   ```bash
   python main.py
   ```

2. **Configuração Inicial**:
   - Ao abrir pela primeira vez, o programa verificará o FFmpeg. Se não encontrar, ele solicitará que você aponte para a pasta `bin` do FFmpeg.
   - Selecione um diretório de saída para os frames.
   - (Opcional) Para seleciona o seu modelo `.keras` ou `.h5` marque a opção "Carregar modelo Keras".

3. **Extração**:
   - Clique no ícone de `+` (Adicionar) para colocar vídeos na fila.
   - Ajuste o controle deslizante para definir quantos frames deseja extrair de cada vídeo.
   - Clique em **"Iniciar Extração"**.

## 🧠 Lógica de IA

O extrator utiliza uma estratégia de "passes" para garantir a qualidade:
1. **Extração Aleatória**: O software escolhe timestamps aleatórios ao longo de toda a duração do vídeo e extrai frames temporários.
2. **Processamento**: Cada frame é redimensionado para 128x128 pixels para ser compatível com a entrada do modelo.
3. **Classificação**: O modelo de Deep Learning analisa o frame. Se a predição for superior a 0.5 (GOOD), o frame é validado.
4. **Persistência**: Apenas frames validados são renomeados e salvos permanentemente. Se um frame for classificado como "BAD", ele é automaticamente deletado e uma nova tentativa é feita até que a meta de frames definida pelo usuário seja atingida.

## 📁 Estrutura do Projeto

- `main.py`: Código principal da aplicação.
- `assets/`: Ícones e recursos visuais.
- `requirements.txt`: Dependências do projeto.
- `ffmpeg.zip`: Binários do FFmpeg compactados.
- `run.bat`: Automação de setup e build para Windows.
- `run.sh`: Script de execução para sistemas baseados em Unix.

## 🛠️ Compilação (Gerar Executável)

### Via run.bat (Windows)
Basta executar o `run.bat` e digitar `s` quando perguntado se deseja compilar. O script gerará um executável único (`ExtratorDeFrame.exe`) na raiz do projeto e limpará os arquivos temporários.

### Via Linha de Comando
```bash
pyinstaller --noconsole --onefile --add-data "assets;assets" --add-data "ffmpeg;ffmpeg" --name "ExtratorDeFrame" main.py
```

---
Desenvolvido para facilitar a criação de datasets e seleção de thumbnails de alta qualidade.
