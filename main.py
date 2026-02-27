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
        super().__init__(timeout=None)

    @discord.ui.button(label="Open Ticket", style=discord.ButtonStyle.green)
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):

        guild = interaction.guild
        user = interaction.user

        existing = discord.utils.get(guild.channels, name=f"ticket-{user.name}")
        if existing:
            await interaction.response.send_message("You already have a ticket open.", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True)
        }

        channel = await guild.create_text_channel(
            f"ticket-{user.name}",
            overwrites=overwrites
        )

        await channel.send(embed=embed_message(
            "🎟 Support Ticket",
            f"{user.mention} please describe your issue."
        ))

        await interaction.response.send_message("Ticket created.", ephemeral=True)

@bot.command()
async def panel(ctx):
    embed = embed_message(
        "Support Panel",
        "Click the button below to open a ticket."
    )
    await ctx.send(embed=embed, view=TicketView())

@bot.command()
async def close(ctx):
    if ctx.channel.name.startswith("ticket-"):
        await ctx.send("Closing ticket...")
        await asyncio.sleep(2)
        await ctx.channel.delete()

# =====================
# MODERATION
# =====================

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.kick(reason=reason)
    await ctx.send(embed=embed_message(
        "User Kicked",
        f"{member.mention} was kicked.\nReason: {reason}",
        0xFF0000
    ))

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.ban(reason=reason)
    await ctx.send(embed=embed_message(
        "User Banned",
        f"{member.mention} was banned.\nReason: {reason}",
        0xFF0000
    ))

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount+1)
    await ctx.send("Messages cleared.", delete_after=3)

# =====================
# VERIFICATION
# =====================

@bot.command()
async def verify(ctx):
    role = discord.utils.get(ctx.guild.roles, name="Verified")

    if not role:
        await ctx.send("Verified role does not exist.")
        return

    await ctx.author.add_roles(role)
    await ctx.send(embed=embed_message(
        "Verification Complete",
        f"{ctx.author.mention} you are now verified!",
        0x00FF00
    ))

bot.run(os.getenv("TOKEN"))
# =====================
# ORDER TICKET SYSTEM
# =====================

@bot.command()
async def order(ctx):
    guild = ctx.guild
    user = ctx.author

    existing = discord.utils.get(guild.channels, name=f"order-{user.name}")
    if existing:
        await ctx.send("You already have an open order ticket.")
        return

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True)
    }

    channel = await guild.create_text_channel(
        f"order-{user.name}",
        overwrites=overwrites
    )

    embed = discord.Embed(
        title="🛒 Order Ticket",
        description=f"{user.mention} please describe what you would like to order.\nA staff member will assist you shortly.",
        color=0x00BFFF
    )

    await channel.send(embed=embed)
    await ctx.send("Your order ticket has been created.", delete_after=5)
