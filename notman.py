#!/usr/bin/env python2
'''Info Bar

is a widget that can be used to show messages to the user without showing a
dialog. It is often temporarily shown at the top or bottom of a document.
'''
# pygtk version: John Stowers <john.stowers@gmail.com>

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

		vb = gtk.VBox()
		scrolled.add_with_viewport(vb)

		self.make_notif(vb, "Title", "Body", "12:34:56", "gtk.png.small", first=True)
		self.make_notif(vb, "Lorem Ipsum", "Dolor sit amet.", "12:34:54", "gtk.png.small")
		self.make_notif(vb, "URGENT", "This is important!", "12:34:50", "gtk.png.small", "critical")
		self.make_notif(vb, "No Image", "Image-less notifications are supported", "12:30:14")
		self.make_notif(vb, "Multi-Line", "Multi-line bodies are supported\n\nSee?", "12:28:07", "gtk.png.small")

		self.show_all()

	def make_notif(self, parent, title, body, time, icon=None, urgency="Normal", first=False):
		if not first:
			hsep = gtk.HSeparator()
			parent.pack_start(hsep, False, False)

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
		parent.pack_start(stroke, False, False)
		#parent.pack_start(bar, False, False)

	def _on_close_clicked(self, button, bar):
		bar.destroy()

	def _on_bar_doubleclicked(self, signal, event, text):
		if event.type == gtk.gdk._2BUTTON_PRESS:
			print "\tTODO: Call function associated with the notification"
			print text

def main():
	InfoBarDemo()
	gtk.main()

if __name__ == '__main__':
	main()
