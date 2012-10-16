import gedit, gtk, gconf, ctypes

class TweaksPlugin(gedit.Plugin):

	def __init__(self):
		pass

	def activate(self, window):
		self.window = window
		self.client = gconf.client_get_default()
		self.ready_id = None
		self.dropMenu = None
		self.bottom_panel_click_id = None
		self.first_run = True
		self.right_pane_old = False
		tab = self.window.get_active_tab()
		if(tab != None):
			self.ready(None, None)
		else:
			self.init()

	def deactivate(self, window):

		if(self.client.get_bool("/apps/gedit-2/plugins/tweaks/paneRight")):
			self.swap_panes(200)

		self.tab_position(2)
		self.hide_tabs(False)
		#self.pane_right()
		self.compact_menu(False)
		self.remove_uglies(False)

	def update_ui(self, window):
		pass

	def init(self):
		if(self.ready_id == None):
			self.ready_id = self.window.connect("event", self.ready)

	def cancel(self, param):
		self.config_dialog.hide()

	def create_configure_dialog(self):
		self.config_dialog = gtk.Dialog("Tab Setup")
		content = self.config_dialog.get_content_area()

		label = gtk.Label("Tab Position:")
		label.show()
		label.set_justify(gtk.JUSTIFY_LEFT)
		label.set_width_chars(10)

		dropbox = gtk.combo_box_new_text()
		dropbox.append_text("Right")
		dropbox.append_text("Left")
		dropbox.append_text("Top")
		dropbox.append_text("Bottom")
		dropbox.show()
		dropbox.set_active(self.client.get_int("/apps/gedit-2/plugins/tweaks/tabPosition"))
		dropbox.connect("changed", self.tab_position_setting)

		box = gtk.HBox()
		box.show()
		box.pack_start(label)
		box.pack_start(dropbox)

		showTabs = gtk.CheckButton("Hide Tabs?")
		showTabs.show()
		showTabs.set_active(self.client.get_bool("/apps/gedit-2/plugins/tweaks/hideTabs"))
		showTabs.connect("clicked", self.hide_tabs_setting)

		paneRight = gtk.CheckButton("Side Pane on the Right?")
		paneRight.show()
		paneRight.set_active(self.client.get_bool("/apps/gedit-2/plugins/tweaks/paneRight"))
		paneRight.connect("clicked", self.pane_right_setting)

		compactMenu = gtk.CheckButton("Compact Menu?")
		compactMenu.show()
		compactMenu.set_active(self.client.get_bool("/apps/gedit-2/plugins/tweaks/compactMenu"))
		compactMenu.connect("clicked", self.compact_menu_setting)

		removeUglies = gtk.CheckButton("Hide \"Uglies\"?")
		removeUglies.show()
		removeUglies.set_active(self.client.get_bool("/apps/gedit-2/plugins/tweaks/removeUglies"))
		removeUglies.connect("clicked", self.remove_uglies_setting)

		tabWidthCheckbox = gtk.CheckButton("Force tab width?")
		tabWidthCheckbox.show()
		tabWidthCheckbox.set_active(self.client.get_bool("/apps/gedit-2/plugins/tweaks/tabWidthEnabled"))
		tabWidthCheckbox.connect("clicked", self.tab_width_enabled_setting)

		width = self.client.get_int("/apps/gedit-2/plugins/tweaks/tabWidth")
		if(width == None):
			width = 100
		tabWidth = gtk.SpinButton(gtk.Adjustment(width, 1, 999, 1), 1)
		tabWidth.show()
		tabWidth.connect("output", self.tab_width_setting)

		tabSetting = gtk.HBox()
		tabSetting.pack_start(tabWidthCheckbox)
		tabSetting.pack_start(tabWidth)
		tabSetting.show()

		vbox = gtk.VBox()
		vbox.pack_start(box)
		vbox.pack_start(showTabs)
		vbox.pack_start(paneRight)
		vbox.pack_start(compactMenu)
		vbox.pack_start(removeUglies)
		vbox.pack_start(tabSetting)
		vbox.show()
		content.pack_start(vbox)

		actions = self.config_dialog.get_action_area()
		cancel = gtk.Button("Close")
		cancel.connect("clicked", self.cancel)
		cancel.show()
		actions.pack_end(cancel)

		return self.config_dialog

	def ready(self, event, data):
		tab = self.window.get_active_tab()
		if(tab != None):
			self.tab_position()
			self.hide_tabs()
			self.pane_right()
			self.compact_menu()
			self.remove_uglies()

			#MOVE STOP BUTTON TO TAB
