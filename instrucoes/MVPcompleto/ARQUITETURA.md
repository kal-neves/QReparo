# Arquitetura do MVP completo

Referências: [MVP](MVP.txt), [telas e fluxo](TELAS_E_FLUXO.md) e etapas 11 a 24 da [ordem de desenvolvimento](../ORDEM_DE_DESENVOLVIMENTO.md). A primeira entrega segue a [arquitetura fácil](../MVPfacil/ARQUITETURA.md). O piloto será simulado.

As regras completas se aplicam aos novos relatos desta fase. Registros da fase fácil mantêm descarte imediato e histórico mínimo, sem reconstrução de textos ou autoria removidos. Seguir a transição definida na etapa 11 do plano principal.

Uma aplicação Django com páginas renderizadas no servidor, PostgreSQL e armazenamento privado de fotos. Os módulos `equipamentos` e `chamados` fazem parte da mesma aplicação.

A árvore abaixo apresenta a estrutura completa planejada; parte dos arquivos ainda será criada.

## Funcionamento geral

```text
Celular ou computador
          |
          v
Django: páginas, requisições e regras de negócio
          |                         |
          v                         v
     PostgreSQL              Fotos privadas

Comando diário --> exclusão de conteúdo vencido
```

Usar Django Templates e Bootstrap nas telas, autenticação do Django para técnicos, administradores e gestores e Django Admin para cadastros. A biblioteca qrcode gera etiquetas; Pillow processa fotos, com pillow-heif para HEIC. JavaScript atende a pequenas interações dos formulários.

O piloto precisa de uma aplicação, um banco e uma pasta privada persistente para fotos. A retenção básica é automática, por comando executado diariamente. Não é necessário adicionar uma interface separada, API REST, Redis, Celery ou microsserviços neste escopo.

## Arquivos e pastas planejados

As descrições abaixo são documentação, não comentários a inserir no código.

