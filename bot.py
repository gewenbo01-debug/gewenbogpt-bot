"""GewenboGPT — Psychonaut Community language-selection bot.

Rebuilt 2026-11-18 after the original host was lost.
Buttons [中文] / [English] on the welcome message assign language roles.
"""

import os
import logging
import threading
import time
import urllib.request

import discord
from discord import app_commands
from discord.ext import commands

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("gewenbogpt")

TOKEN = os.environ["DISCORD_TOKEN"]
WELCOME_CHANNEL_ID = int(os.environ.get("WELCOME_CHANNEL_ID", "0"))
ZH_ROLE_NAME = os.environ.get("ZH_ROLE_NAME", "中文")
EN_ROLE_NAME = os.environ.get("EN_ROLE_NAME", "English")

WELCOME_TEXT = (
    "**Welcome! | 欢迎!**\n"
    "Please select your language below to continue.\n"
    "请在下方选择你的语言以继续。"
)


class LanguageView(discord.ui.View):
    """Persistent buttons — custom_ids are stable across restarts."""

    def __init__(self):
        super().__init__(timeout=None)

    async def _assign(self, interaction: discord.Interaction, role_name: str, label: str):
        role = discord.utils.get(interaction.guild.roles, name=role_name)
        if role is None:
            # fuzzy fallback: 中文/Chinese / English/EN
            lowered = role_name.lower()
            candidates = {"zh": ("中文", "chinese", "zh"), "en": ("english", "en")}
            keys = candidates["zh"] if "中" in role_name or "zh" in lowered else candidates["en"]
            role = next(
                (r for r in interaction.guild.roles if any(k in r.name.lower() or k in r.name for k in keys)),
                None,
            )
        if role is None:
            await interaction.response.send_message(
                f"⚠️ 找不到身份组 `{role_name}`，请管理员用 `/langroles` 核对。", ephemeral=True
            )
            return
        other = {"zh": EN_ROLE_NAME, "en": ZH_ROLE_NAME}["zh" if "中" in role.name or "zh" in role.name.lower() else "en"]
        other_role = discord.utils.get(interaction.guild.roles, name=other)
        if other_role and other_role in interaction.user.roles:
            await interaction.user.remove_roles(other_role, reason="language switch")
        await interaction.user.add_roles(role, reason="language selection")
        await interaction.response.send_message(f"✅ 已为你分配身份组 **{label}** / Role assigned: **{label}**", ephemeral=True)

    @discord.ui.button(label="中文", style=discord.ButtonStyle.primary, custom_id="lang:zh")
    async def chinese(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._assign(interaction, ZH_ROLE_NAME, "中文")

    @discord.ui.button(label="English", style=discord.ButtonStyle.primary, custom_id="lang:en")
    async def english(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._assign(interaction, EN_ROLE_NAME, "English")


class GewenboGPT(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(LanguageView())  # re-register persistent buttons on boot
        await self.tree.sync()
        log.info("persistent view registered, slash commands synced")

    async def on_ready(self):
        log.info("logged in as %s (guilds: %s)", self.user, len(self.guilds))


bot = GewenboGPT()


@bot.tree.command(name="welcome", description="发布语言选择欢迎消息 / Post the language-selection welcome message")
@app_commands.checks.has_permissions(manage_guild=True)
async def welcome(interaction: discord.Interaction):
    channel = interaction.channel if WELCOME_CHANNEL_ID == 0 else bot.get_channel(WELCOME_CHANNEL_ID)
    if channel is None:
        await interaction.response.send_message("⚠️ 未找到欢迎频道，请在目标频道内使用此命令。", ephemeral=True)
        return
    await channel.send(WELCOME_TEXT, view=LanguageView())
    await interaction.response.send_message(f"✅ 已在 {channel.mention} 发布欢迎消息", ephemeral=True)


@bot.tree.command(name="langroles", description="列出本服务器全部身份组 / List all roles")
@app_commands.checks.has_permissions(manage_guild=True)
async def langroles(interaction: discord.Interaction):
    roles = "\n".join(f"`{r.id}` — {r.name}" for r in reversed(interaction.guild.roles))
    await interaction.response.send_message(roles[:1900] or "(无)", ephemeral=True)


@bot.tree.command(name="ping", description="健康检查 / health check")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"pong ({bot.latency * 1000:.0f}ms)", ephemeral=True)


if __name__ == "__main__":
    # --- Render free tier: HTTP server on $PORT + self-ping to dodge 15-min sleep ---
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"gewenbogpt-bot ok")

        def log_message(self, *a):
            pass

    port = int(os.environ.get("PORT", "7860"))
    httpd = HTTPServer(("0.0.0.0", port), H)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    log.info("http keepalive on :%s", port)

    external = os.environ.get("RENDER_EXTERNAL_URL")
    if external:

        def self_ping():
            while True:
                try:
                    urllib.request.urlopen(external, timeout=20)
                except Exception:
                    pass
                time.sleep(600)  # every 10 min < 15-min sleep window

        threading.Thread(target=self_ping, daemon=True).start()
        log.info("self-ping armed: %s", external)

    bot.run(TOKEN)
