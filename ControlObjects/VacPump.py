from Framework4.Control.Core.CObject import CObjectBase, Signal, Slot
import logging

class VacPump(CObjectBase):

    signals = []

    slots = [Slot("exftclose")]


    def __init__(self, *args, **kwargs):
        CObjectBase.__init__(self, *args, **kwargs)

    def init(self):
        pass

    def exftclose(self):
        #DEBUG
        print "Called exftclose"
