# -*- coding: utf-8 -*-

VERSION = "0.1"

import gedit, gtk
from gettext import gettext as _
import cPickle, os

class TabPgUpPgDownPlugin(gedit.Plugin):
    def __init__(self):
        gedit.Plugin.__init__(self)
        self.id_name = 'TabPgUpPgDownPluginID'

    def activate(self, window):
        # The gedit window.
        self.window = window

        l_ids = []
        # Signals to attach to - Only key-press-event
        # at the moment.
        for signal in ('key-press-event',):
            method = getattr(self, 'on_window_' + signal.replace('-', '_'))
            l_ids.append(window.connect(signal, method))
        window.set_data(self.id_name, l_ids)

    def deactivate(self, window):
        l_ids = window.get_data(self.id_name)

        for l_id in l_ids:
            window.disconnect(l_id)

    def on_window_key_press_event(self, window, event):
        key = gtk.gdk.keyval_name(event.keyval)

        if event.state & gtk.gdk.CONTROL_MASK and key in ('Page_Up', 'Page_Down'):
            atab = window.get_active_tab()
            tabs = atab.parent.get_children()
            tlen = len(tabs)
            i = 0
            tab = atab

            for tab in tabs:
                i += 1
                if tab == atab:
                    break

            if key == 'Page_Up':
                i -= 2

            if i < 0:
                tab = tabs[tlen-1]
            elif i >= tlen:
                tab = tabs[0]
            else:
                tab = tabs[i]

            window.set_active_tab(tab)

            return True
        if (event.state & gtk.gdk.MOD1_MASK or event.state & gtk.gdk.SHIFT_MASK) and key in ('Page_Up', 'Page_Down'):
            if (event.state & gtk.gdk.MOD1_MASK):
                panel = window.get_bottom_panel()
                notebook = panel.get_children()[0].get_children()[0]
            elif (event.state & gtk.gdk.SHIFT_MASK):
                panel = window.get_side_panel()
                notebook = panel.get_children()[1]
            else:
                return False
            tlen = notebook.get_n_pages()
            i = notebook.get_current_page()
            if key == 'Page_Up':
                i = i - 1
            else:
                i = i + 1

            if(i > tlen-1):
                next = notebook.get_nth_page(0)
            elif(i < 0):
                next = notebook.get_nth_page(tlen-1)
            else:
                next = notebook.get_nth_page(i)
            panel.activate_item(next)

            last = self.find_focus(window, next)
            if(last != None):
              print "using last"
              last.grab_focus()
            return True
            #next.do_grab_focus()
            #next.do_set_focus_child()
        #if event.state & gtk.gdk.MOD1_MASK and key in ('Home', 'End'):
        #    pass
    def find_focus(self, window, container):
        print "parent"
        try:
            container.do_grab_focus()
        except TypeError:
            try:
              children = container.get_children()
            except AttributeError:
              return
            for child in children:
                if(child.get_can_focus()):
                    print child
                    if ('Gedit' in str(type(child))):
                        child.grab_focus()
                        return
                    elif (type(child) == gtk.Entry):
                        child.grab_focus()
                        return
                    else:
                        return child
                else:
                    return self.find_focus(window, child)
