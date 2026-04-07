# Checklist de Primeira Instalacao e Onboarding

Atualizado em `2026-04-02`.

## Objetivo

Garantir que, na primeira instalacao em um novo cliente, o sistema saia de:

- ambiente vazio

para:

- empresa cadastrada
- configuracao minima concluida
- usuario administrador ativo
- usuarios operacionais criados
- sistema pronto para uso

## Visao Geral do Fluxo

Ordem recomendada:

1. instalar sistema
2. subir banco e migracoes
3. criar `admin master`
4. fazer primeiro login
5. cadastrar empresa principal
6. configurar empresa
7. vincular empresa ao usuario
8. criar usuarios e perfis
9. validar modulos obrigatorios
10. liberar operacao

## Fase 0 - Pre-Instalacao

Objetivo: preparar ambiente do cliente.

- [ ] definir nome do cliente
- [ ] definir branding do cliente
- [ ] definir dominio ou ambiente local
- [ ] definir banco de dados
- [ ] definir caminho de backup
- [ ] definir certificado fiscal, se aplicavel
- [ ] definir impressoras e perifericos, se houver PDV
- [ ] definir quem sera o administrador do cliente

Critério de aceite:

- [ ] ambiente e responsaveis estao definidos antes da instalacao

## Fase 1 - Instalacao Tecnica

Objetivo: colocar o sistema no ar no cliente.

- [ ] instalar pacote do sistema
- [ ] configurar `.env` do cliente
- [ ] configurar segredo, banco, dominio e URLs
- [ ] rodar migracoes
- [ ] coletar estaticos
- [ ] validar acesso HTTP/HTTPS
- [ ] validar pagina de login

Critério de aceite:

- [ ] sistema sobe limpo e pagina de login responde

## Fase 2 - Admin Master Inicial

Objetivo: criar o primeiro usuario com controle total.

- [ ] criar usuario `admin master` inicial
- [ ] forcar troca de senha no primeiro acesso, se desejado
- [ ] registrar email do responsavel
- [ ] validar login administrativo
- [ ] validar acesso ao painel de usuarios

### Regra importante

Esse usuario nao deve ser o usuario operacional do dia a dia.

- [ ] manter `admin master` como conta de contingencia
- [ ] criar depois um usuario gestor para uso normal

Critério de aceite:

- [ ] existe uma conta administrativa segura e validada

## Fase 3 - Primeiro Login Guiado

Objetivo: impedir que o cliente caia num sistema “vazio e solto”.

### Fluxo ideal no primeiro acesso

- [ ] detectar que nao existe empresa cadastrada
- [ ] redirecionar automaticamente para `cadastro da empresa`
- [ ] bloquear acesso pleno ao sistema ate concluir configuracao minima

### Se nao houver wizard ainda

Fluxo manual obrigatorio:

1. login com `admin master`
2. abrir `cadastro de empresa`
3. criar empresa principal
4. selecionar empresa ativa
5. abrir configuracoes obrigatorias

Critério de aceite:

- [ ] nenhum cliente novo fica perdido apos o primeiro login

## Fase 4 - Cadastro da Empresa Principal

Objetivo: criar a entidade central do cliente.

### Dados minimos obrigatorios

- [ ] razao social
- [ ] nome fantasia
- [ ] tipo de pessoa
- [ ] CNPJ ou CPF
- [ ] inscricao estadual, quando aplicavel
- [ ] inscricao municipal, quando aplicavel
- [ ] telefone
- [ ] email
- [ ] endereco completo
- [ ] municipio
- [ ] UF
- [ ] CEP

### Dados recomendados

- [ ] logo
- [ ] regime tributario
- [ ] CNAE
- [ ] CRT
- [ ] informacoes complementares

Critério de aceite:

- [ ] empresa principal existe e pode ser vinculada aos usuarios

## Fase 5 - Configuracao da Empresa

Objetivo: deixar a empresa pronta para operar.

### Configuracoes administrativas

- [ ] selecionar empresa ativa
- [ ] validar branding do cliente
- [ ] validar email padrao
- [ ] validar telefone e contato

### Configuracoes fiscais

- [ ] certificado digital
- [ ] ambiente homologacao/producao
- [ ] serie e numeracao fiscal
- [ ] natureza padrao
- [ ] grupo fiscal padrao

