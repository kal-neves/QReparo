# Telas e fluxo do MVP completo

Referências: [MVP](MVP.txt), [arquitetura](ARQUITETURA.md) e etapas 11 a 24 da [ordem de desenvolvimento](../ORDEM_DE_DESENVOLVIMENTO.md). A primeira entrega segue as [telas fáceis](../MVPfacil/TELAS_E_FLUXO.md).

## Ferramentas

Django e Python para regras e páginas; Django Templates e Bootstrap para interface responsiva; PostgreSQL para dados e transações; autenticação e grupos do Django para os perfis internos; Django Admin para cadastros autorizados; qrcode para etiquetas; Pillow e pillow-heif para fotos. Indicadores usam consultas do Django e tabelas HTML. JavaScript atende pequenas interações. Não há necessidade de API REST, Node, Redis ou Celery no MVP.

## Perfis

| Perfil | Função |
| --- | --- |
| Solicitante sem conta | Identificar equipamento e enviar relato; receber confirmação simples. Sem consulta ou acompanhamento posterior. |
| Técnico | Atender chamados, consultar fotos e histórico, cadastrar equipamentos, gerar etiquetas, consultar indicadores e revisar restrições. |
| Administrador | Gerenciar contas, permissões, laboratórios, locais e tags; cadastrar equipamentos e gerar etiquetas. Chamados, fotos e autoria exigem também perfil técnico; indicadores exigem técnico ou gestor. |
| Gestor | Apenas indicadores agregados, sem relatos, fotos ou autoria. |

Os perfis internos têm funções distintas. Ser técnico não dá autorização para criar contas ou alterar permissões. Perfis podem ser acumulados. Não haverá recuperação de acesso. A primeira conta administrativa será criada por comando do Django.

## Telas públicas

1. **Identificar equipamento:** entrada manual do código impresso quando não for possível ler o QR Code. Mostrar somente identificação e localização básicas.
2. **Equipamento e relato:** QR Code abre diretamente este formulário, com equipamento e laboratório preenchidos. Exigir título de até 35 caracteres, descrição de até 250 caracteres e de 1 a 3 tags predefinidas. Fotos são opcionais. Equipamento desativado não aceita relato.
3. **Confirmação de recebimento:** informar que o envio foi recebido. Não oferecer link, token, lista de chamados ou acompanhamento do estado.

Não coletar contato opcional nem gravidade percebida. Não mostrar relatos semelhantes nem oferecer “Também fui afetado”. Não existe tela de acompanhamento, confirmação de solução ou reabertura pelo solicitante.

## Telas internas

1. **Entrada:** autenticação dos técnicos, administradores e gestores; acesso conforme permissões no servidor.
2. **Painel e chamados:** listagem paginada, filtros por estado, laboratório, equipamento, tags e responsável; agrupamento interno por equipamento. Acesso à lista é restrito por permissão, não apenas por autenticação.
3. **Detalhes e atendimento:** título, descrição, tags, fotos privadas, prioridade, responsável e histórico; notas e soluções são internas.
4. **Resolver selecionados:** conferir chamados do mesmo equipamento e informar solução. Se algum mudar antes da confirmação, interromper todo o lote, identificar o alterado e pedir nova conferência.
5. **Equipamentos:** busca por patrimônio, código e localização; detalhes, etiqueta, QR Code e histórico restrito. Substituir QR Code invalida o identificador anterior.
6. **Cadastros:** laboratórios, locais e tags pelo administrador; equipamentos e etiquetas pelo técnico ou administrador. Somente administrador gerencia contas e permissões no Django Admin.
7. **Restrições:** técnico consulta prazo e justificativa mínima, aplica duração de 1 a 168 horas inteiras ou remove restrição antecipadamente. Não consulta relato malicioso já excluído.
8. **Indicadores:** quantidade de relatos, tempo até primeiro atendimento e tempo total até resolução. Não exigir mapa de incidência nem indicador adicional de recorrência.

## Registrar um problema

1. Ler QR Code ou informar código manual; validar equipamento ativo e conferir localização.
2. Criar ou reutilizar cookie aleatório de navegador. Seu conteúdo não identifica a pessoa. Sem cookies, impedir envio e orientar sua ativação.
3. Preencher título, descrição, tags e até duas fotos.
4. Verificar a chave de reenvio antes de consumir limites. Durante 24 horas, repetição idêntica retorna a confirmação original; conteúdo diferente exige novo envio com outra chave. Chave vencida ou vinculada a chamado excluído informa que a tentativa expirou.
5. Validar campos, imagens e limites; preservar campos quando possível em caso de erro.
6. Processar as fotos e criar o chamado Aberto com prioridade Média em transação, sem fundir relatos semelhantes.
7. Mostrar confirmação simples, sem acesso ao chamado.

Relato independente recebe outra chave. Repetir a mesma solicitação válida não consome limites nem cria novo chamado. Falha que retorna após resolução gera novo relato; o solicitante não reabre o anterior.

## Limites e fotos

