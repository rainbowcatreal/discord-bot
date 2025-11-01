import discord
import aiohttp
import json
import sqlite3
import random
import typing
import scratchattach as sa
import ast
import operator as op
import math
import os
from discord.ext import commands
from dotenv import load_dotenv

# Токены
load_dotenv(dotenv_path='/storage/emulated/0/Android/data/ru.iiec.pydroid3/files/.env')
token = os.getenv('BOT_TOKEN')
cat_token = os.getenv('CATAPITOKEN')
dog_token = os.getenv('DOGAPITOKEN')

# Создание бота
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='a!', intents=intents, help_command=None, status=discord.Status.dnd, activity=discord.Activity(name='за сервером • a!help', type=discord.ActivityType.watching))

# Подключаем базу данных экономики
conn = sqlite3.connect('economy.db')
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    cash INTEGER DEFAULT 0,
    bank INTEGER DEFAULT 0
)
""")

# Переменные экономики
balemoji = '🪙'

# Функции для экономики
def open_account(user_id):
    cur.execute('INSERT OR IGNORE INTO users (user_id, cash, bank) VALUES (?, 0, 0)', (user_id,))
    conn.commit()

def get_balance(user_id):
    cur.execute('SELECT cash, bank FROM users WHERE user_id = ?', (user_id,))
    row = cur.fetchone()
    if not row:
        open_account(user_id)
        return (0, 0)
    return row
    
def update_balance(user_id, cash=None, bank=None):
    cur.execute('SELECT cash, bank FROM users WHERE user_id = ?', (user_id,))
    row = cur.fetchone()
    if row:
        newcash = cash if cash is not None else row[0]
        newbank = bank if bank is not None else row[1]
        cur.execute('UPDATE users SET cash = ?, bank = ? WHERE user_id = ?', (newcash, newbank, user_id,))
        conn.commit()

# Команды
@bot.hybrid_command(name='help', description='Отображает справку')
async def help(ctx):
    await ctx.reply('работает!', mention_author=False)

@bot.hybrid_command(name='cat', description='Присылает рандомного кота')
async def cat(ctx):
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://api.thecatapi.com/v1/images/search?api_key={cat_token}') as r:
            if r.status == 200:
                js = await r.json()
                image = js[0]['url']
                embed = discord.Embed()
                embed.set_image(url=image)
                await ctx.reply(embed=embed, mention_author=False)

@bot.hybrid_command(name='dog', description='Присылает рандомную собаку')
async def dog(ctx):
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://api.thedogapi.com/v1/images/search?api_key={dog_token}') as r:
            if r.status == 200:
                js = await r.json()
                image = js[0]['url']
                embed = discord.Embed()
                embed.set_image(url=image)
                await ctx.reply(embed=embed, mention_author=False)

@bot.hybrid_command(name='fox', description='Присылает рандомную лису')
async def fox(ctx):
    async with aiohttp.ClientSession() as session:
        async with session.get('https://randomfox.ca/floof/') as r:
            if r.status == 200:
                js = await r.json()
                image = js['image']
                embed = discord.Embed()
                embed.set_image(url=image)
                await ctx.reply(embed=embed, mention_author=False)
                
@bot.hybrid_command(name='ping', description='Проверить, работает ли бот')
async def ping(ctx):
    await ctx.reply(f'понг\n**Пинг:** {round(bot.latency * 1000)}мс', mention_author=False)

# Экономика
@bot.hybrid_command(name='balance', description='Показать свой баланс')
async def balance(ctx, member: typing.Optional[discord.Member] = None):
    member = member or ctx.author
    user_id = member.id
    cash, bank = get_balance(user_id)
    embed = discord.Embed(
        title=f'Баланс участника {member.display_name}'
    )
    embed.set_thumbnail(url=member.avatar)
    embed.add_field(name='Наличные', value=f'`{cash}` {balemoji}', inline=True)
    embed.add_field(name='В банке', value=f'`{bank}` {balemoji}', inline=True)
    await ctx.reply(embed=embed, mention_author=False)

@bot.hybrid_command(name='work', description='Поработать и заработать деньги')
async def work(ctx):
    user_id = ctx.author.id
    earnings = random.randint(50, 150)
    cash, bank = get_balance(user_id)
    update_balance(user_id, cash + earnings)
    await ctx.reply(f'Вы поработали и заработали `{earnings}` {balemoji}', mention_author=False)

@bot.hybrid_command(name='deposit', description='Положить деньги в банк')
async def deposit(ctx, amount: int):
    user_id = ctx.author.id
    cash, bank = get_balance(user_id)
    if cash < amount or amount <= 0:
        await ctx.reply('Неверная сумма', mention_author=False)
        return
    update_balance(user_id, cash - amount, bank + amount)
    await ctx.reply(f'Вы положили `{amount}` {balemoji} в банк', mention_author=False)

@bot.hybrid_command(name='withdraw', description='Снять деньги из банка')
async def withdraw(ctx, amount: int):
    user_id = ctx.author.id
    cash, bank = get_balance(user_id)
    if bank < amount or amount <= 0:
        await ctx.reply('Неверная сумма', mention_author=False)
        return
    update_balance(user_id, cash + amount, bank - amount)
    await ctx.reply(f'Вы сняли `{amount}` {balemoji} из банка', mention_author=False)

# Калькулятор
operators = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.Mod: op.mod,
    ast.USub: op.neg,
}

safe_names = {
    "pi": math.pi,
    "e": math.e,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "abs": abs,
    "round": round,
}

def safe_eval(expr):
    expr = expr.replace("%", "/100")

    def _eval(node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise TypeError("Недопустимое значение")

        elif isinstance(node, ast.Name):
            if node.id in safe_names:
                val = safe_names[node.id]
                if callable(val):
                    raise TypeError(f"Функция {node.id} требует аргументы")
                return val
            raise NameError(f"Неизвестная переменная '{node.id}'")

        elif isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in safe_names:
                raise NameError(f"Недопустимая функция '{getattr(node.func, 'id', '?')}'")
            func = safe_names[node.func.id]
            args = [_eval(arg) for arg in node.args]
            return func(*args)

        elif isinstance(node, ast.BinOp):
            if type(node.op) not in operators:
                raise TypeError("Недопустимая операция")
            left = _eval(node.left)
            right = _eval(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 100:
                raise ValueError("Слишком большая степень")
            result = operators[type(node.op)](left, right)
            if abs(result) > 1e100:
                raise ValueError("Результат слишком большой")
            return result

        elif isinstance(node, ast.UnaryOp):
            if type(node.op) not in operators:
                raise TypeError("Недопустимая операция")
            return operators[type(node.op)](_eval(node.operand))

        else:
            raise TypeError("Недопустимое выражение")

    node = ast.parse(expr, mode='eval').body
    return _eval(node)

@bot.hybrid_command(name='calc', dscription='Вычисляет выражение')
async def calc(ctx, *, expression: str):
    try:
        result = safe_eval(expression)
        await ctx.reply(f'```{result}```', mention_author=False)
    except Exception as e:
        embed = discord.Embed(
            title='Ошибка',
            description=f'```{e}```'
        )
        await ctx.reply(embed=embed, mention_author=False)
        
# Скретч команды
@bot.hybrid_command(name='user', description='Ищет пользователя на скретч')
async def user(ctx, *, username):
    user = sa.get_user(username)
    embed = discord.Embed(
        title=user.username
    )
    embed.add_field(name="Обо мне", value=discord.utils.escape_markdown(user.about_me), inline=False)
    embed.add_field(name="Над чем я работаю", value=discord.utils.escape_markdown(user.wiwo), inline=False)
    embed.set_thumbnail(url=user.icon_url)
    await ctx.reply(embed=embed, mention_author=False)

# Верификация аккаунта
@bot.hybrid_command(name='link', description='Привязать аккаунт скретча')
async def link(ctx, *, username):
    await ctx.reply('Готово', mention_author=False)

# Админские команды
@bot.hybrid_command(name='say', description='Написать сообщение под именем бота')
@commands.has_permissions(manage_guild=True)
async def say(ctx, *, msg):
	await ctx.send(msg)
	await ctx.message.delete()

# События
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Бот {bot.user} теперь включён')

# Разрешить вебхукам использовать команды
@bot.event
async def on_message(message):
    if message.webhook_id:
        if message.content.startswith('a!'):
            ctx = await bot.get_context(message)
            if ctx.valid:
                await bot.invoke(ctx)
            else:
                await message.channel.send('erm,,, incorrect')
    else:
        await bot.process_commands(message)

# Запуск бота
bot.run(token)