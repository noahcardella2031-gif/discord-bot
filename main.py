import discord
from discord.ext import commands
import os
import asyncio
import json
from datetime import timedelta

# =====================
# DATA STORAGE
# =====================
DATA_FILE = "bot_data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"warnings": {}, "staff_points": {}}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"warnings": {}, "staff_points": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# =====================
# BOT SETUP
# =====================
intents = discord.Intents.default()
intents.message_content = True  # Required for !cmds and !verify
intents.members = True          # Required for giving roles
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

async def log_event(guild, title, description, color=0x5865F2):
    """Logs actions to '📂-logs' channel"""
    log_channel = discord.utils.get(guild.text_channels, name="📂-logs")
    if log_channel:
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_timestamp()
        await log_channel.send(embed=embed)

# =====================
# PERSISTENT TICKET VIEW
# =====================
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Open Ticket", style=discord.ButtonStyle.green, custom_id="persistent_ticket_v2")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user
        channel_name = f"ticket-{user.name.lower().replace(' ', '-')}"

        if discord.utils.get(guild.channels, name=channel_name):
            return await interaction.response.send_message("You already have an open ticket!", ephemeral=True)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        channel = await guild.create_text_channel(channel_name, overwrites=overwrites)
        embed = discord.Embed(title="🎟 Support Ticket", description=f"Welcome {user.mention}. Staff will assist you shortly.", color=0x2ECC71)
        await channel.send(embed=embed)
        await interaction.response.send_message(f"Ticket created: {channel.mention}", ephemeral=True)
        await log_event(guild, "Ticket Opened", f"👤 **User:** {user.mention}\n📂 **Channel:** {channel.mention}", 0x2ECC71)

# =====================
# EVENTS & COMMANDS
# =====================
@bot.event
async def on_ready():
    bot.add_view(TicketView())
    print(f"✅ {bot.user} is online and connected!")

@bot.command()
async def verify(ctx):
    role = discord.utils.get(ctx.guild.roles, name="Verified")
    if role is None:
        return await ctx.send("❌ Error: Create a role named `Verified` first.")
    
    try:
        await ctx.author.add_roles(role)
        await ctx.send(f"✅ {ctx.author.mention}, you are now verified!", delete_after=5)
        await log_event(ctx.guild, "User Verified", f"👤 {ctx.author.mention}", 0x2ECC71)
    except discord.Forbidden:
        await ctx.send("❌ Error: Move my role to the top of the role list!")

@bot.command()
async def cmds(ctx):
    embed = discord.Embed(title="📜 Command Menu", color=0x5865F2)
    embed.add_field(name="👥 Member", value="`!verify`, `!stats`, `!ping` ", inline=False)
    embed.add_field(name="🛡️ Staff", value="`!warn`, `!timeout`, `!close`, `!clear` ", inline=False)
    embed.add_field(name="👑 Admin", value="`!promote`, `!addpoint`, `!panel` ", inline=False)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)

@bot.command()
async def close(ctx):
    if "ticket-" in ctx.channel.name:
        await ctx.send("Closing in 5 seconds...")
        await asyncio.sleep(5)
        await ctx.channel.delete()

@bot.command()
async def panel(ctx):
    embed = discord.Embed(title="Support Panel", description="Click below to open a ticket.", color=0x5865F2)
    await ctx.send(embed=embed, view=TicketView())

# =====================
# RUN THE BOT
# =====================
token = os.getenv("DISCORD_TOKEN")
if token:
    bot.run(token)
else:
    print("❌ Error: Missing DISCORD_TOKEN in Railway Variables.")
