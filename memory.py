import re
import sys
from helpers import find
import struct
import subprocess


class Memory(object):
    def __init__(self, pid):
        self.pid = pid

        self.mem_file_name = '/proc/{}/mem'.format(pid)
        self.mem_file = open(self.mem_file_name, 'r', 0)

        maps_file = open("/proc/{}/maps".format(pid), 'r')

        self.maps = map(lambda line: re.match(r'([0-9A-Fa-f]+)-([0-9A-Fa-f]+) ([-r]).*\s{8,}(.*)', line), maps_file.readlines())
        self.maps = filter(None, self.maps)
        self.maps = filter(lambda m: m.group(3) == 'r', self.maps)
        self.blocks = map(lambda m: MemoryBlock(
            # os.path.basename(
            #     ' '.join(filter(None, m.strip().split(' '))[5:])
            # ),
            self,
            m.group(4),
            self.mem_file,
            int(m.group(1), 16),
            int(m.group(2), 16)
        ), self.maps)

        maps_file.close()

        self._write_busy = False

    def find_blocks(self, *names):
        return filter(lambda block: any([name in block.full_name for name in names]), self.blocks)

    def find_block(self, name):
        blocks = self.find_blocks(name)
        if len(blocks):
            return blocks[0]

    def find_exclude(self, *names):
        return filter(lambda block: not any([name in block.full_name for name in names]), self.blocks)

    def find_all(self):
        return self.blocks

    def get_abs_block(self):
        return MemoryBlock(self, '[absolute]', self.mem_file, 0, pow(2, 64) - 1)

    def where_is(self, addr):
        for block in self.find_all():
            if block.start <= addr < block.end:
                return block

    def _write(self, offset, data):
        if self._write_busy:
            return False

        # Dirty, dirty hack.
        # But that's python-ptrace's fault!
        self._write_busy = True
        self._write_busy = False
        subprocess.Popen([sys.executable, './writer.py', str(self.pid), str(offset)] + [str(ord(x)) for x in data], stdout=subprocess.PIPE).communicate()

        return True


class MemoryBlock(object):
    def __init__(self, memory, full_name, mem_file, start, end):
        self.memory = memory
        self.full_name = full_name
        self.mem_file = mem_file
        self.file = file
        self.start = start
        self.end = end
        self.data = None

    @property
    def length(self):
        return self.end - self.start

    def read(self, offset=0, length=0):
        self.mem_file.seek(self.start + offset)
        return self.mem_file.read(
            length
            if length > 0
            else self.end - self.start
        )

    def read_float(self, offset):
        return struct.unpack('<f', self.read(offset, 4))[0]

    def read_int32(self, offset):
        return struct.unpack('<l', self.read(offset, 4))[0]

    def read_uint32(self, offset):
        return struct.unpack('<L', self.read(offset, 4))[0]

    def read_int64(self, offset):
        return struct.unpack('<q', self.read(offset, 8))[0]

    def read_uint64(self, offset):
        return struct.unpack('<Q', self.read(offset, 8))[0]

    def find(self, pattern):
        return find(self.read(), pattern)

    def find_float(self, value):
        return find(self.read(), struct.pack('<f', value))

    def find_int32(self, value):
        return find(self.read(), struct.pack('<l', value))

    def find_uint32(self, value):
        return find(self.read(), struct.pack('<L', value))

    def find_int64(self, value):
        return find(self.read(), struct.pack('<q', value))

    def find_uint64(self, value):
        return find(self.read(), struct.pack('<Q', value))

    def write_float(self, offset, value):
        return self.memory._write(self.to_abs(offset), struct.pack('<f', value))

    def write_uint32(self, offset, value):
        return self.memory._write(self.to_abs(offset), struct.pack('<L', value))

    def write_uint64(self, offset, value):
        return self.memory._write(self.to_abs(offset), struct.pack('<Q', value))

    def write(self, offset, data):
        return self.memory._write(self.to_abs(offset), data)

    def __repr__(self):
        return '<MemoryBlock size=%s MB, address=%08x...%08x, name="%s">' % (
            round(float(self.end - self.start) / 1048576, 2),
            self.start,
            self.end,
            self.full_name
        )

    def find_pattern(self, pattern, mask):
        tmp = self.read()
        pattern_len = len(pattern)
        print 'searching...'
        i = 0
        max_i = self.length - pattern_len
        while i < max_i:
            k = 0
            while k < pattern_len:
                if tmp[i + k] != pattern[k] and mask[k] != '?':
                    break
                if k == pattern_len - 1:
                    yield i, tmp[i:i + k + 1]
                k += 1
            i += 1

    def to_rel(self, address):
        return address - self.start

    def to_abs(self, address):
        return address + self.start

    def get_call_address(self, address):
        return address + self.read_uint32(address + 1) + 5


class Struct(object):
    """docstring for Struct"""
    def __init__(self, memory, arg):
        super(Struct, self).__init__()
        self.memory = memory
        self.abs_block = memory.get_abs_block()
        if isinstance(arg, (list, tuple)):
            block, offset = arg
            self.offset = block.to_abs(offset)
        else:
            self.offset = arg

    def get_size_and_offset(self, key):
        offset = self.offset
        for def_key, def_type, def_size in self.get_definition():
            if key == def_key:
                return (def_type, offset, def_size)
            offset += def_size
        raise Exception('Key "{}" not found in struct!'.format(key))

    def get_definition(self):
        raise NotImplementedError()

    def get_value(self, key):
        def_type, offset, size = self.get_size_and_offset(key)
        reader_attr = 'read_{}'.format(def_type)
        if hasattr(self.abs_block, reader_attr):
            return getattr(self.abs_block, reader_attr)(offset)
        else:
            return self.abs_block.read(offset, size)

    def set_value(self, key, value):
        def_type, offset, size = self.get_size_and_offset(key)
        writer_attr = 'write_{}'.format(def_type)
        if hasattr(self.abs_block, writer_attr):
            return getattr(self.abs_block, writer_attr)(offset, value)
        else:
            return self.abs_block.write(offset, value)


class LocalPlayerStruct(Struct):
    def __init__(self, memory, arg):
        super(LocalPlayerStruct, self).__init__(memory, arg)

    def get_definition(self):
        return (
            ('?', 'array', 0x120),
            ('team_number', 'uint32', 4),
            ('?', 'array', 0xAAC0),
            ('flash_alpha', 'float', 4)
        )
