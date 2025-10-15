Atualizando o executável (.exe)

Este projeto inclui um script simples `updater.py` que ajuda a baixar e substituir um .exe existente de forma atômica.

Fluxo recomendado (manual):

1. Gere o novo executável (se for a sua app) com PyInstaller ou sua ferramenta de build.
2. Coloque o novo .exe em um local acessível via HTTP (ex: servidor, GitHub Releases).
3. Obtenha o URL direto do .exe e (opcionalmente) o SHA256 do arquivo.
4. Execute no cliente:

```powershell
python updater.py --url "https://site.com/app-latest.exe" --target "C:\caminho\para\app.exe" --sha256 <sha256> --restart
```

Notas importantes:
- No Windows, não é possível substituir um .exe que estiver em uso. A aplicação alvo deve ser encerrada antes do swap. Se você usar `--restart`, o `updater.py` tentará reiniciar o .exe substituído, mas o swap falhará se o arquivo estiver bloqueado.
- Para atualizar o `ffmpeg.exe`, a lógica é a mesma: aponte `--target` para o `ffmpeg.exe` dentro da pasta `bin` e faça a substituição. Garanta permissões administrativas se necessário.

Automação (recomendada):
- Implementar no seu instalador/atualizador um processo em duas etapas:
  1. App principal baixa o update para um location temporário e solicita ao usuário reiniciar.
  2. No restart, um pequeno atualizador (updater.exe) substitui o arquivo e reinicia a app principal.

Segurança:
- Sempre valide checksums e assine seus releases se possível.
- Use HTTPS para transferências.

Limitações:
- `updater.py` é demonstrativo. Para produção, considere um mecanismo mais robusto (failsafe, rollback, assinatura de binários, atualizações delta).