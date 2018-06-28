import ircbot

def send(irc, message):
  print('Sent message: "' + message + '"')

ircbot.send_message = send_message

ircbot.on_chat('test', '!ping')
ircbot.on_chat('test', '!ping asdfsdff 123123123')
ircbot.on_chat('test', '!commands')
