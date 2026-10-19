# Ordem de desenvolvimento

Plano: entregar primeiro o [MVP fácil](MVPfacil/MVP.txt) e, depois, evoluir para o [MVP completo](MVPcompleto/MVP.txt). Cada etapa deve terminar com algo executável e verificável. Conferir o código existente antes de recriar estruturas.

**Marco 1: etapa 10 = MVP fácil pronto para demonstração.**
**Marco 2: etapa 24 = MVP completo pronto para piloto simulado.**

## O que muda entre as entregas

| Tema | Até a etapa 10: MVP fácil | A partir da etapa 11: evolução |
| --- | --- | --- |
| Formulário | Um problema da lista; descrição opcional, obrigatória para “Outro problema”; sem título. | Título e descrição obrigatórios; de 1 a 3 tags. |
| Fotos | Não existem. | Até duas fotos privadas. |
| Atendimento | Aberto e Resolvido; painel por equipamento e resolução dos selecionados. | Triagem, prioridade, responsável, cinco estados, notas, solução e auditoria. |
| Acesso interno | Técnico; cadastros e contas preparados pela equipe no Admin. | Técnico, administrador e gestor com permissões distintas. |
| Dados do solicitante | Sem conta, contato, identificador persistente de navegador ou dados pessoais solicitados. | Cookie temporário para controle de frequência; continua sem conta ou contato. |
| Encerramento | Apaga imediatamente texto livre; conserva registro técnico mínimo sem autoria pessoal do relato. | Retenção de 60/14 dias com autoria interna preservada; abuso excluído imediatamente. |
| Indicadores | Contagem técnica por equipamento e tipo de problema. | Quantidade de relatos válidos e tempos de primeiro atendimento e resolução. |

Até a etapa 10, seguir as [telas fáceis](MVPfacil/TELAS_E_FLUXO.md) e a [arquitetura fácil](MVPfacil/ARQUITETURA.md). A partir da etapa 11, evoluir para as [telas completas](MVPcompleto/TELAS_E_FLUXO.md) e a [arquitetura completa](MVPcompleto/ARQUITETURA.md). Fotos, perfis adicionais e retenção agendada não bloqueiam o marco fácil.

Nenhuma fase inclui acompanhamento do aluno, lista pública de chamados, pesquisa de semelhantes, “Também fui afetado”, fusão de relatos, conta de aluno ou integração institucional.

## Fase 1 - Entregar o MVP fácil

### 1. Preparar o ambiente compartilhado

Seguir o README e usar `instalar.py`, `.venv`, `pip` e PostgreSQL. Configurar `.env`, executar migrações e criar a primeira conta administrativa. Reutilizar `config/`, `equipamentos/` e `chamados/`.

**Pronto quando:** outro integrante consegue instalar, conectar ao banco e abrir o Admin. `manage.py check` sozinho não comprova conexão com PostgreSQL.

### 2. Cadastrar laboratórios e equipamentos

Criar os modelos mínimos: laboratório, local e equipamento com identificação, descrição, localização e situação ativa. Cadastrar exemplos pelo Django Admin. Equipamento com histórico é desativado em vez de excluído.

**Pronto quando:** a equipe cadastra dois equipamentos e consegue distinguir suas localizações.

### 3. Gerar e conferir etiquetas

Associar um identificador aleatório ao equipamento e gerar QR Code para abrir seu formulário. Disponibilizar etiqueta para impressão. A câmera do celular faz a leitura; não construir leitor dentro da aplicação.

**Pronto quando:** escanear cada etiqueta abre o equipamento e laboratório corretos; identificador inválido ou equipamento desativado não permite envio.

### 4. Criar a lista de problemas e o registro mínimo

Usar uma classificação reutilizável, como `Tag`, e permitir selecionar exatamente um problema nesta fase, incluindo “Outro problema”. Registrar equipamento, laboratório no envio, problema, descrição de até 250 caracteres, data de abertura e estado Aberto/Resolvido. Prever data de resolução e indicação de conteúdo já removido. A relação com tags pode aceitar várias no banco, mas o formulário fácil aceita uma.

