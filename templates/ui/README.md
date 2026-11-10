# Componentes de interface

Catálogo de desenvolvimento: `/_ui/` (somente DEBUG). Includes usam valores escapados e, preferencialmente, `only`. A view fornece dados e destinos já autorizados; componentes não implementam permissões, retenção ou transições. Não passar URLs provenientes diretamente de entradas do usuário.

## Componentes adicionados

| Include/tag | Propriedades | Comportamento |
| --- | --- | --- |
| `tag_selector.html` | `field` (BoundField de MultipleChoiceField com CheckboxSelectMultiple), `minimum=1`, `maximum=3` | Fieldset, erros, escolhas preservadas, contador e limite local. IDs vêm do prefixo do formulário. |
| `photo_input.html` | `field` (FileField com FileInput), `max_bytes=10485760` | Seleção nativa, prévia PNG/JPEG, indicação HEIC, remoção e validação local de tamanho/extensão. Configure `accept` e ajuda no widget/campo. |
| `photo_list.html` | `photos`: lista de `{label, url, thumbnail?, caption?}`, `empty_text` | Miniatura/link, indisponibilidade sem imagem quebrada e estado vazio. URLs de fotos reais devem exigir autorização também no servidor. |
| `filter_bar.html` | `form`, `action`, `clear_url`, `label`, `submit_label`, `clear_label`, `preserved` (dicionário opcional) | Formulário GET com campos existentes; limpar usa URL fornecida. Não aninhar em outro form. |
| `ui_pagination` | `page`, `query` (QueryDict), `parameter='page'`, `label` | Tag que inclui `pagination.html`; preserva filtros multivalorados, limites e página atual. Não renderiza em página única. |
| `metric_card.html` | `label`, `value`, `unit`, `detail`, `icon` | Valor zero é preservado; `None` significa indisponível. Não calcula indicadores. |
| `metadata.html` | `items`: lista de `{label, value}` | Lista de definições responsiva; `None` indica dado não registrado no legado. |
| `navigation.html` | `items`: lista de `{key, label, url, icon?}`, `active`, `label` | Links com seção atual, quebra de linha e nomes acessíveis. |

Exemplos:

```django
{% load ui %}
{% include 'ui/tag_selector.html' with field=form.tags minimum=1 maximum=3 only %}
{% include 'ui/photo_input.html' with field=form.foto only %}
{% ui_pagination page request.GET %}
```

O formulário que envia arquivos precisa de `method="post"`, `enctype="multipart/form-data"` e CSRF. A validação local é uma melhoria: o backend deve validar quantidade de tags, conteúdo real das imagens, dimensões, tamanho total e autorização. O componente não envia arquivos, não converte HEIC e não remove metadados. URLs locais de prévia são liberadas ao trocar/remover a seleção ou sair da página. Não armazena conteúdo em localStorage.

## Componentes ampliados e reutilizados

- `badge.html`: variantes `info`, `warning`, `danger`, além de neutro, `success` e `count`. Sempre informar rótulo textual.
- `report_card.html`: propriedades opcionais `state`, `state_kind`, `tags` (lista de textos), `priority`, `priority_kind`, `assignee`, `detail_url`, `legacy`; mantém parâmetros anteriores e comportamento de seleção. `readonly=True` omite seleção quando não há `can_resolve`. `problem` também pode receber o título do chamado.
- `equipment_card.html`: categoria opcional por `category`; versão compacta quebra em coluna no celular.
- `selection_bar.html`: `label` e `help_text` opcionais; seleção parcial/contagem reaproveitam o JS existente.
- `header.html`: `navigation_items` opcionais dentro do header interno; sem essa propriedade preserva navegação atual. A view deve filtrar os links por autorização. O fluxo público ignora essa lista.
- `table.html`: região rolável com nome e foco por teclado. O mesmo componente serve para histórico, restrições e conferência; não há tabelas concorrentes para cada domínio.
- `field`, `input`, `button`, `alert`, `error_summary`, `empty_state`, `page_heading`, ícones e footer continuam sendo a base. Notas e motivos são textareas existentes; prioridade/responsável/estado são selects existentes. Retenção e exclusão usam alertas existentes.

## Consistência visual

Mantidos logo SVG real, Segoe UI/system-ui, verde `--qr-green`, menta `--qr-mint`, fundo `--qr-bg`, borda `--qr-border`, raio e sombra existentes. Sem gradientes ou novas versões da marca dos protótipos. Estados usam as cores semânticas dos alertas existentes. Botões mantêm altura mínima de 44 px; campos, 48 px. Espaçamento de 8/12/16/20/24 px e layouts com quebra substituem larguras rígidas dos protótipos. O catálogo não exige largura desktop; tabelas extensas rolam dentro de uma região própria.

As demonstrações usam fixtures independentes do banco. Filtros e paginação são GET; a demonstração de tags/foto valida no navegador e não salva dados. Nenhuma tela completa ou rota de atendimento da evolução foi implementada nesta etapa.
