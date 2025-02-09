import os
import json
from discord import app_commands
from discord.ext import commands, tasks
from discord import app_commands
import discord
import requests
import random
import asyncio
from dotenv import load_dotenv

client = commands.Bot(command_prefix="somerandomshit", intents=discord.Intents.all())
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")


LINKED_USERNAMES_PATH = "/home/neko/discord-bots/nutone/linked_usernames.json"
SERVER_IDS_PATH = "/home/neko/discord-bots/nutone/server_ids.json"
LINKED_UIDS_PATH = "/home/neko/discord-bots/nutone/linked_uids.json"
VALID_USERNAMES_PATH = "/home/neko/discord-bots/nutone/valid_usernames.json"
TEMP_USERNAMES_PATH = "/home/neko/discord-bots/nutone/temp_usernames.json"
HIDDEN_PATH = "/home/neko/discord-bots/nutone/hidden.json"
ADMIN_ROLE_PATH = "/home/neko/discord-bots/nutone/admin_role.json"


linked_usernames = {}
server_ids = {}
linked_uids = {}
valid_usernames = {}
temp_usernames = {}
hidden_status = {}
admin_roles = {}


def load_data():
    global linked_usernames, server_ids, linked_uids, valid_usernames, temp_usernames, hidden_status, admin_roles
    if os.path.exists(LINKED_USERNAMES_PATH):
        with open(LINKED_USERNAMES_PATH, 'r') as f:
            linked_usernames.update(json.load(f))
    if os.path.exists(SERVER_IDS_PATH):
        with open(SERVER_IDS_PATH, 'r') as f:
            server_ids.update(json.load(f))
    if os.path.exists(LINKED_UIDS_PATH):
        with open(LINKED_UIDS_PATH, 'r') as f:
            linked_uids.update(json.load(f))
    if os.path.exists(VALID_USERNAMES_PATH):
        with open(VALID_USERNAMES_PATH, 'r') as f:
            valid_usernames.update(json.load(f))
    if os.path.exists(TEMP_USERNAMES_PATH):
        with open(TEMP_USERNAMES_PATH, 'r') as f:
            temp_usernames.update(json.load(f))
    if os.path.exists(HIDDEN_PATH):
        with open(HIDDEN_PATH, 'r') as f:
            hidden_status.update(json.load(f))
    if os.path.exists(ADMIN_ROLE_PATH):
        with open(ADMIN_ROLE_PATH, 'r') as f:
            admin_roles.update(json.load(f))


def save_data():
    with open(LINKED_USERNAMES_PATH, 'w') as f:
        json.dump(linked_usernames, f)
    with open(SERVER_IDS_PATH, 'w') as f:
        json.dump(server_ids, f)
    with open(LINKED_UIDS_PATH, 'w') as f:
        json.dump(linked_uids, f)
    with open(VALID_USERNAMES_PATH, 'w') as f:
        json.dump(valid_usernames, f)
    with open(TEMP_USERNAMES_PATH, 'w') as f:
        json.dump(temp_usernames, f)
    with open(HIDDEN_PATH, 'w') as f:
        json.dump(hidden_status, f)
    with open(ADMIN_ROLE_PATH, 'w') as f:
        json.dump(admin_roles, f)


def delete_temp_usernames():
    if os.path.exists(TEMP_USERNAMES_PATH):
        os.remove(TEMP_USERNAMES_PATH)

@client.event
async def on_ready():
    print(f'Bot is ready. Logged in as {client.user}')
    load_data()
    delete_temp_usernames()
    await client.tree.sync()
    update_status.start()

status_index = 0
statuses = [
    lambda total_members, total_guilds: discord.Game(name=f"I'm looking at the stats of {total_members} discord users and in {total_guilds} discord servers"),
    lambda total_members, total_guilds: discord.Game(name="Sending Stats of players to https://nutone.okudai.dev"),
    lambda total_members, total_guilds: discord.Game(name="Looking at Stats of players on https://nutone.okudai.dev")
]

@tasks.loop(minutes=1)
async def update_status():
    global status_index
    total_guilds = len(client.guilds)
    unique_members = set()
    for guild in client.guilds:
        for member in guild.members:
            unique_members.add(member.id)
    total_members = len(unique_members)
    
    status = statuses[status_index](total_members, total_guilds)
    await client.change_presence(activity=status)
    
    status_index = (status_index + 1) % len(statuses)

