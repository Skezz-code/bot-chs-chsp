import os
import discord
from discord.ext import commands


TOKEN = os.getenv("DISCORD_TOKEN")

PANEL_CHANNEL_ID = 1525129785322504393
REPORT_CHANNEL_ID = 1455306525286600807

CURATOR_ROLE_ID = 1454624496777429091
PING_ROLE_ID = 1454624496777429091

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

ticket_counter = 0


class ReportModal(discord.ui.Modal, title="Подача жалобы"):

    steamid = discord.ui.TextInput(
        label="SteamID нарушителя",
        placeholder="7656119XXXXXXXXXX",
        required=True,
        max_length=32
    )

    nickname = discord.ui.TextInput(
        label="Ник нарушителя",
        placeholder="Введите ник",
        required=True,
        max_length=50
    )

    punishment = discord.ui.TextInput(
        label="ЧСС или ЧСП",
        placeholder="Например: ЧСП",
        required=True,
        max_length=10
    )

    reason = discord.ui.TextInput(
        label="Причина",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000
    )

    evidence = discord.ui.TextInput(
    label="📎 Доказательства",
    placeholder="Видео — только YouTube, скриншоты — только yapx.ru. Вставьте ссылку сюда.",
    required=True,
    style=discord.TextStyle.paragraph,
    max_length=1000
)

    async def on_submit(self, interaction: discord.Interaction):
        global ticket_counter

        ticket_counter += 1

        report_channel = bot.get_channel(REPORT_CHANNEL_ID)

        embed = discord.Embed(
            title=f"📋 Заявка #{ticket_counter}",
            color=discord.Color.orange()
        )

        embed.set_author(
            name=f"{interaction.user}",
            icon_url=interaction.user.display_avatar.url
        )

        embed.add_field(
            name="👤 Подал заявку",
            value=interaction.user.mention,
            inline=False
        )

        embed.add_field(
            name="🆔 SteamID нарушителя",
            value=self.steamid.value,
            inline=False
        )

        embed.add_field(
            name="🎮 Ник нарушителя",
            value=self.nickname.value,
            inline=False
        )

        embed.add_field(
            name="⚖ Наказание",
            value=self.punishment.value,
            inline=False
        )

        embed.add_field(
            name="📝 Причина",
            value=self.reason.value,
            inline=False
        )

        embed.add_field(
            name="📎 Доказательства",
            value=self.evidence.value,
            inline=False
        )

        embed.set_thumbnail(
            url=interaction.user.display_avatar.url
        )

        embed.set_footer(
            text=f"ID автора: {interaction.user.id}"
        )

        await report_channel.send(
            f"<@&{PING_ROLE_ID}>",
            embed=embed,
            view=ReviewButtons()
        )

        await interaction.response.send_message(
            "✅ Ваша заявка успешно отправлена.",
            ephemeral=True
        )


