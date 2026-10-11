# Kanban — Assistência Técnica

Este arquivo é a fonte de acompanhamento das melhorias do sistema. Mova cada item entre as seções conforme o trabalho avança e registre uma observação curta quando necessário.

## A fazer

### Alta — continuidade operacional

- [ ] **Criar backup do sistema** — gerar cópia datada do banco SQLite.
- [ ] **Criar restauração de backup** — permitir selecionar uma cópia, validar e restaurar com confirmação.
- [ ] **Definir escopo do backup completo** — decidir se inclui banco, logos e PDFs emitidos.
- [ ] **Criar política de retenção de backups** — definir pasta, frequência e tempo de guarda.
- [ ] **Declarar dependências do projeto** — criar `requirements.txt` ou `pyproject.toml` com Flet, Flet Charts e ReportLab.
- [ ] **Escrever README de execução** — documentar instalação, execução, backup e localização dos dados.
- [ ] **Adicionar `.gitignore`** — ignorar banco operacional, PDFs, backups, ambientes virtuais e arquivos temporários.
- [ ] **Versionar o código no Git** — adicionar os arquivos do sistema e registrar uma primeira versão organizada.

### Média — banco e arquitetura

- [ ] **Separar o código em módulos** — dividir interface, banco, regras de negócio, PDFs e configurações.
- [ ] **Centralizar constantes e status** — manter nomes de status, cores, rótulos e caminhos em um local único.
- [ ] **Criar migrações versionadas do banco** — substituir ajustes isolados por versões controladas do schema.
- [ ] **Revisar `data_previsao`** — integrar o campo já existente no banco à interface e às consultas, ou removê-lo por migração.
- [ ] **Padronizar datas no banco** — gravar em formato ordenável e apresentar no formato brasileiro na tela.
- [ ] **Padronizar valores monetários** — evitar armazenar preço como texto; usar centavos inteiros ou `Decimal`.
- [ ] **Adicionar índices ao SQLite** — otimizar buscas por cliente, status e data de entrada.
- [ ] **Registrar histórico de status** — guardar data, status anterior, novo status e responsável pela mudança.

### Média — recursos de operação

- [ ] **Vincular peças à ordem de serviço** — registrar quais itens foram usados em cada reparo.
- [ ] **Dar baixa automática no estoque** — atualizar quantidade ao associar peça à OS.
- [ ] **Criar alerta de estoque baixo** — destacar itens abaixo de quantidade mínima.
- [ ] **Registrar custo e fornecedor das peças** — permitir controle de margem por serviço.
- [ ] **Criar tela de detalhe da OS** — visualizar tudo sem entrar imediatamente em edição.
- [ ] **Permitir reimpressão de OS** — localizar ou gerar novamente o PDF de uma ordem existente.
- [ ] **Evitar clientes duplicados na Nota de Entrada** — buscar e selecionar cliente existente antes de criar um novo.
- [ ] **Adicionar busca por número da OS** — complementar busca por cliente, telefone, marca e modelo.
- [ ] **Adicionar filtros de aparelhos** — filtrar por status, período, previsão e prioridade.
- [ ] **Adicionar ordenação e paginação nas listas** — manter a interface fluida com maior volume de dados.

### Baixa — evolução e governança

- [ ] **Criar usuários e permissões** — perfis de administrador, atendente e técnico.
- [ ] **Criar trilha de auditoria** — registrar alterações, exclusões e operações sensíveis.
- [ ] **Criar testes automatizados de banco e regras de status**.
- [ ] **Criar testes de geração de PDF** — contemplar logo ausente, textos longos e campos vazios.
- [ ] **Criar testes de backup e restauração**.
- [ ] **Preparar distribuição para Windows** — avaliar executável/instalador e atualização de versão.

## Em andamento

### Crítico — implementação concluída, aguardando validação visual no Flet/PDF

- [ ] **Corrigir indicadores de status no painel** — distribuição exclusiva por status e cartão de reparos concluídos.
- [ ] **Definir “Reparos concluídos”** — conta `pronto + entregue`.
- [ ] **Padronizar o ciclo de status da OS** — estados centralizados e fluxo recomendado documentado; alteração segue livre.
- [ ] **Manter regra de autorização** — serviço autorizado continua iniciando em `aguardando_peca`.
- [ ] **Ocultar senhas de aparelhos nas listagens e buscas** — senha removida da pesquisa global e mantida apenas em formulário protegido.
- [ ] **Proteger senhas armazenadas** — criptografia com senha-mestra, recuperação por pergunta e migração automática de dados legados.
- [ ] **Corrigir portabilidade da logo** — caminho relativo e migração de referência absoluta.
- [ ] **Criar fallback para logo ausente** — menu, configuração e PDF usam alternativa padrão.

## Concluído

<!-- Mova somente tarefas verificadas para esta seção, preservando uma nota curta de validação. -->

Nenhuma tarefa concluída.

## Convenções

- Use `- [ ]` para tarefas pendentes e `- [x]` quando concluídas.
- Mova a tarefa, não a copie, entre as colunas.
- Mantenha o título da tarefa objetivo; use um subitem ou comentário para contexto técnico.
- Antes de marcar como concluída, valide a mudança com dados reais e registre o resultado quando for relevante.
