# Twitch script for HexChat
## by RenaKunisaki, based on TingPing's Twitch script
## https://github.com/RenaKunisaki/hexchat-twitch

This is a Python script for use with HexChat, providing several enhancements for
Twitch.tv chat.

# Features:
* Map (some) Twitch emotes to Emoji characters
* Display users' correct name colours and capitalization
* Custom nick prefixes (resembling Twitch name badges) for e.g. Mod, Subscriber
* Display jtv/twitchnotify messages in the channel tab
* Display channel title, status, game and viewer count in the channel topic
* More to come...

# Usage:
* Copy the `twitch` directory and `twitch.py` script into your HexChat addons directory (something like `~/.config/hexchat/addons/twitch.py`)
* Use `/twitch help` until proper documentation is written...
* This script is still in development, so expect bugs.

# Notes:
* This script requires Python 3.
* This script is no longer under development, since Twitch switched to using IRCv3 tags, and Hexchat doesn't expose those to scripts. (Also, the whisper system would require connecting to two servers at once, which is also not really feasible with Hexchat's API.)
