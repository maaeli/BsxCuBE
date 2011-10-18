from PyQt4               import QtCore, Qt
import sys, os, time, exceptions
import traceback

#
#  This should become a control object or merged with the collect control object
#
class CollectRobotObject(QtCore.QThread):

    __ATTEMPTS  = 3
    __TIMEOUT   = 1200
    __TOLERANCE = 0.25    

    def __init__(self, pParent, pBrickWidget):
        self.__parent           = pParent
        self.__brickWidget      = pBrickWidget
        self._robotIsCollecting = False
        self.abortFlag          = False

        self.proxySampleChanger = ProxySampleChanger()
        self.proxyRobot         = ProxyRobot()
        
        QtCore.QThread.__init__(self, self.__brickWidget)
   

    def abort(self):
        self.abortFlag = True

    def waitSampleChanger(self):
        while self.proxySampleChanger.isExecuting():
            time.sleep(0.5)
        exception = self.proxySampleChanger.getCommandException()
        if exception is None or exception != "":
            return -1
        else:
            return 0

    def robotStartCollection(self):
        self._robotIsCollecting = True  # is triggered by GUI. nothing to inform back
        self.abortFlag = False

    def robotEndCollection(self):
        self.showMessage(0, "Robot ends collection", notify=0)
        self._robotIsCollecting = False
        self.abortFlag = False
        self.proxyRobot.collectEnd()    # is triggered by robot sequencer. informs the GUI

    def showMessage(self, pLevel, pMessage, notify=0):
        self.proxyRobot.showMessage(pLevel,pMessage,notify)
    
    def checkSCException(self, action="", value=""):
        exception = self.proxySampleChanger.getCommandException()

        if exception is not None and exception != "":
            message = "Error when trying to set %s to '%s'. Aborting collection! (%s)" % (action, value, exception)
            self.showMessage(2, message, notify=1)
            raise exceptions.Warning
        else:
            if self.abortFlag:
                self.showMessage(0,'abort flag is set!!!!')
                raise exceptions.Warning

    def checkAbort(self, step=None ):
        if self.abortFlag:
             if step: 
                  self.showMessage(0,"Abort flag detected in step %d" % step, notify=0 )
             raise exceptions.Warning

    def run(self):
        while True:
            if self._robotIsCollecting:
                try:

                    pars = self.collectpars = self.proxyRobot.getCollectPars()

                    lastBuffer = ""

                    # 
                    # Setting sample type
                    # ==================================================                                                
                    self.checkAbort(1) 
                    self.showMessage(0, "Setting sample type to '%s'..." % pars.sampleType)
                    self.proxySampleChanger.setSampleType(str( pars.sampleType).lower())
                    self.waitSampleChanger()
                    self.checkSCException('sampleType', pars.sampleType)

                    # 
                    #  Setting storage temperature
                    # ==================================================
                    self.checkAbort(1) 
                    self.showMessage(0, "Setting storage temperature to '%s' C..." % pars.storageTemperature )
                    self.proxySampleChanger.setStorageTemperature( pars.storageTemperature )
                    self.waitSampleChanger()
                    self.checkSCException('storageTemperature', pars.storageTemperature)

                    # ==================================================
                    #  INITIAL CLEANING
                    # ==================================================
                    self.checkAbort(2) 
                    if pars.initialCleaning: 
                          self.showMessage(0, "Initial cleaning...")
                          if self.clean() == -1:
                              message ="Error when trying to clean. Aborting collection!"
                              self.showMessage(2, message, notify=1)
                              raise exceptions.Warning
                          else:
                              if self.abortFlag:
                                  raise exceptions.Warning 

                    self.lastSampleTime = time.time()
                    prevSample          = None

                    # ==================================================
                    #   MAIN LOOP on Samples
                    # ==================================================        
                    for sample in pars.sampleList:

                        self.checkAbort(3) 
                        #
                        #  Collect buffer before
                        #     - in mode BufferBefore  , always
                        #     - in mode BufferFirst   , at beginning and every time buffer changes
                        # 
                        # In buffer first mode check also if temperature has changed. If so, consider as
                        #    a change in buffer

                        doFirstBuffer  = pars.bufferBefore

                        # in bufferFirst mode decide when to collect the buffer 
                        if pars.bufferFirst:
                            if sample.buffername != lastBuffer:
                                doFirstBuffer = True 
                            if prevSample is not None: 
                                if prevSample.SEUtemperature != sample.SEUtemperature:
                                    self.showMessage(0,"SEU Temperature different from previous. Collecting buffer.") 
                                    doFirstBuffer = True 

                        if doFirstBuffer:

                            if sample.buffername != lastBuffer: 
                                lastBuffer = sample.buffername
            
                            self.checkAbort(4) 
                            self.collectOne( sample, pars, mode="buffer_before")

                        #
                        # Wait if necessary before collecting sample
                        #
                        if sample.waittime:
                            myStartTime = self.lastSampleTime + sample.waittime  # remember time is given in seconds
                            self.showMessage(0, "Waiting to start next sample. %d secs left..." % (int(myStartTime - time.time())))
                            iter = 0
                            while True:
                                now = time.time()
                                if self.abortFlag:
                                    self.showMessage(0, "    Abort waiting.")
                                    raise exceptions.Warning 
                                    break
                                if now > myStartTime:
                                    break 
                                time.sleep(1)
                                iter += 1
                                if iter%10 == 0: # gives a message every 10 secs
                                   self.showMessage(0, "Waiting to start next sample. %d secs left..." % (int(myStartTime - time.time())))
                            self.showMessage(0, "    Done waiting.")

                        self.lastSampleTime = time.time()
                        
                        #
                        # Collect sample
                        #
                        self.checkAbort(5) 
                        self.collectOne( sample, pars, mode="sample")

                        if pars.bufferAfter:
                            self.checkAbort(6) 
                            self.collectOne( sample, pars, mode="buffer_after")

                        prevSample = sample
                        
                    #
                    # End of for sample loop
                    #---------------------------------- 

                    self.showMessage(0, "The data collection is done!",notify=3)
                    
                except exceptions.Warning:
                    pass
                except:
                    exception, error_string, tb = sys.exc_info()
                    full_tb = traceback.extract_tb(tb)
                    exception_tb = "".join(traceback.format_list(full_tb))
                    self.showMessage(2,'Exception in the logic of collect using robot: %s\n%s' % (error_string, exception_tb))

                self.robotEndCollection()
            else:
                self.msleep(100)

    def collectOne(self, sample, pars, mode=None):


            # ==================================================
            #  SETTING VISCOSITY
            # ==================================================
            filepars = self.proxyRobot.getFileInfo() 
            if mode == "buffer_before":
               # this will allow to use several buffers of same name for same sample
               # we should check if enough volume is not available then go to next buffer in list
               tocollect = sample.buffer[0]    
            elif mode == "buffer_after":
               tocollect = sample.buffer[0]
            else:
               tocollect = sample

            self.checkAbort(101) 
            self.showMessage(0, "Setting viscosity to '%s'..." % tocollect.viscosity)
            if self.setViscosityLevel(tocollect.viscosity.lower()) == -1:
                self.showMessage(2, "Error when trying to set viscosity to '%s'..." % tocollect.viscosity)
                                    
            # ==================================================
            #  SETTING SEU TEMPERATURE
            # ==================================================                        
            # temperature is taken from sample (not from buffer) even if buffer is collected
            self.checkAbort(102) 
            if self.setSEUTemperature(sample.SEUtemperature) == -1:
                self.showMessage(2, "Error when setting SEU temperature " )
                raise exceptions.Warning                                
          
            # ==================================================
            #  FILLING 
            # ==================================================

            self.checkAbort(103) 
            self.showMessage(0, "Filling (%s) from plate '%s', row '%s' and well '%s'..." % (mode,tocollect.plate, tocollect.row, tocollect.well))

            if self.fill( tocollect.plate, tocollect.row, tocollect.well, tocollect.volume ) == -1:
                message ="Error when trying to fill from plate '%s', row '%s' and well '%s'. Aborting collection!" % (tocollect.plate, tocollect.row, tocollect.well)
                self.showMessage(2, message, notify=1)
                raise exceptions.Warning
            
            # ==================================================
            #  FLOW
            # ==================================================
            self.checkAbort(104) 
            self.showMessage(0, "Setting Flow or Fix")

            if tocollect.flow:                                        
                self.showMessage(0, "Flowing with volume '%s' during '%s' second(s)..." % (tocollect.volume, pars.flowTime))
                if self.flow(tocollect.volume, pars.flowTime) == -1: 
                    self.showMessage(2, "Error when trying to flow with volume '%s' during '%s' second(s)..." % (tocollect.volume, pars.flowTime))
            else:
                self.showMessage(0, "Fixing liquid position...") 
                if self.setLiquidPositionFixed() == -1:
                    self.showMessage(2, "Error when trying to fix liquid position...")
                else:
                    self.showMessage(0, "  - liquid position fixed.") 

            self.showMessage(0, "Setting Flow or Fix done")
         
            # ==========================
            #  SETTING TRANSMISSION 
            # ==========================
            self.checkAbort(105) 
            self.showMessage(0, "Setting transmission for plate '%s', row '%s' and well '%s' to %s%s..." % (tocollect.plate, tocollect.row, tocollect.well, tocollect.transmission, "%"))                            
            self.__parent.emit("transmissionChanged", tocollect.transmission)

            # ==================================================
            #  PERFORM COLLECT
            # ==================================================
            self.checkAbort(200) 
            self.showMessage(0, "Start collecting (%s) '%s'..." % (mode,pars.prefix) )
            self.emit(QtCore.SIGNAL("displayReset"))  
            self.proxyRobot.collect(0,                  pars.directory,    pars.prefix,             filepars.runNumber,
                                    pars.frameNumber,   pars.timePerFrame, tocollect.concentration, tocollect.comments,
                                    tocollect.code,     pars.mask,         pars.detectorDistance,   pars.waveLength,
                                    pars.pixelSizeX,    pars.pixelSizeY,   pars.beamCenterX,        pars.beamCenterY,
                                    pars.normalisation, pars.radiationChecked, pars.radiationAbsolute, 
                                    pars.radiationRelative,
                                    pars.processData,   pars.SEUTemperature, pars.storageTemperature)

            while self.__parent._isCollecting:
                if self.abortFlag:
                    self.showMessage(2, "abort detected while collecting. abort will happen at the end of collection")
                self.msleep(100)                                

            self.showMessage(0, "Finish collecting '%s'..." % pars.prefix)

            self.checkAbort(301) 

            if self.abortFlag:
                raise exceptions.Warning

            # ======================
            #  WAIT FOR END OF FLOW 
            # ======================
            self.checkAbort(302) 
            if tocollect.flow:                                        
                self.showMessage(0, "Waiting for end of flow...")
                if self.waitSampleChanger() == -1: 
                    self.showMessage(2, "Error when waiting for end of flow...")
            
            # =============
            #  RECUPERATE 
            # =============
            self.checkAbort(303) 
            if tocollect.recuperate:
                self.showMessage(0, "Recuperating to plate '%s', row '%s' and well '%s'..." % (tocollect.plate, tocollect.row, tocollect.well))
                if self.recuperate( tocollect.plate, tocollect.row, tocollect.well ) == -1:
                    self.showMessage(2, "Error when trying to recuperate to plate '%s', row '%s' and well '%s'..." % (tocollect.plate, tocollect.row, tocollect.well))
                                                                
            # ==================================================
            #  CLEANING
            # ==================================================
            self.checkAbort(304) 
            self.showMessage(0, "Cleaning...")

            if self.clean() == -1:
                message ="Error when trying to clean. Aborting collection!"
                self.showMessage(2, message, notify=1)
                raise exceptions.Warning                                    
    
    #
    # Cleaning command
    #
    def clean(self): 
        i = 0                                        
        while i < self.__ATTEMPTS: 
            self.proxySampleChanger.clean()
            self.waitSampleChanger()
            if self.proxySampleChanger.getCommandException() is not None and self.proxySampleChanger.getCommandException() != "":
                i += 1
            else:
                return 0    
        return -1

    def setLiquidPositionFixed(self):
        i = 0                                        
        while i < self.__ATTEMPTS: 
            self.showMessage(0, "   . trying...")
            self.proxySampleChanger.setLiquidPositionFixed(True)
            self.waitSampleChanger()
            self.showMessage(0, "   . checking...")
            if self.proxySampleChanger.getCommandException() is not None and self.proxySampleChanger.getCommandException() != "":
                self.showMessage(0, "   . error...")
                i += 1
            else:
                self.showMessage(0, "   . ok...")
                return 0    
        return -1
    
    def flow(self, pVolume, pTime):    
        i = 0                                        
        while i < self.__ATTEMPTS: 
            self.proxySampleChanger.flow(pVolume, pTime)
            #self.waitSampleChanger()
            if self.proxySampleChanger.getCommandException() is not None and self.proxySampleChanger.getCommandException() != "":
                i += 1
            else:
                return 0    
        return -1
    
    def setViscosityLevel(self, pValue): 
        i = 0                                        
        while i < self.__ATTEMPTS: 
            self.proxySampleChanger.setViscosityLevel(pValue)
            self.waitSampleChanger()
            if self.proxySampleChanger.getCommandException() is not None and self.proxySampleChanger.getCommandException() != "":
                i += 1
            else:
                return 0    
        return -1
    

    def fill(self, pPlate, pRow, pColumn, pVolume):
        i = 0                                        
        while i < self.__ATTEMPTS:
            self.proxySampleChanger.fill(pPlate, pRow, pColumn, pVolume)
            self.waitSampleChanger()
            if self.proxySampleChanger.getCommandException() is not None and self.proxySampleChanger.getCommandException() != "":
                self.showMessage(1,'sample changer fill failed with message %s' % self.proxySampleChanger.getCommandException())
                i += 1
            else:
                return 0    
        return -1
    
    
    def setSEUTemperature(self, pTemperature):     
        self.showMessage(0, "Waiting for SEU temperature to be '%s' C (timeout in %s seconds)..." % (pTemperature, self.__TIMEOUT))
        self.proxySampleChanger.setSEUTemperature(pTemperature)
        if self.proxySampleChanger.getCommandException() is not None and self.proxySampleChanger.getCommandException() != "":
            message = "Error when trying to set SEU temperature to '%s' C. Aborting collection! (%s)" % (pTemperature, self.proxySampleChanger.getCommandException())
            self.showMessage(2, message, notify=1)
            return -1            
        else:
            i = 0                                        
            while i < self.__TIMEOUT:
                currentSEUTemperature = self.proxySampleChanger.getSEUTemperature()
                self.showMessage(0,"Temp is now %s (target = %s - tolerance = %s)" % (currentSEUTemperature, pTemperature, self.__TOLERANCE))
                if self.proxySampleChanger.getCommandException() is not None and self.proxySampleChanger.getCommandException() != "":
                    message = "Error when waiting for SEU temperature to be '%s' C. Aborting collection!" % pTemperature
                    self.showMessage(2, message, notify=1)
                    return -1
                else:
                    if self.abortFlag or (currentSEUTemperature >= float(pTemperature) - self.__TOLERANCE and currentSEUTemperature <= float(pTemperature) + self.__TOLERANCE):
                        return 0
                    else:
                        i += 1
                        self.msleep(1000)
            self.showMessage(2, "The SEU temperature didn't reach '%s' C after waiting %s seconds..." % (pTemperature, self.__TIMEOUT))
            return 0
        
    def recuperate(self, pPlate, pRow, pColumn):
        i = 0                                        
        while i < self.__ATTEMPTS: 
            self.proxySampleChanger.recuperate(pPlate, pRow, pColumn)
            self.waitSampleChanger()
            if self.proxySampleChanger.getCommandException() is not None and self.proxySampleChanger.getCommandException() != "":
                i += 1
            else:
                return 0
        return -1    

