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

        # Extract tango device name from a file ESRFMachInfo.xml: 
        #======= BEGIN =====
        #<object class = "ESRFMachineInfo" username = "ESRFMachineInfo">
        #    <data name="uri"  value="orion:10000/FE/D/29" />
        #</object>    
        #======== END =========
        # 
        # get device from config file
        devName = str(self.config["/object/data[@name='uri']/@value"][0])
        #
        # read three values
        #
        # We should have read_current_value, read_op_message, read_fill_mode, read_next_fill
        # in tango: SR_Current | SR_Operator_Mesg | SR_Filling_Mode | SR_Refill_Countdown
        # Read Current regularly to update all values
        self.addChannel('tango',
                        'read_current_value',
                        devName,
                        'SR_Current',
                        polling = 3000)
        self.addChannel('tango',
                        'read_op_message',
                        devName,
                        'SR_Operator_Mesg')
        self.addChannel('tango',
                        'read_fill_mode',
                        devName,
                        'SR_Filling_Mode')
        self.addChannel('tango',
                        'read_next_fill',
                        devName,
                        'SR_Refill_CountDown')

        read_current_value = self.channels.get('read_current_value')
        if read_current_value is not None:
            read_current_value.connect('update', self.current_changed)


    def get_current(self):
        return self.machine_current


    def current_changed(self, current):
        self.machine_current = current
        self.next_fill = self.channels.get('read_next_fill').value()
        self.operator_msg = self.channels.get('read_op_message').value().strip()
        self.fill_mode = self.channels.get('read_fill_mode').value().strip()
        self.emit('machine_info_updated',
                  self.machine_current,
                  self.operator_msg,
                  self.fill_mode,
                  self.next_fill)
