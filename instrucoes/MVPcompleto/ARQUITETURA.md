# Arquitetura do MVP completo

Referências: [MVP](MVP.txt), [telas e fluxo](TELAS_E_FLUXO.md) e etapas 11 a 24 da [ordem de desenvolvimento](../ORDEM_DE_DESENVOLVIMENTO.md). A primeira entrega segue a [arquitetura fácil](../MVPfacil/ARQUITETURA.md).

## Arquivos e pastas planejados

```text
QReparo/
├── README.md                  — Configuração, execução, testes e implantação.
├── instrucoes/                — Ordem comum e documentos de MVPfacil/ e MVPcompleto/.
├── guidelines/                — Fontes e decisões de referência do projeto.
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
