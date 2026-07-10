import os
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")

GUILD_ID = 1454624496337158366
STAFF_ROLE_ID = 1454624496777429091


intents = discord.Intents.default()
intents.members = True
intents.message_content = True


bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# -----------------------------
# Запуск
# -----------------------------

@bot.event
async def on_ready():
    print(f"Запущен как {bot.user}")

    bot.add_view(CreateTicket())
    bot.add_view(TicketButtons())

    try:
        guild = discord.Object(id=GUILD_ID)

        synced = await bot.tree.sync(guild=guild)

        print(f"Команд загружено: {len(synced)}")

    except Exception as e:
        print(f"Ошибка синхронизации: {e}")


# -----------------------------
# Создание запроса
# -----------------------------

class CreateTicket(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)


    @discord.ui.button(
        label="➕ Создать запрос",
        style=discord.ButtonStyle.green,
        custom_id="create_ticket"
    )
    async def create(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.send_message(
            "Выберите категорию:",
            view=CategoryMenu(),
            ephemeral=True
        )


# -----------------------------
# Выбор категории
# -----------------------------

class CategoryMenu(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=60)


    @discord.ui.select(
        placeholder="Тип запроса",
        options=[
            discord.SelectOption(
                label="ЧСС",
                emoji="🔴",
                value="ch"
            ),
            discord.SelectOption(
                label="ЧСП",
                emoji="🟡",
                value="chsp"
            )
        ]
    )
    async def select(
        self,
        interaction: discord.Interaction,
        select: discord.ui.Select
    ):

        category = select.values[0]

        guild = interaction.guild
        user = interaction.user


        ticket_category = discord.utils.get(
            guild.categories,
            name="Проверки"
        )

        if ticket_category is None:
            ticket_category = await guild.create_category(
                "Запросы"
            )


        for ch in ticket_category.channels:
            if ch.topic == str(user.id):
                await interaction.response.send_message(
                    "У вас уже есть открытый запрос.",
                    ephemeral=True
                )
                return


        name = (
            f"🔴чсс-{user.name}"
            if category == "ch"
            else
            f"🟡чсп-{user.name}"
        )


        staff_role = guild.get_role(STAFF_ROLE_ID)


        overwrites = {

            guild.default_role:
            discord.PermissionOverwrite(
                view_channel=False
            ),

            user:
            discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True
            ),

            guild.me:
            discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True
            )
        }


        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True
            )


        channel = await guild.create_text_channel(
            name=name,
            category=ticket_category,
            overwrites=overwrites,
            topic=str(user.id)
        )


        embed = discord.Embed(
    title="🔎 Новый запрос",
    description=
    """
После создания запроса заполните форму:

1. 👤 Упомяните себя (@ваш Discord аккаунт)

2. 🎮 Укажите SteamID игрока

3. 📝 Укажите причину добавления

4. 📸 Прикрепите доказательства (скриншоты, видео и т.д.)
""",
    color=discord.Color.red()
)

        embed.add_field(
            name="Пользователь",
            value=user.mention
        )

        embed.add_field(
            name="Категория",
            value="ЧСC" if category == "ch" else "ЧСП"
        )

        embed.add_field(
            name="Статус",
            value="🟢 Открыт"
        )


        await channel.send(
    content=f"{user.mention}, заполните форму выше.",
    embed=embed,
    view=TicketButtons()
)


        await interaction.response.send_message(
            f"Создан канал {channel.mention}",
            ephemeral=True
        )


# -----------------------------
# Кнопки тикета
# -----------------------------

class TicketButtons(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)


    @discord.ui.button(
        label="🛡 Взять запрос",
        style=discord.ButtonStyle.blurple,
        custom_id="claim"
    )
    async def claim(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.channel.send(
            f"🛡 Проверяющий {interaction.user.mention} взял запрос."
        )

        await interaction.response.defer()



    @discord.ui.button(
        label="🔒 Закрыть",
        style=discord.ButtonStyle.red,
        custom_id="close"
    )
    async def close(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.channel.edit(
            name=f"closed-{interaction.channel.name}"
        )

        await interaction.channel.send(
            "🔒 Запрос закрыт."
        )

        await interaction.response.defer()



# -----------------------------
# Setup
# -----------------------------

@bot.tree.command(
    name="setup",
    description="Создать кнопку запросов",
    guild=discord.Object(id=GUILD_ID)
)
async def setup(
    interaction: discord.Interaction
):

    embed = discord.Embed(
        title="📋 Проверка",
        description=
        "Нажмите кнопку ниже чтобы открыть запрос.\n\n"
        "🔴 ЧСС\n"
        "🟡 ЧСП",
        color=discord.Color.blue()
    )


    await interaction.channel.send(
        embed=embed,
        view=CreateTicket()
    )


    await interaction.response.send_message(
        "Готово",
        ephemeral=True
    )


bot.run(TOKEN)