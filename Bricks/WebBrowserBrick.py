import logging
import os
from Framework4.GUI import Core
from Framework4.GUI.Core import Property, Connection, Signal, Slot
from PyQt4 import QtCore, QtGui, Qt


__category__ = "General"



class WebBrowseBrick(Core.BaseBrick):

    properties = {"url": Property("string", "URL", "", "urlChanged")}

    signals = []
    slots = []


    def __init__(self, *args, **kargs):
        Core.BaseBrick.__init__(self, *args, **kargs)

    def init(self):
        self.webViewer = QwebView()

    def urlChanged(self, url):
        self.webViewer.load(url)
