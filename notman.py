#!/usr/bin/env python

#
#   statnot - Status and Notifications
#
#   Lightweight notification-(to-become)-deamon intended to be used
#   with lightweight WMs, like dwm.
#   Receives Desktop Notifications (including libnotify / notify-send)
#   See: http://www.galago-project.org/specs/notification/0.9/index.html
#
#   Note: VERY early prototype, to get feedback.
#
#   Copyright (c) 2009-2011 by the authors
#   http://code.k2h.se
#   Please report bugs or feature requests by e-mail.
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import dbus
import dbus.service
import dbus.mainloop.glib
import gobject
import os
import subprocess
import sys
import thread
import time
from htmlentitydefs import name2codepoint as n2cp
import re
import glib

# ===== CONFIGURATION DEFAULTS =====
#
# See helpstring below for what each setting does

DEFAULT_NOTIFY_TIMEOUT = 3000 # milliseconds
MAX_NOTIFY_TIMEOUT = 5000 # milliseconds
NOTIFICATION_MAX_LENGTH = 100 # number of characters
STATUS_UPDATE_INTERVAL = 2.0 # seconds
STATUS_COMMAND = ["/bin/sh", "%s/.statusline.sh" % os.getenv("HOME")]
USE_STATUSTEXT=False
QUEUE_NOTIFICATIONS=True

import pygtk
pygtk.require('2.0')
import gtk



class InfoBarDemo(gtk.Window):
	def __init__(self, parent=None):
		gtk.Window.__init__(self)
		try:
			self.set_screen(parent.get_screen())
		except AttributeError:
			self.connect('destroy', lambda *w: gtk.main_quit())
		self.set_title(self.__class__.__name__)
		self.set_border_width(8)

		scrolled = gtk.ScrolledWindow()
		scrolled.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)

		self.add(scrolled)

		self.vb = gtk.VBox()
		self.vb.set_spacing(2)
		scrolled.add_with_viewport(self.vb)

		self.make_notif("Title", "Body", "12:34:56", "gtk.png.small", first=True)
		self.make_notif("Lorem Ipsum", "Dolor sit amet.", "12:34:54", "gtk.png.small")
		self.make_notif("URGENT", "This is important!", "12:34:50", "gtk.png.small", "critical")
		self.make_notif("No Image", "Image-less notifications are supported", "12:30:14")
		self.make_notif("Multi-Line", "Multi-line bodies are supported\n\nSee?", "12:28:07", "gtk.png.small", timeout=5000)

		self.show_all()

	def make_notif(self, title, body, time, icon=None, urgency="Normal", first=False, timeout=None):
		#if not first:
		#	hsep = gtk.HSeparator()
		#	self.vb.pack_start(hsep, False, False)

		# HBox needs an eventbox to draw a background
		hbox = gtk.HBox()
		hbox.set_border_width(4)
		eb = gtk.EventBox()
		eb.add(hbox)
		eb.set_border_width(1)
		stroke = gtk.EventBox()
		stroke.add(eb)

		cmap = self.get_colormap()
		#error_bg_color = gtk.gdk.color_parse("#0f0")
		gtk.info_bg_color = cmap.alloc_color("#00ff00", True, False)

		# adjust colors
		if urgency == "critical" :
			eb.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color("#ed3333"))
			stroke.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color("#822b2b"))
		else :
			eb.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color("#ffffff"))
			stroke.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color("#828282"))

		# create image
		image = gtk.Image()
		if( icon ):
			image.set_from_file(icon)
			hbox.pack_start(image, False, False, 8)
		else:
			if urgency == "critical" :
				image.set_from_stock(gtk.STOCK_DIALOG_ERROR, gtk.ICON_SIZE_DIALOG)
			else:
				image.set_from_stock(gtk.STOCK_DIALOG_INFO, gtk.ICON_SIZE_DIALOG)
			hbox.pack_start(image, False, False, 13)

		# for text boxes
		vbox = gtk.VBox()

		# make some labels
		title_label = gtk.Label()
		title_label.set_markup("<b>" +title +"</b>")
		body_label = gtk.Label(body)

		# adjust alignment
		title_label.set_alignment(0, 1)
		body_label.set_alignment(0, 0)
		body_label.set_line_wrap(True)

		# pack the text views
		vbox.pack_start(title_label, True, True)
		vbox.pack_start(body_label, True, True)

		# pack the textview combos
		hbox.pack_start(vbox, True, True)

		# new vbox
		vbox = gtk.VBox(False)

		# make time label
		time_label = gtk.Label()
		time_label.set_markup("<small>" +time +"</small>")
		time_label.set_alignment(1, 1)

		# add time
		vbox.pack_end(time_label, True, True)

		# button
		button = gtk.Button("", gtk.STOCK_CLOSE)
		button.connect( "clicked", self._on_close_clicked, stroke)

		stroke.connect( "event", self._on_bar_doubleclicked, body_label.get_text())

		# dead space
		alignment = gtk.Alignment(1.0, 1.0, 0.0, 0.0)
		alignment.add(button)
		vbox.pack_start(alignment)

		hbox.pack_start(vbox, True, True)


		# add to bar, then main window
		self.vb.pack_start(stroke, False, False)
		#self.vb.pack_start(bar, False, False)
		self.vb.show_all()

		if timeout:
			print "got notification with timeout", timeout
			glib.timeout_add(int(timeout), self._invalidate_notification, stroke)

	def _invalidate_notification(self, bar):
		eventbox = bar.get_child()
		eventbox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color("#cccccc"))


	def _on_close_clicked(self, button, bar):
		bar.destroy()

	def _on_bar_doubleclicked(self, signal, event, text):
		if event.type == gtk.gdk._2BUTTON_PRESS:
			print "\tTODO: Call function associated with the notification"
			print text

