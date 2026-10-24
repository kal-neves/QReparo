# QReparo

## backend em desenvolvimento

o cadastro de equipamentos e o fluxo público de relato já estão conectados ao banco

- cadastre laboratórios, locais, equipamentos e problemas no admin
- a identificação do equipamento pode ser um código interno, sem patrimônio institucional
- preencha a descrição do equipamento e mantenha cada local no seu laboratório original
- para mover um equipamento, escolha outro local no cadastro do equipamento
- execute `python manage.py seed_qreparo` para preparar dois equipamentos de exemplo
- configure `QREPARO_PUBLIC_URL` com a origem da aplicação, como `https://qreparo.example`
- abra o equipamento no admin e use o link de etiqueta
- o qr abre um formulário público com um problema e descrição opcional, obrigatória para outro problema

o endereço configurado para as etiquetas precisa ser acessível pelo celular e permitido em `DJANGO_ALLOWED_HOSTS`

login da aplicação, painel com dados reais, conferência em lote e contagem ainda estão em desenvolvimento

para verificar o backend, configure as variáveis `POSTGRES_*` para um banco de desenvolvimento e execute

```powershell
.\.venv\Scripts\python.exe manage.py test equipamentos chamados config.test_ui
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

os testes usam um banco separado criado pelo django e exigem permissão para criar bancos no postgres

não use credenciais de produção para executar os testes

Aplicação Django para registrar e acompanhar problemas em equipamentos de laboratórios universitários por QR Code.

## Instalação para desenvolvimento

Pré-requisitos: Python **3.14.6 ou superior**, acesso à internet para baixar as
dependências e PostgreSQL para executar a aplicação. No Linux, instale
também o pacote de suporte a `venv` da sua distribuição, caso necessário.

Abra um terminal na pasta do projeto e execute:

```powershell
# Windows
py -3.14 instalar.py
```

```bash
# Linux ou macOS
python3 instalar.py
```

Se o comando `py` não estiver disponível no Windows, use `python instalar.py` com
a versão exigida do Python no PATH.

O instalador cria `.venv`, instala as versões de `requirements.txt` usando `pip`,
verifica as dependências e executa `manage.py check`. Também cria `.env` a partir
de `.env.example`, gerando uma chave secreta aleatória para o ambiente local.
Arquivos `.env` existentes são preservados, inclusive sua chave secreta.
É possível executar o instalador novamente para instalar dependências atualizadas.
Se uma etapa falhar, ele interrompe a execução e informa o erro.

Não é necessário instalar ou usar `uv`, nem ativar o ambiente virtual para os
comandos abaixo. `pyproject.toml` declara as dependências diretas e o requisito de
Python; `requirements.txt` fixa as versões instaladas pela equipe. Ao atualizar
dependências, mantenha esses arquivos coerentes.

## Configuração do ambiente

Edite `.env` com os valores do seu ambiente:

| Variável | Uso |
| --- | --- |
| `DJANGO_SECRET_KEY` | Chave local gerada pelo instalador. Se o `.env` já existia, preencha caso esteja vazia. |
| `DJANGO_DEBUG` | `true` para desenvolvimento local. |
| `DJANGO_ALLOWED_HOSTS` | Hosts permitidos separados por vírgula; o exemplo permite acesso local. |
| `POSTGRES_DB` | Nome do banco, inicialmente `qreparo`. |
| `POSTGRES_USER` | Usuário do PostgreSQL, inicialmente `qreparo`. |
| `POSTGRES_PASSWORD` | Senha do usuário do banco. |
| `POSTGRES_HOST` | Endereço do PostgreSQL, inicialmente `localhost`. |
| `POSTGRES_PORT` | Porta do PostgreSQL, inicialmente `5432`. |

Crie o usuário e o banco no PostgreSQL, dando ao usuário permissão para criar
tabelas no banco escolhido. O instalador prepara o ambiente Python; a instalação
do PostgreSQL, criação do banco e execução de migrações são etapas separadas.
O comando `check` não confirma a conexão com o banco.

O `.env` contém segredos e já está excluído do Git.

## Executar a aplicação

Depois de configurar o PostgreSQL e o `.env`, execute no Windows:

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

No Linux ou macOS:

```bash
./.venv/bin/python manage.py migrate
./.venv/bin/python manage.py createsuperuser
./.venv/bin/python manage.py runserver
```

Crie o superusuário apenas no primeiro acesso ao seu banco. Com o servidor em
execução, acesse [a administração local](http://127.0.0.1:8000/admin/).


## Fluxo de instalação
1. Instalar Python 3.14.6 ou superior e PostgreSQL no computador.
2. Baixar o projeto e executar o instalador:
   py -3.14 instalar.py
   Ele cria .venv, instala as dependências com pip, cria .env com uma chave secreta e verifica a configuração do Django.
3. Criar manualmente no PostgreSQL o usuário qreparo, com senha, e o banco qreparo, com as permissões necessárias.
4. Editar .env, preenchendo POSTGRES_PASSWORD com essa senha. Se os nomes, endereço ou porta forem diferentes dos padrões, ajustar também.
5. Criar as tabelas e a primeira conta administrativa:
   .\.venv\Scripts\python.exe manage.py migrate
   .\.venv\Scripts\python.exe manage.py createsuperuser
6. Iniciar a aplicação:
   .\.venv\Scripts\python.exe manage.py runserver
   Acessar o painel administrativo.
