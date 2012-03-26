from Framework4.Control.Core.CObject import CObjectBase, Signal, Slot
from Framework4.Control.Core.CObject import addChannel, addCommand

class ESRFMachineInfo(CObjectBase):
    signals = [ Signal('machine_info_updated') ]
    slots = []

    def __init__(self, *args, **kwargs):
        CObjectBase.__init__(self, *args, **kwargs)

    def init(self):
        self.machine_current = str()
        self.fill_mode = str()
        self.operator_msg = str()
        self.next_fill = str()

        # We should have read_sig_values, read_op_message, read_fill_mode
        # in taco: DevReadSigValues | DevReadOpMesg | DevReadFillMode
        chans = (('read_op_message', 'DevReadOpMesg'),
                 ('read_fill_mode', 'DevReadFillMode'))
        ds_name = str(self.config["/object/data[@name='uri']/@value"][0])
        self.addChannel('taco',
                        'read_sig_values',
                        ds_name,
                        'DevReadSigValues',
                        polling=3000)
        for (name, call) in chans:
            self.addChannel('taco',
                            name,
                            ds_name,
                            call)

        read_sig_values = self.channels.get('read_sig_values')
        if read_sig_values is not None:
            read_sig_values.connect('update', self.values_changed)


    def get_current(self):
        return self.machine_current


    def values_changed(self, values):
        self.machine_current = values[14]
        self.next_fill = values[16]
        self.operator_msg = self.channels.get('read_op_message').value().strip()
        self.fill_mode = self.channels.get('read_fill_mode').value().strip()
        
        self.emit('machine_info_updated',
                  self.machine_current,
                  self.operator_msg,
                  self.fill_mode,
                  self.next_fill)
