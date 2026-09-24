# Arquitetura do MVP fácil

Referências: [MVP](MVP.txt), [telas e fluxo](TELAS_E_FLUXO.md) e etapas 1 a 10 da [ordem de desenvolvimento](../ORDEM_DE_DESENVOLVIMENTO.md).

Uma aplicação Django com páginas renderizadas no servidor e PostgreSQL. Reutilizar os módulos `equipamentos` e `chamados`; usar Django Templates, Bootstrap, autenticação do Django, Django Admin e qrcode. Não é necessário criar API REST, aplicação de interface separada ou processamento em segundo plano.

```text
Aluno -> QR Code -> Formulário -> Confirmação
                         |
                         v
                    PostgreSQL
                         ^
                         |
Técnico -> Login -> Equipamentos com relatos -> Resolver selecionados
                                                   |
                                                   v
                                      Apagar texto e manter contagem
```

## Estrutura planejada

Esta árvore descreve responsabilidades; não exige criar todos os arquivos antes do primeiro fluxo funcional. Dependências já instaladas para a versão completa podem permanecer, sem antecipar suas funcionalidades.

```text
QReparo/
├── README.md                    - Instalação e execução da entrega atual.
├── instalar.py                  - Preparação do ambiente Python existente.
├── requirements.txt             - Dependências instaladas com pip.
├── pyproject.toml               - Dependências diretas e versão do Python.
├── .env.example                 - Exemplo da configuração local.
├── manage.py                    - Comandos do Django.
├── instrucoes/                  - Ordem comum e documentos dos dois MVPs.
├── config/
│   ├── settings.py              - Banco, módulos, templates e segurança.
│   ├── urls.py                  - Rotas principais, autenticação e Admin.
│   ├── wsgi.py                  - Entrada do servidor.
│   └── asgi.py                  - Entrada convencional do Django.
├── equipamentos/
│   ├── models.py                - Laboratorio, Local e Equipamento.
│   ├── admin.py                 - Cadastros preparados pela equipe.
│   ├── views.py                 - Etiqueta para impressão.
│   ├── urls.py                  - Rotas das etiquetas.
│   ├── servicos.py              - Geração do QR Code.
│   ├── migrations/              - Evolução do banco.
│   └── tests.py                 - Identificação, atividade e etiqueta.
├── chamados/
│   ├── models.py                - Tag e Chamado mínimo.
│   ├── admin.py                 - Lista de problemas; proteger relatos de edição direta.
│   ├── forms.py                 - Problema, descrição e seleção para resolver.
│   ├── views.py                 - Envio, confirmação, painel e resolução.
│   ├── urls.py                  - Rotas públicas e internas.
│   ├── permissoes.py            - Verificação de acesso técnico.
│   ├── servicos.py              - Criar relato e resolver apagando o texto.
│   ├── consultas.py             - Equipamentos ativos no painel e contagem técnica.
│   ├── migrations/              - Evolução do banco.
│   └── tests.py                 - Campos, acesso, lote e descarte imediato.
├── templates/
│   ├── base.html                - Navegação e mensagens comuns.
│   ├── registration/login.html  - Entrada dos técnicos.
│   ├── equipamentos/etiqueta.html - Etiqueta imprimível.
│   └── chamados/
│       ├── novo.html            - Equipamento, problema e descrição.
│       ├── confirmacao.html     - Confirmação simples de envio.
│       ├── painel.html          - Equipamentos com relatos Abertos.
│       ├── detalhe.html         - Relatos ativos do equipamento selecionado.
│       ├── resolver.html        - Conferência dos selecionados.
│       └── contagem.html        - Quantidades por equipamento e problema.
└── static/
    ├── vendor/                 - Bootstrap.
    └── css/app.css             - Ajustes de tela e impressão.
```

Pacotes Python recebem `__init__.py`; manter também os arquivos convencionais gerados pelo Django, como `apps.py`. A árvore é resumida, não uma instrução para excluir arquivos existentes.

## Dados mínimos

| Modelo | Campos e finalidade |
| --- | --- |
| Laboratorio | Identificação única e nome. |
| Local | Sala ou posição dentro do laboratório. |
| Equipamento | Identificação única, descrição, local, situação ativa e identificador aleatório do QR Code. |
| Tag | Problema predefinido, incluindo “Outro problema”. |
| Chamado | Equipamento, laboratório no envio, uma tag, descrição de até 250 caracteres, Aberto/Resolvido, datas de abertura/resolução e indicação de conteúdo removido. |
| User | Conta técnica do Django para autenticação, sem vínculo de autoria no chamado fácil. |

A relação de tags pode ser preparada para várias no banco, mas o formulário e o serviço exigem exatamente uma nesta fase. Registrar laboratório no envio evita alterar contagens históricas quando o equipamento muda de local.

Não adicionar modelos de foto, restrição, controle persistente de navegador ou auditoria de atendimento para completar esta entrega. O aluno não possui conta nem identificação vinculada ao chamado.

## Responsabilidades e regras

- **Views:** recebem a requisição, verificam acesso e escolhem a resposta.
- **Formulários:** validam um problema selecionado e descrição obrigatória somente para “Outro problema”; limite de 250 caracteres.
- **Serviços:** criam relato Aberto para equipamento ativo e resolvem os selecionados com transação. Não confiar no equipamento/laboratório enviados pelo navegador.
- **Consultas:** listam equipamentos com ao menos um chamado Aberto, seus relatos ativos e as contagens técnicas preservadas.
- **Permissões:** todas as consultas e ações internas exigem autorização técnica. Autenticação e CSRF são recursos do Django; não equivalem a identificar o aluno.

Ao resolver, bloquear/revalidar os selecionados no PostgreSQL: todos devem pertencer ao mesmo equipamento e continuar Abertos. Se algum não atender à condição, abortar o lote inteiro e solicitar nova conferência. Caso contrário, gravar Resolvido, data e indicação de conteúdo removido e esvaziar descrição na mesma transação. Somente os selecionados mudam.

Conservar apenas o registro mínimo por relato, suficiente para contar equipamento, laboratório, problema, datas e estado final. Não duplicar textos em histórico ou logs. Não usar edição direta de chamados pelo Admin para contornar descarte ou gerar auditoria com conteúdo pessoal. O Admin prepara contas e cadastros; a resolução passa pelo serviço próprio.

Não há pasta de fotos privadas ou comando diário de retenção necessários nesta fase: o descarte acontece no encerramento. Equipamentos com histórico são desativados; registros resolvidos e já reduzidos não são reativados.

## Verificação e evolução

Verificar identificação correta pelo QR Code, campos, equipamento inativo, bloqueio de acesso anônimo, concorrência na resolução, seleção parcial, remoção do texto e contagens após encerramento. Usar PostgreSQL nos testes de transação. Testar o formulário no celular e o fluxo interno por teclado.

A partir da etapa 11, seguir a [arquitetura completa](../MVPcompleto/ARQUITETURA.md) e as [telas completas](../MVPcompleto/TELAS_E_FLUXO.md). Evoluir por migrações, distinguindo registros fáceis dos novos: manter descarte imediato nos antigos, não reconstruir texto/autoria apagados e aplicar a retenção completa aos novos chamados. A fase fácil deve permanecer demonstrável antes dessa evolução.
