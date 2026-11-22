# Fotos de relatos: contrato do back-end

Suporte incremental de fotos sobre o fluxo atual de relatos, integrado ao formulário público, aos relatos do equipamento e à conferência técnica. O servidor recebe o arquivo produzido pelo navegador; não controla a câmera.

O formulário oferece duas fotos opcionais, prévia local e captura quando suportada pelo navegador. Após erro de envio, é necessário selecionar novamente os arquivos. O técnico vê miniaturas horizontais e abre a imagem em lightbox, com fechamento por botão, Esc ou clique externo. Sem JavaScript, o link abre a página protegida `/tecnico/relatos/<id>/fotos/<uuid>/`.

## Envio

Enviar `POST` com `multipart/form-data` para `/e/<qr_token>/` (fluxo HTML) ou `/chamados/api/` (resposta JSON). Usar os campos atuais `problema` e `descricao`; na API, enviar também `qr_token`. Repetir o campo de arquivo `fotos` até duas vezes. As fotos são opcionais. Arquivos em outros campos são rejeitados. A API continua aceitando JSON sem fotos; imagens em JSON/base64 não são aceitas.

Ambas as rotas exigem CSRF. O formulário HTML retorna a confirmação existente por redirecionamento; a API retorna HTTP 201 com `{"mensagem": "Relato recebido."}`. Não retornar IDs, URLs de anexos ou conteúdo do relato ao solicitante. Erros de validação são apresentados como erros gerais no formulário ou HTTP 400 na API. O corpo acima do limite retorna HTTP 413 com mensagem JSON antes de interpretar os arquivos.

- Até duas fotos PNG, JPEG ou HEIC, identificadas pelo conteúdo real, sem confiar na extensão ou no MIME informado.
- Até 10.000.000 bytes por foto antes da conversão.
- Até 25.000.000 bytes no corpo completo da requisição, incluindo campos e estrutura multipart. Configurar o proxy/servidor de implantação com o mesmo limite; o middleware também verifica o corpo lido.
- Decodificar, corrigir orientação e converter para WebP estático sem EXIF, XMP, perfil ICC ou nome original. Imagens animadas usam o primeiro quadro; HEIC usa a imagem principal exposta pelo decodificador.
- Preservar resolução, ajustando qualidade de compressão de 85 até 65 para buscar aproximadamente 1 MB. Não há teto de saída de 1 MB. Permanecem as proteções do decodificador contra imagens corrompidas e bombas de descompressão.
- Validar todas as imagens antes de persistir. Falha de validação, escrita ou inserção cancela o relato e limpa os arquivos criados nesse envio.

`criar_relato(..., fotos=arquivos)` é o ponto de entrada do serviço. Usa transação durável para que o retorno de sucesso corresponda ao commit do banco. Não chamá-lo dentro de outra transação de produção nem habilitar `ATOMIC_REQUESTS` para essas rotas sem adaptar o contrato de armazenamento.

## Consulta técnica

As respostas existentes de `GET /chamados/api/` e `GET /chamados/api/<id>/` incluem `fotos`, uma lista ordenada por posição com `id`, `url`, `posicao`, `largura`, `altura` e `tamanho` em bytes. Não expor caminho de disco ou nome original.

`GET /chamados/<id>/fotos/<uuid>/` devolve os bytes WebP em resposta inline. Todas essas consultas exigem `chamados.view_chamado`, a permissão técnica usada no MVP atual. Ser staff ou ter apenas permissão de cadastro não concede acesso. O solicitante não recebe acesso nem pelo conhecimento da URL. A futura matriz de perfis deve preservar essa fronteira.

A resposta da imagem usa `Cache-Control` sem armazenamento, `Content-Type: image/webp`, `X-Content-Type-Options: nosniff` e política de conteúdo restritiva. Foto ausente, pertencente a outro relato ou de relato resolvido/reduzido retorna 404 para técnico autorizado. Visitante ou conta sem permissão recebe 403.

## Persistência e descarte

Aplicar `python manage.py migrate` para criar `chamados.Foto` pela migração `0003_foto`. A tabela guarda UUID, relação com o relato, posição, caminho privado, dimensões e tamanho. Restrições de posição e unicidade permitem no máximo duas fotos por relato. Registros existentes permanecem sem anexos.

Os bytes ficam em `QREPARO_FOTOS_ROOT`, configurável por variável de ambiente, com padrão `midia_privada/` na raiz. O nome gravado é aleatório. Essa pasta deve ser persistente, fora dos arquivos estáticos e de qualquer rota pública do servidor web; não configurar alias público ou `MEDIA_URL` para ela. O armazenamento recusa a geração de URL pública. Backups precisam incluir o banco e essa pasta.

Nesta entrega, os relatos ainda seguem o ciclo do MVP fácil: ao resolver, texto e fotos são descartados imediatamente, preservando a contagem. A remoção das linhas ocorre na transação; a remoção dos arquivos ocorre após commit. Rollback conserva arquivos e vínculos. Excluir um relato também remove seus anexos após commit. Falhas de remoção de arquivo são registradas sem conteúdo ou nome original e precisam de intervenção operacional; não há fila automática de recuperação.

A retenção de 60/14 dias, cinco estados, idempotência, limites por navegador e demais funcionalidades completas continuam nas etapas próprias do plano. Não aplicar retenção completa retroativamente aos registros do ciclo fácil.

## Verificação

`python manage.py test chamados.test_fotos` cobre formatos reais, metadados e orientação, quantidade, limites decimais, envio HTML/API, CSRF, autorização, armazenamento privado, erros de gravação, rollback e descarte. Os testes usam pasta temporária e PostgreSQL, sem criar fotos no armazenamento persistente.
