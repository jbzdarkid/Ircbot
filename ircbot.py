from socket import socket
from re import compile
from select import select
import threading
import requests
from config import chat_token, username

from tkinter import *

CHAT_MSG = compile('^:(\w+)!\w+@\w+.tmi.twitch.tv PRIVMSG #' + username + ' :(.*)\r\n$')

def on_chat(username, message):
  print(username+': '+message)
  print((username+': '+message))

  if message.startswith('!'):
    message_parts = message[1:].split(' ')
    if message_parts[0] in COMMANDS:
      COMMANDS[message_parts[0]](message_parts[1:])

def votekick(username, *args):
  print(('votekick start', username))

def ping(*args):
  send_message('pong')

def commands(*args):
  command_list = list(COMMANDS.keys())
  command_list.sort()
  send_message('List of commands: ' + ', '.join(command_list))

COMMANDS = {
  'votekick': votekick,
  'ping': ping,
  'commands': commands,
}

def start_ui():
  root = Tk()
  root.title('Ircbot')
  root.geometry('500x500')

  title = Button(root)
  title['text'] = "QUIT"
  title['fg'] = "red"
  title['command'] = ping
  title.pack({"side": "left"})


  root.mainloop()
  root.destroy()

if __name__ == '__main__':
  thread = threading.Thread(target=start_ui)
  thread.daemon = True
  thread.start()

  # Connect to twitch
  irc = socket()
  irc.connect(('irc.chat.twitch.tv', 6667))
  irc.send('PASS oauth:' + chat_token + '\r\n')
  irc.send('NICK ' + username + '\r\n')
  data = irc.recv(4096) # You are in a maze of twisty passages

  irc.send('JOIN #' + username + '\r\n') 
  data = irc.recv(1024) # /JOIN
  data = irc.recv(1024) # End of /NAMES list
  irc.setblocking(0)

  while 1:
    # Wait for new data so that control-C works
    ready = select([irc], [], [], 1) # 1 second timeout
    if ready[0]:
      data = irc.recv(4096)
      if data == 'PING :tmi.twitch.tv\r\n':
        irc.send('PONG :tmi.twitch.tv\r\n'.encode("utf-8"))
        continue
      m = CHAT_MSG.search(data)
      if not m:
        print('Unable to parse message: "' + data + '"')
        continue
      on_chat(m.group(1), m.group(2))

  def send_whisper(username, message):
    irc.send('PRIVMSG #jtv :/w '+username+' '+message+'\r\n')

  def send_message(message):
    irc.send('PRIVMSG #'+username+' :'+message+'\r\n')
