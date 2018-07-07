from ircbot_reminder import Reminder
from ircbot_chat_window import ChatWindow
from datetime import datetime
from tkinter import *

DEFAULT_TEXT = 'white'
emotes = {}
badges = {
  # TODO: These guids come from somewhere...
  'premium': 'https://static-cdn.jtvnw.net/badges/v1/a1dd5073-19c3-4911-8cb4-c464a7bc1510/1',
  'subscriber': 'https://static-cdn.jtvnw.net/badges/v1/5d9f2208-5dd8-11e7-8513-2ff4adfae661/1',
  'globalmod': 'https://static-cdn.jtvnw.net/chat-badges/globalmod.png',
  'admin': 'https://static-cdn.jtvnw.net/chat-badges/admin.png',
  'broadcaster': 'https://static-cdn.jtvnw.net/chat-badges/broadcaster.png',
  'mod': 'https://static-cdn.jtvnw.net/chat-badges/mod.png',
  'staff': 'https://static-cdn.jtvnw.net/chat-badges/staff.png',
  'turbo': 'https://static-cdn.jtvnw.net/chat-badges/turbo.png',
}

def on_command(line_data, username, message):
  parts = message.split(' ', 1)
  command = parts[0][1:].lower()
  contents = parts[1] if len(parts) > 1 else ''

  if command in ['remind', 'reminder', 'remindme']:
    server_time = datetime.fromtimestamp(int(line_data['tmi-sent-ts']) / 1000) # Float division
    contents = 'Reminder from %s at %s:\n%s' % (username, server_time.strftime('%I:%M:%S'), contents)
    Reminder(reminders, contents, text=username + ' ' + server_time.strftime('%I:%M:%S')).pack()
  
def on_chat(line_data, username, message):
  global emotes
  
  # https://stackoverflow.com/a/40223212
  def to_emoji(char):
    assert ord(char) > 0xFFFF
    encoded = char.encode('utf-16-le')
    return (
      chr(int.from_bytes(encoded[:2], 'little')) + 
      chr(int.from_bytes(encoded[2:], 'little')))
    
  message = ''.join([c if ord(c) <= 0xFFFF else to_emoji(c) for c in message])

  # Parse twitch emote names
  if 'emotes' in line_data and line_data['emotes'] != '':
    for emote in line_data['emotes'].split('/'):
      # 'emotes':'1902:18-22/65:24-31/25:0-4,6-10,12-16'
      id, emote = emote.split(':')
      start, end = emote.split(',')[0].split('-')
      name = message[int(start):int(end)+1]
      # Twitch images. /2.0 and /3.0 are larger images.
      if name not in emotes:
        emotes[name] = 'https://static-cdn.jtvnw.net/emoticons/v1/' + id + '/1.0'

  # TODO: line_data['bits'] (int) ???

  if message.startswith('!'):
    on_command(line_data, username, message)
    # return

  server_time = datetime.fromtimestamp(int(line_data['tmi-sent-ts']) / 1000) # Float division
  chat_window.draw_text(server_time.strftime('%I:%M:%S') + ' ', DEFAULT_TEXT) # Draw the timestamp

  if 'badges' in line_data and line_data['badges'] != '':
    for badge in line_data['badges'].split(','):
      name, _ = badge.split('/')
      chat_window.draw_image('badge_' + name, badges[name])

  if 'display-name' not in line_data or line_data['display-name'] == '':
    line_data['display-name'] = username
  if 'color' not in line_data or line_data['color'] == '':
    line_data['color'] = DEFAULT_TEXT

  chat_window.draw_text(line_data['display-name'], line_data['color'])

  if message.startswith('\x01ACTION '):
    message = message[8:-1] # Trailing \x01 as well
    # Keep username color
  else:
    line_data['color'] = DEFAULT_TEXT
    chat_window.previous_was_text = False # TODO: This is a dirty hack.
    chat_window.draw_text(':', line_data['color'])
  
  for word in message.split(' '):
    if word in emotes:
      chat_window.draw_image('emote_' + word, emotes[word])
    else:
      chat_window.draw_text(word, line_data['color'])
  chat_window.draw_newline()



def start_ui():
  global root
  global reminders
  global canvas
  # Create the UI
  root = Tk()
  root.title('Ircbot')
  root.geometry('1000x1000')
  # root.iconbitmap('favicon.ico')
  reminders = Frame(root, width=250)
  reminders.pack(side='left')
  # TODO: Userlist

  # Button(root, text='Debug', fg='red', command=debug).pack(side='left')
  # Button(root, text='Kappa', fg='red', command=kappa).pack(side='left')
  chat_window = ChatWindow(root, bg='black')
  chat_window.pack(side='left', expand=True, fill='both')
  # chat_window.draw_text('Chat bot started on ' + datetime.now().strftime('%m/%d/%Y'), DEFAULT_TEXT)
  # chat_window.draw_newline()
  
  root.mainloop()