```text
QReparo/
├── README.md                  — Configuração, execução, testes e implantação.
├── instrucoes/                — Plano comum e documentos de MVPfacil/ e MVPcompleto/.
├── pyproject.toml             — Requisitos do Python e dependências diretas.
├── uv.lock                    — Arquivo opcional para colaboradores que usam uv.
├── requirements.txt           — Dependências com versões fixadas para instalação com pip.
├── .python-version            — Versão do Python usada pela equipe.
├── .gitignore                 — Exclusões de segredos, ambientes e arquivos locais.
├── .env.example               — Modelo das variáveis de ambiente.
├── manage.py                  — Comandos de execução, migração, testes e limpeza.
├── config/                    — Configurações gerais e pontos de entrada.
│   ├── __init__.py            — Identifica o pacote Python.
│   ├── settings.py            — Banco, módulos, segurança, limites e retenção.
│   ├── urls.py                — Rotas principais, autenticação e Admin.
│   ├── wsgi.py                — Entrada para o servidor WSGI de produção.
│   └── asgi.py                — Entrada convencional para servidores ASGI.
├── equipamentos/              — Laboratórios, locais, equipamentos e etiquetas.
│   ├── __init__.py            — Identifica o pacote Python.
│   ├── apps.py                — Registra o módulo no Django.
│   ├── models.py              — Modelos Laboratorio, Local e Equipamento.
│   ├── admin.py               — Cadastros e substituição do QR Code.
│   ├── forms.py               — Validação da busca pelo código da etiqueta.
│   ├── views.py               — Busca, páginas dos técnicos e download de etiquetas.
│   ├── urls.py                — Rotas de busca, listagem, detalhes e etiquetas.
│   ├── servicos.py            — Geração de etiquetas e substituição de identificadores.
│   ├── migrations/            — Alterações versionadas do banco.
│   └── tests.py               — Testes de identificação, busca, QR Code e acesso.
├── chamados/                  — Registro, atendimento e retenção.
│   ├── __init__.py            — Identifica o pacote Python.
│   ├── apps.py                — Registra o módulo no Django.
│   ├── models.py              — Chamados, tags, fotos, atualizações e controle de envio.
│   ├── admin.py               — Tags e revisão de restrições temporárias.
│   ├── forms.py               — Formulários de relato, triagem e atendimento.
│   ├── views.py               — Abertura, confirmação e telas internas.
│   ├── urls.py                — Rotas de chamados, fotos e ações técnicas.
│   ├── permissoes.py          — Verificação das permissões de cada perfil.
│   ├── servicos.py            — Criação, mudanças de estado e resolução.
│   ├── consultas.py           — Filtros, histórico por equipamento e indicadores.
│   ├── imagens.py             — Validação, remoção de metadados e compressão.
│   ├── limites.py             — Limites por navegador/equipamento e restrições.
│   ├── retencao.py            — Regras de retenção e exclusão básica.
│   ├── migrations/            — Alterações versionadas do banco deste módulo.
│   ├── management/            — Pacote dos comandos personalizados do Django.
│   │   └── commands/          — Comandos disponíveis pelo manage.py.
│   │       └── limpar_expirados.py — Comando diário de retenção.
│   └── tests/                 — Testes organizados por comportamento.
│       ├── test_acesso.py     — Permissões por perfil e fotos privadas.
│       ├── test_envio.py      — Campos, limites, imagens e reenvios.
│       ├── test_fluxo.py      — Estados, histórico e resolução em lote com transação.
│       └── test_retencao.py   — Prazos e preservação da autoria.
├── templates/                 — Páginas HTML renderizadas no servidor.
│   ├── base.html              — Estrutura comum, navegação, mensagens e estilos.
│   ├── registration/          — Pasta convencional da autenticação do Django.
│   │   └── login.html         — Entrada dos perfis internos.
│   ├── equipamentos/          — Telas relacionadas aos equipamentos.
│   │   ├── busca.html         — Entrada manual do código da etiqueta.
│   │   ├── lista.html         — Busca e listagem para técnicos.
│   │   ├── detalhe.html       — Dados, etiqueta e histórico restrito.
│   │   └── etiqueta.html      — Etiqueta para impressão com QR Code e código manual.
│   └── chamados/              — Telas de registro e atendimento.
│       ├── novo.html          — Equipamento, relato e fotos opcionais.
│       ├── confirmacao.html   — Confirmação simples de recebimento.
│       ├── painel.html        — Contadores, filtros e lista dos técnicos.
│       ├── detalhe.html       — Triagem, atribuição, notas e mudanças de estado.
│       └── resolver.html      — Conferência dos selecionados e confirmação da solução.
├── static/                    — Arquivos públicos da interface, sem fotos dos usuários.
│   ├── vendor/                — Arquivos CSS e JavaScript do Bootstrap.
│   ├── css/app.css            — Ajustes visuais e estilos para impressão.
│   └── js/app.js              — Pequenas interações dos formulários.
└── midia_privada/             — Fotos persistentes, fora do Git e sem acesso público direto.
```

Os pacotes `migrations/`, `management/`, `commands/` e `tests/` também recebem um `__init__.py` vazio. O Django gera migrações numeradas conforme os modelos evoluem. O arquivo inicial `chamados/tests.py` será substituído pelo pacote `chamados/tests/` quando os testes forem separados.

Usar `manage.py` para os comandos do Django e manter `.venv/` local. Verificar a conexão com PostgreSQL e as migrações na etapa 1 da [ordem de desenvolvimento](../ORDEM_DE_DESENVOLVIMENTO.md); a etapa 11 prepara a transição de dados para esta fase. O python-dotenv carrega o `.env`, respeitando as variáveis já fornecidas pelo ambiente.

## Dados armazenados