Não criar título obrigatório, fotos, responsável, prioridades ou histórico de autoria nesta fase. Não associar o relato ao aluno nem a identificador persistente de navegador.

**Pronto quando:** é possível criar um relato e consultá-lo internamente sem coletar identidade do solicitante.

### 5. Entregar o formulário do aluno

Mostrar equipamento e laboratório preenchidos pelo servidor, lista de problemas e descrição opcional; exigir descrição ao selecionar “Outro problema”. Não confiar em equipamento/laboratório alterados no formulário pelo navegador. Usar páginas Django e Bootstrap com proteção CSRF.

**Pronto quando:** o envio válido grava um relato e mostra confirmação simples. Erros preservam os campos quando possível. Orientar a não escrever dados pessoais; não registrar o conteúdo do formulário em logs.

### 6. Proteger a área técnica

Usar autenticação do Django e permissão técnica para todas as páginas e ações de atendimento. Preparar contas pela administração, sem tela de cadastro público ou recuperação de acesso. A autenticação do técnico não deve vincular relatos ao aluno.

**Pronto quando:** técnico entra e sai; visitante não acessa nem altera chamados, inclusive tentando URLs diretamente.

### 7. Construir o painel por equipamento

Listar somente equipamentos com relatos Abertos. Ao abrir um equipamento, mostrar descrição, localização e seus relatos ativos, com seleção individual e seleção de vários relatos.

**Pronto quando:** dois relatos do mesmo equipamento aparecem juntos, mas continuam registros independentes; outro equipamento aparece separado.

### 8. Resolver selecionados e eliminar o texto

Após a correção física, técnico confere e confirma os relatos selecionados do mesmo equipamento. Resolver em transação; conferir novamente permissão, equipamento e se os selecionados ainda estão ativos. Se algum mudou, interromper o lote e solicitar nova conferência.

Apagar imediatamente a descrição dos selecionados e preservar apenas o registro técnico mínimo: equipamento, laboratório, problema, datas e estado final. Não persistir texto livre ou autoria pessoal do atendimento no histórico desta fase, inclusive por auditoria do Admin. Não exigir solução escrita no fluxo fácil.

**Pronto quando:** somente selecionados são resolvidos, seus textos somem e o equipamento sai da lista apenas quando não restar relato ativo. Registro já reduzido não é reativado; falha que retorna gera novo relato.

### 9. Mostrar a contagem técnica mínima

Oferecer consulta interna simples de quantidades por equipamento e tipo de problema, usando os registros mínimos preservados. Não construir mapa, classificação automática de recorrência ou painel de tempos nesta fase.

**Pronto quando:** a contagem continua correta após apagar textos e não revela dados do aluno.

### 10. Validar e entregar o MVP fácil

Demonstrar: cadastrar equipamento, imprimir etiqueta, escanear, enviar, entrar como técnico, selecionar relatos e resolver. Verificar descrição obrigatória apenas em “Outro problema”, acesso restrito, resolução parcial, equipamento sem relatos ativos e exclusão real do texto. Testar concorrência do lote no PostgreSQL e o formulário no celular.

**Entrega do marco 1:** aluno relata; técnico atende e resolve em lote; conteúdo livre é apagado e a contagem mínima permanece. Registrar no README como executar essa versão. Não iniciar as próximas etapas para compensar uma falha desse fluxo.

## Fase 2 - Evoluir para o MVP completo

### 11. Preparar a transição de dados e regras

Criar migrações incrementais e marcar os registros da fase fácil. Manter sua política de descarte imediato até encerrá-los; a política completa passa a valer para chamados novos da fase completa. Não reconstruir textos ou autoria já apagados nem inventar dados históricos.

