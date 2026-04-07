# Checklist de MVP para Revenda

Atualizado em `2026-04-02`.

## Objetivo

Levar o sistema para um estado minimamente seguro, versionado e distribuivel por cliente, com operacao previsivel para comecar a revender.

## Regra Tecnica Importante

Se o codigo roda na maquina do cliente, **nao existe** forma de garantir que ninguem vai extrair, editar ou copiar 100%.

O que existe na pratica:

- `SaaS centralizado`: melhor opcao para proteger codigo
- `self-hosted por cliente`: cliente recebe deploy, acesso ao codigo deve ser controlado por contrato e infraestrutura
- `desktop empacotado`: dificulta acesso, mas nao impede engenharia reversa

## Recomendacao de Modelo

Para revender com mais seguranca:

- [ ] definir se o produto sera `SaaS centralizado` ou `instalacao por cliente`
- [ ] se a prioridade for proteger codigo, preferir `SaaS centralizado`
- [ ] se houver cliente que exige on-premise, tratar como excecao comercial e tecnica

## Fase 1 - Fechamento de MVP Funcional

Objetivo: garantir que o produto esta vendavel do ponto de vista operacional.

- [ ] fechar validacao dos modulos criticos: `cadastro`, `vendas`, `compras`, `estoque`, `financeiro`, `fiscal`
- [ ] registrar fluxos obrigatorios de demo e onboarding
- [ ] validar perfis e permissoes basicas por papel
- [ ] revisar mensagens de erro e estados vazios mais importantes
- [ ] definir lista oficial do que entra no MVP e do que fica fora

Critério de aceite:

- [ ] existe lista fechada de funcionalidades vendaveis
- [ ] existe roteiro de demonstracao comercial
- [ ] fluxos principais nao quebram em ambiente limpo

## Fase 2 - Seguranca Basica Obrigatoria

Objetivo: subir o nivel minimo para vender sem expor o sistema de forma amadora.

- [ ] separar `DEBUG=False` em ambiente de producao
- [ ] revisar `SECRET_KEY`, credenciais, `.env` e variaveis por ambiente
- [ ] forcar HTTPS em producao
- [ ] revisar cookies de sessao e CSRF
- [ ] revisar uploads e validacao de arquivos
- [ ] limitar acesso ao admin Django
- [ ] registrar auditoria minima de login, logout e acoes sensiveis
- [ ] configurar backup automatico de banco e arquivos
- [ ] definir politica de restauracao de backup

Critério de aceite:

- [ ] nenhuma credencial sensivel fica hardcoded no repositorio
- [ ] ambiente produtivo nao roda com configuracao de desenvolvimento
- [ ] existe backup automatico e teste de restauracao

## Fase 3 - Empacotamento e Protecao do Codigo

Objetivo: dificultar copia/edicao indevida quando houver entrega fora do seu servidor.

### Opcao A - SaaS

- [ ] centralizar deploy em servidor seu
- [ ] nao entregar codigo ao cliente
- [ ] isolar base de dados por cliente ou por schema/tenant
- [ ] controlar dominio, SSL e acesso de suporte

### Opcao B - Self-hosted / On-premise

- [ ] distribuir so build/deploy, nao o workspace de desenvolvimento
- [ ] entregar via container ou pacote fechado
- [ ] remover arquivos desnecessarios do pacote final
- [ ] obfuscar camada Python apenas se realmente precisar aumentar barreira
- [ ] definir contrato/licenca proibindo copia e redistribuicao

### Opcao C - Executavel Empacotado

- [ ] avaliar `PyInstaller` ou `Nuitka`
- [ ] empacotar sem fontes auxiliares soltos
- [ ] assinar instalador/executavel
- [ ] testar upgrade sem quebrar banco nem media

Critério de aceite:

- [ ] existe pacote padrao de entrega
- [ ] existe procedimento padrao de instalacao
- [ ] existe procedimento padrao de rollback

## Fase 4 - Versionamento de Produto

Objetivo: vender e atualizar com previsibilidade.

- [ ] adotar versao semantica: `MAJOR.MINOR.PATCH`
- [ ] centralizar versao do sistema em um unico ponto
- [ ] registrar changelog por release
- [ ] gerar identificador da build entregue ao cliente
- [ ] vincular versao ao pacote de distribuicao
- [ ] registrar versao instalada por cliente

Critério de aceite:

- [ ] cada entrega possui versao unica
- [ ] voce consegue dizer rapidamente qual cliente esta em qual versao

