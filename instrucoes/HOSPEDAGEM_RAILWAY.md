# Hospedagem temporária no Railway

Preparação para uma feira com 30–50 visitantes ao longo do dia. A aplicação usa um serviço web, um PostgreSQL e um volume privado de fotos. Não exige Redis, armazenamento de objetos, domínio comprado ou mudança nos modelos. O número de visitantes não informa o pico simultâneo: faça o ensaio abaixo antes de imprimir as etiquetas.

Este roteiro não cria recursos. Publicação, contratação, backups cobrados e importação de dados devem ser autorizados antes da execução.

## Configuração entregue

- `Dockerfile` usa Python 3.14.6 e `requirements-railway.txt`. A lista explícita de arquivos e `.dockerignore` excluem segredos, banco, fotos e arquivos de trabalho da imagem.
- `config.settings_railway` exige configuração de produção válida, sem recorrer ao PostgreSQL local. A configuração padrão permanece em `config.settings`.
- Gunicorn escuta `0.0.0.0:$PORT`, com um processo e duas threads, sem log de URLs de acesso. É um ponto de partida econômico, não uma garantia de capacidade.
- WhiteNoise serve CSS, JS e marca após `collectstatic`, com nomes versionados e compressão. Nunca serve fotos.
- O início executa verificações de segurança, `collectstatic`, verificação do volume e banco, `migrate` e Gunicorn. Não cria contas nem cadastros automaticamente. Uma falha interrompe o início.
- `/saude/` retorna 200 quando o PostgreSQL responde e 503 quando indisponível, sem detalhes internos. Somente essa rota dispensa redirecionamento HTTPS para permitir o healthcheck interno.

Os arquivos de fotos ficam no volume; o PostgreSQL guarda suas referências e os relatos. A rota existente exige usuário com permissão de consultar chamados, retorna conteúdo privado sem cache e recusa acesso anônimo. Não configure `MEDIA_URL`, bucket público ou rota de arquivos para o volume. Resolver um relato continua apagando seus anexos após a confirmação da transação. Backups anteriores podem conter os arquivos já descartados.

## Etapas no painel, após autorização

