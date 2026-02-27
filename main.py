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
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

async def log_event(guild, title, description, color=0x5865F2):
    """Logs actions to a channel named '📂-logs'"""
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

    @discord.ui.button(label="Open Ticket", style=discord.ButtonStyle.green, custom_id="persistent_ticket_v1")
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
        
        embed = discord.Embed(
            title="🎟 Support Ticket", 
            description=f"Welcome {user.mention}. Staff will assist you shortly.\nUse `!close` to end this ticket.", 
            color=0x2ECC71
        )
        await channel.send(embed=embed)
        await interaction.response.send_message(f"Ticket created: {channel.mention}", ephemeral=True)
        await log_event(guild, "Ticket Opened", f"👤 **User:** {user.mention}\n📂 **Channel:** {channel.mention}", 0x2ECC71)

# =====================
# EVENTS
# =====================
@bot.event
async def on_ready():
    bot.add_view(TicketView())
    print(f"✅ Logged in as {bot.user}")

# =====================
# MODERATION & STAFF
# =====================
@bot.command()
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member, *, reason="No reason provided"):
    data = load_data()
    uid = str(member.id)
    if uid not in data["warnings"]: data["warnings"][uid] = []
    
    data["warnings"][uid].append({"reason": reason, "mod": ctx.author.name})
    save_data(data)
    
    count = len(data["warnings"][uid])
    await ctx.send(f"⚠️ {member.mention} has been warned ({count}/3).")
    
    log_msg = f"👤 **User:** {member.mention}\n🛡️ **Mod:** {ctx.author.mention}\n📝 **Reason:** {reason}"
    if count >= 3: log_msg += "\n🚨 **USER HAS REACHED 3 WARNINGS!**"
    
    await log_event(ctx.guild, "User Warning", log_msg, 0xE74C3C)

@bot.command()
@commands.has_permissions(moderate_members=True)
async def timeout(ctx, member: discord.Member, minutes: int, *, reason="No reason provided"):
    duration = timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)
    await ctx.send(f"🔇 {member.name} timed out for {minutes}m.")
    await log_event(ctx.guild, "User Timeout", f"👤 **User:** {member.mention}\n⏰ **Length:** {minutes}m", 0xF1C40F)

@bot.command()
@commands.has_permissions(administrator=True)
async def promote(ctx, member: discord.Member):
    roles_list = ["Helper", "Moderator", "Admin"]
    current_index = -1
    for i, r_name in enumerate(roles_list):
        if discord.utils.get(member.roles, name=r_name): current_index = i
            
    if current_index + 1 >= len(roles_list):
        return await ctx.send("User is already at the highest staff rank!")

    new_role_name = roles_list[current_index + 1]
    role = discord.utils.get(ctx.guild.roles, name=new_role_name)
    
    if role:
        await member.add_roles(role)
        await ctx.send(f"🎊 {member.mention} promoted to **{new_role_name}**!")
        await log_event(ctx.guild, "Staff Promotion", f"👤 **Staff:** {member.mention}\n📈 **Rank:** {new_role_name}", 0x9B59B6)

# =====================
# UTILITY
# =====================
@bot.command()
async def cmds(ctx):
    embed = discord.Embed(title="📜 Command Menu", color=0x5865F2)
    embed.add_field(name="👥 Member", value="`!verify`, `!stats`, `!ping` ", inline=False)
    embed.add_field(name="🛡️ Staff", value="`!warn`, `!timeout`, `!close`, `!clear` ", inline=False)
    embed.add_field(name="👑 Admin", value="`!promote`, `!addpoint`, `!panel` ", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def close(ctx):
    if "ticket-" in ctx.channel.name or "order-" in ctx.channel.name:
        await log_event(ctx.guild, "Channel Closed", f"📂 **Name:** {ctx.channel.name}\n🛡️ **By:** {ctx.author.mention}", 0x95A5A6)
        await ctx.send("Deleting channel in 5s...")
        await asyncio.sleep(5)
        await ctx.channel.delete()

@bot.command()
async def panel(ctx):
    embed = discord.Embed(title="Support Panel", description="Click the button to open a ticket.", color=0x5865F2)
    await ctx.send(embed=embed, view=TicketView())

@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 Pong! {round(bot.latency * 1000)}ms")

# =====================
# RUN THE BOT
# =====================
token = os.getenv("DISCORD_TOKEN") # Railway looks for this variable name

if token:
    bot.run(token)
else:
    print("❌ CRITICAL ERROR: DISCORD_TOKEN variable not found in Railway Settings.")
