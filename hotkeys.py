#!/usr/bin/env python2

from pykeyboard import PyKeyboard
from Xlib.display import Display
from Xlib import X
from Xlib.ext import record
from Xlib.protocol import rq
from threading import Thread
import time


class HotkeyListener(Thread):
    def __init__(self):
        super(HotkeyListener, self).__init__()

        self.daemon = True

        self.disp = Display()
        self.root = self.disp.screen().root
        self.pressed = set()
        self.callbacks = {}
        self.prevents = {}

        # Monitor keypress and button press
        self.ctx = self.disp.record_create_context(
            0,
            [
                record.AllClients
            ],
            [
                {
                    'core_requests': (0, 0),
                    'core_replies': (0, 0),
                    'ext_requests': (0, 0, 0, 0),
                    'ext_replies': (0, 0, 0, 0),
                    'delivered_events': (0, 0),
                    'device_events': (X.KeyReleaseMask, X.ButtonReleaseMask),
                    'errors': (0, 0),
                    'client_started': False,
                    'client_died': False,
                }
            ]
        )

    def handler(self, reply):
        """ This function is called when a xlib event is fired """
        data = reply.data

        while len(data):
            event, data = rq.EventField(None).parse_binary_value(data, self.disp.display, None, None)

            # KEYCODE IS FOUND USERING event.detail

            if event.type == X.KeyPress:
                # BUTTON PRESSED
                if event.detail not in self.pressed:
                    self.pressed.add(event.detail)
                    if event.detail in self.callbacks.keys():
                        self.callbacks[event.detail]()
                    # self.prevents[event.detail] = True
                    # if event.detail in self.callbacks.keys():
                    #     self.callbacks[event.detail]()
            elif event.type == X.KeyRelease:
                # BUTTON RELEASED
                if event.detail in self.pressed:
                    self.pressed.remove(event.detail)
                    # del self.prevents[event.detail]

    def register(self, key, callback):
        self.callbacks[key] = callback

    def run(self):
        self.disp.record_enable_context(self.ctx, self.handler)
        self.disp.record_free_context(self.ctx)

        while 1:
            # Infinite wait, doesn't do anything as no events are grabbed
            event = self.root.display.next_event()
