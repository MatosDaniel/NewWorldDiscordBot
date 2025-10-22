import discord
from discord.ext import commands, tasks
import json
import os
import asyncio
from datetime import datetime, time
import aiofiles


class ChecklistBot(commands.Bot):

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True

        super().__init__(command_prefix='!', intents=intents)
        self.checklist_file = 'data/checklists.json'
        self.config_file = 'data/config.json'

    async def setup_hook(self):
        await self.load_data()
        self.daily_reset.start()

    async def load_data(self):
        os.makedirs('data', exist_ok=True)

        if not os.path.exists(self.checklist_file):
            async with aiofiles.open(self.checklist_file, 'w') as f:
                await f.write('{}')

        if not os.path.exists(self.config_file):
            async with aiofiles.open(self.config_file, 'w') as f:
                await f.write('{"role_id": null, "tasks": []}')

    async def get_checklists(self):
        async with aiofiles.open(self.checklist_file, 'r') as f:
            content = await f.read()
            return json.loads(content)

    async def save_checklists(self, data):
        async with aiofiles.open(self.checklist_file, 'w') as f:
            await f.write(json.dumps(data, indent=2))

    async def get_config(self):
        async with aiofiles.open(self.config_file, 'r') as f:
            content = await f.read()
            return json.loads(content)

    async def save_config(self, data):
        async with aiofiles.open(self.config_file, 'w') as f:
            await f.write(json.dumps(data, indent=2))

    @tasks.loop(time=time(hour=0, minute=0))
    async def daily_reset(self):
        print(f"Executando reset diário às {datetime.now()}")
        checklists = await self.get_checklists()

        for user_id in checklists:
            for task_id in checklists[user_id]:
                checklists[user_id][task_id]['completed'] = False

        await self.save_checklists(checklists)
        print("Reset diário completo!")


async def get_discord_token():
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        raise Exception(
            'DISCORD_BOT_TOKEN não configurado! Por favor, adicione seu Bot Token.'
        )
    return token


bot = ChecklistBot()


@bot.event
async def on_ready():
    print(f'{bot.user} está online!')
    print(f'Bot está em {len(bot.guilds)} servidor(es)')


@bot.command(name='configurar_role')
@commands.has_permissions(administrator=True)
async def set_role(ctx, role: discord.Role):
    """Define qual role terá acesso às check-lists (apenas administradores)"""
    config = await bot.get_config()
    config['role_id'] = role.id
    await bot.save_config(config)
    await ctx.send(
        f'✅ Role configurada: {role.name}. Usuários com esta role agora têm acesso às check-lists!'
    )


async def sync_user_checklists():
    """Sincroniza todas as check-lists dos usuários com as tarefas configuradas"""
    config = await bot.get_config()
    checklists = await bot.get_checklists()

    for user_id in checklists:
        old_checklist = checklists[user_id]
        new_checklist = {}

        for i, task in enumerate(config['tasks']):
            task_id = str(i)
            old_task = None

            for old_id, old_data in old_checklist.items():
                if old_data['description'] == task:
                    old_task = old_data
                    break

            if old_task:
                new_checklist[task_id] = {
                    'description': task,
                    'completed': old_task['completed']
                }
            else:
                new_checklist[task_id] = {
                    'description': task,
                    'completed': False
                }

        checklists[user_id] = new_checklist

    await bot.save_checklists(checklists)


@bot.command(name='add_task')
@commands.has_permissions(administrator=True)
async def add_task(ctx, *, task_description: str):
    """Adiciona uma tarefa à check-list global (apenas administradores)"""
    config = await bot.get_config()
    config['tasks'].append(task_description)
    await bot.save_config(config)
    await sync_user_checklists()
    await ctx.send(
        f'✅ Tarefa adicionada: "{task_description}"\n💡 Todas as check-lists foram atualizadas!'
    )


@bot.command(name='remover_tarefa')
@commands.has_permissions(administrator=True)
async def remove_task(ctx, task_number: int):
    """Remove uma tarefa da check-list global (apenas administradores)"""
    config = await bot.get_config()

    if task_number < 1 or task_number > len(config['tasks']):
        await ctx.send('❌ Número de tarefa inválido!')
        return

    removed_task = config['tasks'].pop(task_number - 1)
    await bot.save_config(config)
    await sync_user_checklists()
    await ctx.send(
        f'✅ Tarefa removida: "{removed_task}"\n💡 Todas as check-lists foram atualizadas!'
    )


@bot.command(name='listar_tarefas_admin')
@commands.has_permissions(administrator=True)
async def list_all_tasks(ctx):
    """Lista todas as tarefas configuradas (apenas administradores)"""
    config = await bot.get_config()

    if not config['tasks']:
        await ctx.send('📋 Nenhuma tarefa configurada ainda!')
        return

    embed = discord.Embed(title="📋 Tarefas Configuradas",
                          color=discord.Color.blue())

    tasks_text = '\n'.join(
        [f"{i+1}. {task}" for i, task in enumerate(config['tasks'])])
    embed.add_field(name="Tarefas Diárias", value=tasks_text, inline=False)

    await ctx.send(embed=embed)


