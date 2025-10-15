"""
updater.py

Script simples para atualizar um executável (.exe) local a partir de um URL.
Funcionalidades:
- Baixa o novo arquivo para um arquivo temporário
- (Opcional) valida checksum SHA256
- Substitui o executável alvo de forma atômica (move/rename)
- Pode reiniciar a aplicação substituída

Uso básico:
    python updater.py --url https://example.com/app-latest.exe --target "C:\path\to\app.exe" --restart

Observações:
- No Windows, substituir um executável em uso falhará se o arquivo estiver bloqueado; por isso a app pode precisar se encerrar antes do swap.
- Para atualizações do ffmpeg, use o mesmo fluxo apontando para o ffmpeg.exe alvo.
"""

import argparse
import hashlib
import os
import shutil
import sys
import tempfile
import urllib.request
from urllib.error import URLError, HTTPError


def download_file(url, dest_path, show_progress=True):
    try:
        with urllib.request.urlopen(url) as response:
            total = response.length or 0
            with open(dest_path, 'wb') as out_file:
                downloaded = 0
                chunk_size = 8192
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    downloaded += len(chunk)
                    if show_progress and total:
                        pct = downloaded * 100 / total
                        print(f"\rBaixando: {pct:.1f}% ({downloaded}/{total} bytes)", end='', flush=True)
        if show_progress:
            print('\nDownload concluído')
        return True
    except (URLError, HTTPError) as e:
        print(f"Erro ao baixar arquivo: {e}")
        return False
    except Exception as e:
        print(f"Erro inesperado no download: {e}")
        return False


def sha256_of_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def atomic_replace(src, dest):
    """Tenta mover/renomear src para dest de forma atômica.
    No Windows, se o dest existir e estiver em uso, a operação falhará.
    """
    backup = dest + '.backup'
    try:
        if os.path.exists(dest):
            # cria backup
            if os.path.exists(backup):
                os.remove(backup)
            os.replace(dest, backup)
        os.replace(src, dest)
        # se chegou aqui, remove backup
        if os.path.exists(backup):
            os.remove(backup)
        return True
    except Exception as e:
        print(f"Erro ao substituir o arquivo: {e}")
        # tenta reverter se possível
        if os.path.exists(backup) and not os.path.exists(dest):
            try:
                os.replace(backup, dest)
            except Exception:
                pass
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True, help='URL do .exe a baixar')
    parser.add_argument('--target', required=True, help='Caminho completo do .exe alvo a ser substituído')
    parser.add_argument('--sha256', help='Checksum SHA256 esperado (opcional)')
    parser.add_argument('--restart', action='store_true', help='Reinicia o executável alvo (se aplicável)')
    args = parser.parse_args()

    url = args.url
    target = args.target

    if not os.path.isabs(target):
        print('Por favor, forneça um caminho absoluto para --target')
        sys.exit(2)

    # local temporário para download
    tmp_dir = tempfile.mkdtemp(prefix='updater_')
    tmp_file = os.path.join(tmp_dir, 'new.exe')

    print(f"Baixando {url} para temporário {tmp_file} ...")
    ok = download_file(url, tmp_file)
    if not ok:
        print('Falha no download. Abortando.')
        shutil.rmtree(tmp_dir, ignore_errors=True)
        sys.exit(1)

    if args.sha256:
        print('Verificando checksum...')
        got = sha256_of_file(tmp_file)
        if got.lower() != args.sha256.lower():
            print(f"Checksum inválido: esperado {args.sha256}, obtido {got}")
            shutil.rmtree(tmp_dir, ignore_errors=True)
            sys.exit(1)
        print('Checksum OK')

    print(f"Tentando substituir {target} ...")
    success = atomic_replace(tmp_file, target)
    if not success:
        print('Não foi possível substituir o arquivo. Verifique se o executável alvo está em uso e tente novamente.')
        print(f'O download foi salvo em: {tmp_file}')
        sys.exit(1)

    print('Atualização aplicada com sucesso.')

    if args.restart:
        try:
            # tentar reiniciar o executável
            print('Tentando reiniciar o executável atualizado...')
            os.startfile(target)
        except Exception as e:
            print(f'Falha ao reiniciar: {e}')

    shutil.rmtree(tmp_dir, ignore_errors=True)

if __name__ == '__main__':
    main()
