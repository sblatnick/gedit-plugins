# Released in May 2010 by Mike Doty
#  www.psyguygames.com
#
#  It's ok, I keep typing spyguy too.
#
#  Version... um... version 3!
#
# License?
#
# I'm releasing this under the "The I Really Could Care Less About You Public License."  Read it here:  http://www.revinc.org/pages/license

import gedit
import gtk

import os

import cgi

import urllib

SEARCH_DOCUMENTS = "Active Documents"
SEARCH_DIRECTORY = "Active Directory"
SEARCH_BOTH      = "Both"

ROOT = os.path.expanduser( '~' ) + "/.gnome2/gedit/plugins/"

class ResultsView(gtk.VBox):
    def __init__(self, geditwindow):
        gtk.VBox.__init__(self)
        
        # We have to use .geditwindow specifically here (self.window won't work)
        self.geditwindow = geditwindow
        
        # Save the document's encoding in a variable for later use (when opening new tabs)
        try: self.encoding = gedit.encoding_get_current()
        except: self.encoding = gedit.gedit_encoding_get_current()
        
        # Preferences (we'll control them with toggled checkboxes)
        self.ignore_comments = False
        self.case_sensitive = False
        self.search_all_files = False
        
        # We save the grep search result data in a ListStore
        # Format:  ID (COUNT)  |  FILE (without path)  |  LINE  |  FILE (with path) | line text was found in (string)
        #    Note: We use the full-path version when opening new tabs (when necessary)
        self.search_data = gtk.ListStore(str, str, str, str, str)

        # Create a list (a "tree view" without children) to display the results
        self.results_list = gtk.TreeView(self.search_data)

        # Get the selection attribute of the results_list and assign a couple of properties
        tree_selection = self.results_list.get_selection()
        
        # Properties...
        tree_selection.set_mode(gtk.SELECTION_SINGLE)
        tree_selection.connect("changed", self.view_result)
        
        # Create the cells for our results list treeview
        #   Note:  We don't need to create a cell or text renderer
        #          for the full-path filename variable because we
        #          won't actually be displaying that information.
        cell_id = gtk.TreeViewColumn("#", gtk.CellRendererText(), markup = 0)
        cell_filename = gtk.TreeViewColumn("File", gtk.CellRendererText(), text = 1)
        cell_line_number = gtk.TreeViewColumn("Line", gtk.CellRendererText(), text = 2)
        cell_preview = gtk.TreeViewColumn("Preview", gtk.CellRendererText(), markup = 4)
        
        # Now add the cell objects to the results_list treeview object
        self.results_list.append_column(cell_id)
        self.results_list.append_column(cell_filename)
        self.results_list.append_column(cell_line_number)
        self.results_list.append_column(cell_preview)
        
        # Create text-rendering objects so that we can actually
        # see the data that we'll put into the objects
        #text_renderer_id = gtk.CellRendererText()
        #text_renderer_filename = gtk.CellRendererText()
        #text_renderer_line_number = gtk.CellRendererText()
        #text_renderer_result_preview = gtk.CellRendererText()
        
        # Pack the text renderer objects into the cell objects we created
        #cell_id.pack_start(text_renderer_id, True)
        #cell_filename.pack_start(text_renderer_filename, True)
        #cell_line_number.pack_start(text_renderer_line_number, True)
        #cell_preview.pack_start(text_renderer_result_preview, True)
        
        # Now set the IDs to each of the text renderer objects and set them to "text" mode
        #cell_id.add_attribute(text_renderer_id, "text", 0)
        #cell_filename.add_attribute(text_renderer_filename, "text", 1)
        #cell_line_number.add_attribute(text_renderer_line_number, "text", 2)
        #cell_preview.add_attribute(text_renderer_result_preview, "text", 4)

        # Create a scrolling window object and add our results_list treeview object to it
        scrolled_window = gtk.ScrolledWindow()        
        scrolled_window.add(self.results_list)
        
        # Pack in the scrolled window object
        self.pack_start(scrolled_window)
        
        # Create a "Find" button; we'll pack it into an HBox in a moment...
        button_find = gtk.Button("Find")
        button_find.connect("clicked", self.button_press)
        # Create a "search bar" to type the search string into; we'll pack it
        # into the HBox as well...
        self.search_form = gtk.Entry()
        self.search_form.connect("activate", self.button_press)

        # Here's the HBox I mentioned...
        search_box = gtk.HBox(False, 0)
        search_box.pack_start(self.search_form, True, True)
        search_box.pack_start(button_find, False, False)
        
        # Pack the search box (search bar + Find button) into the side panel
        self.pack_start(search_box, False, False)
        
        # Create a check box to decide whether or not to ignore comments
        self.check_ignore = gtk.CheckButton("Ignore comments")
        self.check_ignore.connect("toggled", self.toggle_ignore)
        # Pack it in...
        self.pack_start(self.check_ignore, False, False)
        
        # Create a check box to determine whether to pay attention to case
        self.check_case = gtk.CheckButton("Case Sensitive")
        self.check_case.connect("toggled", self.toggle_case)
        # Pack it in...
        self.pack_start(self.check_case, False, False)

        # Create a combo box for search options (current documents, current directory documents, both, whatever)
        label = gtk.Label("Search Options:")
        self.pack_start(gtk.Label(""), False, False) # A hacky way to insert a line break.  Sorry!
        self.pack_start(label, False, False)

        # We use this to set the tooltip later...
        #tooltip = gtk.Tooltip()

        # This dropdown will allow the user to decide how the search will work
        self.search_setting_dropdown = gtk.combo_box_new_text()

        # Hardcoded tooltip string
        #tooltip.set_text(self.search_setting_dropdown, "Active Documents:  Use grep to search for\nkey terms in all currently open files.\n\nActive Directory:  Use grep to search\n(nonrecursively) through the directory\nof the currently active document.\n\nBoth:  Use grep in both fashions\nsimultaneously.")
        self.search_setting_dropdown.set_tooltip_text("Active Documents:  Use grep to search for\nkey terms in all currently open files.\n\nActive Directory:  Use grep to search\n(nonrecursively) through the directory\nof the currently active document.\n\nBoth:  Use grep in both fashions\nsimultaneously.")

        # See top of file for global variable definitions
        self.search_setting_dropdown.append_text(SEARCH_DOCUMENTS)
        self.search_setting_dropdown.append_text(SEARCH_DIRECTORY)
        self.search_setting_dropdown.append_text(SEARCH_BOTH)

        # Set the first option to active
        self.search_setting_dropdown.set_active(0)

        # Pack it in...
        self.pack_start(self.search_setting_dropdown, False, False)
        
        # Show all UI elements
        self.show_all()

    # A click of the "Ignore comments" check box calls to this function        
    def toggle_ignore(self, widget):
        self.ignore_comments = not self.ignore_comments
        
    # A click of the "Case sensitive" check box calls to this function
    def toggle_case(self, widget):
        self.case_sensitive = not self.case_sensitive

    # A click of the "search all files" check box calls to this function
    def toggle_search_all(self, widget):
        self.search_all_files = not self.search_all_files

    # A call goes to view_result whenever the user clicks on
    # one of the results after a search.  In response to the
    # click, we'll go to that file's tab (or open it in a 
    # new tab if they since closed that tab) and scroll to
    # the line that the result appears in.
    def view_result(self, widget):
        # Get the selection object
        tree_selection = self.results_list.get_selection()
        
        # Get the model and iterator for the row selected
        (model, iterator) = tree_selection.get_selected()
        
        if (iterator):
            # Get the absolute path of the file
            absolute_path = model.get_value(iterator, 3)
            
            # Get the line number
            line_number = int(model.get_value(iterator, 2)) - 1
            
            # Get all open tabs
            documents = self.geditwindow.get_documents()
            
            # Loop through the tabs until we find which one matches the file
            # If we don't find it, we'll create it in a new tab afterwards.
            for each in documents:

                if (each.get_uri()):
            
                    if (each.get_uri().replace("file://", "") == absolute_path.replace(" ", "%20")):
                        # This sets the active tab to "each"
                        self.geditwindow.set_active_tab(gedit.tab_get_from_document(each))
                        each.goto_line(line_number)

                        # Get the bounds of the document                        
                        (start, end) = each.get_bounds()
                    
                        self.geditwindow.get_active_view().scroll_to_iter(end, 0.0)
                    
                        x = each.get_iter_at_line_offset(line_number, 0)
                        self.geditwindow.get_active_view().scroll_to_iter(x, 0.0)
                    
                        return

            # If we got this far, then we didn't find the file open in a tab.
            # Thus, we'll want to go ahead and open it...
            if (not (absolute_path.endswith(".fid.txt"))):
                self.geditwindow.create_tab_from_uri("file://" + absolute_path.replace(" ", "%20"), self.encoding, int(model.get_value(iterator, 2)), False, True)
        
    # Clicking the "Find" button or hitting return in the search area calls button_press.
    # This function, of course, searches each open document for the search query and
    # displays the results in the side panel.
    def button_press(self, widget):
        # Get all open tabs
        documents = self.geditwindow.get_documents()

        # We'll save search result data in a string
        data = ""

        # We'll save our actual results in a list
        results = []

        # We can't do a search on empty string
        if (len(self.search_form.get_text()) <= 0):
            return

        # Create a string to hold the documents / directory we want to search
        files_string = ""

        # Get the currently selected search option
        active_text = self.search_setting_dropdown.get_active_text()

        search_term = self.search_form.get_text()

        str_case_operator = ""
        if (not self.case_sensitive):
            str_case_operator = " -i"

        # Track any "unsaved" files (we save them as temp files
        # but want to load the original files)
        temp_file_tracker = {}

        # Did we want to search active documents?
        if (active_text in (SEARCH_DOCUMENTS, SEARCH_BOTH)):

            count = 1

            for each in documents:

                # Can't grep on an unsaved file
                if ( ( not each.is_untitled() ) and ( not each.get_modified() ) ):

                    # get_uri() returns files:///whatever.ext.  When we call grep,
                    # we don't want that file:// part.
                    files_string += " '%s'" % each.get_uri().replace("file://", "").replace("%20", " ")

                else:

                    # Make sure our cache dir exists
                    if (not os.path.exists( os.path.join(ROOT, "find_in_docs_cache") )):
                        os.mkdir( os.path.join(ROOT, "find_in_docs_cache") )

                    #print "Trying to get text..."
                    #text_iter1 = gtk.TextIter()
                    #text_iter2 = gtk.TextIter()
                    #text_iter2.forward_to_end()
                    active_document_data = each.get_property("text")#get_text(text_iter1, text_iter2, False)
                    #print "Hey! ... %d" % len(data)

                    if (each.is_untitled()):
                        file = open(os.path.join(ROOT, "find_in_docs_cache", "untitled %d.fid.txt" % count), "w")
                        file.write(active_document_data)
                        file.close()

                        files_string += " '%s'" % os.path.join(ROOT, "find_in_docs_cache", "untitled %d.fid.txt" % count)

                        count += 1

                    else:
                        file = open(os.path.join(ROOT, "find_in_docs_cache", "temp %d.fid.txt" % count), "w")
                        file.write(active_document_data)
                        file.close()

                        temp_file_tracker["temp %d.fid.txt" % count] = urllib.unquote( each.get_uri().replace("file://", "") )

                        files_string += " '%s'" % os.path.join(ROOT, "find_in_docs_cache", "temp %d.fid.txt" % count)

                        count += 1

        # Did we want to search the currently active directory?
        if (active_text in (SEARCH_DIRECTORY, SEARCH_BOTH)):

            active_document = self.geditwindow.get_active_document()

            try:
                active_directory = active_document.get_uri().replace("file://", "").replace("%20", " ")

                # Need to remove the trailing file name
                active_directory = "/".join( active_directory.split("/")[0:-1] )

                # This query will check all of the files in the current document's directory,
                # but it will not use recursion (maxdepth 1).
                query = "find '%s' -maxdepth 1 -name '*.*' -exec grep -n -H%s \"%s\" {} \;" % (active_directory, str_case_operator, self.search_form.get_text().replace("\"", "\\\"").replace("[", "\["))
                #print query

                pipe = os.popen(query)

                # Save any files we found...
                data = pipe.read() # Save temp for processing below...

            except:
                pass

        # Now, if we don't have any files / directories to search, we'll have to just return
        if (files_string == "" and data == ""):
            return

        # Create a pipe and call the grep command, then read it
        if (files_string != ""):
            query = "grep -n -H" + str_case_operator + " \"%s\" %s" % (self.search_form.get_text().replace("\"", "\\\"").replace("[", "\["), files_string)
            #print query

            pipe = os.popen(query)
            data += pipe.read()

        # No results?
        if (data == ""):
            self.search_data.clear()
            return

        # Extend the results to our "results"
        #results.extend( data.split("\n") )
        results = data.split("\n")
        
        # Clear any current results from the side panel
        self.search_data.clear()

        results.sort()

        result_data = []

        # Process each result...        
        for each in results:
            # Each result will look like this:
            #   FILE (absolute path):Line number:string
            #
            #   ... where string is the line that the search data was found in.
            pieces = each.split(":", 2)
            
            if (len(pieces) == 3):
                filename = os.path.basename(pieces[0].lstrip(".").lstrip("/")) # We just want the filename, not the path
                line_number = pieces[1]

                # We'll use Pango markup to highlight the search term, but we don't want
                # pango to think existing markup should be rendered as well.
                string = cgi.escape( pieces[2].lstrip(" ") )

                # Also, we don't want to have a preview that's 5000 characters long.  Let's limit it to, say, 100 character.
                preview = string[0:100] # Stops at len(string) if < 100

                # But, wait!  What if it's a long string, but the search term appears at the end?
                # Or right in the middle of the 100 character cutoff point?
                pos = string.find(search_term)
                if (pos + len(search_term) >= 100):
                    preview = "..." + string[pos:pos+100]

                # I know what you're thinking.
                # What if the search term itself exceeds 100 characters?
                # Well, that means someone's doing some kind of crazy search.
                if (len(search_term) > 100):

                    # It's time to abbreviate the search term.  Let's save its old length.
                    x = len(search_term)

                    # "some really long crazy search term pretend I'm longer than this" -> "some really long...longer than this"
                    search_term = search_term[0:25] + "..." + search_term[x-25:x]
                    preview = string[max(0, pos - 25):pos] + search_term + string[pos+x:pos+x+25]

                preview = preview.replace(search_term, "<span background = 'black' foreground = 'yellow'><b>%s</b></span>" % search_term) # Remove leading whitespace

                # If we want to ignore comments, then we'll make sure it doesn't start with # or //                        
                if (filename.endswith("~")):
                    pass

                else:
                    basename = os.path.basename(filename)

                    if (basename.endswith(".fid.txt")):
                        if (basename in temp_file_tracker):
                            filename = temp_file_tracker[basename]
                            pieces[0] = temp_file_tracker[basename]

                    if (self.ignore_comments):
                        if (not string.startswith("#") and not string.startswith("//")):
                            data = ("%d" % (len(self.search_data) + 1), os.path.basename(filename), line_number, pieces[0], preview)

                            if (not (data in result_data)):
                                result_data.append(data)
                    else:
                        data = ("%d" % (len(self.search_data) + 1), os.path.basename(filename), line_number, pieces[0], preview)

                        if (not (data in result_data)):
                            result_data.append(data)

        for each in result_data:

            self.search_data.append(each)

