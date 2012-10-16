import gedit, gtk, sqlalchemy, time, gconf, re

ui_str = """
<ui>
	<menubar name="MenuBar">
		<menu name="ToolsMenu" action="Tools">
			<menuitem name="Run SQL" action="SQLquery"/>
		</menu>
	</menubar>
</ui>
"""

class SqlPlugin(gedit.Plugin):
	def __init__(self):
		self.client = gconf.client_get_default()
		self.connectionString = self.client.get_string("/apps/gedit-2/plugins/sql/connection")
		if(self.connectionString == None):
			self.connectionString = "";
		gedit.Plugin.__init__(self)
		self.instances = {}

	def activate(self, window):
		self.window = window
		self.instances[window] = Sql(window, self.connectionString)

	def deactivate(self, window):
		self.instances[window].deactivate()

	def update_ui(self, window):
		self.instances[window].update_ui()

	def is_configurable(self):
		return True

	def get_port(self, engine):
		engine = engine.lower()
		if(engine == 'mysql'):
			self.portText.set_text("3306")
			return "3306"
		elif(engine == 'postgresql'):
			self.portText.set_text("5432")
			return "5432"
		else: #custom
			return self.portText.get_text()

	def onChange(self, state, data):
		engine = str(self.engineDropbox.get_active_text()).lower()
		user = self.userText.get_text()
		password = self.passwordText.get_text()
		location = self.locationText.get_text()
		port = self.get_port(engine)
		database = self.databaseText.get_text()

		if(engine == "custom"):
			engine = self.engineText.get_text()

		connectionString = engine + "://" + user + ":" + password + "@" + location + ":" + port + "/" + database
		self.resultText.set_text(connectionString)

	def dropboxChange(self, dropbox):
		engine = dropbox.get_active_text()
		enable = bool(engine.lower() == 'custom')
		self.resultText.set_editable(enable)
		self.portText.set_editable(enable)
		self.engineText.set_editable(enable)
		if(enable):
			white = gtk.gdk.Color(65535, 65535, 65535)
			self.resultText.modify_base(gtk.STATE_NORMAL, white)
			self.portText.modify_base(gtk.STATE_NORMAL, white)
			self.engineText.modify_base(gtk.STATE_NORMAL, white)
			self.engineText.set_text("")
		else:
			gray = gtk.gdk.Color(60000, 60000, 60000)
			self.resultText.modify_base(gtk.STATE_NORMAL, gray)
			self.portText.modify_base(gtk.STATE_NORMAL, gray)
			self.engineText.modify_base(gtk.STATE_NORMAL, gray)
			self.engineText.set_text(engine.lower())
			self.onChange(None,None)

	def connectionChange(self, state, data):
		connectionString = self.resultText.get_text()
		result = re.search("^([^:]*)://([^:]*):([^@]*)@([^:]*):([^/]*)/(.*)$", connectionString)
		if(result != None):
			self.engineDropbox.set_active(2)
			self.engineText.set_text(result.group(1))
			self.userText.set_text(result.group(2))
			self.passwordText.set_text(result.group(3))
			self.locationText.set_text(result.group(4))
			self.portText.set_text(result.group(5))
			self.databaseText.set_text(result.group(6))

	def create_entry(self, string, function=None):
		if(function == None):
			function = self.onChange
		label = gtk.Label(string)
		label.show()
		label.set_justify(gtk.JUSTIFY_LEFT)
		label.set_width_chars(10)
		text = gtk.Entry()
		text.set_width_chars(30)
		text.show()
		text.connect("key-release-event", function)
		self.box = gtk.HBox()
		self.box.show()
		self.box.pack_start(label)
		self.box.pack_start(text)
		self.content.pack_start(self.box)
		return text

	def create_configure_dialog(self):
		self.dialog = gtk.Dialog("Connection Setup")
		#FORMAT: 'engine://user:password@location:port/database'

		self.content = self.dialog.get_content_area()
		self.engineText = self.create_entry("Engine:")
		self.engineDropbox = gtk.combo_box_new_text()
		self.engineDropbox.append_text("MySQL")
		self.engineDropbox.append_text("PostgreSQL")
		self.engineDropbox.append_text("Custom")
		self.engineDropbox.show()
		self.engineDropbox.connect("changed", self.dropboxChange)

		self.box.pack_start(self.engineDropbox)
		self.box.reorder_child(self.engineDropbox, 1)

		self.userText = self.create_entry("User:")
		self.passwordText = self.create_entry("Password:")
		self.locationText = self.create_entry("Location:")
		self.portText = self.create_entry("Port:")
		self.databaseText = self.create_entry("Database:")

		self.resultText = self.create_entry("Connection:", self.connectionChange)
		self.engineDropbox.set_active(0)

		actions = self.dialog.get_action_area()
		save = gtk.Button("Save & Close")
		save.connect("clicked", self.save)
		save.show()
		cancel = gtk.Button("Cancel")
		cancel.connect("clicked", self.cancel)
		cancel.show()
		actions.pack_end(save)
		actions.pack_end(cancel)

		connection = self.client.get_string("/apps/gedit-2/plugins/sql/connection")
		if(connection == None):
			connection = ""
		self.resultText.set_text(connection)

		self.connectionChange(None, None)

		return self.dialog

	def cancel(self, user_param):
		self.dialog.hide()

	def save(self, user_param):
		self.client.set_string("/apps/gedit-2/plugins/sql/connection", self.resultText.get_text())
		self.connectionString = self.resultText.get_text()
		self.instances[self.window].changeEngine(self.connectionString)
		self.dialog.hide()

