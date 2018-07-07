from tkinter import *

class Reminder(Button):
  def __init__(self, parent, contents, *args, **kwargs):
    Button.__init__(self, parent, *args, **kwargs)
    self.contents = contents
    self.height = 20
    self.width = 250
    self.popup = None
    self.bind('<Button-1>', self.leftclick)
    self.bind('<Button-3>', self.rightclick)

  def leftclick(self, event):
    if self.popup:
      return
    self.popup = Toplevel()
    self.popup.geometry('200x200')
    Label(self.popup, text=self.contents).pack()

  def rightclick(self, event):
    if self.popup:
      self.popup.destroy()
    self.destroy()

class User(Label):
  def __init__(self, parent, *args, **kwargs):
    pass