@client.event
async def on_guild_join(guild):
    guild_id = str(guild.id)
    hidden_status[guild_id] = True
    save_data()

@client.event
async def on_command_error(ctx, error):
    await ctx.send(f'An error occurred: {error}', ephemeral=True)

def is_nutone_contributor(ctx):
    if ctx.guild.owner_id == ctx.user.id:
        return True
    if str(ctx.user) == "fvnkhead":
        return True
    if str(ctx.user) == "okudai":
        return True
    if str(ctx.user) == "nekouwugamerfnf":
        return True
    return False

def is_admin(ctx):
    guild_id = str(ctx.guild.id)
    role_id = admin_roles.get(guild_id)
    if role_id and any(role.id == role_id for role in ctx.user.roles):
        return True
    if is_nutone_contributor:
        return True
    return False

async def fetch_stats(interaction, player, server_id, ephemeral):
    if server_id == "All":
        url = f'https://nutone.okudai.dev/players/{player}'
    else:
        url = f'https://nutone.okudai.dev/players/{player}?server_id={server_id}'

    try:
        r = await asyncio.wait_for(asyncio.to_thread(requests.get, url), timeout=10.0)
        r.raise_for_status()
    except asyncio.TimeoutError:
        await interaction.followup.send(f"Request timed out while fetching stats for server ID: {server_id}.", ephemeral=ephemeral)
        return None
    except requests.exceptions.HTTPError as e:
        if r.status_code == 404:
            await interaction.followup.send(f"No stats found for player: {player} on server: {server_id}", ephemeral=ephemeral)
        else:
            await interaction.followup.send(f"An error occurred: {e}", ephemeral=ephemeral)
        return None
    except requests.exceptions.RequestException as e:
        await interaction.followup.send(f"An error occurred: {e}", ephemeral=ephemeral)
        return None

    try:
        data = r.json()
    except ValueError:
        await interaction.followup.send("Error: Received invalid JSON response", ephemeral=ephemeral)
        return None

    uid = data.get('uid')
    if uid:
        valid_usernames[player] = True
        linked_uids[player] = uid
        save_data()

    return data

async def fetch_uid(interaction, player, ephemeral):
    url = f'https://nutone.okudai.dev/players/{player}'
    try:
        r = await asyncio.wait_for(asyncio.to_thread(requests.get, url), timeout=10.0)
        r.raise_for_status()
    except asyncio.TimeoutError:
        await interaction.followup.send("Request timed out while fetching UID.", ephemeral=ephemeral)
        return 'N/A'
    except requests.exceptions.HTTPError:
        return 'N/A'
    except requests.exceptions.RequestException as e:
        await interaction.followup.send(f"An error occurred: {e}", ephemeral=ephemeral)
        return 'N/A'

    try:
        data = r.json()
    except ValueError:
        await interaction.followup.send("Error: Received invalid JSON response", ephemeral=ephemeral)
        return 'N/A'

    uid = data.get('uid', 'N/A')
    return uid

@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
@client.tree.command(name="stats", description="Search for a player's stats on all servers or by server")
async def stats(interaction: discord.Interaction, player: str = None, server_id: str = None):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return

    guild_id = str(interaction.guild.id)
    ephemeral = hidden_status.get(guild_id, True)

    await interaction.response.defer(ephemeral=ephemeral)

    if player is None:
        discord_user = str(interaction.user)
        player = linked_usernames.get(discord_user, temp_usernames.get(discord_user, discord_user))

    load_data()
    available_server_ids = server_ids.get(guild_id, []) + ["All"]

    if server_id:
        data = await fetch_stats(interaction, player, server_id, ephemeral)
        if data:
            total_stats = data.get('total', {})
            kills = total_stats.get('kills', 'N/A')
            deaths = total_stats.get('deaths', 'N/A')
            kd_ratio = total_stats.get('kd', 'N/A')

            embed = discord.Embed(
                title=f"Stats for {player} on server {server_id}",
                color=discord.Color.blue()
            )
            embed.add_field(name="Kills", value=kills, inline=True)
            embed.add_field(name="Deaths", value=deaths, inline=True)
            embed.add_field(name="K/D Ratio", value=kd_ratio, inline=True)

            await interaction.followup.send(embed=embed, ephemeral=ephemeral)
    else:
        for sid in available_server_ids:
            data = await fetch_stats(interaction, player, sid, ephemeral)
            if data:
                total_stats = data.get('total', {})
                kills = total_stats.get('kills', 'N/A')
                deaths = total_stats.get('deaths', 'N/A')
                kd_ratio = total_stats.get('kd', 'N/A')

                embed = discord.Embed(
                    title=f"Stats for {player} on server {sid}",
                    color=discord.Color.blue()
                )
                embed.add_field(name="Kills", value=kills, inline=True)
                embed.add_field(name="Deaths", value=deaths, inline=True)
                embed.add_field(name="K/D Ratio", value=kd_ratio, inline=True)

                await interaction.followup.send(embed=embed, ephemeral=ephemeral)

