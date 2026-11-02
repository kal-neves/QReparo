# QReparo

Aplicação Django com PostgreSQL para registrar problemas em equipamentos de laboratórios universitários por QR Code.

O aluno envia um relato sem criar conta. O técnico consulta os relatos por equipamento, confere quais foram solucionados e confirma a resolução. Ao resolver, o sistema apaga a descrição e preserva os dados técnicos necessários para a contagem.

Esta versão implementa o MVP.

## Requisitos

- Python 3.14.6 ou superior
- PostgreSQL com um banco e um usuário para a aplicação
- Acesso à internet para instalar as dependências
- Suporte a `venv` instalado no sistema, se necessário no Linux

## Instalação

Na pasta do projeto, execute o instalador.

**Windows:**

```powershell
py -3.14 instalar.py
```

**Linux ou macOS:**

```bash
python3 instalar.py
```

Se `py` não estiver disponível no Windows, use `python instalar.py` com a versão exigida do Python.

O instalador cria `.venv`, instala as dependências de `requirements.txt` e cria `.env` a partir de `.env.example`, com uma chave secreta aleatória. Um `.env` existente é preservado. É possível executar o instalador novamente para atualizar as dependências conforme o arquivo de versões.

Não é necessário ativar o ambiente virtual ou instalar `uv` para seguir os comandos deste documento. O instalador não instala o PostgreSQL, não cria o banco e não aplica migrações. A verificação `manage.py check` também não confirma a conexão com o banco.

## Configuração

Crie o banco e o usuário no PostgreSQL, com permissão para criar tabelas no banco escolhido. Depois, ajuste o `.env`:

| Variável | Configuração |
| --- | --- |
| `DJANGO_SECRET_KEY` | Chave secreta gerada pelo instalador; preencha se o arquivo existente não tiver uma |
| `DJANGO_DEBUG` | `true` para desenvolvimento local; `false` fora desse ambiente |
| `DJANGO_ALLOWED_HOSTS` | Hosts permitidos, separados por vírgula, sem protocolo ou porta |
| `POSTGRES_DB` | Nome do banco; padrão `qreparo` |
| `POSTGRES_USER` | Usuário do banco; padrão `qreparo` |
| `POSTGRES_PASSWORD` | Senha do usuário do banco |
| `POSTGRES_HOST` | Endereço do PostgreSQL; padrão `localhost` |
| `POSTGRES_PORT` | Porta do PostgreSQL; padrão `5432` |
| `QREPARO_PUBLIC_URL` | Origem usada nas etiquetas, com protocolo e porta quando necessária, sem caminho; exemplo `http://127.0.0.1:8000` |

O `.env` contém segredos e não deve ser incluído no Git. Ao trocar de computador, configure o ambiente local e execute o instalador novamente, sem copiar a `.venv` de outra máquina.

## Primeira execução

Depois de configurar o banco e o `.env`, aplique as migrações, crie a primeira conta administrativa e inicie o servidor.

**Windows:**

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

**Linux ou macOS:**

```bash
./.venv/bin/python manage.py migrate
./.venv/bin/python manage.py createsuperuser
./.venv/bin/python manage.py runserver
```

Crie o superusuário apenas no primeiro acesso ao banco. Nas próximas execuções, basta iniciar o servidor; aplique novas migrações quando houver atualizações do projeto.