1. Revise o plano, os preços e o orçamento da conta. Configure alerta e limite de gastos em **Workspace / Usage**. Um limite atingido pode derrubar os serviços durante a feira; reserve margem. Não se pressupõe gratuidade. Veja [controle de custos](https://docs.railway.com/pricing/cost-control).
2. Crie um projeto e um serviço PostgreSQL. Crie o serviço web ligado ao repositório e à branch escolhida para a feira. Mantenha web e banco na mesma região e ambiente. Suspenda deploy automático enquanto prepara variáveis e volume.
3. No serviço web, anexe um volume em **`/dados`**. Defina `QREPARO_FOTOS_ROOT=/dados/fotos`. O Railway injeta `RAILWAY_VOLUME_MOUNT_PATH`; não simule essa variável para esconder uma montagem ausente. O comando de inicialização exige uma subpasta do volume e testa leitura/escrita.
4. Em **Networking / Public Networking**, gere o domínio Railway do serviço web. Defina explicitamente a porta de destino **8000** e `PORT=8000`. O domínio recebe HTTPS. Não publique a porta do banco para uso pela aplicação: use a conexão privada. Veja [rede pública](https://docs.railway.com/networking/public-networking).
5. Configure as variáveis da tabela. Substitua `seu-app.up.railway.app` pelo domínio real, sem protocolo em `DJANGO_ALLOWED_HOSTS`. Se o PostgreSQL tiver outro nome de serviço, ajuste a referência `${{Postgres.DATABASE_URL}}`.
6. Confirme uso do Dockerfile e de `railway.json`, uma única réplica, healthcheck `/saude/` e timeout de 300 segundos. Não configure comando de build ou pre-deploy que dependa do banco ou volume. Não sobrescreva o comando de início da imagem.
7. Publique somente depois da revisão. Aguarde o healthcheck e confira logs. Pelo terminal do serviço web (ou `railway ssh` no serviço correto), execute os comandos de preparação abaixo.
8. No Admin, crie a conta do técnico com `chamados.view_chamado`, `chamados.change_chamado` e `equipamentos.view_equipamento`, conforme o acesso necessário. Use conta administrativa separada para gerenciar cadastros. Gere as etiquetas no ambiente hospedado e teste com um celular fora da rede do computador.

| Variável no serviço web | Valor |
| --- | --- |
| `DJANGO_SETTINGS_MODULE` | `config.settings_railway` (também definido na imagem) |
| `DJANGO_DEBUG` | `false` |
| `DJANGO_SECRET_KEY` | Segredo exclusivo, aleatório, com pelo menos 50 caracteres |
| `DJANGO_ALLOWED_HOSTS` | `seu-app.up.railway.app` (outros hosts exatos separados por vírgula) |
| `QREPARO_PUBLIC_URL` | `https://seu-app.up.railway.app` |
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}`, usando a referência privada do serviço |
| `QREPARO_FOTOS_ROOT` | `/dados/fotos` |
| `PORT` | `8000` |

Gere o segredo com `python -c "import secrets; print(secrets.token_urlsafe(64))"`, copie diretamente para a variável e não o registre no repositório. Não use o segredo nem as credenciais de desenvolvimento. `POSTGRES_*` continuam disponíveis para o ambiente padrão, mas não substituem `DATABASE_URL` neste perfil.

O perfil confia em `X-Forwarded-Proto` fornecido pelo proxy Railway, força HTTPS, habilita cookies seguros e aceita CSRF apenas da origem pública configurada. Essa confiança pressupõe acesso pelo proxy da plataforma, que [normaliza o cabeçalho para HTTPS](https://docs.railway.com/networking/public-networking/specs-and-limits). Não exponha diretamente a porta interna à internet em outra infraestrutura sem revisar essa configuração.

HSTS vale por uma hora, sem incluir subdomínios nem solicitar preload para uma hospedagem temporária. Somente os avisos Django `security.W005` e `security.W021` ficam silenciados por essa decisão; as demais advertências de deploy impedem o início.

```sh
python manage.py check --deploy --fail-level WARNING
python manage.py showmigrations --plan
python manage.py seed_qreparo
python manage.py createsuperuser
python manage.py verificar_hospedagem --fotos
```

`seed_qreparo` é repetível: prepara duas máquinas de demonstração e o catálogo, sem contas ou relatos. Para dados reais, cadastre os equipamentos necessários no Admin. Não é necessário importar o banco de desenvolvimento para uma demonstração. Se houver importação autorizada, banco e fotos precisam ser transferidos juntos, preservando caminhos relativos e tokens dos equipamentos.

O Railway monta [volumes somente em execução](https://docs.railway.com/volumes), não durante build/pre-deploy. Por isso a preparação está no comando de início. Use uma réplica; deploys com volume têm uma pequena interrupção. Evite atualizações durante a feira. O [healthcheck](https://docs.railway.com/deployments/healthchecks) verifica a entrada do deploy, não oferece monitoramento contínuo.

## Ensaio antes da feira

1. Confirme HTTPS sem alertas, `/saude/` com 200, login e estilos/ícones carregados. HTTP deve redirecionar para HTTPS.
2. Imprima uma etiqueta da hospedagem. Escaneie em celular usando dados móveis: a URL deve ter o domínio público, nunca localhost. Mudar `QREPARO_PUBLIC_URL` exige gerar novas etiquetas; não altera as já impressas.
3. Envie um relato com duas fotos, inclusive uma tirada pela câmera. Entre como técnico e abra miniaturas/lightbox. Copie a URL da foto para uma janela anônima: ela deve ser recusada. Uma conta sem permissão também não deve vê-la.
4. Reinicie o serviço web e confirme relato, foto e etiqueta ainda válidos. Execute `verificar_hospedagem --fotos` novamente. Isso comprova persistência além do filesystem descartável do container.
5. Resolva um relato de teste. Confirme desaparecimento das fotos e preservação da contagem. Use outro relato aberto para o ensaio de recuperação.
6. Faça alguns envios simultâneos com fotos nos aparelhos disponíveis. Observe memória, CPU, latência e erros no painel. A conversão de fotos é o principal pico de memória; só aumente recursos ou concorrência com evidência e orçamento autorizado.
7. Conclua um backup e um ensaio de restauração. Registre data, versão do código, contagens e resultado em registro operacional privado. Não teste carga destrutiva nem rode a suíte automatizada contra o banco da feira.

## Backup e recuperação

São necessários **banco e diretório de fotos do mesmo período**, além da versão do código. Um dump PostgreSQL não contém os bytes das fotos. Reserve uma janela sem envios ou resolução de relatos para produzir o par consistente; suspenda o serviço web e aguarde as requisições terminarem antes de copiar. Não apague o volume ao parar o serviço.

### Cópia independente da plataforma

Em uma máquina administrativa confiável, use ferramentas PostgreSQL compatíveis com a versão do servidor. Configure `PGHOST`, `PGPORT`, `PGUSER`, `PGDATABASE` e autenticação segura (`PGPASSFILE` ou `PGPASSWORD` temporária) com a conexão externa exibida pelo serviço, sem guardar senhas em comandos ou arquivos versionados. O hostname privado do Railway não funciona fora da rede da plataforma. A aplicação continua usando a conexão privada.

```sh
pg_dump --format=custom --no-owner --no-acl --file=qreparo-feira.dump
pg_restore --list qreparo-feira.dump
```

Selecione o projeto/ambiente correto na CLI autenticada e baixe a pasta do volume de fotos. O caminho da CLI é relativo à raiz do volume: `/fotos`, não `/dados/fotos`.

```sh
railway volume files --volume NOME_DO_VOLUME_DE_FOTOS download /fotos ./fotos-backup
```

Confira o sucesso dos dois comandos antes de retomar o serviço. Guarde dump e fotos fora do repositório, em armazenamento privado, junto com a data e a versão do código. Verifique tamanhos e hashes na transferência. Veja [backup PostgreSQL](https://railway.com/guides/postgres-backups-restores) e [transferência de arquivos do volume](https://docs.railway.com/cli/volume).

### Ensaio de restauração

1. Prepare um PostgreSQL vazio e uma pasta de fotos vazia em ambiente isolado, nunca por cima do banco ativo. Use a mesma versão do código do backup. Criar um segundo serviço pago exige autorização; o ensaio também pode usar infraestrutura de teste já disponível.
2. Aponte as variáveis `PG*` para esse banco vazio e confira host/nome antes de executar:

   ```sh
   pg_restore --exit-on-error --no-owner --no-acl --dbname=BANCO_VAZIO qreparo-feira.dump
   ```

3. Restaure o conteúdo de `fotos-backup` na pasta configurada em `QREPARO_FOTOS_ROOT`, preservando subdiretórios e nomes. No Railway, use o volume do ambiente de recuperação:

   ```sh
   railway volume files --volume VOLUME_DE_RECUPERACAO upload ./fotos-backup /fotos
   ```

4. Aponte a aplicação de recuperação para esse banco e volume. Confira `showmigrations --plan` e execute `verificar_hospedagem --fotos`. Esse comando confere conexão, escrita e presença/tamanho de cada foto referenciada; não prova integridade criptográfica nem encontra todos os arquivos órfãos.
5. Compare contagens de equipamentos, relatos e fotos com o backup; abra uma foto como técnico, confira bloqueio anônimo e teste um QR preservado. Só considere a recuperação comprovada depois dessas verificações. Não resolva relatos durante a conferência.
6. Em incidente real, mantenha o ambiente danificado preservado, interrompa escritas e só reative atendimento após validar o par restaurado. Uma restauração pode perder alterações posteriores ao backup e trazer conteúdo já descartado; escolha o ponto conscientemente.

### Snapshots opcionais no painel

Após autorizar o custo, faça backups dos volumes do PostgreSQL e do serviço web na aba **Backups**, durante a mesma janela sem escritas. Para restaurar, selecione o snapshot de cada serviço, revise as mudanças preparadas e aplique a restauração do par. Não restaure apenas o banco quando fotos também mudaram. Snapshots ficam sujeitos às limitações da plataforma e não substituem cópia externa; apagar um volume também elimina seus backups. Consulte [backups de volumes](https://docs.railway.com/volumes/backups).

## Encerramento

Após a feira, faça a cópia final e confira a restauração antes de remover recursos. Defina com os responsáveis o prazo de retenção dos backups, pois podem incluir fotos descartadas pela aplicação. Depois de autorizado, remova os recursos temporários e confira a cobrança: parar o processo web não equivale a eliminar custos de volumes, banco ou backups.

## Verificação de desenvolvimento

Instale `requirements-railway.txt` no ambiente de desenvolvimento para incluir os testes específicos do perfil. Gunicorn só é instalado em Linux; o servidor local continua usando a configuração padrão.

```sh
python -m pip install -r requirements-railway.txt
python manage.py test equipamentos chamados config --noinput
python manage.py makemigrations --check --dry-run
```

Os testes usam PostgreSQL de teste e pastas temporárias. Cobrem configuração insegura, URL do banco, healthcheck, proxy HTTPS, estáticos e detecção/recuperação de anexos ausentes. A construção Docker, o Gunicorn em Linux, o proxy Railway, a montagem real e a restauração dos recursos hospedados ainda precisam do ensaio no ambiente de destino; testes locais não comprovam esses itens.
