import gedit
from gettext import gettext as _
import gtk
import gtk.glade
import os
import re

ui_str = """
<ui>
	<menubar name="MenuBar">
		<menu name="SearchMenu" action="Search">
			<placeholder name="SearchOps_3">
				<menuitem name="Regular expression..." action="RegexSearch"/>
			</placeholder>
		</menu>
	</menubar>
</ui>
"""

GLADE_FILE = os.path.join(os.path.dirname(__file__), "regexsearch.glade")

class RegexSearchInstance:

	###
	# Object initialization
	def __init__(self, window):
		self.id_name = 'RegexCustomPluginID'
		self._window = window
		self.keyboard_shortcuts()
		self.load_dialog()


	def keyboard_shortcuts(self):
		action_group = gtk.ActionGroup("RegexSearchActions")
		self._focus_action = gtk.Action("RegexSearch", _("Regex"), _("Regex"), gtk.STOCK_FIND_AND_REPLACE)
		self._focus_action.connect("activate", self.focus_action)
		action_group.add_action_with_accel(self._focus_action, "<Ctrl>comma")
		manager = self._window.get_ui_manager()
		manager.insert_action_group(action_group, -1)
		manager.add_ui_from_string(ui_str)

	def show(self, path, key, mode, changed):
		print path
		print key
		print mode
		print changed

	def focus_action(self, action):
		panel = self._window.get_bottom_panel()
		panel.show()
		panel.activate_item(self._search_dialog)
		self._window.set_focus(self._search_text_box)
		if not self._use_regex.get_active():
			document = self._window.get_active_document()
			document.set_search_text(self._search_text_box.get_text(), 0)

	###
	# Load dialog.
	#   - Load dialog from its Glade file
	#   - Connect widget signals
	#   - Put needed widgets in object variables.
	def load_dialog(self):
		self.enable_replace = False
		glade_xml = gtk.glade.XML(GLADE_FILE)

		self._search_dialog = glade_xml.get_widget("search_dialog")

		panel = self._window.get_bottom_panel()
		image = gtk.Image()
		image.set_from_stock(gtk.STOCK_FIND_AND_REPLACE, gtk.ICON_SIZE_MENU)
		ui_id = panel.add_item(self._search_dialog, "Regex", image)

		self._search_dialog.connect("delete_event", self._search_dialog.hide_on_delete)

		self._find_button = glade_xml.get_widget("find_button")
		self._find_button.connect("clicked", self.on_find_button_clicked)

		self._replace_button = glade_xml.get_widget("replace_button")
		self._replace_button.connect("clicked", self.on_replace_button_clicked)
		self._replace_all_button = glade_xml.get_widget("replace_all_button")
		self._replace_all_button.connect("clicked", self.on_replace_all_button_clicked)

		self._search_text_box = glade_xml.get_widget("search_text")
		self._search_text_box.connect("changed", self.on_search_text_changed)

		self._replace_text_box = glade_xml.get_widget("replace_text")
		self._replace_text_box.connect("changed", self.on_replace_text_changed)

		self._wrap_around_check = glade_xml.get_widget("wrap_around_check")
		self._use_backreferences_check = glade_xml.get_widget("use_backreferences_check")
		self._use_regex = glade_xml.get_widget("use_regex")
		self._dot_newline = glade_xml.get_widget("dot_newline")
		self._case_sensitive_check = glade_xml.get_widget("case_sensitive_check")


	###
	# Called when the "Find" button is clicked.
	def on_find_button_clicked(self, find_button):
		self.search_document()

	###
	# Called when the "Replace" button is clicked.
	def on_replace_button_clicked(self, replace_button):
		self.search_document(button = 'replace')

	# Called when the "Replace All" button is clicked.
	def on_replace_all_button_clicked(self, replace_button):
		document = self._window.get_active_document()
		start_iter = document.get_start_iter()
		end_iter = document.get_end_iter()
		alltext = unicode(document.get_text(start_iter, end_iter, False), "utf-8")

		regex = self.create_regex()
		if regex==None: return

		replace_string = self._replace_text_box.get_text()
		if not self._use_backreferences_check.get_active():
			replace_string = replace_string.replace('\\','\\\\') # turn \ into \\ so that backreferences are not done.
		new_string, n_replacements = regex.subn(replace_string, alltext)

		selection_bound_mark = document.get_mark("selection_bound")
		document.place_cursor(start_iter)
		document.move_mark(selection_bound_mark, end_iter)
		document.delete_selection(False, False)
		document.insert_at_cursor(new_string)

		self.show_alert_dialog(u"%d replacement(s)." % (n_replacements))

	###
	# Called when the "Close" button is clicked.
	def on_close_button_clicked(self, close_button):
		self._search_dialog.hide()

	def create_regex(self):
		try:
			# note multi-line flag, and dot does not match newline.
			text = self._search_text_box.get_text()
			if not self._use_regex.get_active():
				document = self._window.get_active_document()
				document.set_search_text(text, 0)
				text = re.sub(r'([\[\]])',r'\\\1',text)
				text = re.sub(r'(.)',r'[\1]',text) # escape everything for normal searching
				text = re.sub(r'\[\\\]\[([rnt])\]',r'\\\1',text)

			if self._dot_newline.get_active():
				if self._case_sensitive_check.get_active():
					regex = re.compile( unicode(text, "utf-8"), re.MULTILINE | re.DOTALL)
				else:
					regex = re.compile( unicode(text, "utf-8"), re.MULTILINE | re.IGNORECASE | re.DOTALL)
			else:
				if self._case_sensitive_check.get_active():
					regex = re.compile( unicode(text, "utf-8"), re.MULTILINE)
				else:
					regex = re.compile( unicode(text, "utf-8"), re.MULTILINE | re.IGNORECASE)
		except:
			self.show_alert_dialog(u"Invalid regular expression.")
			return None
		return regex

	###
	# Called when the text to be searched is changed. We enable the fields once. (still want to be able to replace '')
	def on_search_text_changed(self, search_text_entry):
		search_text  = search_text_entry.get_text()
		#if not self._use_regex.get_active():
		#	document.set_search_text(search_text, 0)
		#	search_text = re.sub(r'(.)',r'\\\1',search_text) # escape everything for normal searching
		#	print search_text
		replace_text_entry = self._replace_text_box

		if len(search_text) > 0:
			self._find_button.set_sensitive(True)
		else:
			self._find_button.set_sensitive(False)

		self.on_replace_text_changed(replace_text_entry)

	###
	# Called when the text to be replaced is changed.
	def on_replace_text_changed(self, replace_text_entry):
		if not self.enable_replace:
			replace_text = replace_text_entry.get_text()
			search_text  =  self._search_text_box.get_text()

			if len(search_text) > 0 and len(replace_text) > 0:
				self._replace_button.set_sensitive(True)
				self._replace_all_button.set_sensitive(True)
				self.enable_replace = True

	###
	# To update plugin's user interface
	def update_ui(self):
		pass


	###
	# Called to open the Regex Search dialog.
	def on_open_regex_dialog (self, action = None):
		self.enable_replace = False
		self._search_dialog.show()


	###
	# Search the document.
	#
	# The search begins from the current cursor position.
	def search_document(self, start_iter = None, wrapped_around = False, button = 'search'):
		document = self._window.get_active_document()

		if start_iter == None:
			start_iter = document.get_iter_at_mark(document.get_insert())

		end_iter = document.get_end_iter()

		regex = self.create_regex()

		if regex==None: return

		text = unicode(document.get_text(start_iter, end_iter, False), "utf-8")

		result = regex.search(text)

		if result != None:
			# There is a match

			self.handle_search_result(result, document, start_iter, wrapped_around, button)
		else:
			# No match found

			if self._wrap_around_check.get_active() and not wrapped_around and start_iter.get_offset() > 0:
				# Let's wrap around, searching the whole document
				self.search_document(document.get_start_iter(), True,button)
			else:
				# We've already wrapped around. There's no match in the whole document.
				self.show_alert_dialog(u"No match found for regular expression \"%s\"." % self._search_text_box.get_text())



	def show_alert_dialog(self, s):
		dlg = gtk.MessageDialog(self._window,
								gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
								gtk.MESSAGE_INFO,
								gtk.BUTTONS_CLOSE,
								_(s))
		dlg.run()
		dlg.hide()

	###
	# Handle search's result.
	# If the result is already selected, we search for the next match.
	# Otherwise we show it.
	#
	# The parameter "result" should contain the match result of a regex search.
	def handle_search_result(self, result, document, start_iter, wrapped_around = False,button='search'):
		curr_iter = document.get_iter_at_mark(document.get_insert())

		selection_bound_mark = document.get_mark("selection_bound")
		selection_bound_iter = document.get_iter_at_mark(selection_bound_mark)

		if button=='search':
			# If our result is already selected, we will search again starting from the end of
			# of the current result.
			if start_iter.get_offset() + result.start() == curr_iter.get_offset() and \
			   start_iter.get_offset() + result.end() == selection_bound_iter.get_offset():

				start_iter.forward_chars(result.end()+1) # To the first char after the current selection/match.

				# fixed bug- no wrapping when match at end of document, used to be get_offset() < document
				if start_iter.get_offset() <= document.get_end_iter().get_offset() and not wrapped_around:
					self.search_document(start_iter,False,button)
			else:
				self.show_search_result(result, document, start_iter, button)
		else:
			# If we are replacing, and there is a selection that matches, we want to replace the selection.
			# don't advance the cursor
			self.show_search_result(result, document, start_iter, button)

	###
	# Show search's result.
	# i.e.: Select the search result text, scroll to that position, etc.
	#
	# The parameter "result" should contain the match result of a regex search.
	def show_search_result(self, result, document, start_iter,button):

		selection_bound_mark = document.get_mark("selection_bound")

		result_start_iter = document.get_iter_at_offset(start_iter.get_offset() + result.start())
		result_end_iter = document.get_iter_at_offset(start_iter.get_offset() + result.end())

		document.place_cursor(result_end_iter) #REVERSED THESE - steve
		document.move_mark(selection_bound_mark, result_start_iter)

		if (button == 'replace'):
			replace_text = self._replace_text_box.get_text()
			self.replace_text(document,replace_text, result)

		view = self._window.get_active_view()
		view.scroll_to_cursor()

	def replace_text(self,document,replace_string, result):
		if not self._use_backreferences_check.get_active():
			replace_text = replace_string
		else:
			replace_text = result.expand(replace_string) # perform backslash expansion, like \1
		document.delete_selection(False, False)
		document.insert_at_cursor(replace_text)

		#now select the text that was replaced
