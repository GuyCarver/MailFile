# Sublime Text 2 MailFile Package adding smtp e-mail support for e-mailing selections or files.

## Install

    $ https://github.com/GuyCarver/MailFile

## Instructions

This package supports e-mailing of either selected text or of an entire file.

### mail_file command arguments

recipients = "; separated list of e-mail recipients"<br>
subject = "Subject line string"

**example keybinding:**

	{ "keys": ["ctrl+shift+f1"], "command": "mail_file", "args": {"recipients": "myfriend@yahoo.com", "subject": "Here's my file."} },

### Settings:
* maxhist = 40 - Maximum number of e-mail addresses to store in the history.
* from = youremail@address.com - You will need to set this.
* host = The IP address of your e-mail host.  You will also need to set this.

### Key Bindings:

* ctrl+f1 = e-mail file or selection.

#### TODO:
* Support multiple selections.
* History listing/editing.
