# bot.py
import os
import discord
from discord.ext import commands
from discord import ButtonStyle
from discord.ui import Button, View

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Bot setup
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ---- TICKET SYSTEM ----
class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="Create Ticket", style=ButtonStyle.green, custom_id="create_ticket"))

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component:
        if interaction.data["custom_id"] == "create_ticket":
            guild = interaction.guild
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True)
            }
            channel = await guild.create_text_channel(
                name=f"ticket-{interaction.user.name}",
                overwrites=overwrites,
                category=None  # Optional: add a category ID here
            )
            await channel.send(f"{interaction.user.mention}, your ticket has been created!")
            await interaction.response.send_message("Ticket created!", ephemeral=True)

# ---- COMMANDS ----
@bot.command()
async def panel(ctx):
    """Sends the ticket panel."""
    view = TicketView()
    await ctx.send("Click the button below to create a ticket.", view=view)

@bot.command()
async def close(ctx):
    """Closes the ticket."""
    if ctx.channel.name.startswith("ticket-"):
        await ctx.channel.delete()
    else:
        await ctx.send("This command can only be used in a ticket channel.")

# ---- MODERATION ----
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f"✅ {member} has been kicked for: {reason}")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f"✅ {member} has been banned for: {reason}")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount)
    await ctx.send(f"🧹 Cleared {amount} messages.", delete_after=5)

# ---- VERIFICATION ----
@bot.command()
async def verify(ctx):
    """Simple verification command."""
    role = discord.utils.get(ctx.guild.roles, name="Verified")
    if not role:
        role = await ctx.guild.create_role(name="Verified")
    await ctx.author.add_roles(role)
    await ctx.send(f"✅ {ctx.author.mention} has been verified!")

# ---- LOGGING SYSTEM ----
@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="logs")
    if channel:
        await channel.send(f"📥 {member} has joined the server.")

@bot.event
async def on_member_remove(member):
    channel = discord.utils.get(member.guild.text_channels, name="logs")
    if channel:
        await channel.send(f"📤 {member} has left the server.")

# ---- ERROR HANDLING ----
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You do not have permission to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Missing required argument.")
    else:
        await ctx.send(f"❌ An error occurred: {error}")

# ---- RUN BOT ----
TOKEN = os.getenv("TOKEN")
bot.run(TOKEN)