## Fase 5 - Atualizacao por Cliente

Objetivo: atualizar sem virar operacao manual caotica.

- [ ] definir estrategia de update: `automatico`, `assistido` ou `manual controlado`
- [ ] criar rotina padrao de migracao de banco
- [ ] criar rotina padrao de backup antes de atualizar
- [ ] validar compatibilidade entre versoes consecutivas
- [ ] documentar janela de manutencao e rollback
- [ ] criar checklist de pos-atualizacao

Critério de aceite:

- [ ] uma nova versao consegue ser aplicada sem improviso
- [ ] existe rollback documentado

## Fase 6 - Distribuicao por Cliente

Objetivo: estruturar a revenda como produto, nao como copia manual.

- [ ] definir modelo por cliente:
- [ ] `cliente unico por banco`
- [ ] `cliente unico por servidor`
- [ ] `multicliente com isolamento`
- [ ] definir nomenclatura de cliente, ambiente e dominio
- [ ] criar pasta/pacote padrao de entrega
- [ ] criar parametros por cliente: nome, branding, versao, dominio, certificados, dados fiscais
- [ ] documentar onboarding de novo cliente

Critério de aceite:

- [ ] novo cliente pode ser provisionado com roteiro padrao

## Fase 7 - Licenciamento e Controle Comercial

Objetivo: nao vender sem travas comerciais minimas.

- [ ] definir tipo de licenca: `mensal`, `anual`, `perpetua com manutencao`, `por usuarios`
- [ ] definir politica de suporte e SLA
- [ ] definir politica de implantacao
- [ ] definir politica de inadimplencia/bloqueio
- [ ] criar contrato com clausulas de uso, copia, redistribuicao e suporte
- [ ] decidir se havera validacao de licenca no sistema

Critério de aceite:

- [ ] existe modelo comercial e juridico padrao

## Fase 8 - Observabilidade e Suporte

Objetivo: conseguir manter clientes sem voar cego.

- [ ] centralizar logs de aplicacao
- [ ] registrar erros criticos
- [ ] registrar falhas de integracao fiscal
- [ ] criar rotina de coleta de diagnostico
- [ ] definir canal de suporte
- [ ] criar documento de troubleshooting rapido

Critério de aceite:

- [ ] suporte consegue identificar problema sem acessar o codigo-fonte inteiro

## Fase 9 - Branding por Cliente

Objetivo: distribuir para varios clientes sem editar codigo toda vez.

- [ ] centralizar nome do sistema, logo, cores e versao por configuracao
- [ ] centralizar textos institucionais e links de documentacao
- [ ] separar branding global de branding por cliente
- [ ] definir o que e customizavel sem fork de codigo

Critério de aceite:

- [ ] novo cliente recebe branding sem alterar templates manualmente

## Fase 10 - Pacote de Entrega

Objetivo: ter um produto entregavel de verdade.

- [ ] instalador ou pacote zip padrao
- [ ] arquivo de configuracao por cliente
- [ ] manual de instalacao
- [ ] manual de atualizacao
- [ ] manual de backup e restauracao
- [ ] changelog da versao
- [ ] termo/licenca de uso

Critério de aceite:

- [ ] qualquer entrega comercial sai a partir do mesmo pacote base

## Prioridade Real para Comecar a Revender

### Obrigatorio antes da primeira venda

- [ ] definir `SaaS` ou `on-premise`
- [ ] fechar MVP funcional
- [ ] desligar modo de desenvolvimento em producao
- [ ] montar backup e restore
- [ ] definir versionamento
- [ ] definir pacote de distribuicao
- [ ] definir contrato/licenca

### Muito recomendado na primeira onda

- [ ] branding por cliente
- [ ] rotina de update
- [ ] logs centralizados
- [ ] build empacotada

### Pode entrar na segunda onda

- [ ] obfuscacao avancada
- [ ] licenciamento automatico
- [ ] auto-update completo
- [ ] multi-tenant mais sofisticado

## Caminho Mais Seguro

Se o foco agora e comecar a vender rapido com mais controle:

1. `SaaS centralizado`
2. `versao fechada + changelog + backup`
3. `branding por configuracao`
4. `provisionamento por cliente`
5. `pacote comercial e operacional padrao`

## Proximo Passo Pratico

Se for seguir com revenda agora, a ordem mais pragmatica e:

1. fechar `modelo de entrega`
2. fechar `seguranca basica`
3. fechar `versionamento`
4. fechar `pacote de deploy`
5. fechar `contrato/licenca`
