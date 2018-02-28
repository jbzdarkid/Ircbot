import ircbot

def send_message(message):
  print 'Sent message: "' + message + '"'

ircbot.send_message = send_message

ircbot.on_chat('test', '!ping')
ircbot.on_chat('test', '!ping asdfsdff 123123123')
ircbot.on_chat('test', '!commands')

print ircbot.twitch_api_get()
print ircbot.twitch_api_get('channel')