@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
@client.tree.command(name="kd", description="Get the K/D ratio of a linked game username")
async def kd(interaction: discord.Interaction, player: str = None, server_id: str = None):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return

    guild_id = str(interaction.guild.id)
    ephemeral = hidden_status.get(guild_id, True)

    await interaction.response.defer(ephemeral=ephemeral)

    if player is None:
        discord_user = str(interaction.user)
        player = linked_usernames.get(discord_user, temp_usernames.get(discord_user, discord_user))

    load_data()
    available_server_ids = server_ids.get(guild_id, []) + ["All"]

    if server_id:
        data = await fetch_stats(interaction, player, server_id, ephemeral)
        if data:
            total_stats = data.get('total', {})
            kd_ratio = total_stats.get('kd', 'N/A')

            embed = discord.Embed(
                title=f"K/D Ratio for {player} on server {server_id}",
                color=discord.Color.blue()
            )
            embed.add_field(name="K/D Ratio", value=kd_ratio, inline=True)

            await interaction.followup.send(embed=embed, ephemeral=ephemeral)
    else:
        for sid in available_server_ids:
            data = await fetch_stats(interaction, player, sid, ephemeral)
            if data:
                total_stats = data.get('total', {})
                kd_ratio = total_stats.get('kd', 'N/A')

                embed = discord.Embed(
                    title=f"K/D Ratio for {player} on server {sid}",
                    color=discord.Color.blue()
                )
                embed.add_field(name="K/D Ratio", value=kd_ratio, inline=True)

                await interaction.followup.send(embed=embed, ephemeral=ephemeral)

@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
@client.tree.command(name="uid", description="Get the UID of a linked game username")
async def uid(interaction: discord.Interaction, player: str = None):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return

    guild_id = str(interaction.guild.id)
    ephemeral = hidden_status.get(guild_id, True)

    await interaction.response.defer(ephemeral=ephemeral)

    if player is None:
        discord_user = str(interaction.user)
        player = linked_usernames.get(discord_user, temp_usernames.get(discord_user, discord_user))

    if player in linked_uids:
        uid = linked_uids[player]
    else:
        uid = await fetch_uid(interaction, player, ephemeral)
        if uid != 'N/A':
            linked_uids[player] = uid
            save_data()

    await interaction.followup.send(f'Game Username: {player}\nUID: {uid}', ephemeral=ephemeral)

@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
@client.tree.command(name="link", description="Link a game username to your Discord account")
async def link(interaction: discord.Interaction, game_username: str):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    discord_user = str(interaction.user)
    ephemeral = hidden_status.get(str(interaction.guild.id), True)

    if game_username in valid_usernames:
        valid = True
        uid = linked_uids.get(game_username, 'N/A')
    else:
        url = f'https://nutone.okudai.dev/players/{game_username}'
        try:
            r = requests.get(url)
            r.raise_for_status()
            valid = True
        except requests.exceptions.HTTPError:
            valid = False
        except requests.exceptions.RequestException:
            await interaction.followup.send("An error occurred while checking the username validity.", ephemeral=ephemeral)
            return

        if valid:
            uid = await fetch_uid(interaction, game_username, ephemeral)
            if uid != 'N/A':
                linked_uids[game_username] = uid
            valid_usernames[game_username] = valid

    linked_usernames[discord_user] = game_username
    temp_usernames[discord_user] = game_username
    save_data()
    message = f'Game username "{game_username}" linked to Discord account "{discord_user}".'
    if not valid:
        message += " However, the username is not valid on Nutone."
    await interaction.followup.send(message, ephemeral=ephemeral)