@bot.command(name='NWDailies')
async def my_checklist(ctx):
    """Mostra sua check-list pessoal"""
    config = await bot.get_config()

    if config['role_id'] is None:
        await ctx.send(
            '❌ O administrador ainda não configurou a role para check-lists!')
        return

    role = ctx.guild.get_role(config['role_id'])
    if role not in ctx.author.roles:
        await ctx.send('❌ Você não tem permissão para acessar as check-lists!')
        return

    if not config['tasks']:
        await ctx.send('📋 Nenhuma tarefa configurada ainda!')
        return

    checklists = await bot.get_checklists()
    user_id = str(ctx.author.id)

    if user_id not in checklists:
        checklists[user_id] = {}

    old_checklist = checklists[user_id]
    new_checklist = {}

    for i, task in enumerate(config['tasks']):
        task_id = str(i)
        old_task = None

        for old_id, old_data in old_checklist.items():
            if old_data['description'] == task:
                old_task = old_data
                break

        if old_task:
            new_checklist[task_id] = {
                'description': task,
                'completed': old_task['completed']
            }
        else:
            new_checklist[task_id] = {'description': task, 'completed': False}

    checklists[user_id] = new_checklist
    await bot.save_checklists(checklists)

    user_checklist = new_checklist

    embed = discord.Embed(
        title=f"📋 New World Dailies",
        description=
        f"Use `!done <número>` para marcar uma tarefa como concluída",
        color=discord.Color.green())

    for task_id, task_data in user_checklist.items():
        status = "✅" if task_data['completed'] else "⬜"
        embed.add_field(
            name=f"{status} {int(task_id)+1}. {task_data['description']}",
            value="\u200b",
            inline=False)

    completed = sum(1 for t in user_checklist.values() if t['completed'])
    total = len(user_checklist)
    embed.set_footer(text=f"Progresso: {completed}/{total} tarefas concluídas")

    await ctx.send(embed=embed)


@bot.command(name='done')
async def mark_task(ctx, task_number: int):
    """Marca uma tarefa como concluída"""
    config = await bot.get_config()

    if config['role_id'] is None:
        await ctx.send(
            '❌ O administrador ainda não configurou a role para check-lists!')
        return

    role = ctx.guild.get_role(config['role_id'])
    if role not in ctx.author.roles:
        await ctx.send('❌ Você não tem permissão para acessar as check-lists!')
        return

    checklists = await bot.get_checklists()
    user_id = str(ctx.author.id)

    if user_id not in checklists:
        await ctx.send(
            '❌ Você ainda não tem uma check-list! Use `!NWDailies` primeiro.')
        return

    task_id = str(task_number - 1)

    if task_id not in checklists[user_id]:
        await ctx.send('❌ Número de tarefa inválido!')
        return

    checklists[user_id][task_id][
        'completed'] = not checklists[user_id][task_id]['completed']
    await bot.save_checklists(checklists)

    user_checklist = checklists[user_id]

    embed = discord.Embed(
        title=f"📋 New World Dailies",
        description=f"Use `!done <número>` para marcar outra tarefa",
        color=discord.Color.green())

    for tid, task_data in user_checklist.items():
        status = "✅" if task_data['completed'] else "⬜"
        embed.add_field(
            name=f"{status} {int(tid)+1}. {task_data['description']}",
            value="\u200b",
            inline=False)

    completed = sum(1 for t in user_checklist.values() if t['completed'])
    total = len(user_checklist)
    embed.set_footer(text=f"Progresso: {completed}/{total} tarefas concluídas")

    await ctx.send(embed=embed)


@bot.command(name='help_dailies')
async def help_command(ctx):
    """Mostra todos os comandos disponíveis"""
    embed = discord.Embed(
        title="📚 Comandos do Bot de Check-list",
        description="Aqui estão todos os comandos disponíveis:",
        color=discord.Color.blue())

    embed.add_field(name="👤 Comandos de Usuário",
                    value=("`!NWDailies` - Mostra sua check-list pessoal\n"
                           "`!done <número>` - Marca/desmarca uma tarefa\n"
                           "`!help_dailies` - Mostra esta mensagem"),
                    inline=False)

    embed.add_field(
        name="👑 Comandos de Administrador",
        value=
        ("`!configurar_role <@role>` - Define a role com acesso às check-lists\n"
         "`!add_task <descrição>` - Adiciona uma tarefa diária\n"
         "`!remover_tarefa <número>` - Remove uma tarefa\n"
         "`!listar_tarefas_admin` - Lista todas as tarefas configuradas"),
        inline=False)

    embed.set_footer(
        text="As check-lists resetam automaticamente à meia-noite!")

    await ctx.send(embed=embed)


async def main():
    token = await get_discord_token()
    await bot.start(token)


if __name__ == '__main__':
    asyncio.run(main())
