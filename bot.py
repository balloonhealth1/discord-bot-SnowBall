import os
import json
from pathlib import Path
from threading import Thread

from flask import Flask
import discord
from discord.ext import commands
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
TOKEN = os.getenv("DISCORD_TOKEN")
CONFIG_PATH = BASE_DIR / "config.json"

with CONFIG_PATH.open("r", encoding="utf-8") as f:
    CONFIG = json.load(f)

intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
dynamic_channels = {}
app = Flask(__name__)


@app.route("/")
def home():
    return "Bot is alive and running 24/7!"


def run_flask():
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, use_reloader=False)


def keep_alive():
    Thread(target=run_flask, daemon=True).start()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")


@bot.event
async def on_voice_state_update(member, before, after):
    if after.channel is not None:
        joined_channel_id = after.channel.id
        for category_cfg in CONFIG.get("categories", []):
            if joined_channel_id == category_cfg["create_channel_id"]:
                guild = after.channel.guild
                category = after.channel.category

                existing_count = sum(
                    1 for cfg in dynamic_channels.values()
                    if cfg["name"] == category_cfg["name"]
                )
                channel_name = f"{category_cfg['channel_prefix']}{existing_count + 1}"

                new_channel = await guild.create_voice_channel(
                    name=channel_name,
                    category=category,
                    user_limit=category_cfg.get("user_limit", 0),
                )
                dynamic_channels[new_channel.id] = category_cfg
                await member.move_to(new_channel)
                break

    if before.channel is not None:
        left_channel = before.channel
        if left_channel.id in dynamic_channels and len(left_channel.members) == 0:
            del dynamic_channels[left_channel.id]
            try:
                await left_channel.delete()
            except discord.HTTPException as exc:
                print(f"Could not delete empty voice channel {left_channel.id}: {exc}")


if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError(
            "DISCORD_TOKEN is not set. Add it to the Render environment variables or a .env file."
        )
    keep_alive()
    bot.run(TOKEN)
