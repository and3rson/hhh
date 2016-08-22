from gi.repository import Gtk
from threading import Thread
from gi.repository import Gdk


class Gui(Thread):
    def __init__(self):
        Gdk.threads_init()
        super(Gui, self).__init__()

    def spawn_window(self):
        self.window = Gtk.Window()
        self.window.show_all()
        self.debug_view = Gtk.TextView()
        self.layout = Gtk.VBox()
        self.layout.add(self.debug_view)
        self.window.add(self.layout)
        # self.window.set_keep_above()
        self.window.show_all()

    def run(self):
        self.spawn_window()

        Gtk.main()

    def log(self, text):
        def _log():
            buf = self.debug_view.get_buffer()
            end_iter = buf.get_end_iter()
            buf.insert(end_iter, text + '\n')
        Gdk.threads_add_idle(0, _log)
