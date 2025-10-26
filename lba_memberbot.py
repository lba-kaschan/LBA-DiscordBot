import discord
from discord import app_commands
import os
from flask import Flask
import threading

# --- Render無料プランで停止されないための擬似Webサーバー ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    app.run(host="0.0.0.0", port=10000)

# --- Discord設定 ---
TOKEN = os.getenv("TOKEN")
ALLOWED_CHANNEL_ID = 1431929455554592879  # あなたの指定チャンネルID

intents = discord.Intents.default()
intents.members = True

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        print("✅ Slash commands synced.")

client = MyClient()

@client.event
async def on_ready():
    print(f"✅ ログイン完了: {client.user}")

# --- /members コマンド ---
@client.tree.command(name="members", description="サーバーのメンバー一覧を表示します（R4限定）")
async def members(interaction: discord.Interaction):
    if interaction.channel.id != ALLOWED_CHANNEL_ID:
        await interaction.response.send_message(
            "❌ このコマンドは指定チャンネルでのみ使用できます。",
            ephemeral=True
        )
        return

    # R4 or 管理者のみ許可
    allowed = interaction.user.guild_permissions.administrator
    role_names = [r.name for r in interaction.user.roles]
    if "R4" in role_names:
        allowed = True
    if not allowed:
        await interaction.response.send_message(
            "❌ あなたにはこのコマンドを実行する権限がありません。",
            ephemeral=True
        )
        return

    # メンバー一覧取得
    members = [m for m in interaction.guild.members if not m.bot]
    lines = ["**🗂 メンバー一覧**"]
    for m in members:
        roles = ", ".join([r.name for r in m.roles if r.name != "@everyone"])
        lines.append(f"- {m.display_name}（{roles or 'ロールなし'}）")

    output = "\n".join(lines)
    if len(output) > 1900:
        parts = [output[i:i+1900] for i in range(0, len(output), 1900)]
        await interaction.response.send_message(parts[0])
        for p in parts[1:]:
            await interaction.followup.send(p)
    else:
        await interaction.response.send_message(output)

# --- Flaskを別スレッドで起動（Render監視回避） ---
threading.Thread(target=run_web).start()

# --- Discord Bot起動 ---
client.run(TOKEN)
