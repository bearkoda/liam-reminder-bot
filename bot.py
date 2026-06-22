import discord
from discord.ext import commands
import asyncio
import random

import os

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

active_chores = {}


class ChoreView(discord.ui.View):
    def __init__(self, chore_id):
        super().__init__(timeout=None)
        self.chore_id = chore_id

    @discord.ui.button(label="Done", style=discord.ButtonStyle.success, emoji="✅")
    async def done_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.chore_id in active_chores:
            active_chores[self.chore_id]["done"] = True

        await interaction.response.send_message(
            "Marked done. Peace has been restored. ✅",
            ephemeral=True
        )

    @discord.ui.button(label="Snooze 15 min", style=discord.ButtonStyle.secondary, emoji="😴")
    async def snooze_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.chore_id in active_chores:
            active_chores[self.chore_id]["snooze"] = 15 * 60

        await interaction.response.send_message(
            "Snoozed for 15 minutes. Luxury has been granted. 😴",
            ephemeral=True
        )


def get_reminder_message(task, count):
    messages = [
        f"🔔 Reminder #{count}\n\nTask: {task}",
        f"🔔 Reminder #{count}\n\nBestie. The chore remains undefeated: {task}",
        f"🔔 Reminder #{count}\n\nThe house goblins report this is still not done: {task}",
        f"🔔 Reminder #{count}\n\nThis message will continue until morale improves: {task}",
        f"🔔 Reminder #{count}\n\nThe task has entered its villain era: {task}",
        f"🔔 Reminder #{count}\n\nHistorians will study this delay: {task}",
        f"🔔 Reminder #{count}\n\nThe chore is still standing. Bold. Disrespectful. {task}",
    ]

    if count <= len(messages):
        return messages[count - 1]

    return random.choice(messages)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print("Servers:")
    for guild in bot.guilds:
        print(f"- {guild.name}")

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s).")
    except Exception as e:
        print(f"Slash command sync failed: {e}")


@bot.tree.command(name="chore", description="Send chore reminders until the person clicks Done.")
async def chore(
    interaction: discord.Interaction,
    user: discord.User,
    task: str,
    minutes: int,
    max_reminders: int
):
    if minutes < 1:
        await interaction.response.send_message(
            "Minutes must be at least 1.",
            ephemeral=True
        )
        return

    if max_reminders < 1:
        await interaction.response.send_message(
            "Max reminders must be at least 1.",
            ephemeral=True
        )
        return

    chore_id = f"{user.id}-{interaction.id}"

    active_chores[chore_id] = {
        "user": user,
        "task": task,
        "minutes": minutes,
        "max_reminders": max_reminders,
        "done": False,
        "snooze": 0,
    }

    await interaction.response.send_message(
        f"Started reminding {user.mention} every {minutes} minute(s) about: **{task}**\n"
        f"Max reminders: **{max_reminders}**",
        ephemeral=True
    )

    asyncio.create_task(reminder_loop(chore_id))


async def reminder_loop(chore_id):
    chore_data = active_chores[chore_id]
    user = chore_data["user"]
    task = chore_data["task"]
    minutes = chore_data["minutes"]
    max_reminders = chore_data["max_reminders"]

    count = 1

    while count <= max_reminders:
        if chore_data["done"]:
            try:
                await user.send(f"✅ Completed: {task}")
            except:
                pass

            active_chores.pop(chore_id, None)
            return

        try:
            await user.send(
                get_reminder_message(task, count),
                view=ChoreView(chore_id)
            )
        except:
            active_chores.pop(chore_id, None)
            return

        wait_time = chore_data.get("snooze", 0)

        if wait_time > 0:
            chore_data["snooze"] = 0
        else:
            wait_time = minutes * 60

        await asyncio.sleep(wait_time)
        count += 1

    if not chore_data["done"]:
        try:
            await user.send(
                f"Final reminder reached for: {task}\n\nI am retreating dramatically."
            )
        except:
            pass

    active_chores.pop(chore_id, None)


bot.run(TOKEN)