#			notebook = self.window.get_bottom_panel().get_children()[0].get_children()[0]
#			stop = notebook.get_children()[1].get_children()[1]
#			stop.get_parent().remove(stop)
#			notebook.get_tab_label(notebook.get_children()[1]).pack_start(stop)
#			buttonBox = notebook.get_tab_label(notebook.get_children()[1]).get_children()[1]
#			buttonBox.set_property("border-width", 0)
			#button = buttonBox.get_children()[0]
			#END MOVE

			if(self.ready_id != None):
				self.window.disconnect(self.ready_id)
				self.ready_id = None
			#self.addMiddleClick()


	def remove_uglies_setting(self, checkbox):
		self.client.set_bool("/apps/gedit-2/plugins/tweaks/removeUglies", checkbox.get_active())
		self.remove_uglies()

	def get_child_by_type(self, obj, type):
		if(isinstance(obj, type)):
			self.temp = obj

	def remove_uglies(self, force=None):
		do = force
		if(force == None):
			do = self.client.get_bool("/apps/gedit-2/plugins/tweaks/removeUglies")
		bottom_panel_tabs = self.window.get_bottom_panel().get_children()[0].get_children()

		#bottom_panel_tabs[0].foreach(self.get_child_by_type, gtk.HBox)
		#shell = self.temp

		uglies = []
		try:
			uglies = [
				self.window.get_side_panel().get_children()[0], #title to side bar
				bottom_panel_tabs[1], #close button to bottom panel (use middle click)
				bottom_panel_tabs[0].get_children()[0].get_children()[1]
			]
		except IndexError:
			return

		if(do):
			for ugly in uglies:
				ugly.hide()
			#allow closing bottom panel with a middle click
			self.bottom_panel_click_id = self.window.get_bottom_panel().connect("button-press-event", self.close_bottom_panel)
		else:
			for ugly in uglies:
				ugly.show()
			if(self.bottom_panel_click_id != None):
				self.window.get_bottom_panel().disconnect(self.bottom_panel_click_id)
				self.bottom_panel_click_id = None

	def close_bottom_panel(self, widget, event):
		if(event.button == 2):
			self.window.get_bottom_panel().hide()

	def hide_tabs_setting(self, checkbox):
		self.client.set_bool("/apps/gedit-2/plugins/tweaks/hideTabs", checkbox.get_active())
		self.hide_tabs()

	def hide_tabs(self, force=None):
		tab = self.window.get_active_tab()
		if(tab != None):
			notebook = tab.get_parent()
			if(force == None):
				notebook.set_show_tabs(not self.client.get_bool("/apps/gedit-2/plugins/tweaks/hideTabs"))
			else:
				notebook.set_show_tabs(not force)
			notebook.foreach(self.tab_adjustment)
			#self.tab_small()
			notebook.connect("page-added", self.tab_adjustment_wrapper)
			notebook.set_property("tab_border", 0)


	def pane_right_setting(self, checkbox):
		self.right_pane_old = self.client.get_bool("/apps/gedit-2/plugins/tweaks/paneRight")
		self.client.set_bool("/apps/gedit-2/plugins/tweaks/paneRight", checkbox.get_active())
		self.pane_right()

	def pane_right(self):
		do_swap = self.client.get_bool("/apps/gedit-2/plugins/tweaks/paneRight")
		if(self.first_run):
			if(do_swap): #MOVE SIDE PANE TO THE RIGHT
				self.swap_panes()
			self.first_run = False
		elif(do_swap != self.right_pane_old):
			self.right_pane_old = do_swap
			if(do_swap):
				self.swap_panes()
			else:
				self.swap_panes(200)
		self.right_pane_old = do_swap


	def swap_panes(self, position=None):
		paned = self.window.get_side_panel().get_parent()
		one = paned.get_child1()
		two = paned.get_child2()
		paned.remove(one)
		paned.remove(two)
		paned.pack1(two, True)
		paned.pack2(one, False)
		paned = self.window.get_side_panel().get_parent()
		(width, height) = self.window.get_default_size()
		paned.compute_position(width, 100, 100)
		if(position == None):
			self.movedRight = True
			paned.set_position(width - 200)
		else:
			self.movedRight = False
			paned.set_position(position)

	def tab_width_enabled_setting(self, checkbox):
		self.client.set_bool("/apps/gedit-2/plugins/tweaks/tabWidthEnabled", checkbox.get_active())
		if(self.client.get_int("/apps/gedit-2/plugins/tweaks/tabWidth") == None):
			self.client.set_int("/apps/gedit-2/plugins/tweaks/tabWidth", 100)
		self.hide_tabs()

	def tab_width_setting(self, obj):
		self.client.set_int("/apps/gedit-2/plugins/tweaks/tabWidth", int(obj.get_value()))
		self.hide_tabs()

	def tab_position_setting(self, dropbox):
		self.client.set_int("/apps/gedit-2/plugins/tweaks/tabPosition", dropbox.get_active())
		self.tab_position()
	def tab_position(self, position=None):
		tab = self.window.get_active_tab()
		if(tab != None):
			if(position == None):
				position = self.client.get_int("/apps/gedit-2/plugins/tweaks/tabPosition")
			if(position == 0):
				self.position = gtk.POS_RIGHT
			elif(position == 1):
				self.position = gtk.POS_LEFT
			elif(position == 2):
				self.position = gtk.POS_TOP
			else:
				self.position = gtk.POS_BOTTOM
			notebook = tab.get_parent()
			notebook.set_tab_pos(self.position)
			#notebook.foreach(self.tab_adjustment)
			#notebook.set_property("tab_border", 0)

	def tab_adjustment_wrapper(self, notebook, tab, which):
		self.tab_adjustment(tab)


	def tab_adjustment(self, tab):
		width = self.client.get_int("/apps/gedit-2/plugins/tweaks/tabWidth")
		enabled = self.client.get_bool("/apps/gedit-2/plugins/tweaks/tabWidthEnabled")
		if(width != None and enabled != None and enabled):
			tab.get_parent().get_tab_label(tab).set_property("width-request", width)
		else:
			tab.get_parent().get_tab_label(tab).set_property("width-request", -1)

	def tab_small(self):
		tab = self.window.get_active_tab()
		if(tab != None):
			tab.get_parent().set_tab_vborder(0)


	def compact_menu_setting(self, checkbox):
		self.client.set_bool("/apps/gedit-2/plugins/tweaks/compactMenu", checkbox.get_active())
		self.compact_menu()

	def compact_menu(self, force=None):
		do = force
		if(force == None):
			do = self.client.get_bool("/apps/gedit-2/plugins/tweaks/compactMenu")

		bar = self.window.get_children()[0].get_children()
		if(do):
			self.compactMenuButton = gtk.MenuToolButton(gtk.STOCK_ADD)

			self.dropMenu = gtk.Menu()
			for entry in bar[0].get_children():
				bar[0].remove(entry)
				self.dropMenu.append(entry)

			self.compactMenuButton.set_menu(self.dropMenu)
			self.compactMenuButton.show()
			bar[1].insert(self.compactMenuButton, 0)
			self.compactMenuButton.get_children()[0].get_children()[0].hide()
		else:
			if(self.dropMenu != None):
				for entry in self.dropMenu.get_children():
					self.dropMenu.remove(entry)
					bar[0].append(entry)
				self.compactMenuButton.get_parent().remove(self.compactMenuButton)
				self.dropMenu = None
				self.compactMenuButton = None