ibd = InfoBarDemo()

# dwm
def update_text(text):
    # Get first line
    first_line = text.splitlines()[0] if text else ''
    if first_line != '':
        print first_line
    #subprocess.call(["xsetroot", "-name", first_line])

# ===== CONFIGURATION END =====

def _getconfigvalue(configmodule, name, default):
    if hasattr(configmodule, name):
        return getattr(configmodule, name)
    return default

def readconfig(filename):
    import imp
    try:
        config = imp.load_source("config", filename)
    except Exception as e:
        print "Error: failed to read config file %s" % filename
        print e
        sys.exit(2)

    for setting in ("DEFAULT_NOTIFY_TIMEOUT", "MAX_NOTIFY_TIMEOUT", "NOTIFICATION_MAX_LENGTH", "STATUS_UPDATE_INTERVAL",
                    "STATUS_COMMAND", "USE_STATUSTEXT", "QUEUE_NOTIFICATIONS", "update_text"):
        if hasattr(config, setting):
            globals()[setting] = getattr(config, setting)

def strip_tags(value):
  "Return the given HTML with all tags stripped."
  return re.sub(r'<[^>]*?>', '', value)

# from http://snipplr.com/view/19472/decode-html-entities/
# also on http://snippets.dzone.com/posts/show/4569
def substitute_entity(match):
  ent = match.group(3)
  if match.group(1) == "#":
    if match.group(2) == '':
      return unichr(int(ent))
    elif match.group(2) == 'x':
      return unichr(int('0x'+ent, 16))
  else:
    cp = n2cp.get(ent)
    if cp:
      return unichr(cp)
    else:
      return match.group()

def decode_htmlentities(string):
  entity_re = re.compile(r'&(#?)(x?)(\w+);')
  return entity_re.subn(substitute_entity, string)[0]

# List of not shown notifications.
# Array of arrays: [id, text, timeout in s]
# 0th element is being displayed right now, and may change
# Replacements of notification happens att add
# message_thread only checks first element for changes
notification_queue = []
notification_queue_lock = thread.allocate_lock()

def add_notification(notif):
    with notification_queue_lock:
        for index, n in enumerate(notification_queue):
            if n[1] == notif[1]: # same id, replace instead of queue
                n = notif
                return

        notification_queue.append(notif)



def message_thread(dummy):
    last_status_update = 0
    last_notification_update = 0
    current_notification_text = ''

    while 1:
        if notification_queue :
            for notif in notification_queue :
                print notification_queue.pop()
            print "-"*25

        time.sleep(0.1)