@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
@client.tree.command(name="unlink", description="Unlink the linked game username from your Discord account")
async def unlink(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    discord_user = str(interaction.user)
    ephemeral = hidden_status.get(str(interaction.guild.id), True)

    if discord_user in linked_usernames:
        game_username = linked_usernames[discord_user]
        del linked_usernames[discord_user]
        if game_username in linked_uids:
            del linked_uids[game_username]
        save_data()
        await interaction.followup.send(f'Unlinked the game username "{game_username}" from Discord account "{discord_user}".', ephemeral=ephemeral)
    else:
        await interaction.followup.send(f'No game username is linked to your Discord account "{discord_user}".', ephemeral=ephemeral)

@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
@client.tree.command(name="gamename", description="Show the linked game username and your Discord account username")
async def gamename(interaction: discord.Interaction, user: discord.User = None):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return
      
    guild_id = str(interaction.guild.id)
    ephemeral = hidden_status.get(guild_id, True)
    await interaction.response.defer(ephemeral=ephemeral)
    
    if user is None:
        discord_user = str(interaction.user)
    else:
        discord_user = str(user)

    game_username = linked_usernames.get(discord_user, temp_usernames.get(discord_user, None))
    if not game_username:
        if discord_user in valid_usernames:
            game_username = discord_user
        else:
            url = f'https://nutone.okudai.dev/players/{discord_user}'
            try:
                r = requests.get(url)
                r.raise_for_status()
                valid = True
            except requests.exceptions.HTTPError:
                valid = False
            except requests.exceptions.RequestException:
                await interaction.response.send_message("An error occurred while checking the username validity.", ephemeral=True)
                return

            if valid:
                valid_usernames[discord_user] = True
                game_username = discord_user
                save_data()
            else:
                game_username = "N/A"

    await interaction.followup.send(f'Discord Username: {discord_user}\nGame Username: {game_username}', ephemeral=ephemeral)

@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
@client.tree.command(name="roll", description="Roll a number between 1 and 100")
async def roll(interaction: discord.Interaction, number: int = None):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return

    guild_id = str(interaction.guild.id)
    ephemeral = hidden_status.get(guild_id, True)

    if number is None:
        max_number = 100
    else:
        if number < 1:
            await interaction.response.send_message("Number must be at least 1.", ephemeral=True)
            return
        elif number > 100:
            await interaction.response.send_message("Number must be at most 100.", ephemeral=True)
            return
        max_number = number

    roll_result = random.randint(1, max_number)
    await interaction.response.send_message(f'You rolled: {roll_result} (Max: {max_number})', ephemeral=ephemeral)

@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
@client.tree.command(name="ping", description="Check the bot's latency")
async def ping(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return
    latency = client.latency
    guild_id = str(interaction.guild.id)
    ephemeral = hidden_status.get(guild_id, True)

    await interaction.response.send_message(f'Pong! Latency: {latency * 1000:.2f} ms', ephemeral=ephemeral)

@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
@client.tree.command(name="help", description="Show the help message with available commands")
async def help(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return
    embed = discord.Embed(
        title="Help - Available Commands",
        color=discord.Color.green()
    )
    embed.add_field(
        name="/stats [player] [server_id]",
        value="Search for a player's stats on all servers or by server. If no player is specified, it will use your linked username or Discord username. Optionally specify a server ID.",
        inline=False
    )
    embed.add_field(
        name="/kd [player] [server_id]",
        value="Get the K/D ratio of a linked game username. If no player is specified, it will use your linked username or Discord username. Optionally specify a server ID.",
        inline=False
    )
    embed.add_field(
        name="/uid [player]",
        value="Get the UID of a linked game username on 'All' the servers. If no player is specified, it will use your linked username or Discord username.",
        inline=False
    )
    embed.add_field(
        name="/roll [number]",
        value="Roll a number between 1 and 100.",
        inline=False
    )
    embed.add_field(
        name="/ping",
        value="Check the bot's latency.",
        inline=False
    )
    embed.add_field(
        name="/rps [choice]",
        value="Play Rock-Paper-Scissors against the bot. Choose rock, paper, or scissors.",
        inline=False
    )
    embed.add_field(
        name="/help",
        value="Show this help message with available commands.",
        inline=False
    )
    embed.add_field(
        name="/link [game_username]",
        value="Link a game username to your Discord account.",
        inline=False
    )
    embed.add_field(
        name="/unlink",
        value="Unlink the linked game username from your Discord account.",
        inline=False
    )
    embed.add_field(
        name="/gamename [user]",
        value="Show the linked game username and your Discord account username. Optionally specify a user to see their linked game username.",
        inline=False
    )
    embed.add_field(
        name="/add_server_id [server_id]",
        value="Associate a server-specific ID with this Discord server. Only the server owner can use this command.",
        inline=False
    )
    embed.add_field(
        name="/remove_server_id [server_id]",
        value="Remove a server-specific ID from this Discord server. Only the server owner can use this command.",
        inline=False
    )
    embed.add_field(
        name="/server_id",
        value="Display the current server IDs being used. Always includes 'All'.",
        inline=False
    )
    embed.add_field(
        name="/hidden",
        value="Hide the bot's messages from everyone. Only the server owner can use this command.",
        inline=False
    )
    embed.add_field(
        name="/unhidden",
        value="Unhide the bot's messages from everyone. Only the server owner can use this command.",
        inline=False
    )
    embed.add_field(
        name="/setadminrole [role]",
        value="Set a role that can use admin commands. Only the server owner can use this command.",
        inline=False
    )

    guild_id = str(interaction.guild.id)
    ephemeral = hidden_status.get(guild_id, True)
    await interaction.response.send_message(embed=embed, ephemeral=ephemeral)

@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
@client.tree.command(name="add_server_id", description="Associate a server-specific ID with this Discord server")
async def add_server_id(interaction: discord.Interaction, server_id: str):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=hidden_status.get(str(interaction.guild.id), True))
        return

    if not is_admin(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=hidden_status.get(str(interaction.guild.id), True))
        return

    guild_id = str(interaction.guild.id)
    load_data()
    if guild_id not in server_ids:
        server_ids[guild_id] = []
    if server_id not in server_ids[guild_id]:
        server_ids[guild_id].append(server_id)
        save_data()
        await interaction.response.send_message(f'Server-specific ID "{server_id}" associated with this Discord server.', ephemeral=hidden_status.get(str(interaction.guild.id), True))
    else:
        await interaction.response.send_message(f'Server-specific ID "{server_id}" is already associated with this Discord server.', ephemeral=hidden_status.get(str(interaction.guild.id), True))

@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
@client.tree.command(name="remove_server_id", description="Remove a server-specific ID from this Discord server")
async def remove_server_id(interaction: discord.Interaction, server_id: str):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=hidden_status.get(str(interaction.guild.id), True))
        return
    
    if not is_admin(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=hidden_status.get(str(interaction.guild.id), True))
        return

    guild_id = str(interaction.guild.id)
    load_data()
    if guild_id in server_ids and server_id in server_ids[guild_id]:
        server_ids[guild_id].remove(server_id)
        save_data()
        await interaction.response.send_message(f'Server-specific ID "{server_id}" removed from this Discord server.', ephemeral=hidden_status.get(str(interaction.guild.id), True))
    else:
        await interaction.response.send_message(f'Server-specific ID "{server_id}" is not associated with this Discord server.', ephemeral=hidden_status.get(str(interaction.guild.id), True))

@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
@client.tree.command(name="server_id", description="Display the current server IDs being used")
async def server_id(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=hidden_status.get(str(interaction.guild.id), True))
        return

    guild_id = str(interaction.guild.id)
    load_data()
    ids = server_ids.get(guild_id, []) + ["All"]
    await interaction.response.send_message(f'The current server IDs being used are: {", ".join(ids)}', ephemeral=hidden_status.get(str(interaction.guild.id), True))

@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
@client.tree.command(name="rps", description="Play Rock-Paper-Scissors against the bot")
async def rps(interaction: discord.Interaction, choice: str):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=hidden_status.get(str(interaction.guild.id), True))
        return

    choices = ["rock", "paper", "scissors"]
    if choice.lower() not in choices:
        await interaction.response.send_message("Invalid choice. Please choose rock, paper, or scissors.", ephemeral=hidden_status.get(str(interaction.guild.id), True))
        return

    bot_choice = random.choice(choices)
    result = ""
    if choice == bot_choice:
        result = "It's a tie!"
    elif (choice == "rock" and bot_choice == "scissors") or \
            (choice == "scissors" and bot_choice == "paper") or \
            (choice == "paper" and bot_choice == "rock"):
        result = "You win!"
    else:
        result = "You lose!"

    embed = discord.Embed(
        title="Rock-Paper-Scissors",
        color=discord.Color.blue()
    )
    embed.add_field(name="Your Choice", value=choice, inline=True)
    embed.add_field(name="Bot's Choice", value=bot_choice, inline=True)
    embed.add_field(name="Result", value=result, inline=True)

    await interaction.response.send_message(embed=embed, ephemeral=hidden_status.get(str(interaction.guild.id), True))

