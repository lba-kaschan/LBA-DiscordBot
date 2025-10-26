import discord
from discord import app_commands
import os

TOKEN = os.getenv("TOKEN")

# ✅ あなた専用のチャンネルID（㊙️discord-command）
ALLOWED_CHANNEL_ID = 1431929455554592879  

# 🔧 メンバー情報取得のためのintent
intents = discord.Intents.default()
intents.members = True

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

client = MyClient()


@client.event
async def on_ready():
    print(f"✅ ログイン完了: {client.user}")


@client.tree.command(name="get_members", description="メンバー一覧をチャンネルに出力します")
async def get_members(interaction: discord.Interaction):
    # 🚪 実行チャンネル制限
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        await interaction.response.send_message(
            "❌ このコマンドは指定のチャンネルでのみ使用できます。",
            ephemeral=True
        )
        return

    # 👑 実行権限チェック（R4ロールまたは管理者）
    allowed = False
    if interaction.user.guild_permissions.administrator:
        allowed = True

    role_names = [role.name for role in interaction.user.roles]
    if "R4" in role_names:
        allowed = True

    if not allowed:
        await interaction.response.send_message(
            "❌ あなたにはこのコマンドを実行する権限がありません。",
            ephemeral=True
        )
        return

    # 📋 メンバー一覧の生成
    guild = interaction.guild
    members = guild.members

    lines = ["**🗂 メンバー一覧**"]
    for m in members:
        roles = ", ".join([r.name for r in m.roles if r.name != "@everyone"])
        lines.append(f"- {m.display_name}（{roles or 'ロールなし'}）")

    output_text = "\n".join(lines)

    # ✂️ Discordの文字数制限（2000文字）対策：分割送信
    if len(output_text) > 1900:
        parts = [output_text[i:i+1900] for i in range(0, len(output_text), 1900)]
        await interaction.response.send_message(parts[0])
        for p in parts[1:]:
            await interaction.followup.send(p)
    else:
        await interaction.response.send_message(output_text)


client.run(TOKEN)