class NotificationFetcher(dbus.service.Object):
    _id = 0

    @dbus.service.method("org.freedesktop.Notifications",
                         in_signature='susssasa{ss}i',
                         out_signature='u')
    def Notify(self, app_name, notification_id, app_icon,
               summary, body, actions, hints, expire_timeout):
        if (expire_timeout < 0) or (expire_timeout > MAX_NOTIFY_TIMEOUT):
            expire_timeout = DEFAULT_NOTIFY_TIMEOUT

        if not notification_id:
            self._id += 1
            notification_id = self._id

        add_notification( [app_name.strip(), notification_id,
                          summary.strip(), body.strip(),
                          int(expire_timeout) / 1000.0, app_icon] )
        ibd.make_notif( summary.strip(), body.strip(), time.strftime("%d %b %Y %H:%M:%S", time.localtime()), icon=app_icon, timeout=3000)
        print "made notif"
        return notification_id

    @dbus.service.method("org.freedesktop.Notifications", in_signature='', out_signature='as')
    def GetCapabilities(self):
        return ("body")

    @dbus.service.signal('org.freedesktop.Notifications', signature='uu')
    def NotificationClosed(self, id_in, reason_in):
        pass

    @dbus.service.method("org.freedesktop.Notifications", in_signature='u', out_signature='')
    def CloseNotification(self, id):
        pass

    @dbus.service.method("org.freedesktop.Notifications", in_signature='', out_signature='ssss')
    def GetServerInformation(self):
      return ("statnot", "http://code.k2h.se", "0.0.2", "1")

if __name__ == '__main__':
    for curarg in sys.argv[1:]:
        if curarg in ('-v', '--version'):
            print "%s CURVERSION" % sys.argv[0]
            sys.exit(1)
        elif curarg in ('-h', '--help'):
            print "  Usage: %s [-h] [--help] [-v] [--version] [configuration file]" % sys.argv[0]
            print "    -h, --help:    Print this help and exit"
            print "    -v, --version: Print version and exit"
            print ""
            print "  Configuration:"
            print "    A file can be read to set the configuration."
            print "    This configuration file must be written in valid python,"
            print "    which will be read if the filename is given on the command line."
            print "    You do only need to set the variables you want to change, and can"
            print "    leave the rest out."
            print ""
            print "    Below is an example of a configuration which sets the defaults."
            print ""
            print "      # Default time a notification is show, unless specified in notification"
            print "      DEFAULT_NOTIFY_TIMEOUT = 3000 # milliseconds"
            print "      "
            print "      # Maximum time a notification is allowed to show"
            print "      MAX_NOTIFY_TIMEOUT = 5000 # milliseconds"
            print "      "
            print "      # Maximum number of characters in a notification. "
            print "      NOTIFICATION_MAX_LENGTH = 100 # number of characters"
            print "      "
            print "      # Time between regular status updates"
            print "      STATUS_UPDATE_INTERVAL = 2.0 # seconds"
            print "      "
            print "      # Command to fetch status text from. We read from stdout."
            print "      # Each argument must be an element in the array"
            print "      # os must be imported to use os.getenv"
            print "      import os"
            print "      STATUS_COMMAND = ['/bin/sh', '%s/.statusline.sh' % os.getenv('HOME')] "
            print ""
            print "      # Always show text from STATUS_COMMAND? If false, only show notifications"
            print "      USE_STATUSTEXT=True"
            print "      "
            print "      # Put incoming notifications in a queue, so each one is shown."
            print "      # If false, the most recent notification is shown directly."
            print "      QUEUE_NOTIFICATIONS=True"
            print "      "
            print "      # update_text(text) is called when the status text should be updated"
            print "      # If there is a pending notification to be formatted, it is appended as"
            print "      # the final argument to the STATUS_COMMAND, e.g. as $1 in default shellscript"
            print ""
            print "      # dwm statusbar update"
            print "      import subprocess"
            print "      def update_text(text):"
            print "          subprocess.call(['xsetroot', '-name', text])"
            sys.exit(1)
        else:
            readconfig(curarg)

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    session_bus = dbus.SessionBus()
    name = dbus.service.BusName("org.freedesktop.Notifications", session_bus)
    nf = NotificationFetcher(session_bus, '/org/freedesktop/Notifications')

    # We must use contexts and iterations to run threads
    # http://www.jejik.com/articles/2007/01/python-gstreamer_threading_and_the_main_loop/
    gobject.threads_init()
    context = gobject.MainLoop().get_context()
    thread.start_new_thread(message_thread, (None,))

    while 1:
        context.iteration(True)

	#InfoBarDemo()
	gtk.main()

