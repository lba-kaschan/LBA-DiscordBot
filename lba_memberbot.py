import discord
from discord import app_commands
import os

# DiscordトークンはRenderの環境変数から取得
TOKEN = os.getenv("TOKEN")

# ✅ コマンドを実行できるチャンネルID（あなたの #㊙️discord-command）
ALLOWED_CHANNEL_ID = 1431929455554592879

# 🔧 メンバー情報取得を許可
intents = discord.Intents.default()
intents.members = True

# --- Bot本体 ---
class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # スラッシュコマンドをDiscordに登録
        await self.tree.sync()
        print("✅ Slash commands synced.")

client = MyClient()


# --- 起動ログ ---
@client.event
async def on_ready():
    print(f"✅ ログイン完了: {client.user}")


# --- /members コマンド定義 ---
@client.tree.command(name="members", description="サーバーのメンバー一覧を表示します（R4限定）")
async def members(interaction: discord.Interaction):
    # 🚪 チャンネル制限
    if interaction.channel.id != ALLOWED_CHANNEL_ID:
        await interaction.response.send_message(
            "❌ このコマンドは指定チャンネルでのみ使用できます。",
            ephemeral=True  # 自分にしか見えない
        )
        return

    # 👑 実行者権限チェック
    allowed = False
    if interaction.user.guild_permissions.administrator:
        allowed = True

    # R4ロールを持っているか確認
    role_names = [role.name for role in interaction.user.roles]
    if "R4" in role_names:
        allowed = True

    if not allowed:
        await interaction.response.send_message(
            "❌ あなたにはこのコマンドを実行する権限がありません。",
            ephemeral=True
        )
        return

    # 📋 メンバー一覧作成
    guild = interaction.guild
    members = guild.members

    lines = ["**🗂 メンバー一覧**"]
    for m in members:
        if m.bot:
            continue  # Botを除外
        roles = ", ".join([r.name for r in m.roles if r.name != "@everyone"])
        lines.append(f"- {m.display_name}（{roles or 'ロールなし'}）")

    # 📜 出力をDiscordに直接貼り付け（2000文字制限対応）
    output_text = "\n".join(lines)
    if len(output_text) > 1900:
        parts = [output_text[i:i+1900] for i in range(0, len(output_text), 1900)]
        await interaction.response.send_message(parts[0])
        for p in parts[1:]:
            await interaction.followup.send(p)
    else:
        await interaction.response.send_message(output_text)

# --- Bot起動 ---
client.run(TOKEN)