class Sql():
	def deactivate(self):
		#self.window.get_children()[0].get_children()[2].get_children()[1].get_children()[0].set_tab_pos(gtk.POS_TOP)
		tab = self.window.get_active_tab()
		if(tab != None):
			#tab.get_parent().set_show_tabs(True)
			tab.get_parent().set_tab_pos(gtk.POS_TOP)

	def update_ui(self):
		pass

	def tr(self, tds):
		if(self.first_row):
			types = []
			for td in tds:
				types.append(str)#(type(td))
			self.list = gtk.ListStore(*types)
			if(self.resultSet is not None):
				self.container.remove(self.resultSet)
			self.resultSet = gtk.TreeView(self.list)
			self.resultSet.connect("row-activated", self.dblClick)
			self.ths(tds)
			self.first_row = False
		else:
			self.list.append(tds)

	def ths(self, ths):
		for i,th in enumerate(ths):
			self.th(th, i)

	def th(self, text, col):
		column = gtk.TreeViewColumn(text)
		self.resultSet.append_column(column)
		column.pack_start(self.cell, True)
		column.set_attributes(self.cell, text=col)

	def table(self, result):
		self.first_row = True
		try:
			first = result.fetchone()
		except (sqlalchemy.exc.InvalidRequestError) as details:
			self.output(str(int(result.rowcount)) + " rows affected.", True)
			return
		if first is not None:
			self.tr(first.keys())
			self.tr(first.values())
			for row in result:
				values = []
				for col in row:
					values.append(str(col))
				self.tr(values)
			#self.scrollable.remove(self.textarea)
			#self.scrollable.add(self.resultSet)
			self.container.add(self.resultSet)
			self.resultSet.show()
			self.container.show()
			description = "rows returned."
			hide = False
		else:
			description = "rows affected."
			hide = True
		self.output(str(int(result.rowcount)) + " " + description, hide)


	def dblClick(treeview, iter, path, column):
		print treeview, iter, path, column
		cell = column.get_cell_renderers()[0]
		#widget = cell.get_widget()
		#cell.start_editing(gtk.gdk.Event(gtk.gdk.BUTTON_PRESS), widget, path)

	def changeEngine(self, connectionString):
		self.connectionString = connectionString
		self.connect()

	def __init__(self, window, connection):
		#SETTINGS:
		self.showTabs = False
		self.panelRight = True
		self.connectionString = connection

		self.resultSet = None
		self.action_group = gtk.ActionGroup("SQLActions")
		self.runQuery = gtk.Action("SQLquery", _("Run SQL"), _("Run SQL"), gtk.STOCK_EXECUTE)
		self.runQuery.connect("activate", self.run)
		self.action_group.add_action_with_accel(self.runQuery, "<Ctrl>G")
		#self.action_group.add_action(self.runQuery)

		self.window = window
		self.cell = gtk.CellRendererText()
		#self.cell.editable = True

		self.manager = self.window.get_ui_manager()
		self.manager.insert_action_group(self.action_group, -1)
		self.manager.add_ui_from_string('<ui><toolbar name="ToolBar"><toolitem name="SQLquery" action="SQLquery" /></toolbar></ui>')
		self.manager.add_ui_from_string(ui_str)

		self.textarea = gtk.TextView()
		self.textarea.set_wrap_mode(gtk.WRAP_WORD)
		self.textarea.show()
		self.buffer = self.textarea.get_buffer()

		self.scrollable = gtk.ScrolledWindow()
		self.scrollable.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		self.scrollable.show()

		self.box = gtk.VBox()
		self.box.show()

		self.container = gtk.VBox()
		self.container.show()

		self.timearea = gtk.TextView()
		self.timearea.set_wrap_mode(gtk.WRAP_WORD)
		self.timearea.show()
		self.timer = self.timearea.get_buffer()

		self.box.pack_start(self.container)
		self.box.pack_end(self.timearea)
		self.box.pack_end(self.textarea)

		self.viewport = gtk.Viewport()
		self.viewport.add(self.box)
		self.viewport.show()

		self.scrollable.add(self.viewport)

		self.textarea.hide()
		self.container.hide()
		self.connect()

		panel = self.window.get_bottom_panel()
		image = gtk.Image()
		image.set_from_stock(gtk.STOCK_EXECUTE, gtk.ICON_SIZE_MENU)

		ui_id = panel.add_item(self.scrollable, "SQL", image)


	def output(self, results, hide = True):
		self.buffer.set_text(str(results))
		if hide:
			self.container.hide()
		self.textarea.show()
		#self.scrollable.remove(self.resultSet)
		#self.scrollable.add(self.textarea)

	def set_clock(self, result):
		self.timer.set_text(str(result * 1000)[0:4] + " ms")

	def query(self, sql):
		sql = re.sub('--[^\n]*', '\n', sql, re.MULTILINE)
		try:
				result = self.engine.execute(sql)
		except (sqlalchemy.exc.SQLAlchemyError) as details: #(sqlalchemy.exc.ProgrammingError, sqlalchemy.exc.OperationalError, sqlalchemy.exc.DataError, sqlalchemy.exc.IntegrityError) as details:
				self.output(details)
				return
		self.table(result)

	def connect(self):
		try:
				self.engine = sqlalchemy.create_engine(self.connectionString)
		except ImportError as details:
				print self.output(details)
				return False
		return True

	def run(self, action):
		self.window.get_bottom_panel().activate_item(self.scrollable)
		doc = self.window.get_active_document()
		try:
			start, end = doc.get_selection_bounds()
		except ValueError as details:
			start, end = doc.get_bounds()
		query = doc.get_text(start, end)
		then = time.time()
		self.query(query)
		self.set_clock(time.time() - then)
