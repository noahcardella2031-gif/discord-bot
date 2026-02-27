import discord
from discord.ext import commands
import os
import asyncio
import json
from datetime import timedelta

# =====================
# BOT SETUP
# =====================
intents = discord.Intents.default()
intents.message_content = True 
intents.members = True          
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Data helpers
DATA_FILE = "bot_data.json"
def load_data():
    if not os.path.exists(DATA_FILE): return {"warnings": {}, "staff_points": {}}
    try:
        with open(DATA_FILE, "r") as f: return json.load(f)
    except: return {"warnings": {}, "staff_points": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f, indent=4)

async def log_event(guild, title, description, color=0x5865F2):
    # LOOKS FOR EXACT NAME: 📂-logs
    log_channel = discord.utils.get(guild.text_channels, name="📂-logs")
    if log_channel:
        embed = discord.Embed(title=title, description=description, color=color)
        await log_channel.send(embed=embed)

# =====================
# TICKET SYSTEM
# =====================
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Open Ticket", style=discord.ButtonStyle.green, custom_id="ticket_v3")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel_name = f"ticket-{interaction.user.name.lower()}"
        if discord.utils.get(interaction.guild.channels, name=channel_name):
            return await interaction.response.send_message("Ticket already open!", ephemeral=True)

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True)
        }
        channel = await interaction.guild.create_text_channel(channel_name, overwrites=overwrites)
        await interaction.response.send_message(f"Created: {channel.mention}", ephemeral=True)
        await log_event(interaction.guild, "Ticket Opened", f"👤 {interaction.user.mention}", 0x2ECC71)

# =====================
# COMMANDS
# =====================
@bot.command()
async def verify(ctx):
    role = discord.utils.get(ctx.guild.roles, name="Verified")
    if not role: return await ctx.send("❌ Create a role named `Verified`!")
    try:
        await ctx.author.add_roles(role)
        await ctx.send(f"✅ Verified!", delete_after=5)
        await log_event(ctx.guild, "User Verified", f"👤 {ctx.author.mention}", 0x2ECC71)
    except: await ctx.send("❌ Move my role to the TOP of the role list!")

@bot.command()
async def order(ctx, *, item="General Order"):
    channel_name = f"order-{ctx.author.name.lower()}"
    overwrites = {ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False), ctx.author: discord.PermissionOverwrite(read_messages=True)}
    channel = await ctx.guild.create_text_channel(channel_name, overwrites=overwrites)
    await ctx.send(f"Order channel created: {channel.mention}")
    await log_event(ctx.guild, "New Order", f"📦 {ctx.author.mention} ordered {item}")

@bot.command()
@commands.has_permissions(administrator=True)
async def promote(ctx, member: discord.Member):
    roles = ["Helper", "Moderator", "Admin"]
    for i, r_name in enumerate(roles):
        if discord.utils.get(member.roles, name=r_name):
            if i+1 < len(roles):
                new_role = discord.utils.get(ctx.guild.roles, name=roles[i+1])
                await member.add_roles(new_role)
                return await ctx.send(f"🎊 Promoted to {roles[i+1]}!")
    await ctx.send("Could not promote (Check role names/hierarchy)")

@bot.command()
async def cmds(ctx):
    embed = discord.Embed(title="📜 Command Menu", color=0x5865F2)
    embed.add_field(name="👥 Member", value="`!verify`, `!order`, `!stats`, `!ping` ", inline=False)
    embed.add_field(name="🛡️ Staff", value="`!warn`, `!timeout`, `!close`, `!clear` ", inline=False)
    embed.add_field(name="👑 Admin", value="`!promote`, `!addpoint`, `!panel` ", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def panel(ctx): await ctx.send(view=TicketView())

@bot.event
async def on_ready():
    bot.add_view(TicketView())
    print(f"🚀 Bot is live!")

bot.run(os.getenv("DISCORD_TOKEN"))