### Configuracoes comerciais

- [ ] local de estoque padrao
- [ ] condicao de pagamento padrao
- [ ] transportadora padrao, se houver

### Configuracoes financeiras

- [ ] plano de contas minimo
- [ ] caixa ou conta principal
- [ ] classificacoes iniciais

Critério de aceite:

- [ ] empresa esta configurada para operar os modulos do MVP

## Fase 6 - Vinculo da Empresa ao Administrador

Objetivo: garantir que o usuario entre no contexto correto.

- [ ] vincular empresa principal ao `admin master`
- [ ] validar selecao de empresa no login
- [ ] validar acesso do usuario dentro da empresa correta

Critério de aceite:

- [ ] usuario administrativo opera na empresa certa

## Fase 7 - Criacao de Usuarios

Objetivo: criar os usuarios reais do cliente.

### Usuarios minimos recomendados

- [ ] `admin master`
- [ ] `gestor`
- [ ] `financeiro`
- [ ] `vendas`
- [ ] `estoque`
- [ ] `caixa` ou `pdv`, se houver PDV

### Dados por usuario

- [ ] nome
- [ ] login
- [ ] senha inicial
- [ ] email
- [ ] empresa vinculada
- [ ] perfil/permissoes
- [ ] status ativo

Critério de aceite:

- [ ] usuarios operacionais foram criados e testados

## Fase 8 - Perfis e Permissoes

Objetivo: evitar que todo mundo tenha acesso total.

### Perfis minimos

- [ ] administrador
- [ ] gestor
- [ ] financeiro
- [ ] vendedor
- [ ] estoque
- [ ] operador de caixa

### Validacoes

- [ ] operador nao acessa configuracao sensivel
- [ ] vendedor nao acessa financeiro completo
- [ ] caixa nao acessa retaguarda completa
- [ ] gestor tem visao ampla sem ser superuser tecnico

Critério de aceite:

- [ ] acesso por perfil esta coerente com a operacao do cliente

## Fase 9 - Cadastros Minimos para Operar

Objetivo: evitar que o cliente tente usar o sistema sem base minima.

### Obrigatorios

- [ ] ao menos 1 empresa
- [ ] ao menos 1 local de estoque
- [ ] ao menos 1 categoria
- [ ] ao menos 1 unidade
- [ ] ao menos 1 forma/condicao de pagamento, se aplicavel
- [ ] ao menos 1 produto, se for iniciar vendas
- [ ] ao menos 1 cliente, se o fluxo exigir

### Financeiro

- [ ] plano de contas minimo criado
- [ ] grupo/classificacao inicial configurado

Critério de aceite:

- [ ] o cliente consegue realizar o primeiro fluxo real

## Fase 10 - Checklist de Go-Live

Objetivo: liberar uso real com risco controlado.

- [ ] login validado
- [ ] empresa criada
- [ ] empresa configurada
- [ ] usuario gestor criado
- [ ] usuarios operacionais criados
- [ ] permissoes testadas
- [ ] backup configurado
- [ ] impressao validada, se houver
- [ ] fiscal validado, se houver
- [ ] primeiro cadastro real realizado
- [ ] primeiro fluxo real validado

Critério de aceite:

- [ ] sistema pronto para uso do cliente

## Wizard Ideal de Primeira Instalacao

Se formos implementar isso no produto, o fluxo ideal seria:

1. tela `Bem-vindo`
2. criar `admin master`
3. cadastrar `empresa principal`
4. configurar dados obrigatorios da empresa
5. criar `usuario gestor`
6. configurar modulos minimos
7. tela `Sistema pronto`

## MVP de Onboarding

Se for fazer so o minimo agora:

- [ ] detectar ausencia de empresa
- [ ] redirecionar para cadastro da empresa
- [ ] criar rotina segura para gerar `admin master`
- [ ] obrigar selecao de empresa
- [ ] criar tela/checklist de configuracao inicial
- [ ] criar usuarios basicos

## Proximo Passo Pratico

Se quisermos transformar isso em produto de verdade, a ordem mais pragmatica e:

1. `admin master inicial`
2. `bloqueio ate empresa existir`
3. `cadastro guiado da empresa`
4. `vinculo da empresa ao usuario`
5. `criacao de usuarios e perfis`
6. `checklist final de liberacao`
