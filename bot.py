import os
import json
import asyncio
from threading import Thread
from flask import Flask
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
dynamic_channels = {}

app = Flask("")

@app.route("/")
def home():
    return "Bot is alive and running 24/7!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

@bot.event
async def on_ready():
    print(f"機器人已成功登入：{bot.user.name}")

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
                    user_limit=category_cfg.get("user_limit", 0)
                )
                
                dynamic_channels[new_channel.id] = category_cfg
                await member.move_to(new_channel)
                break

    if before.channel is not None:
        left_channel = before.channel
        if left_channel.id in dynamic_channels:
            if len(left_channel.members) == 0:
                del dynamic_channels[left_channel.id]
                try:
                    await left_channel.delete()
                except:
                    pass

if __name__ == "__main__":
    keep_alive()
    if TOKEN:
        bot.run(TOKEN)