class ProxySampleChanger(Qt.QObject):
    def __init__(self,*args):
        Qt.QObject.__init__(self, *args)

    def __getattr__(self, name):
        def sccall(*args):
            ret={"args":args, "returned":"nada"}
            self.emit( QtCore.SIGNAL("doSampleChangerAction"), name, ret)
            while ret["returned"] == "nada":
              time.sleep(0.5)
            return ret["returned"]
        return sccall

#
# This class is to avoid access to Qt from Thread
#  (should be overriden once we gid rid of Thread
#
class ProxyRobot(Qt.QObject):
    def __init__(self,*args):
        Qt.QObject.__init__(self, *args)

    def collect(self, *args):
        ret={"args": args, "returned":"nada"}
        self.emit( QtCore.SIGNAL("robotCollect"),ret)
        while ret["returned"] == "nada":
              time.sleep(0.5)
        return ret["returned"]

    def collectEnd(self, *args):
        ret={"returned":"nada"}
        self.emit( QtCore.SIGNAL("robotCollectEnd"),ret)
        while ret["returned"] == "nada":
              time.sleep(0.5)
        return ret["returned"]

    def getFileInfo(self):
        ret={"returned":"nada"}
        self.emit( QtCore.SIGNAL("getFileInfo"),ret)
        while ret["returned"] == "nada":
              time.sleep(0.5)
        return ret["returned"]

    def getCollectPars(self):
        ret={"returned":"nada"}
        self.emit( QtCore.SIGNAL("getCollectPars"),ret)
        while ret["returned"] == "nada":
              time.sleep(0.5)
        return ret["returned"]

    def printCollectPars(self):
        self.emit( QtCore.SIGNAL("printCollectPars"))

    def showMessage(self, *args):
        ret={"args": args, "returned":"nada"}
        self.emit( QtCore.SIGNAL("showMessage"),ret)
        while ret["returned"] == "nada":
              time.sleep(0.5)
        return ret["returned"]

