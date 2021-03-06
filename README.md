# ![Avatar](https://i.imgur.com/Sv7L0a1.png) A.C.E. - Autonomous Command Executor

[![Discord Bots](https://discordbots.org/api/widget/status/367977994486022146.svg)](https://discordbots.org/bot/367977994486022146)

A fun, general purpose Discord bot that I run!

Want it in your server? [Click here to add it!](https://discordapp.com/oauth2/authorize?&client_id=367977994486022146&scope=bot&permissions=67497025)

The bot was initially made for the [AutoHotkey server](https://discord.gg/tPGdSr2).

## General Commands

To get a random animal picture:
```
.woof		Get a random doggo picture
.meow		Get a random cat picture
.quack		Get a random duck picture
.floof		Get a random fox picture
```

Miscellaneous other commands:
```
.stats		Gets command usage stats for your guild.
.define		Returns definition of a word.
.weather	Display weather information for a location.
.wolfram	Query Wolfram Alpha.
.fact		Get a random fact.
```

A complete list of available commands can be browsed by doing `.help`

## Modules

### Tags

The tags module makes it easy to bring up text. The tags system works like this:

```py
# this command creates a tag called 'test'
.tag create supportserver Hi there! Join my support server at https://discord.gg/X7abzRe

# calling the tag will make the bot echo back the tag contents:
.tag supportserver
# > Hi there! Join my support server at https://discord.gg/X7abzRe
```

To see a full list of tag related commands, do `.help tags`

### Welcome

The welcome module makes it easy to welcome new server members with a welcoming message. Has to be enabled using `.enable`

```py
# configure welcome channel and message:
.welcome channel #general
# > Channel is set to: #general
.welcome msg Hi there {user}! Welcome to {guild}!
# > New welcome message set. Do ".welcome test" to test!
.welcome test
# The above command will send a test message so you can confirm it works and looks like you want it to.
```

When a member joins, `{user}` is replaced with a mention and `{guild}` is replaced with the server name.

To see a full list of welcome message related commands, do `.help welcome`. To enable/disable welcome messages, simply toggle the module.

### Moderator

The moderator module has some basic moderation functionality. Has to be enabled using `.enable`

These commands are only available to members with the Ban Members permission.

`.clear [message_count] [user]`
Clears the newest `message_count` messages in the current channel, either indiscriminately or only messages from `user`.

`.info [user]`
Shows all practically useful information about a member or yourself.

### Highlighter

Makes it easier to paste code into the chat. Has to be enabled using `.enable`

`.hl <code>`
Deletes your message and reports the code in a code box, with emojis for message deletion.

`.lang <language>`
Change what syntax highlighting the bot should use for your code. For example: `py`, `ahk`, `html`, etc.

`.guildlang <language>`
Sets the default server specific syntax highlighting for `.hl`. Only changable by users with the Manage Server permission.

### Coins

Bet virtual coins. Lose it all or get rich! Has to be enabled using `.enable`

`.bet <coins>`
Bet an amount of coins. 50% of losing your bet!

`.coins [member]`
Show your balance, and other misc. stats.

## Bot moderation

To moderate the bot, you can list available modules by doing:
```
.mods
```

Then to enable or disable any module, do:
```
.enable <module>
.disable <module>
```

## Installation

If you want this bot in your server, I would prefer if you invite the official instance (which has excellent uptime!) using the invite link above. Nevertheless, here's how to set it up!

Create a PostgreSQL database and a role:
```sql
CREATE ROLE ace WITH LOGIN PASSWORD 'your_pw';
CREATE DATABASE acebot OWNER ace;
```

Then in the root folder, make a file called `config.py` and insert your bot token, api keys and miscellaneous:
```py
token = 'your_bot_token'
command_prefix = '.'
owner_id = user_id
db_bind = 'postgresql://ace:your_pw@host/acebot'
log_level = 'INFO'

dbl_key = 'key'
thecatapi_key = 'key'
wolfram_key = 'key'
apixu_key = 'key'
oxford_id, oxford_key = 'id', 'key'
```
## Acknowledgements

Avatar artwork: Vinter Borge
Contributors: Cap'n Odin #8812 and GeekDude #2532