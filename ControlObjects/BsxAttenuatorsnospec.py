from Framework4.Control.Core.CObject import CObjectBase, Signal, Slot
import logging
from PyTransmission import matt_control


class BsxAttenuators(CObjectBase):

    signals = [Signal("attenuatorsStateChanged"),
               Signal("attenuatorsFactorChanged")]

    slots = [Slot("toggleFilter"),
             Slot("setTransmission"), Slot("getEnergy")]


    def __init__(self, *args, **kwargs):
        CObjectBase.__init__(self, *args, **kwargs)

    def init(self):
        # get spec motor as described in href and the corresponding *.xml
        self.__energyMotor = self.objects["getEnergy"]
        wago_ip = str(self.config["/object/data[@name='wago_ip']/@value"][0])
        nb_filter = int(self.config["/object/data[@name='nb_filter']/@value"][0])
        type = int(self.config["/object/data[@name='type']/@value"][0])
        alternate = str(self.config["/object/data[@name='alternate']/@value"][0])
        status_module = str(self.config["/object/data[@name='status_module']/@value"][0])
        control_module = str(self.config["/object/data[@name='control_module']/@value"][0])
        self.__matt = matt_control.MattControl(wago_ip, nb_filter, 0, \
                                               type, alternate, status_module, control_module)
        self.__matt.connect()    
        self.__attenuatorsState = None
        self.__attenuatorsFactor = None
        self.__attenuatorsList = []
        for data_elt in self.config["//data"]:
            key = data_elt.attrib["name"]
            bits = map(int, data_elt.attrib['bits'].split())
            for b in bits:
                self.__attenuatorsList.append([key, b])
        # the list contains [label, bits] lists
        # sort by bits
        self.__attenuatorsList.sort(key = lambda x: x[1])

        """
        # Set up all channels
        self.channels["attenuatorsState_oh"].connect("update", self.attenuatorsStateChanged)
        self.channels["attenuatorsState_exp"].connect("update", self.attenuatorsStateChanged)
        self.channels["attenuatorsFactor_oh"].connect("update", self.attenuatorsFactorChanged)
        self.channels["attenuatorsFactor_exp"].connect("update", self.attenuatorsFactorChanged)
        


    def connectNotify(self, pValue):
        try:
            value = getattr(self, pValue[:-7]).value()
            getattr(self, pValue)(value)
        except:
            pass


    def getAttenuatorsList(self):
        logging.getLogger().debug('is sending attribute list %s', self.__attenuatorsList)
        if len(self.__attenuatorsList) == 0:
            return None
        else:
            return self.__attenuatorsList


    def getAttenuatorsState(self):   
        self.__attenuatorsState = elf.__matt.pos_read()
        return self.__attenuatorsState

    def getAttenuatorsFactor(self):
        energy = self.__energyMotor.position()
        self.__matt.set_energy(energy)
        self.__attenuatorsFactor = self.__matt.transmission_get()
        return self.__attenuatorsFactor

    def getEnergy(self):
        return self.__energyMotor.position()

    def is_in(self, attenuator_index):
        curr_bits = self.getAttenuatorsState()
        idx = self.__attenuatorsList[attenuator_index]
        return bool((1<<idx) & curr_bits)

    # =============================================
    #  COMMANDS
    # =============================================      
    def toggleFilter(self, attenuator_index):
        idx = self.__attenuatorsList[attenuator_index]
        if self.is_in(attenuator_index):
            self.__matt.mattout(idx)
        else:
            self.__matt.mattin(idx)
        self._update()


    def setTransmission(self, pValue):
        energy = self.__energyMotor.position()
        self.__matt.set_energy(energy)
        self.__matt.transmission_set(pValue)


    # =============================================
    #  CHANNELS
    # =============================================
    def _update(self):
        self.emit("attenuatorsStateChanged",self.getAttenuatorsState())
        self.emit("attenuatorsFactorChanged", self.getAttenuatorsFactor())
        
    def attenuatorsStateChanged(self, pValue):
        self.__attenuatorsState = self.getAttenuatorsState()
        self.emit("attenuatorsStateChanged", self.__attenuatorsState)


    def attenuatorsFactorChanged(self, pValue):
        self.__attenuatorsFactor = self.getAttenuatorsFactor()
        self.emit("attenuatorsFactorChanged", self.__attenuatorsFactor)