class CreateRequestView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Создать запрос",
        emoji="📨",
        style=discord.ButtonStyle.primary
    )
    async def create_request(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_modal(
            ReportModal()
        )


class ReviewButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Одобрить",
        emoji="✅",
        style=discord.ButtonStyle.success
    )
    async def approve(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        curator_role = interaction.guild.get_role(
            CURATOR_ROLE_ID
        )

        if curator_role not in interaction.user.roles:
            return await interaction.response.send_message(
                "❌ У вас нет доступа.",
                ephemeral=True
            )

        embed = interaction.message.embeds[0]
        embed = discord.Embed.from_dict(embed.to_dict())

        embed.color = discord.Color.green()

        embed.add_field(
            name="✅ Решение",
            value=f"Одобрено куратором {interaction.user.mention}",
            inline=False
        )

        for item in self.children:
            item.disabled = True

        await interaction.message.edit(
            embed=embed,
            view=self
        )

        await interaction.response.send_message(
            "Заявка одобрена.",
            ephemeral=True
        )

    @discord.ui.button(
        label="Отклонить",
        emoji="❌",
        style=discord.ButtonStyle.danger
    )
    async def reject(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        curator_role = interaction.guild.get_role(
            CURATOR_ROLE_ID
        )

        if curator_role not in interaction.user.roles:
            return await interaction.response.send_message(
                "❌ У вас нет доступа.",
                ephemeral=True
            )

        embed = interaction.message.embeds[0]
        embed = discord.Embed.from_dict(embed.to_dict())

        embed.color = discord.Color.red()

        embed.add_field(
            name="❌ Решение",
            value=f"Отклонено куратором {interaction.user.mention}",
            inline=False
        )

        for item in self.children:
            item.disabled = True

        await interaction.message.edit(
            embed=embed,
            view=self
        )

        await interaction.response.send_message(
            "Заявка отклонена.",
            ephemeral=True
        )


@bot.command()
@commands.has_permissions(administrator=True)
async def panel(ctx):

    if ctx.channel.id != PANEL_CHANNEL_ID:
        return await ctx.send(
            f"Используй команду только в канале подачи."
        )

    embed = discord.Embed(
        title="📋 Подача жалоб",
        description=(
            "Нажмите кнопку ниже для создания заявки."
        ),
        color=discord.Color.blurple()
    )

    await ctx.send(
        embed=embed,
        view=CreateRequestView()
    )


@bot.event
async def on_ready():
    print(f"Бот запущен как {bot.user}")

@bot.command(name="база")
async def database(ctx):

    channel = bot.get_channel(REPORT_CHANNEL_ID)

    if channel is None:
        return await ctx.send("❌ Канал заявок не найден.")

    chsp = []
    chss = []

    async for message in channel.history(limit=None):

        if not message.embeds:
            continue

        embed = message.embeds[0]

        fields = {}

        for field in embed.fields:
            fields[field.name] = field.value


        # Берём только одобренные заявки
        decision = ""

        for name, value in fields.items():
            if "Решение" in name:
                decision = value


        if "Одобрено" not in decision:
            continue


        steamid = None
        punishment = None


        for name, value in fields.items():

            if "SteamID" in name:
                steamid = value

            if "Наказание" in name:
                punishment = value.upper()


        if steamid and punishment:

            if "ЧСП" in punishment:
                if steamid not in chsp:
                    chsp.append(steamid)

            elif "ЧСС" in punishment:
                if steamid not in chss:
                    chss.append(steamid)



    embed = discord.Embed(
        title="📚 База ЧСС / ЧСП",
        color=discord.Color.red()
    )


    embed.add_field(
        name="🚫 ЧСП",
        value="\n".join(chsp) if chsp else "Нет записей",
        inline=False
    )


    embed.add_field(
        name="⛔ ЧСС",
        value="\n".join(chss) if chss else "Нет записей",
        inline=False
    )


    embed.set_footer(
        text=f"Всего записей: {len(chsp)+len(chss)}"
    )


    await ctx.send(embed=embed)




@bot.command(name="проверить")
async def check_steam(ctx, steamid=None):

    if not steamid:
        return await ctx.send(
            "❌ Использование: `!проверить STEAMID`"
        )


    channel = bot.get_channel(REPORT_CHANNEL_ID)

    if channel is None:
        return await ctx.send("❌ Канал заявок не найден.")


    async for message in channel.history(limit=None):

        if not message.embeds:
            continue


        embed = message.embeds[0]

        fields = {}

        for field in embed.fields:
            fields[field.name] = field.value


        decision = ""

        for name, value in fields.items():
            if "Решение" in name:
                decision = value


        if "Одобрено" not in decision:
            continue


        saved_steam = None
        punishment = "Не указано"
        reason = "Не указана"


        for name, value in fields.items():

            if "SteamID" in name:
                saved_steam = value

            if "Наказание" in name:
                punishment = value

            if "Причина" in name:
                reason = value



        if saved_steam == steamid:


            embed = discord.Embed(
                title="🔎 Проверка SteamID",
                color=discord.Color.red()
            )


            embed.add_field(
                name="🆔 SteamID",
                value=steamid,
                inline=False
            )


            embed.add_field(
                name="⚖ Наказание",
                value=punishment,
                inline=False
            )


            embed.add_field(
                name="📝 Причина",
                value=reason,
                inline=False
            )


            embed.add_field(
                name="👮 Решение",
                value=decision,
                inline=False
            )


            await ctx.send(embed=embed)
            return



    embed = discord.Embed(
        title="🔎 Проверка SteamID",
        description=(
            f"✅ `{steamid}` не найден "
            "в базе ЧСС/ЧСП"
        ),
        color=discord.Color.green()
    )


    await ctx.send(embed=embed)

bot.run(TOKEN)