@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
@client.tree.command(name="hidden", description="Hide the bot's messages from everyone")
async def hidden(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return

    if not is_admin(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    guild_id = str(interaction.guild.id)
    hidden_status[guild_id] = True
    save_data()
    await interaction.response.send_message("Bot messages are now hidden from everyone.", ephemeral=True)

@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
@client.tree.command(name="unhidden", description="Unhide the bot's messages from everyone")
async def unhidden(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return

    if not is_admin(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    guild_id = str(interaction.guild.id)
    hidden_status[guild_id] = False
    save_data()
    await interaction.response.send_message("Bot messages are now visible to everyone.", ephemeral=True)

@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
@client.tree.command(name="setadminrole", description="Set a role that can use admin commands")
async def setadminrole(interaction: discord.Interaction, role: discord.Role):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return

    if not is_nutone_contributor:
        await interaction.response.send_message("Only the server owner or nutone contributors can use this command.", ephemeral=True)
        return

    guild_id = str(interaction.guild.id)
    admin_roles[guild_id] = role.id
    save_data()
    await interaction.response.send_message(f'The role "{role.name}" is now set as the admin role for this server.', ephemeral=True)

@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
@client.tree.command(name="uiduser", description="Get the UID of a specific Discord user")
async def uiduser(interaction: discord.Interaction, user: discord.User):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return

    guild_id = str(interaction.guild.id)
    ephemeral = hidden_status.get(guild_id, True)

    await interaction.response.defer(ephemeral=ephemeral)
    
    discord_user = str(user)
    player = linked_usernames.get(discord_user, temp_usernames.get(discord_user, discord_user))

    if player in linked_uids:
        uid = linked_uids[player]
    else:
        uid = await fetch_uid(interaction, player, ephemeral)
        if uid != 'N/A':
            linked_uids[player] = uid
            save_data()

    await interaction.followup.send(f'Discord User: {discord_user}\nGame Username: {player}\nUID: {uid}', ephemeral=ephemeral)

@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
@client.tree.command(name="kduser", description="Get the K/D ratio of a specific Discord user")
async def kduser(interaction: discord.Interaction, user: discord.User, server_id: str = None):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return

    guild_id = str(interaction.guild.id)
    ephemeral = hidden_status.get(guild_id, True)

    await interaction.response.defer(ephemeral=ephemeral)

    discord_user = str(user)
    player = linked_usernames.get(discord_user, temp_usernames.get(discord_user, discord_user))

    load_data()
    available_server_ids = server_ids.get(guild_id, []) + ["All"]

    if server_id:
        data = await fetch_stats(interaction, player, server_id, ephemeral)
        if data:
            total_stats = data.get('total', {})
            kd_ratio = total_stats.get('kd', 'N/A')

            embed = discord.Embed(
                title=f"K/D Ratio for {player} on server {server_id}",
                color=discord.Color.blue()
            )
            embed.add_field(name="K/D Ratio", value=kd_ratio, inline=True)

            await interaction.followup.send(embed=embed, ephemeral=ephemeral)
    else:
        for sid in available_server_ids:
            data = await fetch_stats(interaction, player, sid, ephemeral)
            if data:
                total_stats = data.get('total', {})
                kd_ratio = total_stats.get('kd', 'N/A')

                embed = discord.Embed(
                    title=f"K/D Ratio for {player} on server {sid}",
                    color=discord.Color.blue()
                )
                embed.add_field(name="K/D Ratio", value=kd_ratio, inline=True)

                await interaction.followup.send(embed=embed, ephemeral=ephemeral)


client.remove_command('help')

client.run(TOKEN)