Acesse a [administração local](http://127.0.0.1:8000/admin/) para preparar os cadastros e as contas. O `runserver` é um servidor de desenvolvimento, não de produção.

### Banco com dados antigos

Antes de atualizar um banco existente, faça um backup e ensaie a migração em uma cópia separada. As migrações `0002_mvp_facil` removem campos antigos, apagam textos de relatos resolvidos e não podem ser desfeitas automaticamente.

Relatos cancelados, estados desconhecidos ou descrições abertas acima de 250 caracteres interrompem a conversão e precisam de revisão. Depois da migração, revise os equipamentos associados ao laboratório `LEGADO-REVISAR`.

## Cadastros e permissões

No Admin, cadastre laboratórios, locais, equipamentos e problemas. A identificação de um equipamento pode ser um código interno, sem patrimônio institucional. Preencha sua categoria (por exemplo, Computador ou Impressora), descrição e localização. A categoria identifica o tipo de equipamento, não o problema relatado.

A migração `equipamentos.0003_equipamento_categoria` acrescenta o campo sem inferir categorias para equipamentos existentes. Revise esses cadastros pelo Admin; o formulário exige categoria ao salvar. O comando de demonstração define a categoria somente para equipamentos novos e preserva os já cadastrados.

Cada local permanece no laboratório em que foi criado. Para transferir um equipamento, selecione outro local no cadastro. Equipamentos com histórico devem ser desativados, em vez de excluídos.

Crie as contas internas pelo Admin e atribua as permissões diretamente ou por grupo:

| Acesso | Permissões necessárias |
| --- | --- |
| Consultar relatos e contagem | `chamados.view_chamado` |
| Resolver relatos | `chamados.view_chamado` e `chamados.change_chamado` |
| Gerar etiquetas | `equipamentos.view_equipamento` |
| Usar o Admin | Conta ativa com `is_staff` e permissões dos cadastros correspondentes |

Ter acesso ao Admin não concede automaticamente acesso aos relatos.

Para preparar dois equipamentos e uma lista de problemas de demonstração, execute:

```powershell
.\.venv\Scripts\python.exe manage.py seed_qreparo
```

No Linux ou macOS, use `./.venv/bin/python manage.py seed_qreparo`. O comando pode ser repetido e não cria contas, senhas ou relatos.

## Uso da aplicação

1. Abra o equipamento no Admin e use **Ver etiqueta** para imprimir seu QR Code.
2. Escaneie a etiqueta e confira o equipamento e o laboratório.
3. Selecione um problema e envie o relato. A descrição aceita até 250 caracteres e é obrigatória apenas para **Outro problema**. Não inclua dados pessoais.
4. Entre na [área técnica local](http://127.0.0.1:8000/entrar/), abra o equipamento e selecione os relatos solucionados.
5. Confira a seleção e confirme a resolução. A descrição será apagada, sem possibilidade de reabertura nesta versão.
6. Consulte a contagem técnica, que permanece disponível após o descarte do texto.

Se algum relato selecionado já tiver sido resolvido, nenhum item daquele lote será alterado e será necessária uma nova conferência. Se ocorrer uma falha sem confirmação do resultado, consulte o painel antes de repetir a operação.

Equipamentos desativados não recebem novos relatos, mas continuam no painel enquanto tiverem relatos abertos. O aluno recebe apenas uma confirmação de envio, sem acompanhamento público.

### Acesso pelo celular

O endereço em `QREPARO_PUBLIC_URL` precisa ser acessível pelo celular. `localhost` e `127.0.0.1` apontam para o próprio aparelho, não para o computador que executa a aplicação.

Para um teste na rede local, configure essa variável com o endereço do computador, inclua o host em `DJANGO_ALLOWED_HOSTS` e inicie o servidor com `runserver 0.0.0.0:8000`. O celular precisa alcançar esse endereço e a porta deve estar permitida na rede. Use HTTPS ao disponibilizar a aplicação em rede fora desse teste local.

## Testes

Use uma conta PostgreSQL de desenvolvimento com permissão para criar bancos. O Django cria um banco de testes separado; o teste de migração legada cria e remove outro banco temporário. Não execute os testes com credenciais de produção.

**Windows:**

```powershell
.\.venv\Scripts\python.exe manage.py test equipamentos chamados config
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

**Linux ou macOS:**

```bash
./.venv/bin/python manage.py test equipamentos chamados config
./.venv/bin/python manage.py makemigrations --check --dry-run
```

## Documentação

Consulte a [documentação do projeto](instrucoes/README.md) e a [ordem de desenvolvimento](instrucoes/ORDEM_DE_DESENVOLVIMENTO.md) para conhecer o escopo e a sequência de entregas.
