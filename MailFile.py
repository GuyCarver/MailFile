import sublime, sublime_plugin
import sys, smtplib, functools, collections
from email.mime.text import MIMEText
from Edit.edit import Edit

sets_file = "MailFile.sublime-settings"
mf_settings = None

def plugin_loaded(  ) :
  global mf_settings
  mf_settings = sublime.load_settings(sets_file)

def SendMail( aRecipients, aSubject, aMessage ) :
  sender = mf_settings.get("from", "")
  mailhost = mf_settings.get("host", "10.0.0.68")
  recipientList = aRecipients.split(";")

  mimemsg = MIMEText(aMessage.encode("utf-8"), _charset="utf-8")
  mimemsg['Subject'] = aSubject
  mimemsg['From'] = sender
  mimemsg['To'] = aRecipients

  mailport = smtplib.SMTP(mailhost)
  try:
    mailport.sendmail(sender, recipientList, mimemsg.as_string())
  except:
    sublime.error_message("Failed to send mail")
  finally:
    mailport.quit()

# def GetViewName( aView ) :
#   return(aView.name() if aView.name() else aView.file_name())

class MailFileCommand( sublime_plugin.TextCommand ) :
  Active = None
  Commands = { "" : None }
  Processing = False

  def __init__( self, aView ) :
    super(MailFileCommand, self).__init__(aView)
    self.inputView = None

    MaxHist = mf_settings.get("maxhist", 20)
    entries = mf_settings.get("history", [""])
    # print "Entries %d:" % len(entries)
    # print entries
    #Read settings into history.
    self.History = collections.deque(entries, MaxHist)
    self.HistIndex = -1

  def IsInputView( self, aView ) :
    return (aView and self.inputView and aView.id() == self.inputView.id())

  def run( self, edit, cmd = "show", recipients = "", subject = "" ) :
    if cmd == "show" :
      MailFileCommand.Active = self
      self.inputView = self.view.window().show_input_panel("E-Mail Recipients separated by ;",
        recipients, functools.partial(self.OnDone, subject), None, self.OnCancel)
      self.inputView.set_name("Mail")
    else:
      theCommand = MailFileCommand.Commands[cmd]
      if theCommand :
        theCommand(self)

  def MoveHist( self, aDir ) :
    self.HistIndex = (self.HistIndex + aDir) % len(self.History)
    addr = self.History[self.HistIndex]
    if addr :
      vw = MailFileCommand.Active.inputView
      ext = vw.size()

      #Get entire text in view.
      whole = vw.substr(sublime.Region(0, ext))
      keep = whole.rfind(';')
      #Position of search start is either at the beginning or the last semicolon.
      search = (keep + 1) if keep != -1 else 0

      with Edit(vw) as edit:
        edit.replace(sublime.Region(search, ext), addr)

  def HistUp( self ) :
    self.MoveHist(1)

  def HistDown( self ) :
    self.MoveHist(-1)

  def HistMatch( self, bNext = True ) :
    MailFileCommand.Processing = True
    vw = MailFileCommand.Active.inputView
    #Start from beginning of selection and go to end of text.
    selStart = vw.sel()[0].a
    #Get entire text in view.
    whole = vw.substr(sublime.Region(0, vw.size()))
    keep = whole.rfind(';')
    #Position of search start is either at the beginning or the last semicolon.
    search = (keep + 1) if keep != -1 else 0

    #End search at cursor or selection begin.
    srch = unicode(vw.substr(sublime.Region(search, selStart)).strip(' '))

    # print(bNext)

    hsize = len(self.History)                             #Number of items to search.

    start = 1 if bNext else 0

    #Loop for items starting at next in history.
    for i in range(start, hsize):
      hi = (self.HistIndex + i) % hsize                   #Wrap index to beginning.
      n = self.History[hi]
      #If the history item begins with the search text then we found a match.
      if n.find(srch) == 0 :
        with Edit(vw) as edit :
          edit.replace(sublime.Region(search, vw.size()), n)
          vw.sel().clear()                                  #Clear previous selections.
          vw.sel().add(sublime.Region(selStart, vw.size())) # and add selection for new text.
        self.HistIndex = hi                               #Next index for next search.
        break

    MailFileCommand.Processing = False

  def HistList( self ) :
    print("MailFile History: " + str(len(self.History)))
    print(self.History)

  def SaveHistory( self ) :
    histList = [ h for h in self.History ]
    mf_settings.set("history", histList)
    sublime.save_settings(sets_file)

  def UpdateHistory( self, aRecipients ) :
    rlist = aRecipients.split(";")
    for r in rlist :
      rs = r.strip(' ')
      try:
        self.History.remove(rs)
      except:
        pass
      self.History.appendleft(rs)
    self.SaveHistory()

  def OnDone( self, subject, recipients ) :
    MailFileCommand.Active = None
    self.UpdateHistory(recipients)
    self.Send(recipients, subject)

  def OnCancel( self ) :
    MailFileCommand.Active = None

  def Send( self, recipients, subject ) :
    vw = self.view
    s = vw.sel()[0]
    fileName = lambda v : v.name() if v.name() else v.file_name()
    #if a selection is made then send it.
    #TODO: compile all selected text and send it.
    if s.a != s.b :
      if len(subject) == 0 :
        subject = "Here is a snippet from file: " + fileName(vw)
      message = vw.substr(s)
    else:
      if len(subject) == 0 :
        subject = "Here is file: " + fileName(vw)
      wholeFileReg = sublime.Region(0, vw.size() - 1)
      message = vw.substr(wholeFileReg)

    iview = self.view.window().show_input_panel("E-Mail Subject:",
        subject, functools.partial(self.OnSubjectDone, recipients, message), None, self.OnCancel)
    iview.set_name("MailSubject")

  def OnSubjectDone( self, aRecipients, aMessage, aSubject ):
    SendMail(aRecipients, aSubject, aMessage)

  @classmethod
  def IsActive( aClass, aView, aKey, aOperator, aOperand ) :
    ###Return true if the given view is the mailpanel.
    tf = False

    if aKey == "mailpanel" :
      if aClass.Active :
        tf = aClass.Active.IsInputView(aView)
    return tf

  @classmethod
  def TryComplete( aClass, aView ) :
    ###If mail recipient input is active try to auto complete any input.
    if aClass.Active and aClass.Active.IsInputView(aView) and not aClass.Processing :
      # print("TryComplete")
      aClass.Active.HistMatch(False)
      # print("TryCompleteEnd")

#List of run command types (Note show is not in this list  It is parsed separately).
MailFileCommand.Commands = { "hist_up" : MailFileCommand.HistUp,
                             "hist_down" : MailFileCommand.HistDown,
                             "hist_match" : MailFileCommand.HistMatch,
                             "hist_list" : MailFileCommand.HistList,
                           }

class RecipientEventListener( sublime_plugin.EventListener ) :
  def on_query_context( self, aView, aKey, aOperator, aOperand, match_all ) :
    return(MailFileCommand.IsActive(aView, aKey, aOperator, aOperand))

#This is interfering with the tab completion and doesn't work well with delete or backspace.
#  def on_modified( self, aView ) :
#    MailFileCommand.TryComplete(aView)
