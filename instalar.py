"""Prepara o ambiente local com a biblioteca padrão do Python, venv e pip."""

import os
from pathlib import Path
import secrets
import subprocess
import sys
import venv


RAIZ = Path(__file__).resolve().parent
AMBIENTE = RAIZ / '.venv'
PYTHON_MINIMO = (3, 14, 6)


def executar(*argumentos):
    subprocess.run([str(item) for item in argumentos], cwd=RAIZ, check=True)


def instalar():
    if sys.version_info < PYTHON_MINIMO:
        raise RuntimeError('Use Python 3.14.6 ou superior para executar instalar.py.')

    for nome in ('requirements.txt', '.env.example', 'manage.py'):
        if not (RAIZ / nome).is_file():
            raise RuntimeError(f'Arquivo obrigatório ausente: {nome}.')

    python = AMBIENTE / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if AMBIENTE.exists():
        if not (AMBIENTE / 'pyvenv.cfg').is_file() or not python.is_file():
            raise RuntimeError(
                'A pasta .venv não contém um ambiente válido. '
                'Renomeie-a e execute novamente para criar outro ambiente.'
            )
        print('Reutilizando .venv existente.', flush=True)
    else:
        print('Criando .venv...', flush=True)
        venv.EnvBuilder(with_pip=True).create(AMBIENTE)

    executar(
        python, '-c',
        'import sys; sys.exit(0 if sys.version_info >= (3, 14, 6) else '
        '"O Python da .venv é antigo. Renomeie .venv e execute o instalador novamente.")',
    )
    pip_disponivel = subprocess.run(
        [str(python), '-m', 'pip', '--version'], cwd=RAIZ,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    if pip_disponivel.returncode != 0:
        executar(python, '-m', 'ensurepip', '--upgrade')

    print('Instalando as dependências de requirements.txt...', flush=True)
    executar(python, '-m', 'pip', 'install', '-r', RAIZ / 'requirements.txt')
    executar(python, '-m', 'pip', 'check')

    destino = RAIZ / '.env'
    if destino.exists():
        print('.env existente preservado.', flush=True)
    else:
        modelo = (RAIZ / '.env.example').read_text(encoding='utf-8')
        chave = secrets.token_urlsafe(50)
        linhas = modelo.splitlines()
        if 'DJANGO_SECRET_KEY=' not in linhas:
            raise RuntimeError('O modelo .env.example deve conter DJANGO_SECRET_KEY= vazio.')
        conteudo = '\n'.join(
            f'DJANGO_SECRET_KEY={chave}' if linha == 'DJANGO_SECRET_KEY=' else linha
            for linha in linhas
        ) + '\n'
        with destino.open('x', encoding='utf-8') as arquivo:
            arquivo.write(conteudo)
        print('.env criado com uma chave secreta local.', flush=True)

    print('Verificando a configuração do Django...', flush=True)
    executar(python, RAIZ / 'manage.py', 'check')
    print(
        '\nInstalação concluída. Configure o PostgreSQL e as variáveis POSTGRES_* '
        'no .env. Depois execute migrate e runserver conforme o README.\n'
        'Esta verificação não testa a conexão com o banco de dados.',
        flush=True,
    )


if __name__ == '__main__':
    try:
        instalar()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as erro:
        print(f'\nInstalação interrompida: {erro}', file=sys.stderr)
        print('Corrija o problema indicado e execute o instalador novamente.', file=sys.stderr)
        sys.exit(1)