- Até 3 envios aceitos por navegador e 5 por equipamento, em janela fixa de 15 minutos. O terceiro envio do navegador inicia bloqueio de 15 minutos; o quinto envio do equipamento também inicia bloqueio de 15 minutos. As janelas são alinhadas ao relógio (10:00-10:15, por exemplo); mudar de janela não encerra bloqueio vigente.
- Tentativas recusadas não renovam o bloqueio. Restrição do equipamento afeta todos os navegadores; a do navegador afeta seus novos relatos.
- Mensagem: “Muitos envios em pouco tempo. Tente novamente em alguns minutos.” Não mostrar horário de liberação ou contagem regressiva.
- Cookie de 30 dias e registros auxiliares por até 30 dias, eliminados antes quando desnecessários. Chave de reenvio vale apenas 24 horas.
- Cookie é solução temporária do piloto; matrícula e senha são possibilidade futura, fora do MVP. Não usar IP como único critério de restrição nem ausência de cookie como prova de abuso.
- Até duas fotos PNG, JPG/JPEG ou HEIC, até 10 MB cada antes da compressão e 25 MB para a requisição completa. MB significa 1.000.000 bytes; a folga total não aumenta o limite por foto.
- Sem limite de dimensões como regra do produto. Validar conteúdo, remover metadados e armazenar em WebP estático, usando imagem principal/primeiro quadro quando houver vários. Buscar aproximadamente 1 MB por foto, priorizando clareza; não é teto rígido de saída. Falhas de processamento devem gerar mensagem compreensível.
- Fotos ficam em armazenamento privado, disponíveis apenas a perfis internos com permissão. Não aceitar vídeos, PDFs ou outros tipos de arquivo.

## Triagem, atendimento e encerramento

O técnico confere relato, fotos e demais registros do equipamento; ajusta tags, prioridade e responsável. Prioridades: Baixa, Média, Alta e Crítica. Tags iniciais: `não liga`, `sem internet`, `lentidão`, `periférico`, `software`, `monitor`, `teclado/mouse`, `áudio`, `impressora`, `outro`. Exigir de 1 a 3 tags; prioridade inicial Média.

| Estado | Significado e exigência |
| --- | --- |
| Aberto | Registrado e aguardando triagem ou atendimento. |
| Em atendimento | Equipe trabalhando no problema. |
| Pendente | Atendimento interrompido; exige motivo. |
| Resolvido | Exige solução registrada pelo técnico. |
| Cancelado | Encerrado por invalidade ou abuso; exige justificativa. |

Todas as transições entre estados são permitidas para técnicos autorizados, respeitando os campos obrigatórios e vedando reativação após remoção de conteúdo pela retenção. Pode resolver diretamente Aberto ou Pendente e desfazer encerramento incorreto. Isso não substitui um novo relato quando a falha realmente retorna. Ao desfazer encerramento, suspender a retenção; novo encerramento inicia novo prazo. Registros já reduzidos pela retenção não são reativados: registrar novo chamado.

Toda mudança registra autor, data, horário e valores anteriores e novos, sem edição do histórico pela interface comum. A autoria deve permanecer; textos livres seguem a retenção. Não há informações destinadas ao acompanhamento do solicitante.

Na resolução individual ou em lote, registrar solução e data. Lote exige mesmo equipamento, permissão e versões inalteradas desde a conferência, validadas dentro da transação. Se algum selecionado mudou, não resolver nenhum e mostrar qual precisa ser conferido novamente. Somente os selecionados são alterados; não há fusão nem compartilhamento de links.

## Abuso e revisão

Semelhança, relato curto ou incompleto não comprovam abuso. Cancelamento por invalidade mantém o prazo normal de 14 dias. Abuso confirmado exige exclusão imediata e integral do chamado malicioso, fotos, textos e histórico vinculado, inclusive autoria.

O técnico pode aplicar restrição opcional ao navegador, de 1 a 168 horas inteiras, e removê-la antecipadamente. A restrição permanece mesmo após exclusão do chamado; manter somente navegador, prazo, técnico responsável e justificativa breve, sem cópia do relato. Descartar esses dados em até 30 dias, ou antes quando desnecessários.

## Retenção e indicadores

Após 60 dias da resolução ou 14 dias do cancelamento sem abuso, remover fotos, textos livres e vínculos pessoais, exceto autoria das alterações. Preservar equipamento, laboratório no envio, tags, datas, estado final e autoria estruturada. Aplicar a remoção de textos também à auditoria. Como a autoria permanece identificável, o histórico não é totalmente anônimo.

Não há prazo definido para chamados Abertos, Em atendimento, Pendentes nem para o histórico preservado. Executar exclusão básica automaticamente todos os dias para prazos vencidos. Abuso confirmado é excluído imediatamente. Não implementar recuperação avançada ou filas de novas tentativas; registrar falhas sem dados pessoais.

Indicadores mostram quantidade de relatos, tempo até primeiro atendimento e tempo total até resolução, sem contar cancelamentos como demanda válida nem confundir relatos com defeitos distintos. Preservar as datas necessárias. O primeiro atendimento é a primeira entrada em Em atendimento ou a resolução direta, o que ocorrer primeiro. Tempo até primeiro atendimento = essa data menos a abertura. Tempo total até resolução = data da resolução vigente menos a abertura, incluindo pendências. Sem primeiro atendimento ou resolução, o respectivo tempo fica sem valor, não zero. Ao desfazer encerramento, manter a primeira data de atendimento, suspender a retenção e retirar a resolução desfeita do cálculo atual. Novo encerramento inicia novo prazo (60 dias se resolvido; 14 dias se cancelado sem abuso); nova resolução atualiza o tempo total. Registros cujo conteúdo já foi removido pela retenção não podem ser reativados: registrar novo chamado.
