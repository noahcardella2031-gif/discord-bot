import discord
from discord.ext import commands
import os
import asyncio
import json
from datetime import timedelta

# =====================
# BOT SETUP & INTENTS
# =====================
intents = discord.Intents.default()
intents.message_content = True  # MUST BE ON IN DEV PORTAL
intents.members = True          # MUST BE ON IN DEV PORTAL
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

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
    except:
        return {"warnings": {}, "staff_points": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

async def log_event(guild, title, description, color=0x5865F2):
    """Sends logs to a channel named exactly 📂-logs"""
    log_channel = discord.utils.get(guild.text_channels, name="📂-logs")
    if log_channel:
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_timestamp()
        await log_channel.send(embed=embed)

# =====================
# TICKET SYSTEM (Persistent)
# =====================
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Open Ticket", style=discord.ButtonStyle.green, custom_id="persistent_ticket_final")
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
# MEMBER COMMANDS
# =====================
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
        await ctx.send("❌ Permission Error: Move my role to the TOP of the role list!")

@bot.command()
async def order(ctx, *, item="General Order"):
    channel_name = f"order-{ctx.author.name.lower()}"
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        ctx.guild.me: discord.PermissionOverwrite(read_messages=True)
    }
    channel = await ctx.guild.create_text_channel(channel_name, overwrites=overwrites)
    await ctx.send(f"📦 Order channel created: {channel.mention}")
    await log_event(ctx.guild, "New Order", f"👤 {ctx.author.mention} ordered: **{item}**", 0xF1C40F)

@bot.command()
async def stats(ctx, member: discord.Member = None):
    member = member or ctx.author
    data = load_data()
    pts = data["staff_points"].get(str(member.id), 0)
    warns = len(data["warnings"].get(str(member.id), []))
    
    embed = discord.Embed(title=f"📊 Stats for {member.name}", color=0x5865F2)
    embed.add_field(name="Staff Points", value=f"⭐ {pts}")
    embed.add_field(name="Warnings", value=f"⚠️ {warns}")
    await ctx.send(embed=embed)

# =====================
# STAFF & ADMIN COMMANDS
# =====================
@bot.command()
@commands.has_permissions(administrator=True)
async def addpoint(ctx, member: discord.Member, amount: int = 1):
    data = load_data()
    uid = str(member.id)
    data["staff_points"][uid] = data["staff_points"].get(uid, 0) + amount
    save_data(data)
    await ctx.send(f"⭐ Added {amount} point(s) to {member.mention}!")
    await log_event(ctx.guild, "Points Added", f"👤 {member.mention} | Amount: {amount}")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member, *, reason="No reason provided"):
    data = load_data()
    uid = str(member.id)
    if uid not in data["warnings"]: data["warnings"][uid] = []
    data["warnings"][uid].append({"reason": reason, "mod": ctx.author.name})
    save_data(data)
    
    count = len(data["warnings"][uid])
    await ctx.send(f"⚠️ {member.mention} warned ({count}/3).")
    await log_event(ctx.guild, "User Warning", f"👤 {member.mention}\n🛡️ Mod: {ctx.author.mention}\n📝 Reason: {reason}", 0xE74C3C)

@bot.command()
@commands.has_permissions(administrator=True)
async def promote(ctx, member: discord.Member):
    roles_list = ["Helper", "Moderator", "Admin"]
    for i, r_name in enumerate(roles_list):
        if discord.utils.get(member.roles, name=r_name):
            if i + 1 < len(roles_list):
                new_role = discord.utils.get(ctx.guild.roles, name=roles_list[i+1])
                await member.add_roles(new_role)
                return await ctx.send(f"🎊 {member.mention} promoted to **{roles_list[i+1]}**!")
    await ctx.send("❌ Promotion failed. Check role names/hierarchy.")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🧹 Cleared {amount} messages.", delete_after=3)

# =====================
# UTILITY & SYSTEM
# =====================
@bot.command()
async def cmds(ctx):
    embed = discord.Embed(title="📜 Command Menu", color=0x5865F2)
    embed.add_field(name="👥 Member", value="`!verify`, `!order`, `!stats`, `!ping` ", inline=False)
    embed.add_field(name="🛡️ Staff", value="`!warn`, `!timeout`, `!close`, `!clear` ", inline=False)
    embed.add_field(name="👑 Admin", value="`!promote`, `!addpoint`, `!panel` ", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def panel(ctx):
    embed = discord.Embed(title="Support Panel", description="Click below to open a ticket.", color=0x5865F2)
    await ctx.send(embed=embed, view=TicketView())

@bot.command()
async def close(ctx):
    if "ticket-" in ctx.channel.name or "order-" in ctx.channel.name:
        await ctx.send("Closing in 5 seconds...")
        await asyncio.sleep(5)
        await ctx.channel.delete()

@bot.event
async def on_ready():
    bot.add_view(TicketView())
    print(f"🚀 {bot.user} is fully operational!")

# =====================
# EXECUTION
# =====================
bot.run(os.getenv("DISCORD_TOKEN"))
