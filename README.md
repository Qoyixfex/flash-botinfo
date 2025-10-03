# Flash Bot - Bot Info Command

A Discord bot featuring an advanced `!botinfo` command with interactive menus and detailed statistics.

## 🎯 Command
```
!botinfo
!bi
```

## 📊 Features

### Interactive Menu System
- **Dropdown selector** with 5 categories
- **Action buttons** (Invite, Support, Website)
- **Real-time statistics**
- **Beautiful embeds**

### Information Categories

1. **🏠 Home** - Basic bot info and main statistics
2. **📈 Statistics** - Detailed server and user analytics  
3. **⚙️ System** - Hardware and performance monitoring
4. **📡 Latency** - Bot and database response times
5. **👨‍💻 Developer** - Team information and technologies

## 🛠️ Setup

1. **Install requirements:**
```bash
pip install discord.py psutil aiosqlite wavelink
```

2. **Add your bot token to `token.txt`**

3. **Run the bot:**
```bash
python main.py
```

## 📁 Files Needed
- `main.py` - Bot setup and token handling
- `stats.py` - Bot info command and menus  
- `config/emojis.py` - Custom emoji definitions
- `requirements.txt` - Dependencies

## 🎵 Additional Features
- Music system with Wavelink
- Song play tracking
- Database statistics
- System monitoring

**Perfect for showing off your bot's capabilities!** 🚀

**Made with ❤️ by the Flash Development Team**