Preservar a categoria antiga como uma tag e admitir campos novos ausentes nos registros antigos. A exigência de título/descrição completos vale para novos envios; não impedir consultas aos registros mínimos existentes. Manter a contagem histórica sem duplicar linhas. Testar a migração com registros fáceis abertos e resolvidos.

**Pronto quando:** migrar preserva a primeira entrega, distingue registros antigos/novos e não expõe conteúdo excluído.

### 12. Implementar os três perfis

Técnico atende, consulta fotos/histórico, cadastra equipamentos, gera etiquetas, revisa restrições e consulta indicadores. Administrador gerencia contas, permissões, laboratórios, locais e tags, além de equipamentos/etiquetas; precisa acumular técnico para acessar chamados/fotos/autoria e técnico ou gestor para indicadores. Gestor consulta somente agregados. Não adicionar recuperação de acesso.

**Pronto quando:** cada operação tem acesso permitido e negado verificado, inclusive no Admin. Contas técnicas da fase fácil continuam utilizáveis.

### 13. Completar identificação e formulário

Adicionar entrada manual do código da etiqueta e substituição do identificador do QR Code, invalidando o anterior. Para novos chamados, exigir título de até 35 caracteres, descrição de até 250 e de 1 a 3 tags. Estado inicial Aberto e prioridade Média. Manter equipamento desativado sem aceitar relatos.

**Pronto quando:** novos envios usam o formulário completo; equipamentos e registros antigos continuam acessíveis pelas permissões corretas.

### 14. Proteger os reenvios

Criar chave aleatória por solicitação, vinculada ao navegador/sessão, única no banco e válida por 24 horas. Repetição idêntica retorna confirmação; conteúdo diferente exige outro envio/chave. Chave vencida ou ligada a chamado excluído informa expiração. Um relato independente recebe nova chave.

**Pronto quando:** reenvios simultâneos da mesma solicitação não duplicam o chamado. A confirmação não permite acompanhá-lo.

### 15. Aplicar limites por navegador e equipamento

Exigir cookie aleatório de 30 dias; sem cookies, impedir envio e orientar ativação. Permitir até 3 envios por navegador e 5 por equipamento em janela fixa de 15 minutos alinhada ao relógio. O terceiro/quinto envio é aceito e inicia bloqueio de 15 minutos, que continua na virada da janela. Recusas não renovam o prazo. Verificar reenvio antes de consumir limite; proteger contadores contra concorrência.

**Pronto quando:** os limites funcionam entre navegadores e mostram “Muitos envios em pouco tempo. Tente novamente em alguns minutos.”, sem tempo restante. Não usar IP como único critério.

### 16. Adicionar fotos privadas

Aceitar até duas imagens PNG/JPEG/HEIC, até 10 MB cada e 25 MB na requisição completa; MB decimal. Validar conteúdo, remover metadados e converter para WebP estático com Pillow/pillow-heif, usando imagem principal/primeiro quadro. Buscar cerca de 1 MB por foto sem prejudicar clareza, sem teto rígido de saída nem limite de dimensões como regra do produto. Tratar falhas e remover arquivos de envios incompletos.

**Pronto quando:** foto válida é consultada apenas por técnico autorizado; visitante e gestor não acessam o arquivo, mesmo com sua URL.

### 17. Completar triagem, estados e auditoria

Adicionar prioridade Baixa/Média/Alta/Crítica, responsável, notas internas e estados Em atendimento, Pendente e Cancelado. Motivo obrigatório para pendência/cancelamento; solução obrigatória para resolução. Registrar autor, data, horário e valores anteriores/novos, sem edição comum do histórico. Aplicar a mesma regra pelo Admin.

**Pronto quando:** novos chamados percorrem todos os estados e toda alteração relevante tem autoria. Relatos antigos mantêm a política da etapa 11.

### 18. Completar resolução e correção de encerramento

