#!/usr/bin/env python2.7

import sys
import time
from memory import Memory
from helpers import dump, pidof, recast
# from gui import Gui
from hotkeys import HotkeyListener
from cs import CSGO
from notifications import notify


class App(object):
    def __init__(self, pid):
        self.pid = pid
        self.hl = HotkeyListener()
        self.ready = False
        self.flash_hack = False

    def _reset_flashbang(self):
        if self.cs.is_ready:
            local_player = self.cs.get_local_player()
            self.flash_hack = not self.flash_hack
            if not local_player.set_value('flash_alpha', 70.0 if self.flash_hack else 255.0):
                self.flash_hack = not self.flash_hack
                notify('steam', 'HHH', 'Failed to toggle flash_hack! Memory is busy.', timeout=5)
            else:
                notify('steam', 'HHH', 'flash_hack {}'.format('ENABLED' if self.flash_hack else 'DISABLED'), timeout=1)
        else:
                notify('steam', 'HHH', 'Failed to reset flash_hask: hack not ready yet.', timeout=5)

    def run(self):
        notify('steam', 'HHH', 'HHH is starting', timeout=3)

        self.hl.register(78, self._reset_flashbang)
        self.hl.start()

        self.memory = Memory(self.pid)

        self.cs = CSGO(self.memory)

        arr = self.cs.get_glow_array()
        # print len(arr)
        for entity in arr:
            print entity.dump()
            # print entity.get_value('is_dormant'), entity.get_value('health'), entity.get_value('team_num')

        # self.client_dll = self.memory.find_block('client_client.so')
        # if not self.client_dll:
        #     raise Exception('client_client.so not found!')

        # self.abs_block = self.memory.get_abs_block()

        # print 'Client DLL:', self.client_dll

        # self.ready = True

        notify('steam', 'HHH', 'HHH is ready', timeout=5)

        while True:
            time.sleep(0.2)


# part = sys.argv[1]
part = 'csgo_linux64'
pid, app, args = pidof(part)
if not pid:
    raise Exception('Process with name "{}" not found.'.format(part))
    sys.exit(1)
print 'Found PID:            ', pid
print 'Process executable:   ', app
print 'Args:                 ', args
app = App(pid)
app.run()