| Modelo | Finalidade |
| --- | --- |
| Laboratorio | Nome e identificação única do laboratório. |
| Local | Sala ou posição do equipamento dentro de um laboratório. |
| Equipamento | ID estável, código único da etiqueta, patrimônio opcional único, categoria, local, situação ativa e identificador aleatório substituível do QR Code. |
| User e grupos do Django | Contas internas e perfis acumuláveis de técnico, administrador e gestor. |
| Tag | Categoria predefinida de problema. |
| Chamado | Equipamento, laboratório no envio, título, descrição, tags, estado, prioridade, responsável e datas de abertura, primeiro atendimento e encerramentos. Sem credencial de acompanhamento. |
| Atualizacao | Autor, data, horário, campos alterados, valores anteriores e novos e nota interna. A autoria permanece após a retenção normal; abuso confirmado exclui o histórico inteiro. Textos livres são removidos. |
| Foto | Imagem processada e privada; no máximo duas por chamado. |
| Envio | Chave de reenvio, validade, referência temporária ao navegador/equipamento e informação para comparar o conteúdo da solicitação. |
| Restricao | Bloqueio temporário, início, fim, justificativa mínima e decisões de revisão, sem cópia de relato excluído. |

Os modelos de `chamados` dependem de `equipamentos`. A tela de equipamento pode consultar `chamados.consultas` para mostrar o histórico. Registrar o laboratório no envio evita alterar indicadores antigos quando o equipamento muda de lugar. Equipamentos com histórico devem ser desativados em vez de excluídos; equipamentos desativados não aceitam novos relatos.

## Acesso e perfis

- **Solicitante:** registra um problema sem conta e recebe apenas confirmação de recebimento. Não consulta lista, histórico, estado, fotos ou solução de chamados. Não há acompanhamento, token de consulta, contato opcional nem gravidade percebida.

| Perfil | Permissões |
| --- | --- |
| Técnico | Atender chamados, consultar fotos e histórico, cadastrar equipamentos, gerar etiquetas, aplicar e revisar restrições; consultar indicadores. |
| Administrador | Gerenciar contas, permissões, laboratórios, locais e tags; cadastrar equipamentos e gerar etiquetas. Para acessar chamados, fotos e autoria, deve acumular o perfil técnico; para indicadores, o perfil técnico ou gestor. |
| Gestor | Consultar apenas indicadores agregados, sem acesso a relatos, fotos ou autoria. |

Perfis podem ser acumulados. Somente administrador cria contas e altera permissões. A primeira conta administrativa é criada por comando do Django; não haverá fluxo de recuperação de acesso.

Usar grupos e permissões do Django, com validação no servidor. Administrador de negócio não deve receber automaticamente permissões irrestritas de superusuário. Não liberar ações apenas por estar autenticado ou ter acesso ao Admin. Fotos ficam fora dos arquivos públicos, acessíveis somente por rotas internas autorizadas. O QR Code identifica o equipamento e abre seu formulário, sem liberar chamados. Usar `no-store` e `no-referrer` em páginas sensíveis.

## Organização das regras

As views recebem requisições e escolhem respostas; formulários validam dados; serviços aplicam regras e gravam pelos modelos; consultas reúnem leituras compartilhadas. O Admin deve respeitar as mesmas regras de negócio.

### Abertura e reenvios

Exigir título de até 35 caracteres, descrição de até 250 caracteres e de 1 a 3 tags predefinidas. Fotos são opcionais. Todo chamado novo entra como Aberto, com prioridade Média. Não fundir relatos nem oferecer “Também fui afetado”; semelhança não é motivo de rejeição ou cancelamento.

Cada solicitação recebe chave aleatória vinculada ao navegador ou sessão, com unicidade no banco e validade de 24 horas. Dentro da validade, repetição idêntica retorna a confirmação original sem consumir limites; conteúdo diferente exige novo envio com outra chave. Chave vencida ou associada a chamado excluído informa que a tentativa expirou. A confirmação não permite consultar o chamado. Verificar reenvios antes de consumir limites e usar transações contra envios simultâneos. O prazo de validade da chave é distinto do prazo máximo de armazenamento dos registros auxiliares.

### Limites e restrições

