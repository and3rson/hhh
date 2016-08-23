from helpers import dump
import struct


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
        offset = 0
        for parts in self.get_definition():
            if len(parts) == 3:
                def_key, def_type, def_size = parts
                def_offset = offset
            else:
                def_key, def_type, def_size, def_offset = parts

            if key == def_key:
                return (def_type, self.offset + def_offset, def_size)
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

    def dump(self):
        return self.__class__.__name__ + ':\n' + '\n'.join([
            ' * {}: {}'.format(item[0], self.get_value(item[0]))
            for item
            in self.get_definition()
            if item[0] != '?'
        ])


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


class BaseEntityStruct(Struct):
    def __init__(self, memory, arg):
        super(BaseEntityStruct, self).__init__(memory, arg)

    def get_definition(self):
        return (
            ('index', 'uint32', 4, 0x64),
            ('is_dormant', 'uint8', 4, 0xE9),
            ('team_num', 'uint32', 4, 0xF0),
            ('health', 'float', 4, 0xFC),
        )
        # return (
        #     ('?', 'array', 0x11D),
        #     ('is_dormant', 'uint8', 1),
        #     ('?', 'array', 0x6),
        #     ('team_num', 'uint32', 4),
        #     ('?', 'uint32', 4),
        #     ('?', 'uint32', 4),
        #     ('health', 'uint32', 4),
        #     ('?', 'array', 0x15B),
        #     ('lite_state', 'uint32', 4),
        # )

    # struct Entity
    # {
    #     unsigned char unk0[0x11D];  
    #     unsigned char m_isDormant;  
    #     unsigned char unk01[0x6];   
    #     int           m_iTeamNum;   
    #     int           unk1;         
    #     int           unk2;         
    #     int           m_iHealth;    
    #     unsigned char unk3[0x15B];  
    #     int           m_lifeState;  
    # };



class CSGO(object):
    def __init__(self, memory):
        self._ready = False

        self.memory = memory
        self.client_dll = self.memory.find_block('client_client.so')
        self.abs_block = self.memory.get_abs_block()
        if not self.client_dll:
            raise Exception('client_client.so not found!')

        # Find local player pointer

        call, _ = next(self.client_dll.find_pattern('\x48\x89\xe5\x74\x0e\x48\x8d\x05\x00\x00\x00\x00', 'xxxxxxxx????'))
        # print '%x' % call

        self.pp_local_player = self.client_dll.get_call_address(call + 0x7)
        # print '%x' % self.pp_local_player
        self.pp_local_player_abs = self.client_dll.to_abs(self.pp_local_player)
        # print 'FoundLocalPlayerLea: %x (%x)' % (self.client_dll.to_abs(self.match_address), self.match_address)
        print '* Local player pointer address: %x (%x)' % (self.pp_local_player_abs, self.pp_local_player)

        # Find glow pointer address

        call_ref, _ = next(self.client_dll.find_pattern('\xE8\x00\x00\x00\x00\x48\x8b\x10\x48\xc1\xe3\x06\x44', 'x????xxxxxxxx'))

        print 'Glow pointer call reference: %x' % call_ref
        call = self.client_dll.get_call_address(call_ref)
        print 'Glow function address: %x' % call
        self.pp_glow_pointer = self.client_dll.get_call_address(call + 0xF)
        self.pp_glow_pointer_abs = self.client_dll.to_abs(self.pp_glow_pointer)
        print '* Glow pointer address: %x (%x)' % (self.pp_glow_pointer_abs, self.pp_glow_pointer)

        self._ready = True

    def get_local_player(self):
        if not self._ready:
            return
        p_local_player = self.abs_block.read_uint32(self.pp_local_player_abs)
        return LocalPlayerStruct(self.memory, p_local_player)

    def get_glow_array(self):
        entities = []
        print 'start'
        print dump(self.abs_block.read(self.pp_glow_pointer_abs, 128))
        count = self.abs_block.read_uint32(self.pp_glow_pointer_abs + 0x10)
        print 'Entity count:', count
        data_ptr = self.abs_block.read_uint32(self.pp_glow_pointer_abs)
        for i in xrange(0, count):
            # self.abs_block.write(data_ptr + 0x40 * i + 4, struct.pack('<ffff', 0.5, 0.5, 0.5, 0.5))
            # self.abs_block.write(data_ptr + 0x40 * i + 4 + 16 + 16, '\x01\x00\x00')

            # self.abs_block.write_float(data_ptr + 0x40 * i + 4, 0.5)
            # self.abs_block.write_float(data_ptr + 0x40 * i + 8, 0.5)
            # self.abs_block.write_float(data_ptr + 0x40 * i + 12, 0.5)
            # self.abs_block.write_float(data_ptr + 0x40 * i + 16, 0.5)
            p_entity = self.abs_block.read_uint32(data_ptr + 0x40 * i)
            # print '%x' % p_entity
            if p_entity:
                entities.append(BaseEntityStruct(self.memory, p_entity))
        # print dump(self.abs_block.read(data_ptr, 1024))
        return entities
        # p_glow_array = self.abs_block.read_uint32(self.pp_glow_pointer)
        # print p_glow_array
        # print self.abs_block.read_uint32(p_glow_array)
        # print self.abs_block.read_uint32(p_glow_array + 4)
        print 'end'

    @property
    def is_ready(self):
        return self._ready
