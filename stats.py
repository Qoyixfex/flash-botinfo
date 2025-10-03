import discord
import psutil
import sys
import os
import time
import aiosqlite
import platform
import pkg_resources
import datetime
import logging
from discord import Embed, ButtonStyle, SelectOption
from discord.ui import Button, View, Select
from discord.ext import commands
import aiosqlite 
import wavelink
from config.emojis import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('flash_bot')

class StatsSelect(Select):
    def __init__(self, stats_cog, ctx):
        self.stats_cog = stats_cog
        self.ctx = ctx
        options = [
            SelectOption(label="Home", description="View bot information and main stats", emoji=INFO, value="home"),
            SelectOption(label="Statistics", description="View detailed bot statistics", emoji=AI_EMOJI, value="general"),
            SelectOption(label="System", description="View system and hardware info", emoji=SETTINGS, value="system"),
            SelectOption(label="Latency", description="Check bot and database latency", emoji=LOADING, value="ping"),
            SelectOption(label="Developer Info", description="View developer information", emoji=NITRO_EMOJI, value="developer"),
        ]
        super().__init__(placeholder=f"Select a category to view...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            logger.warning(f"Unauthorized menu access attempt by {interaction.user}")
            return await interaction.response.send_message(f"{CHECK_NO} You cannot use this menu!", ephemeral=True)
        
        await interaction.response.defer()
        logger.info(f"User {interaction.user} selected {self.values[0]} in stats menu")
        
        if self.values[0] == "home":
            embed = await self.stats_cog.create_home_embed()
        elif self.values[0] == "general":
            embed = await self.stats_cog.create_general_embed()
        elif self.values[0] == "system":
            embed = await self.stats_cog.create_system_embed()
        elif self.values[0] == "ping":
            embed = await self.stats_cog.create_ping_embed()
        elif self.values[0] == "developer":
            embed = await self.stats_cog.create_developer_embed()
        
        await interaction.message.edit(embed=embed)

class StatsView(View):
    def __init__(self, stats_cog, ctx):
        super().__init__(timeout=120)
        self.stats_cog = stats_cog
        self.ctx = ctx
        self.add_item(StatsSelect(stats_cog, ctx))
        
        invite_button = Button(emoji="<:links:1393824211121868832>", label="Invite", style=ButtonStyle.url, url="https://discord.com/oauth2/authorize?client_id=1399950183323664405&permissions=8&scope=bot%20applications.commands", row=1)
        support_button = Button(emoji="<:Dev_mg1ck3ji_cpm4:1421245309631332392>", label="Support", style=ButtonStyle.url, url="https://discord.gg/ZtAuPVJ2bS", row=1)
        website_button = Button(emoji="<:idk:1393824732192833547>", label="Website", style=ButtonStyle.url, url="https://soon.com", row=1)
        
        self.add_item(invite_button)
        self.add_item(support_button)
        self.add_item(website_button)
        
        delete_button = Button(emoji="<:disabled:1393866554050871318>", style=ButtonStyle.red, row=2)
        async def delete_callback(interaction):
            if interaction.user == self.ctx.author:
                logger.info(f"Stats message deleted by {interaction.user}")
                await interaction.message.delete()
        delete_button.callback = delete_callback
        self.add_item(delete_button)

class Stats(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()
        self.total_songs_played = 0
        self.bot.loop.create_task(self.setup_database())
        logger.info("Stats cog initialized")

    async def setup_database(self):
        try:
            async with aiosqlite.connect("db/stats.db") as db:
                await db.execute("CREATE TABLE IF NOT EXISTS stats (key TEXT PRIMARY KEY, value INTEGER)")
                await db.commit()
                async with db.execute("SELECT value FROM stats WHERE key = 'total_songs_played'") as cursor:
                    row = await cursor.fetchone()
                    self.total_songs_played = row[0] if row else 0
                logger.info("Stats database setup completed")
        except Exception as e:
            logger.error(f"Database setup failed: {e}")

    async def update_total_songs_played(self):
        async with aiosqlite.connect("db/stats.db") as db:
            await db.execute("INSERT OR REPLACE INTO stats (key, value) VALUES ('total_songs_played', ?)", (self.total_songs_played,))
            await db.commit()

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload):
        self.total_songs_played += 1
        await self.update_total_songs_played()
        logger.debug(f"Track started, total songs now: {self.total_songs_played}")

    def count_code_stats(self, file_path):
        total_lines = 0
        total_words = 0
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    stripped_line = line.strip()
                    if stripped_line and not stripped_line.startswith(('〇')):
                        total_lines += 1
                        total_words += len(stripped_line.split())
        except (UnicodeDecodeError, IOError) as e:
            logger.warning(f"Could not read file {file_path}: {e}")
        return total_lines, total_words

    def gather_file_stats(self, directory):
        total_files = 0
        total_lines = 0
        total_words = 0
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if file.endswith('.py') and '.local' not in root:
                    total_files += 1
                    file_lines, file_words = self.count_code_stats(file_path)
                    total_lines += file_lines
                    total_words += file_words
        return total_files, total_lines, total_words

    async def create_home_embed(self):
        guild_count = len(self.bot.guilds)
        user_count = sum(g.member_count for g in self.bot.guilds if g.member_count is not None)
        
        uptime_seconds = int(round(time.time() - self.start_time))
        uptime_timedelta = datetime.timedelta(seconds=uptime_seconds)
        uptime = f"{uptime_timedelta.days}d {uptime_timedelta.seconds // 3600}h {(uptime_timedelta.seconds // 60) % 60}m"

        embed = Embed(
            title=f"Flash - Multipurpose Discord Bot",
            description=f"**Flash is a feature-rich multipurpose bot designed to enhance your Discord experience with moderation, music, utility, and more!**\n"
                       f"━━━━━━━━━━━━━━━━━━━━━━━━",
            color=0x000000
        )
        
        embed.add_field(
            name=f"{AI_EMOJI} BOT STATISTICS",
            value=f"{SERVERS_EMOJI} **SERVERS:** `{guild_count:,}`\n"
                  f"{USERS_EMOJI} **USERS:** `{user_count:,}`\n"
                  f"{UPTIME_EMOJI} **UPTIME:** `{uptime}`",
            inline=False
        )
        
        embed.add_field(
            name=f"{INFO} BOT INFORMATION",
            value=f"{AI_EMOJI} **Language:** `Python`\n"
                  f"{MODS} **Library:** `discord.py`\n"
                  f"{BUYER} **Version:** `{discord.__version__}`",
            inline=True
        )
        
        embed.set_footer(
            text=f"Powered by FlashHQ | Made with Love by Qøyi <\>",
            icon_url=self.bot.user.display_avatar.url
        )
        
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        return embed

    async def create_general_embed(self):
        guild_count = len(self.bot.guilds)
        user_count = sum(g.member_count for g in self.bot.guilds if g.member_count is not None)
        bot_count = sum(sum(1 for m in g.members if m.bot) for g in self.bot.guilds)
        human_count = user_count - bot_count
        channel_count = len(set(self.bot.get_all_channels()))
        text_channel_count = len([c for c in self.bot.get_all_channels() if isinstance(c, discord.TextChannel)])
        voice_channel_count = len([c for c in self.bot.get_all_channels() if isinstance(c, discord.VoiceChannel)])
        category_channel_count = len([c for c in self.bot.get_all_channels() if isinstance(c, discord.CategoryChannel)])
        slash_commands = len([cmd for cmd in self.bot.tree.get_commands()])
        commands_count = len(set(self.bot.walk_commands()))
        
        uptime_seconds = int(round(time.time() - self.start_time))
        uptime_timedelta = datetime.timedelta(seconds=uptime_seconds)
        uptime = f"{uptime_timedelta.days} days, {uptime_timedelta.seconds // 3600} hours, {(uptime_timedelta.seconds // 60) % 60} minutes, {uptime_timedelta.seconds % 60} seconds"

        total_files, total_lines, total_words = self.gather_file_stats('.')
        total_libraries = sum(1 for _ in pkg_resources.working_set)
        channels_connected = sum(1 for vc in self.bot.voice_clients if vc)
        playing_tracks = sum(1 for vc in self.bot.voice_clients if vc.playing)

        embed = Embed(title=f"{INFO} Flash Statistics", color=0x000000)
        
        embed.add_field(
            name=f"{SERVERS_EMOJI} Server Statistics",
            value=f"{DOT} **Servers:** {guild_count}\n{DOT} **Users:** {user_count:,}\n{DOT} **Channels:** {channel_count}",
            inline=True
        )
        
        embed.add_field(
            name=f"{AI_EMOJI} Bot Information", 
            value=f"{DOT} **Uptime:** {uptime}\n{DOT} **Commands:** {commands_count}\n{DOT} **Slash:** {slash_commands}",
            inline=True
        )
        
        embed.add_field(
            name=f"{USERS_EMOJI} User Distribution",
            value=f"{DOT} **Humans:** {human_count:,}\n{DOT} **Bots:** {bot_count:,}\n{DOT} **Total:** {user_count:,}",
            inline=True
        )
        
        embed.add_field(
            name=f"{WELCOMER} Channel Distribution", 
            value=f"{DOT} **Text:** {text_channel_count}\n{DOT} **Voice:** {voice_channel_count}\n{DOT} **Categories:** {category_channel_count}",
            inline=True
        )
        
        embed.add_field(
            name=f"<:developer:1393826423835459686> Development",
            value=f"{DOT} **Libraries:** {total_libraries}\n{DOT} **Python Files:** {total_files}\n{DOT} **Code Lines:** {total_lines:,}",
            inline=True
        )
        
        embed.add_field(
            name=f"{SUPPORT} Music",
            value=f"{DOT} **Connected:** {channels_connected}\n{DOT} **Playing:** {playing_tracks}\n{DOT} **Total Plays:** {self.total_songs_played:,}",
            inline=True
        )

        embed.set_footer(text=f"Powered by Flash | Multipurpose Discord Bot", icon_url=self.bot.user.display_avatar.url)
        return embed

    async def create_system_embed(self):
        cpu_info = psutil.cpu_freq()
        memory_info = psutil.virtual_memory()
        
        embed = Embed(title=f"{SETTINGS} System Information", color=0x000000)
        
        embed.add_field(
            name=f"{INFO} Software", 
            value=f"{DOT} **Python:** {platform.python_version()}\n{DOT} **Discord.py:** {discord.__version__}\n{DOT} **Platform:** {platform.system()}\n{DOT} **Architecture:** {platform.machine()}",
            inline=True
        )
        
        embed.add_field(
            name=f"{SETTINGS} Memory", 
            value=f"{DOT} **Total:** {memory_info.total / (1024 ** 3):.1f} GB\n{DOT} **Used:** {memory_info.used / (1024 ** 3):.1f} GB\n{DOT} **Available:** {memory_info.available / (1024 ** 3):.1f} GB\n{DOT} **Usage:** {memory_info.percent}%",
            inline=True
        )
        
        embed.add_field(
            name=f"{DRAGON} Processor", 
            value=f"{DOT} **Cores:** {psutil.cpu_count(logical=False)}\n{DOT} **Threads:** {psutil.cpu_count()}\n{DOT} **Usage:** {psutil.cpu_percent()}%\n{DOT} **Speed:** {cpu_info.current:.2f} MHz",
            inline=True
        )

        embed.set_footer(text=f"Powered by FlashHQ", icon_url=self.bot.user.display_avatar.url)
        return embed

    async def create_ping_embed(self):
        s_id = 0
        if hasattr(self, 'ctx') and self.ctx.guild:
            s_id = self.ctx.guild.shard_id
        sh = self.bot.get_shard(s_id)

        db_latency = None
        try:
            async with aiosqlite.connect("db/afk.db") as db:
                start_time = time.perf_counter()
                await db.execute("SELECT 1")
                end_time = time.perf_counter()
                db_latency = (end_time - start_time) * 1000
                db_latency = round(db_latency, 2)
        except Exception as e:
            db_latency = "N/A"
            logger.warning(f"Database latency check failed: {e}")

        wsping = round(self.bot.latency * 1000, 2)

        embed = Embed(title=f"{LOADING} Bot Latency", color=0x000000)
        
        embed.add_field(
            name=f"{ANIMATED_YES} Bot Latency", 
            value=f"{DOT} **{round(sh.latency * 1000)} ms**", 
            inline=True
        )
        embed.add_field(
            name=f"{VERIFY} Database Latency", 
            value=f"{DOT} **{db_latency} ms**", 
            inline=True
        )
        embed.add_field(
            name=f"{SERVER} Websocket Latency", 
            value=f"{DOT} **{wsping} ms**", 
            inline=True
        )

        embed.set_footer(text=f"Powered by FlashHQ", icon_url=self.bot.user.display_avatar.url)
        return embed

    async def create_developer_embed(self):
        embed = Embed(
            title=f"**Developer Information**",
            description="Meet the developers behind Flash Bot!",
            color=0x000000
        )
        
        embed.add_field(
            name=f"<:developer:1393826423835459686> Qoyi - Lead Developer",
            value=f"{DOT} **Role:** Lead Developer & Project Manager\n"
                  f"{DOT} **Specialization:** Backend Development, Bot Architecture\n"
                  f"{DOT} **Experience:** 3+ years in Discord bot development\n"
                  f"{DOT} **Contact:** `@qoyi_new` on Discord",
            inline=False
        )
        
        embed.add_field(
            name=f"<:developer:1393826423835459686> kraken - Co-Developer",
            value=f"{DOT} **Role:** Co-Developer & Feature Implementation\n"
                  f"{DOT} **Specialization:** Frontend, User Experience\n"
                  f"{DOT} **Experience:** 2+ years in Discord bot development\n"
                  f"{DOT} **Contact:** `@devravager` on Discord",
            inline=False
        )
        
        embed.add_field(
            name=f"{MODS} Development Team",
            value=f"{DOT} **Team Size:** 2 Developers\n"
                  f"{DOT} **Project Started:** 2024\n"
                  f"{DOT} **Commitment:** Active Development & Support\n"
                  f"{DOT} **Support Server:** [Join Here](https://discord.gg/ZtAuPVJ2bS)",
            inline=False
        )
        
        embed.add_field(
            name=f"{AI_EMOJI} Technologies",
            value=f"{DOT} **Language:** Python 3.8+\n"
                  f"{DOT} **Library:** discord.py\n"
                  f"{DOT} **Database:** SQLite with aiosqlite\n"
                  f"{DOT} **Music:** Wavelink for audio playback",
            inline=False
        )
        
        embed.set_footer(
            text="Thank you for using Flash Bot! We're constantly working to improve it.",
            icon_url=self.bot.user.display_avatar.url
        )
        
        return embed

    @commands.hybrid_command(name="stats", aliases=["botinfo", "botstats", "bi", "statistics", "about"], help="Shows the bot's information.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 7, commands.BucketType.user)
    async def stats(self, ctx):
        logger.info(f"Stats command invoked by {ctx.author} in {ctx.guild}")
        processing_message = await ctx.send(f"{LOADING} Loading Flash information...")
        
        self.ctx = ctx
        
        embed = await self.create_home_embed()
        view = StatsView(self, ctx)
        
        await processing_message.delete()
        await ctx.reply(embed=embed, view=view)
        logger.info(f"Stats command completed for {ctx.author}")

async def setup(bot):
    await bot.add_cog(Stats(bot))
    logger.info("Stats cog loaded successfully")
# either can be noprefix or just normal one
if __name__ == "__main__":
    bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
    
    @bot.event
    async def on_ready():
        print(f'Logged in as {bot.user.name}')
        print(f'Bot ID: {bot.user.id}')
        print('------')
    
    asyncio.run(setup(bot))
    
    # bot token
    bot.run("token")
