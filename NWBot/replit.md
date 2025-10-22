# Discord Bot - Check-list Diária

## Visão Geral
Bot do Discord que fornece check-lists diárias personalizadas para usuários com uma role específica. As tarefas podem ser marcadas como concluídas e resetam automaticamente à meia-noite.

## Estado Atual
- ✅ Bot implementado e funcionando
- ✅ Autenticação configurada via DISCORD_BOT_TOKEN
- ✅ Sistema de armazenamento em JSON
- ✅ Reset automático diário às 00:00
- ✅ Comandos para usuários e administradores

## Funcionalidades

### Para Usuários
- `!NWDailies` - Visualiza sua check-list pessoal
- `!done <número>` - Marca/desmarca uma tarefa como concluída
- `!help_dailies` - Mostra todos os comandos disponíveis

### Para Administradores
- `!configurar_role @role` - Define qual role terá acesso às check-lists
- `!add_task <descrição>` - Adiciona uma nova tarefa diária
- `!remover_tarefa <número>` - Remove uma tarefa existente
- `!listar_tarefas_admin` - Lista todas as tarefas configuradas

## Arquitetura

### Estrutura de Arquivos
```
.
├── main.py                 # Código principal do bot
├── data/
│   ├── checklists.json    # Check-lists dos usuários
│   └── config.json        # Configuração global (role e tarefas)
└── replit.md              # Esta documentação
```

### Sistema de Armazenamento
- **config.json**: Armazena a role_id e a lista de tarefas diárias
- **checklists.json**: Armazena o progresso individual de cada usuário

### Reset Automático
O bot usa `@tasks.loop` do discord.py para executar um reset automático todos os dias à meia-noite (00:00), marcando todas as tarefas como não concluídas.

## Configuração Inicial

1. **Adicionar o bot ao servidor**: Use o link de convite gerado no Discord Developer Portal
2. **Configurar a role**: Use `!configurar_role @NomeDaRole` para definir quem tem acesso
3. **Adicionar tarefas**: Use `!adicionar_tarefa` para criar as tarefas diárias
4. **Testar**: Usuários com a role podem usar `!minha_checklist`

## Dependências
- discord.py (2.6.4)
- aiofiles (25.1.0)
- python-dotenv (1.1.1)

## Variáveis de Ambiente
- `DISCORD_BOT_TOKEN`: Token de autenticação do bot (obrigatório)

## Data de Criação
22 de Outubro de 2025

## Notas Importantes

### Sincronização de Tarefas
O bot sincroniza automaticamente as check-lists de todos os usuários quando:
- Um administrador adiciona uma nova tarefa com `!add_task`
- Um administrador remove uma tarefa com `!remover_tarefa`
- Um usuário visualiza sua check-list com `!NWDailies`

O progresso das tarefas é preservado durante a sincronização, desde que a descrição da tarefa permaneça a mesma. Tarefas novas são adicionadas como não concluídas, e tarefas removidas são descartadas.

**Dica para Administradores**: Evite renomear tarefas diretamente. Se precisar mudar uma tarefa, remova a antiga e adicione a nova.

## Alterações Recentes
- 22/10/2025: Implementação inicial do bot
  - Sistema de check-lists por usuário
  - Comandos de administração
  - Reset automático diário
  - Armazenamento em JSON
  - Sincronização automática de tarefas entre admin e usuários
