class CSGO(object):
    def __init__(self, memory):
        self.memory = memory
        self.client_dll = self.memory.find_block('client_client.so')
        self.abs_block = self.memory.get_abs_block()
        if not self.client_dll:
            raise Exception('client_client.so not found!')

        for match_address, matched_data in self.client_dll.find_pattern('\x48\x89\xe5\x74\x0e\x48\x8d\x05\x00\x00\x00\x00', 'xxxxxxxx????'):
            self.match_address = match_address
            self.local_player_address = self.client_dll.get_call_address(match_address + 0x7)
            break

        print 'FoundLocalPlayerLea: %x (%x)' % (self.client_dll.to_abs(self.match_address), self.match_address)
        print 'Local player address: %x (%x)' % (self.client_dll.to_abs(self.local_player_address), self.local_player_address)

    def get_local_player_a_abs(self):
        local_player_aa_abs = self.client_dll.to_abs(self.local_player_address)
        return self.abs_block.read_uint32(local_player_aa_abs)
