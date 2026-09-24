# Telas e fluxo do MVP fácil

Base: [MVP fácil](MVP.txt). Esta versão corresponde às etapas 1 a 10 da [ordem de desenvolvimento](../ORDEM_DE_DESENVOLVIMENTO.md). A evolução posterior está documentada em [MVP completo](../MVPcompleto/MVP.txt).

## Ferramentas e acesso

Django Templates e Bootstrap para páginas adaptadas ao celular e computador; autenticação do Django para técnicos; Django Admin para a equipe preparar contas, laboratórios, locais, equipamentos e a lista de problemas. O QR Code é lido pela câmera do celular.

O aluno não tem conta e apenas envia o relato. Somente técnicos autenticados e autorizados consultam ou resolvem chamados. As contas internas são necessárias ao acesso, mas não são vinculadas aos relatos como identidade do aluno ou autoria de atendimento nesta versão.

## Telas

| Tela | Acesso | Conteúdo e ações |
| --- | --- | --- |
| Equipamento e relato | Público, pelo QR Code | Identificação do equipamento e laboratório, seleção de um problema e descrição. |
| Confirmação | Público, após envio | Mensagem de recebimento, sem link de acompanhamento ou consulta ao chamado. |
| Entrada | Técnico | Autenticação com credenciais preparadas pela equipe; opção de sair após entrar. |
| Equipamentos com chamados | Técnico | Somente equipamentos com ao menos um relato Aberto, com localização e quantidade de relatos ativos. |
| Relatos do equipamento | Técnico | Descrição/localização do equipamento, problemas e descrições dos relatos ativos, seleção de um ou vários relatos. |
| Conferência da resolução | Técnico | Selecionados do mesmo equipamento e ação de confirmar a resolução. Não exige solução escrita. |
| Contagem técnica | Técnico | Quantidades por equipamento e tipo de problema, sem texto livre ou autoria. |
| Cadastros e etiqueta | Equipe autorizada | Cadastros pelo Admin e etiqueta com QR Code para impressão. Sem construir um painel administrativo próprio. |

Equipamento desativado ou QR Code inválido gera mensagem compreensível e não permite envio. Falta de relatos ativos gera estado vazio no painel; equipamento não é apagado do cadastro ao sair dessa lista.

## Fluxo do aluno

1. Escanear o QR Code e conferir equipamento e laboratório preenchidos automaticamente.
2. Selecionar exatamente um problema da lista, incluindo a opção “Outro problema”.
3. Escrever descrição de até 250 caracteres, opcional para os demais problemas e obrigatória para “Outro problema”. Essa escolha segue a simplificação adotada na ordem de desenvolvimento.
4. Enviar. O servidor valida os campos, o equipamento ativo e a proteção CSRF; não aceita equipamento/laboratório adulterados no formulário.
5. Em caso de erro, orientar a correção e preservar campos quando possível. Se válido, criar um relato Aberto e mostrar confirmação simples.

Cada relato é independente. Não mostrar relatos semelhantes nem perguntar se o aluno também foi afetado. Não solicitar título, fotos, nome, contato, matrícula ou senha. Orientar a não incluir dados pessoais na descrição e evitar cópia do conteúdo em logs.

## Fluxo do técnico

1. Entrar e abrir a lista de equipamentos com relatos ativos.
2. Selecionar um equipamento e consultar sua localização, descrição e relatos Abertos.
3. Avaliar o equipamento e executar a correção.
4. Selecionar somente os relatos solucionados e conferir a seleção.
5. Confirmar. O servidor verifica autorização, equipamento comum e se todos os selecionados continuam ativos, dentro de uma transação.
6. Se algum selecionado mudou de estado, não resolver nenhum; informar o conflito e pedir nova conferência.
7. Marcar os selecionados como Resolvidos, registrar a data e apagar imediatamente suas descrições na mesma operação do banco.
8. Atualizar a lista. O equipamento sai do painel quando não houver relato Aberto; os não selecionados permanecem ativos.

Não há fusão de relatos. Falha que retorna exige novo relato; registro já reduzido não é reativado. A detecção de qualquer alteração por versão, além da validação do estado ativo, será adicionada na fase completa.

## Estados e dados após resolução

| Estado | Dados disponíveis |
| --- | --- |
| Aberto | Equipamento, laboratório no envio, problema, descrição opcional e data de abertura. |
| Resolvido | Apenas equipamento, laboratório no envio, problema, datas e estado final. |

O registro técnico mínimo sustenta a contagem por equipamento/problema. Não guardar descrição em histórico, logs ou auditoria do Admin nem associar autoria pessoal ao atendimento. As contas dos técnicos existem separadamente para autenticação.

## Critério de entrega

Demonstrar cadastro, etiqueta, envio pelo celular, entrada técnica, resolução parcial e saída do equipamento da lista quando todos os relatos forem resolvidos. Conferir acesso restrito, conflito no lote, remoção efetiva de texto e permanência da contagem técnica.

Fotos, título, múltiplas tags, prioridade, atribuição, notas, outros estados, gestor, controle de frequência por cookie e retenção de 60/14 dias pertencem à fase completa. Cookies técnicos de CSRF e autenticação podem existir; não criar identificador persistente do aluno para o relato fácil.