| Regra | Definição |
| --- | --- |
| Navegador | Até 3 chamados aceitos por janela fixa de 15 minutos. O terceiro envio é aceito e inicia bloqueio de 15 minutos para novos envios. |
| Equipamento | Até 5 chamados aceitos por janela fixa de 15 minutos, somando navegadores. O quinto envio é aceito e inicia bloqueio de 15 minutos no equipamento. |
| Tentativas recusadas | Não renovam o prazo do bloqueio. |
| Mensagem | “Muitos envios em pouco tempo. Tente novamente em alguns minutos.” Sem horário de liberação ou tempo restante; preservar campos quando possível. |
| Abuso confirmado | Exclusão integral do chamado malicioso. Restrição do navegador é opcional, de 1 a 168 horas inteiras escolhidas pelo técnico, com remoção antecipada. Excluir também o histórico e sua autoria; preservar apenas os dados mínimos de eventual restrição. |
| Cookie | Identificador aleatório de navegador com duração de 30 dias, sem dados pessoais no conteúdo. |
| Registros auxiliares | Excluir em até 30 dias, ou antes quando desnecessários. |

A restrição do equipamento afeta todos os navegadores; a do navegador afeta seus novos chamados. O cookie identifica navegador, não pessoa; apagar cookies ou trocar de navegador pode gerar outro identificador. A solução é temporária para o piloto simulado. Identificação por matrícula e senha é uma possibilidade futura, fora do MVP. Não usar IP como único critério nem tratar ausência de cookie como abuso. Sem cookies, impedir o envio e orientar sua ativação.

Janelas fixas alinhadas ao relógio em intervalos de 15 minutos, como 10:00-10:15. A virada da janela não encerra bloqueio ainda vigente.

A exclusão do chamado malicioso não elimina uma restrição ainda vigente. Manter apenas identificador do navegador, prazo, técnico responsável e justificativa breve, sem copiar o relato. Revisar a restrição por esses dados mínimos. Texto curto ou incompleto, isoladamente, não comprova abuso.

### Fotos

Aceitar PNG, JPG/JPEG e HEIC, no máximo duas fotos, até 10.000.000 bytes por foto antes da compressão. O envio completo, incluindo campos e estrutura da requisição, não pode ultrapassar 25.000.000 bytes. Os 5 MB adicionais não aumentam o limite por foto.

Não definir limite de dimensões como regra do produto. Validar conteúdo decodificado, quantidade e bytes; tratar falhas de processamento e preservar os outros campos quando possível. Reprocessar, remover metadados e salvar em armazenamento privado; remover arquivos de envios incompletos.

**Escolha técnica autorizada:** armazenar em WebP estático, com Pillow e pillow-heif para leitura de HEIC. Ajustar compressão priorizando legibilidade, buscando aproximadamente 1.000.000 bytes por foto, sem teto rígido de saída. Para imagens com vários quadros, usar a imagem principal ou o primeiro quadro; não armazenar animações. Evitar redução de resolução que torne detalhes ilegíveis.

### Atendimento e auditoria

Estados: Aberto, Em atendimento, Pendente, Resolvido e Cancelado. Permitir todas as transições entre estados para técnicos autorizados, exceto reativação de registros já reduzidos pela retenção. Pendente e Cancelado exigem motivo; Resolvido exige solução. É permitido resolver diretamente um chamado Aberto ou Pendente. Técnicos podem desfazer encerramento incorreto; falha que realmente retorna gera outro chamado.

Registrar autor, data, horário, campos e estados anteriores e novos; histórico não editável pela interface comum. Toda anotação de atendimento é interna, sem mensagens destinadas ao solicitante.

Na resolução em lote, conferir os selecionados do mesmo equipamento e revalidar permissão, equipamento e versão de cada chamado dentro de uma transação. Se qualquer selecionado tiver sido alterado desde a conferência, não resolver nenhum: mostrar qual mudou e exigir nova conferência. Alterar somente os selecionados, sem fusão ou compartilhamento de links.

### Retenção

