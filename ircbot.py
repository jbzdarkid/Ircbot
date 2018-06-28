from socket import socket
from re import compile
from select import select
import threading
import requests
from config import chat_token, my_username
from datetime import datetime

from tkinter import *
import tkinter.scrolledtext as tkst # TODO: Non-absolute import?
from PIL import Image, ImageTk

#:jbzdarkid!jbzdarkid@jbzdarkid.tmi.twitch.tv PRIVMSG #jbzdarkid :Test Message
CHAT_MSG = compile('^:(\w+)!\w+@\w+.tmi.twitch.tv PRIVMSG #' + my_username + ' :(.*)\r\n$')
#:jtv!jtv@jtv.tmi.twitch.tv PRIVMSG jbzdarkid :PunchEmileAgainPlease is now hosting you.
JTV_MSG = compile('^:(\w+)!\w+@\w+.tmi.twitch.tv PRIVMSG ' + my_username + ' :(.*)\r\n$')

loaded_images = []
def on_chat(username, message):
  global text_label
  
  line = datetime.now().strftime('%I:%M:%S') + ' ' + username + ': ' + message

  if 'Kappa' in message:
    print(text_label.index(END))
    img = Image.open(r'C:\Users\localhost\Downloads\smile.png')
    loaded_images.insert(0, ImageTk.PhotoImage(img))
    image_label = Label(text_label.frame, image=loaded_images[0])

    x = line.index('Kappa')
    line.replace('Kappa', ' ')
    y = float(text_label.index(END))-1
    image_label.place(x=10*x, y=18*y)
  raw = text_label.get(1.0, END)

  text_label.configure(state='normal')
  text_label.insert(END, '\n' + line)
  text_label.see(END) # TODO: Doesn't respect if you are currently scrolling
  text_label.configure(state='disabled')

  if message.startswith('!'):
    message_parts = message[1:].split(' ')
    if message_parts[0] in COMMANDS:
      COMMANDS[message_parts[0]](message_parts[1:])

def send_whisper(username, message):
  send(irc, 'PRIVMSG #jtv :/w ' + username + ' ' + message)

def send_message(message):
  send(irc, 'PRIVMSG #jtv ' + my_username + ' :' + message)

def votekick(username, *args):
  print(('votekick start', username))

def ping(*args):
  send_message('pong')
  
def debug():
  on_chat('Ircbot', 'DEBUG')
  
def kappa():
  on_chat('Ircbot', 'Kappa ;)')

def commands(*args):
  command_list = list(COMMANDS.keys())
  command_list.sort()
  send_message('List of commands: ' + ', '.join(command_list))

COMMANDS = {
  'votekick': votekick,
  'ping': ping,
  'commands': commands,
}

def send(irc, message):
  irc.send(message.encode('utf-8') + b'\r\n')

def chat_listen():
  global irc
  global ui_running
  while ui_running: # Wait on messages from IRC
    # Wait for new data so that control-C works
    ready = select([irc], [], [], 1) # 1 second timeout
    if ready[0]:
      data = irc.recv(4096).decode('utf-8')
      if data == 'PING :tmi.twitch.tv\r\n':
        send(irc, 'PONG :tmi.twitch.tv')
        continue
      if CHAT_MSG.search(data):
        m = CHAT_MSG.search(data)
        on_chat(m.group(1), m.group(2))
      elif JTV_MSG.search(data):
        m = JTV_MSG.search(data)
        on_chat('Twitch', m.group(2))
      else:
        print('Unable to parse message: "' + data + '"')


if __name__ == '__main__':
  # Connect to twitch
  irc = socket()
  irc.connect(('irc.chat.twitch.tv', 6667))
  send(irc, 'PASS oauth:' + chat_token)
  send(irc, 'NICK ' + my_username)
  data = irc.recv(4096) # You are in a maze of twisty passages

  send(irc, 'JOIN #' + my_username)
  data = irc.recv(1024) # /JOIN
  data = irc.recv(1024) # End of /NAMES list
  
  send(irc, 'JOIN #jtv')
  data = irc.recv(1024) # /JOIN
  data = irc.recv(1024) # End of /NAMES list
  
  send(irc, 'JOIN #williamsem42')
  data = irc.recv(1024) # /JOIN
  data = irc.recv(1024) # End of /NAMES list

  irc.setblocking(0)

  send_message('Test') # TODO: This doesn't work.

  # Tkinter window
  root = Tk()
  root.title('Ircbot')
  root.geometry('500x500')

  Button(root, text='Ping', fg='red', command=ping).pack(side='bottom')
  Button(root, text='Debug', fg='red', command=debug).pack(side='bottom')
  Button(root, text='Kappa', fg='red', command=kappa).pack(side='bottom')
  
  chat_text = StringVar()
  # TODO: Replace this with a canvas, which will let me scroll images
  text_label = tkst.ScrolledText(root, font='courier', wrap=WORD)
  text_label.pack(expand=True, fill=BOTH)
  text_label.insert(INSERT, 'Chat bot started on ' + datetime.now().strftime('%m/%d/%Y'))
  text_label.configure(state='disabled')
  
  ui_running = True
  thread = threading.Thread(target=chat_listen)
  thread.daemon = True
  thread.start()
  root.mainloop()
  ui_running = False
  thread.join()
