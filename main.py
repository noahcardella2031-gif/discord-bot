import discord
from discord.ext import commands
import os
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =====================
# READY
# =====================

@bot.event
async def on_ready():
    # Register the view so buttons work after a bot restart
    bot.add_view(TicketView()) 
    print(f"Logged in as {bot.user}")

# =====================
# EMBED HELPER
# =====================

def embed_message(title, description, color=0x5865F2):
    return discord.Embed(title=title, description=description, color=color)

# =====================
# TICKET SYSTEM
# =====================

class TicketView(discord.ui.View):
    def __init__(self):
        # timeout=None makes the button last forever
        super().__init__(timeout=None)

    @discord.ui.button(label="Open Ticket", style=discord.ButtonStyle.green, custom_id="persistent_view:open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):

        guild = interaction.guild
        user = interaction.user

        # Better naming to avoid conflicts (lowercase/replaces spaces)
        channel_name = f"ticket-{user.name.lower().replace(' ', '-')}"
        
        existing = discord.utils.get(guild.channels, name=channel_name)
        if existing:
            await interaction.response.send_message("You already have a ticket open.", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        channel = await guild.create_text_channel(
            channel_name,
            overwrites=overwrites
        )

        await channel.send(embed=embed_message(
            "🎟 Support Ticket",
            f"{user.mention} please describe your issue."
        ))

        await interaction.response.send_message(f"Ticket created: {channel.mention}", ephemeral=True)

@bot.command()
async def panel(ctx):
    embed = embed_message(
        "Support Panel",
        "Click the button below to open a ticket."
    )
    await ctx.send(embed=embed, view=TicketView())

@bot.command()
async def close(ctx):
    # Checks if it's a ticket or order channel
    if ctx.channel.name.startswith("ticket-") or ctx.channel.name.startswith("order-"):
        await ctx.send("Closing ticket in 5 seconds...")
        await asyncio.sleep(5)
        await ctx.channel.delete()
    else:
        await ctx.send("This is not a ticket channel.", delete_after=3)

# =====================
# MODERATION
# =====================

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.kick(reason=reason)
    await ctx.send(embed=embed_message("User Kicked", f"{member.mention} was kicked.\nReason: {reason}", 0xFF0000))

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.ban(reason=reason)
    await ctx.send(embed=embed_message("User Banned", f"{member.mention} was banned.\nReason: {reason}", 0xFF0000))

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"Cleared {amount} messages.", delete_after=3)

# =====================
# VERIFICATION & UTILITY
# =====================

@bot.command()
async def verify(ctx):
    role = discord.utils.get(ctx.guild.roles, name="Verified")
    if not role:
        await ctx.send("Verified role does not exist. Please create a role named 'Verified'.")
        return
    await ctx.author.add_roles(role)
    await ctx.send(embed=embed_message("Verification Complete", f"{ctx.author.mention} you are now verified!", 0x00FF00))

@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 Pong! Latency: {round(bot.latency * 1000)}ms")

@bot.command()
async def order(ctx):
    guild = ctx.guild
    user = ctx.author
    channel_name = f"order-{user.name.lower().replace(' ', '-')}"

    existing = discord.utils.get(guild.channels, name=channel_name)
    if existing:
        await ctx.send("You already have an open order ticket.", delete_after=5)
        return

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True)
    }

    channel = await guild.create_text_channel(channel_name, overwrites=overwrites)
    embed = discord.Embed(
        title="🛒 Order Ticket",
        description=f"{user.mention} please describe your order.",
        color=0x00BFFF
    )
    await channel.send(embed=embed)
    await ctx.send(f"Order ticket created: {channel.mention}", delete_after=5)

@bot.command()
async def cmds(ctx):
    embed = discord.Embed(title="📜 Bot Command List", color=0x5865F2)
    embed.add_field(name="🎟 Tickets", value="`!panel`, `!order`, `!close`", inline=False)
    embed.add_field(name="🛡 Moderation", value="`!kick`, `!ban`, `!clear`", inline=False)
    embed.add_field(name="✅ Verification", value="`!verify`", inline=False)
    embed.add_field(name="ℹ️ Utility", value="`!ping`, `!cmds`", inline=False)
    await ctx.send(embed=embed)

# =====================
# RUN THE BOT (MUST BE LAST)
# =====================
token = os.getenv("TOKEN")
if token:
    bot.run(token)
else:
    print("Error: No TOKEN found in environment variables.")
