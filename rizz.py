import discord
from discord.ext import commands
from discord.ui import Button, View
import requests


intents = discord.Intents.default()
intents.members = True  # Enable member intents

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

# Channel IDs 
WELCOME_CHANNEL_ID = 1292065832167280721  # WELECOME
TICKET_INFO_CHANNEL_ID = 1292128885080850513 # TICKET

# Welecome
@bot.event
async def on_member_join(member):
    welcome_channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if welcome_channel is not None:
        await welcome_channel.send(f"Welcome on Nazy Market, {member.mention}!")


# This event is triggered when the bot is ready
@bot.event
async def on_ready():
    print(f'Bot is online as {bot.user}')


class TicketButton(Button):
    def __init__(self):
        super().__init__(label="Create Ticket", style=discord.ButtonStyle.primary)

    async def callback(self, interaction):
        guild = interaction.guild
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True)
        }
        ticket_channel = await guild.create_text_channel(f'ticket-{interaction.user.name}', overwrites=overwrites)

        await ticket_channel.send(f'This ticket was created by {interaction.user.mention}. How can we help you?')
        
        # Send buttons to the ticket channel
        await ticket_channel.send("Manage your ticket:", view=TicketManagementView(interaction.user, ticket_channel))

        await interaction.response.send_message(f'Ticket created: {ticket_channel.mention}', ephemeral=True)

class TicketManagementView(View):
    def __init__(self, creator: discord.User, ticket_channel: discord.TextChannel):
        super().__init__(timeout=None)  
        self.creator = creator
        self.ticket_channel = ticket_channel
        self.add_item(CloseTicketButton(creator, ticket_channel))
        self.add_item(AddMemberButton(ticket_channel))

class CloseTicketButton(Button):
    def __init__(self, creator: discord.User, ticket_channel: discord.TextChannel):
        super().__init__(label="Close Ticket", style=discord.ButtonStyle.danger)
        self.creator = creator
        self.ticket_channel = ticket_channel

    async def callback(self, interaction):
        await interaction.response.send_modal(CloseTicketModal(self.creator, self.ticket_channel))

class CloseTicketModal(discord.ui.Modal, title="Close Ticket"):
    reason = discord.ui.TextInput(label="Reason for closing", placeholder="Enter the reason...")

    def __init__(self, creator: discord.User, ticket_channel: discord.TextChannel):
        super().__init__()
        self.creator = creator
        self.ticket_channel = ticket_channel

    async def on_submit(self, interaction: discord.Interaction):
        reason = self.reason.value
        await self.ticket_channel.send(f"Ticket closed by {interaction.user.mention}.\nReason: {reason}")
        await interaction.user.send(f"Your ticket has been closed. Reason: {reason}")
        # Notify admin here (you can customize this part)
        admin_channel = bot.get_channel(1292849949867769856)  
        await admin_channel.send(f"Ticket closed by {interaction.user.mention} in {self.ticket_channel.mention}.\nReason: {reason}")
        
        await self.ticket_channel.delete()  

class AddMemberButton(Button):
    def __init__(self, ticket_channel: discord.TextChannel):
        super().__init__(label="Add Member", style=discord.ButtonStyle.secondary)
        self.ticket_channel = ticket_channel

    async def callback(self, interaction):
        await interaction.response.send_modal(AddMemberModal(self.ticket_channel))

class AddMemberModal(discord.ui.Modal, title="Add Member to Ticket"):
    member_name = discord.ui.TextInput(label="Member's Username", placeholder="Enter the username to add...")

    def __init__(self, ticket_channel: discord.TextChannel):
        super().__init__()
        self.ticket_channel = ticket_channel

    async def on_submit(self, interaction: discord.Interaction):
        member_name = self.member_name.value
        member = discord.utils.get(self.ticket_channel.guild.members, name=member_name)
        
        if member:
            await self.ticket_channel.set_permissions(member, read_messages=True)
            await self.ticket_channel.send(f"{member.mention} has been added to the ticket.")
        else:
            await interaction.response.send_message("Member not found.", ephemeral=True)

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)  
        self.add_item(TicketButton())


@bot.command()
async def setup_ticket(ctx):
    channel = bot.get_channel(TICKET_INFO_CHANNEL_ID)
    if channel is not None:
        view = TicketView()
        await channel.send("Interact with the button to buy accounts!", view=view)
        await ctx.send("Ticket setup complete!")
    else:
        await ctx.send("Ticket info channel not found.")

# Command for admin tools
@bot.command()
@commands.has_permissions(administrator=True)
async def admin(ctx):
    await ctx.send("Admin tools available! Use the following commands:\n- `!setup_ticket`: Set up the ticket system\n- `!skincheck <username>`: Check Fortnite skins.")

# Fortnite Skin Checker
@bot.command()
async def skincheck(ctx, username: str):
    # Replace with the actual Raika API endpoint and token
    api_url = f"https://api.raika.gg/fortnite/locker/{username}"
    headers = {
        'Authorization': 'TOKEN'  
    }
    
    response = requests.get(api_url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        skins = data.get('skins', [])
        if skins:
            skins_list = "\n".join(skin['name'] for skin in skins)
            await ctx.send(f"{username}'s skins:\n{skins_list}")
        else:
            await ctx.send(f"No skins found for {username}.")
    else:
        await ctx.send("Error fetching skin data. Please check the username or try again later.")


@admin.error
async def admin_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You do not have permission to use this command.")


bot.run('TOKEN')  
