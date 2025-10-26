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
ALLOWED_CHANNEL_ID = 1431929455554592879  # コマンドを許可するチャンネルID

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
    # チャンネル制限
    if interaction.channel.id != ALLOWED_CHANNEL_ID:
        await interaction.response.send_message(
            "❌ このコマンドは指定チャンネルでのみ使用できます。",
            ephemeral=True
        )
        return

    guild = interaction.guild

    # 実行権限チェック（管理者またはR4）
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

    # --- BOTとBOTロール除外 ---
    bot_roles = [r for r in guild.roles if r.managed]  # 管理対象ロール（Botロール）
    bot_role_ids = [r.id for r in bot_roles]

    members = [
        m for m in guild.members
        if not m.bot and not any(r.id in bot_role_ids for r in m.roles)
    ]

    # --- ソート設定 ---
    priority_roles = ["サーバ管理者", "R4", "R3", "ゲスト"]

    sorted_members = []
    other_members = []

    for member in members:
        # 管理者権限最優先
        if member.guild_permissions.administrator:
            sorted_members.append(("サーバ管理者", member.display_name))
        else:
            role_found = False
            for role in priority_roles[1:]:  # R4, R3, ゲスト
                if discord.utils.get(member.roles, name=role):
                    sorted_members.append((role, member.display_name))
                    role_found = True
                    break
            if not role_found:
                other_members.append(("一般", member.display_name))

    # --- グループ化 ---
    grouped = {}
    for role_name, name in sorted_members + other_members:
        grouped.setdefault(role_name, []).append(name)

    total_members = len(members)  # BOT除外後の実人数

    # --- 出力整形 ---
    result_text = f"👥 **サーバーメンバー一覧（合計 {total_members} 名）**\n\n"
    for role in priority_roles + ["一般"]:
        if role in grouped:
            result_text += f"**{role}（{len(grouped[role])}名）**\n" + "\n".join(grouped[role]) + "\n\n"

    # --- メッセージ送信 ---
    if len(result_text) > 1900:
        parts = [result_text[i:i+1900] for i in range(0, len(result_text), 1900)]
        await interaction.response.send_message(parts[0])
        for p in parts[1:]:
            await interaction.followup.send(p)
    else:
        await interaction.response.send_message(result_text)

# --- Flaskを別スレッドで起動（Render監視回避） ---
threading.Thread(target=run_web).start()

# --- Discord Bot起動 ---
client.run(TOKEN)