Permitir resolver diretamente Aberto ou Pendente. Evoluir o lote para detectar qualquer alteração desde a conferência por versão do registro; revalidar tudo em transação. Se algum mudou, não resolver nenhum e indicar qual exige nova conferência.

Permitir desfazer encerramento incorreto somente antes da remoção do conteúdo. Suspender retenção, preservar primeiro atendimento e invalidar a resolução atual; novo encerramento inicia outro prazo. Falha recorrente ou registro já reduzido exige novo chamado.

**Pronto quando:** não há sucesso parcial, fusão nem reativação de registro cujo texto/fotos já foram removidos.

### 19. Tratar abuso e restrições manuais

Permitir ao técnico confirmar abuso e excluir imediatamente chamado, fotos, histórico e autoria. Restrição do navegador é opcional, de 1 a 168 horas inteiras, com remoção antecipada. Manter apenas navegador, prazo, técnico responsável e justificativa breve da restrição, sem cópia do relato.

**Pronto quando:** excluir o relato não remove uma restrição vigente; sua revisão não depende de recuperar conteúdo apagado. Semelhança ou informação incompleta, isoladamente, não prova abuso.

### 20. Aplicar retenção diária aos novos registros

Executar comando diário para remover conteúdo de resolvidos após 60 dias e cancelados sem abuso após 14 dias. Preservar equipamento, laboratório, tags, datas, estado final e autoria estruturada. Limpar textos também da auditoria. Excluir dados auxiliares em até 30 dias ou antes quando desnecessários. Chamados ativos e histórico preservado não têm prazo definido.

**Pronto quando:** prazos e correções de encerramento são respeitados, sem restaurar registros da fase fácil. Registrar falhas sem dados pessoais; não implementar recuperação avançada ou filas de novas tentativas.

### 21. Calcular os três indicadores

Quantidade de relatos válidos, excluindo cancelamentos; tempo até primeiro atendimento; tempo total até resolução. Primeiro atendimento é primeira entrada em Em atendimento ou resolução direta. Tempo total inclui pendências e usa resolução vigente. Após correção de encerramento, manter primeiro atendimento e recalcular total na nova resolução. Sem data disponível, mostrar valor indisponível, não zero; não inventar tempos para registros antigos.

**Pronto quando:** indicadores continuam funcionando após retenção e gestor consulta somente agregados, sem navegar para relatos, fotos ou autoria.

### 22. Completar painel e histórico interno

Adicionar paginação, filtros por laboratório, equipamento, tags, estado e responsável; manter acesso por equipamento. Mostrar histórico conforme os dados ainda disponíveis e sinalizar conteúdo removido. Conservar somente os três indicadores exigidos, sem mapa ou cálculo adicional de recorrência.

**Pronto quando:** técnico encontra os relatos e distingue registros antigos, novos e reduzidos sem expor informações além de suas permissões.

### 23. Verificar a entrega completa

Testar migração, matriz de acesso, campos, reenvios, limites simultâneos, fotos privadas, estados, auditoria, conflito no lote, restrição e retenção. Usar PostgreSQL nos testes transacionais. Verificar celular, teclado, mensagens e as [metas de qualidade](README.md#metas-de-qualidade).

**Pronto quando:** o fluxo completo passa nas verificações e dados da fase fácil continuam corretos. Corrigir falhas antes de declarar o segundo marco entregue.

### 24. Preparar e executar o piloto simulado

Documentar instalação, migrações, perfis, rotas, fotos privadas e agendamento diário no README. Preparar banco, armazenamento persistente, arquivos estáticos e segredos; HTTPS quando disponível em rede. Demonstrar com equipamentos de exemplo o envio completo, atendimento, correção de encerramento, indicadores e retenção.

**Entrega do marco 2:** comportamento de [MVPcompleto/MVP.txt](MVPcompleto/MVP.txt) implementado e verificado. Identificação por matrícula/senha, integrações institucionais e recuperação avançada continuam fora do escopo.
