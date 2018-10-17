from io import BytesIO
from PIL import Image as PIL_Image
from PIL import ImageTk
from tkinter import *
from urllib import request
from datetime import datetime
from ircbot_reminder import Reminder

class ChatWindow(Canvas):
  def __init__(self, parent, reminders, *args, **kwargs):
    Canvas.__init__(self, parent, *args, **kwargs)
    scrollbar = Scrollbar(parent, orient='vertical', command=self.yview)
    scrollbar.pack(side='right', fill='y')
    self.config(yscrollcommand=scrollbar.set)
    self.bind_all('<MouseWheel>', self.onscroll)

    self.x = 2
    self.y = 9 # Half-line height
    self.reminders = reminders
    self.loaded_images = {}

  def load_image(self, name, url):
    # TODO: Disk caching?
    if name in self.loaded_images:
      return self.loaded_images[name]
    try:
      img_bytes = BytesIO(request.urlopen(url).read())
    except:
      print('Failed to load image [%s] from url [%s]' % (name, url))
      return
    self.loaded_images[name] = ImageTk.PhotoImage(PIL_Image.open(img_bytes))
    print('Loaded image [%s] from url [%s]' % (name, url))
    return self.loaded_images[name]

  def onscroll(self, event):
    # TODO: On mac, this should be just "event.delta"
    self.yview_scroll(event.delta//-120, 'units')

  def linewrap(self, length):
    self.update()
    if self.x + length > self.winfo_width():
      self.draw_newline()

  def draw_text(self, text, fill=None):
    if fill == None or fill == '':
      fill = 'white' # DEFAULT_TEXT

    self.linewrap(len(text)*10)
    self.create_text((self.x, self.y), anchor='w', font='courier', text=text, fill=fill)
    self.x += len(text)*10

  def draw_image(self, name, url):
    image = self.load_image(name, url)
    if not image:
      return
    self.linewrap(image.width())
    self.create_image((self.x, self.y), image=image, anchor='w')
    self.x += image.width() + 4

  def draw_newline(self):
    self.x = 0
    self.y += 28 # Standard twitch image height
    self.config(scrollregion=(0, 0, 0, self.y))
    self.yview_moveto(1.0)

  def on_command(self, line_data, username, message):
    parts = message.split(' ', 1)
    command = parts[0][1:].lower()
    contents = parts[1] if len(parts) > 1 else ''

    if command in ['remind', 'reminder', 'remindme']:
      server_time = datetime.fromtimestamp(int(line_data['tmi-sent-ts']) / 1000) # Float division
      contents = 'Reminder from %s at %s:\n%s' % (username, server_time.strftime('%I:%M:%S'), contents)
      Reminder(self.reminders, contents, text=username + ' ' + server_time.strftime('%I:%M:%S')).pack()

  def on_chat(self, line_data, username, message):
    global emotes # TODO: Class member?

    # https://stackoverflow.com/a/40223212
    def to_emoji(char):
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

    if 'bits' in line_data:
      print(line_data['bits']) # TODO: ???

    if message.startswith('!'):
      self.on_command(line_data, username, message)
      # return

    server_time = datetime.fromtimestamp(int(line_data['tmi-sent-ts']) / 1000) # Float division
    self.draw_text(server_time.strftime('%I:%M:%S') + ' ') # Draw the timestamp

    if 'badges' in line_data and line_data['badges'] != '':
      for badge in line_data['badges'].split(','):
        name, _ = badge.split('/')
        self.draw_image('badge_' + name, badges[name])

    if 'display-name' not in line_data or line_data['display-name'] == '':
      line_data['display-name'] = username

    if 'color' not in line_data:
      line_data['color'] = None
    self.draw_text(line_data['display-name'], line_data['color'])

    # 'Action' or '/me' message, should keep username color
    if message.startswith('\x01ACTION '):
      message = message[8:-1] # Trailing \x01 as well
    else: # Normal message, reset color
      line_data['color'] = None
      self.draw_text(': ')


    for word in message.split(' '):
      if word in emotes:
        self.draw_image('emote_' + word, emotes[word])
      else:
        self.draw_text(word + ' ', line_data['color'])
    self.draw_newline()


emotes = {
  'Kappa': 'https://static-cdn.jtvnw.net/emoticons/v1/25/1.0',
}

badges = {
  # TODO: These GUIDs come from somewhere...
  'premium': 'https://static-cdn.jtvnw.net/badges/v1/a1dd5073-19c3-4911-8cb4-c464a7bc1510/1',
  'subscriber': 'https://static-cdn.jtvnw.net/badges/v1/5d9f2208-5dd8-11e7-8513-2ff4adfae661/1',
  'bits': 'https://static-cdn.jtvnw.net/badges/v1/73b5c3fb-24f9-4a82-a852-2f475b59411c/1',
  'globalmod': 'https://static-cdn.jtvnw.net/chat-badges/globalmod.png',
  'admin': 'https://static-cdn.jtvnw.net/chat-badges/admin.png',
  'broadcaster': 'https://static-cdn.jtvnw.net/chat-badges/broadcaster.png',
  'mod': 'https://static-cdn.jtvnw.net/chat-badges/mod.png',
  'staff': 'https://static-cdn.jtvnw.net/chat-badges/staff.png',
  'turbo': 'https://static-cdn.jtvnw.net/chat-badges/turbo.png',
}
