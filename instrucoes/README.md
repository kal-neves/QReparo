# Documentação do QReparo

A entrega prioritária é o MVP fácil. A evolução completa começa depois que o fluxo da primeira entrega estiver implementado e verificado. A [ordem de desenvolvimento](ORDEM_DE_DESENVOLVIMENTO.md) é o plano principal: etapas 1 a 10 para a primeira entrega e 11 a 24 para a evolução.

## Documentos por fase

Operação: [hospedagem temporária no Railway](HOSPEDAGEM_RAILWAY.md), incluindo volume privado, verificações e recuperação.

| Fase | Escopo | Interface | Arquitetura |
| --- | --- | --- | --- |
| MVP fácil | [Resumo](MVPfacil/MVP.txt) | [Telas e fluxo](MVPfacil/TELAS_E_FLUXO.md) | [Arquitetura](MVPfacil/ARQUITETURA.md) |
| MVP completo | [Resumo](MVPcompleto/MVP.txt) | [Telas e fluxo](MVPcompleto/TELAS_E_FLUXO.md) | [Arquitetura e regras técnicas](MVPcompleto/ARQUITETURA.md) |

As regras de cada fase devem ser lidas junto com o plano principal. As funcionalidades completas não são condição para aceitar o MVP fácil. Na transição, registros antigos mantêm descarte imediato e histórico mínimo; a retenção completa vale para novos relatos. Não reconstruir texto ou autoria removidos.

Os documentos descrevem o comportamento esperado e não atestam implementação ou testes aprovados. As decisões funcionais estão incorporadas nos documentos de cada fase.

## Metas de qualidade

Aplicar às funcionalidades efetivamente entregues em cada fase, no piloto simulado:

- Pelo menos 95% das páginas de equipamento apresentam o conteúdo principal em até 3 segundos em condições normais de rede.
- Pelo menos 95% das consultas internas, registros e atualizações concluem ou fornecem confirmação inicial em até 3 segundos, desconsiderando envio de arquivos.
- Pelo menos 80% dos participantes registram relato válido sem auxílio em até 2 minutos, medidos até a confirmação.
- Todos os fluxos principais funcionam por teclado, com campos identificados, contraste adequado e sem erros críticos nas verificações automatizadas adotadas pela equipe.
- Os fluxos principais funcionam em larguras de 360 a 1920 pixels e nas duas versões estáveis mais recentes de Chrome, Edge e Firefox à época do teste.
- Verificar permissões no servidor e usar HTTPS quando disponibilizado em rede. Usar PostgreSQL nos testes de transação e concorrência.
