# Todo list:

* More commands:
  * refresh/redownload user/channel info from Twitch API
  * hook Twitch commands: /ban, /commercial, etc
  * hook `/topic` to trigger a manual update and display it, especially since it does nothing currently
  * make `/twitch set` use a better syntax, like `/twitch set user.joe.bot true`
  * be able to change settings: `/twitch set usertypes.mod.format %B{}`
  * be able to display the unformatted text for an emote (`/twitch emote raw Kappa`) to be able to edit it easily
    * non-case-sensitive matching for emote commands
	* can the emote commands be e.g. `/twitch set emote.Kappa ;)` instead of
	  a separate command? (would need to also add del/show/list commands)
	  * Not if we want to be able to list all emotes you can use (whether we
	    have emojis for them or not).
  * be able to change the log levels for file/console output
  * better command handling in general
  
* More Twitch integration:
  * WHISPER function: figure out what servers we can use that support this AND actually relay chat messages
  * Ignore people who are on your Twitch account's ignore list
    * Be able to edit that list
	* Optional notification when someone is ignored
  * Open a PM window when you receive a message on Twitch
    * also look into group/private chat system
  * Notify message when someone you follow goes online
  * Correctly request specific API version: https://github.com/justintv/twitch-api
  
* More local customization:
  * Be able to edit user attributes locally, such as nick colour, displayed nick, custom badges, etc (per user)
  * Be able to launch livestreamer for the current channel
  
* Better handling of some events:
  * Option to filter out repeated "this room is in slow mode" messages when the slow mode setting hasn't changed
    * Check for slow mode, subs-only mode, r9k mode etc when joining
	* Include these attributes in the `channel` object so they can be shown in topic
  * logger: Be able to emit log events to a context of their own
  * Synthesize NICK message to rename users to their proper display name once we know what it is, so it shows up in the user list.
    * Will need to queue these like we do with TOPIC because posting them from another thread will probably crash hexchat again.
	  * Probably should change that mechanism to just be a list of commands to run in the main thread rather than topic changes specifically.
  * Maybe auto prune the user list, removing users who haven't spoken for a while, since we can't reliably tell when they actually leave
    * Or, give +v to people who speak, and -v if they're idle for a while.
  * Reloading the script, then speaking, wipes out the userlist (but only if someone else has spoken before you?)
    * This is not surprising, since reloading loses all channel/user state, so we send a new JOIN when someone (including ourselves) speaks, and hexchat responds by wiping out the userlist.
	* This is probably not a big deal.
	* Simple fix might be to go through the userlist on load (like we do for the channel list) and mark people as being in the channel, so we don't re-send JOINs for them.
  * Make messages like "Joe just subscribed" and "Joe has been timed out" look different than actions
  
* Better emote handling:
  * If we don't have an emoji for some emote, colour the text differently so it's still clear it's meant to be an emote
    * Refresh user info periodically to check their emote sets
  * Use the same regexes as Twitch (e.g. `Kappatest` shouldn't match `Kappa`)
    * Currently also KappaHD renders as 😏HD, since emotes.json is sorted, and Kappa comes first
  * Don't require %R after every coloured emote