- Resolvidos: após **60 dias da resolução**, remover fotos, textos livres, identificadores de navegador e vínculos pessoais, **exceto autoria das alterações**.
- Cancelados sem abuso confirmado: aplicar a mesma redução após **14 dias do cancelamento**.
- Preservar ID do equipamento, laboratório, tags, datas, estado final e registro estruturado de autoria das alterações. Remover textos livres também da auditoria do Admin. Não chamar o conjunto de totalmente anônimo enquanto houver autoria identificável.
- Abertos, Em atendimento e Pendentes: sem prazo de retenção definido. Histórico técnico e autoria preservados: sem prazo de expiração definido.
- Abuso confirmado: excluir imediatamente o chamado, fotos, textos e histórico vinculado, inclusive autoria. Se houver restrição, preservar somente os dados mínimos dela até seu descarte.

Executar a exclusão básica automaticamente uma vez por dia, processando prazos já vencidos; abuso confirmado é excluído imediatamente, sem esperar a rotina. Não implementar mecanismos avançados de recuperação nem filas de novas tentativas. Registrar falhas sem copiar conteúdo pessoal. A execução diária não permite reativar registros que já perderam textos e fotos.

### Indicadores

Mostrar quantidade de relatos, tempo até o primeiro atendimento e tempo total até a resolução. Distinguir relatos de defeitos; excluir cancelados da demanda válida. Manter datas necessárias após a retenção. O primeiro atendimento é a primeira entrada em Em atendimento ou a resolução direta, o que ocorrer primeiro. Tempo até primeiro atendimento = essa data menos a abertura. Tempo total até resolução = data da resolução vigente menos a abertura, incluindo pendências. Sem primeiro atendimento ou resolução, o respectivo tempo fica sem valor, não zero. Ao desfazer encerramento, manter a primeira data de atendimento, suspender a retenção e retirar a resolução desfeita do cálculo atual. Novo encerramento inicia novo prazo (60 dias se resolvido; 14 dias se cancelado sem abuso); nova resolução atualiza o tempo total. Registros cujo conteúdo já foi removido pela retenção não podem ser reativados: registrar novo chamado. Não exigir mapa de incidência ou cálculo adicional de recorrência no MVP.

## Classificações

Prioridades: Baixa, Média, Alta e Crítica. Tags iniciais: `não liga`, `sem internet`, `lentidão`, `periférico`, `software`, `monitor`, `teclado/mouse`, `áudio`, `impressora`, `outro`. Exigir de 1 a 3 tags e usar prioridade inicial Média. Todos esses parâmetros estão aprovados.

## Implementação e verificação

Seguir as etapas 11 a 24 da [ordem de desenvolvimento](../ORDEM_DE_DESENVOLVIMENTO.md). Os documentos descrevem o comportamento pretendido, não atestam que `config/settings.py` ou o código já o implementam.

Usar PostgreSQL nos testes de transações, limites simultâneos e resolução em lote. Verificar permissões, ausência de consulta pública, fotos privadas, campos, reenvios e estados. A equipe executará as [metas de qualidade](../README.md#metas-de-qualidade) no piloto simulado; não há necessidade de definir participantes ou autorização de implantação real para desenvolver o MVP.

Para execução, preparar banco, armazenamento privado persistente, arquivos estáticos, variáveis de ambiente e servidor apropriado. Usar HTTPS quando disponibilizado em rede. Documentar comandos, rotas e permissões no README. Integrações institucionais, autenticação de alunos e recuperação de acesso ficam fora do MVP.

## Convenções

O fluxo padrão usa `venv` e `pip`, com instalação pelo `requirements.txt`. Não exigir uv. Manter as dependências diretas de `pyproject.toml` compatíveis com esse arquivo; `uv.lock` é opcional.

Usar português brasileiro e nomes curtos em português para variáveis, funções, classes e arquivos próprios, sem acentos nos identificadores. Evitar comentários no código; manter explicações na documentação. Preservar nomes convencionais do Python, Django e ferramentas, como `manage.py`, `settings.py`, `models.py`, `views.py` e `pyproject.toml`.