class FreeDialog(gtk.Dialog):
    def __init__(self, parent_app):
        gtk.Dialog.__init__(self, "Find in...", parent_app.window)

        self.parent_app = parent_app

        self.connect("destroy", self.end_dialog)
        self.connect("delete-event", self.end_dialog)

    def end_dialog(self, widget = None, event = None):
        self.hide()
        return True # Don't really destroy it, we'll re-use it...

class PluginHelper:
    def __init__(self, plugin, window):
        self.window = window
        self.plugin = plugin
        
        self.ui_id = None
        self.ui_id2 = None
        
        self.add_panel(window)

        self.build_menu()
        
    def deactivate(self):        
        self.remove_menu_item()
        
        self.window = None
        self.plugin = None
        
    def update_ui(self):
        pass

    def build_menu(self):
        manager = self.window.get_ui_manager()
        
        self.action_group = gtk.ActionGroup("PluginActions")

        action_name = "find_in_files_1"

        self.ui_id2 = manager.new_merge_id()

        path = "/MenuBar/SearchMenu/SearchOps_1"

        # Add the submenu to the menu
        manager.add_ui(merge_id = self.ui_id2,
                        path = path,
                        name = action_name,
                        action = action_name,
                        type = gtk.UI_MANAGER_MENUITEM,
                        top = False)
                        
        # Define an action for the submenu
        submenu_action = gtk.Action(name = action_name,
                                    label = "Find in Files",
                                    tooltip = "Jump to the Find in Files panel",
                                    stock_id = None)
                                    
        submenu_action.set_visible(True) # Make it visible
        submenu_action.connect("activate", self.show_panel)
        self.action_group.add_action_with_accel(submenu_action, "<Ctrl><Shift>F") # Add the action

        # Add the action group.
        manager.insert_action_group(self.action_group, -1)

    def show_panel(self, widget = None, event = None):

        panel = self.window.get_side_panel()

        if (panel.get_property("visible") == True):

            panel.activate_item(self.results_view)

            self.results_view.search_form.grab_focus()

        else:

            self.dialog.show()
        
    def add_panel(self, window):
        panel = self.window.get_side_panel()
        
        self.results_view = ResultsView(window)
        self.free_results_view = ResultsView(window)

        self.dialog = FreeDialog(self)
        self.dialog.set_default_size(240, 600)
        vbox = self.dialog.get_content_area()
        vbox.pack_start(self.free_results_view, True, True)
        #vbox.pack_start(gtk.Label("???"), False, False)
        vbox.show_all()
        
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_DND_MULTIPLE, gtk.ICON_SIZE_BUTTON)
        self.ui_id = panel.add_item(self.results_view, "Find in Open Documents", image)
        
    def remove_menu_item(self):
        panel = self.window.get_side_panel()
        
        panel.remove_item(self.results_view)

class FindInDocumentsPlugin(gedit.Plugin):
    def __init__(self):
        gedit.Plugin.__init__(self)
        self.instances = {}
        
    def activate(self, window):
        self.instances[window] = PluginHelper(self, window)
        
    def deactivate(self, window):
        self.instances[window].deactivate()
        
    def update_ui(self, window):
        self.instances[window].update_ui()
