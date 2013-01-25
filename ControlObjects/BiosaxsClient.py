from Framework4.Control.Core.CObject import CObjectBase, Slot, Signal
from suds.client import Client
from suds.transport.http import HttpAuthenticated
from math import fabs
import time
import sys
import traceback


class BiosaxsClient(CObjectBase):
    signals = [
               Signal("onSuccess"),
               Signal("onError")
               ]
    slots = [
             Slot("getExperimentNamesByProposalCodeNumber"),
             Slot("setUser"),
             Slot("getRobotXMLByExperimentId")
             ]

    def init(self):
        self.client = None
        self.URL = 'http://pcantolinos:8080/ispyb-ejb3/ispybWS/ToolsForBiosaxsWebService?wsdl'
        self.selectedExperimentId = None
        self.user = None
        self.password = None
        self.timeout = 5
        self.experiments = None

    def __initWebservice(self):

        self.httpAuthenticatedToolsForAutoprocessingWebService = HttpAuthenticated(username = self.user, password = self.password)
        self.client = Client(self.URL, transport = self.httpAuthenticatedToolsForAutoprocessingWebService, cache = None, timeout = self.timeout)
        self.experiments = []
        self.response = None


    def setUser(self, user, password):
        self.user = user #"mx1438"
        self.password = password #"Rfo4-73"


    #Return list containing [["ExperimentName1", "experimentId1"], ["ExperimentName2", "experimentId2"]]
    def getExperimentNames(self):
#        print "------------ Getting experiment Names"
        experimentNames = []
        for experiment in self.experiments:
            experimentNames.append([experiment.experiment.name, experiment.experiment.experimentId])
        return experimentNames

    def getExperimentNamesByProposalCodeNumber(self, code, number):
        if (self.client is None):
            self.__initWebservice()
        response = self.client.service.findExperimentByProposalCode(code, number)
        self.experiments = []
        for experiment in response:
            self.experiments.append(Experiment(experiment))
        experimentNames = self.getExperimentNames()
        self.emit("onSuccess", "getExperimentNamesByProposalCodeNumber", experimentNames)
        #self.emit("onSuccess", "getExperimentNamesByProposalCodeNumber", experimentNames)



#    def getExperimentsByProposalId(self, proposalId):
#        if (self.client is None):
#            self.__initWebservice()
#
#        response = self.client.service.findExperimentByPosposalId(3124)
#        self.experiments = []
#        for experiment in response:
#            self.experiments.append(Experiment(experiment))
#        return self.getExperimentNames()


    def getSpecimenIdBySampleCode(self, sampleCode):
        print "[ISPyB] getSpecimenIdBySampleCode " + str(sampleCode)
        if self.experiment is None:
            print "[ISPyB] Experiment is None"
            return None
        if self.selectedExperimentId is None:
            print "[ISPyB] Experiment is None"
            return None
        for experiment in self.experiments:
            #print experiment.experiment.experimentId
            if experiment.experiment.experimentId == self.selectedExperimentId:
                for sample in experiment.experiment.samples:
                    for specimen in sample.specimen3VOs:
                        if specimen.code == sampleCode:
                            return specimen.specimenId
        return None

    def getSpecimenIdBySampleCodeConcentrationAndSEU(self, sampleCode, concentration, seu):
        print "[ISPyB] getSpecimenIdBySampleCodeConcentrationAndSEU " + str(sampleCode) + " " + str(concentration) + " " + str(seu)
        if self.experiment is None:
            print "[ISPyB] Experiment is None"
            return None
        if self.selectedExperimentId is None:
            print "[ISPyB] Experiment is None"
            return None
        for experiment in self.experiments:
            #print experiment.experiment.experimentId
            if experiment.experiment.experimentId == self.selectedExperimentId:
                for sample in experiment.experiment.samples:
                    for specimen in sample.specimen3VOs:
                        #and (specimen.exposureTemperature == seu)
                        #print "----------------------------------------------------"
                        #print "[TEST] " + str(specimen.code) + " " + str(sampleCode)
                        #print "[TEST] " + str(str(specimen.code) == str(sampleCode))
                        #print "[TEST] " + str(specimen.exposureTemperature) + " " + str(seu)
                        #print "[TEST] " + str(round(float(specimen.exposureTemperature), 2) == round(float(seu), 2))
                        #print "[TEST] " + str(float(specimen.concentration)) + " " + str(float(concentration))
                        #print "[TEST] " + str(round(float(specimen.concentration), 2) == round(float(concentration), 2))

                        #print "--"
                        #print str(round(float(specimen.concentration), 2))
                        #print str(round(float(concentration), 2))

                        if (float(specimen.exposureTemperature) == float(seu)
                            and (str(specimen.code) == str(sampleCode))
                            and (round(float(specimen.concentration), 2) == round(float(concentration), 2))):
                            #print "[TEST] found" + str(specimen.specimenId)
                            #print "[TEST] et" + str(float(specimen.exposureTemperature))
                            #print "[TEST] set" + str(float(seu))
                            return specimen.specimenId
        #print "[TEST] It is a buffer"
        return None

#    def saveFrameSetBefore(self, sampleCode, exposureTemperature, storageTemperature, timePerFrame, timeStart, timeEnd, energy, detectorDistance, fileArray, snapshotCapillary, currentMachine, tocollect, pars):
#        try:
#            print "[ISPyB] Request for saveFrameSetBefore " + str(sampleCode)
#            if (self.client is None):
#                self.__initWebservice()
#            specimenId = self.getSpecimenIdBySampleCode(sampleCode)
#            if specimenId is None:
#                specimenId = -1
#            print "[ISPyB] Specimen found with specimenId: " + str(specimenId)
#            print tocollect
#            print pars
#            self.client.service.saveFrameBefore(self.selectedExperimentId, specimenId, sampleCode, exposureTemperature, storageTemperature, timePerFrame, timeStart, timeEnd, energy, detectorDistance, fileArray, snapshotCapillary, currentMachine, tocollect, pars)
#        except Exception:
#            print Exception
#            print "[ISPyB] error", sys.exc_info()[0]
#            traceback.print_exc()

#    def saveFrameSetAfter(self, sampleCode, exposureTemperature, storageTemperature, timePerFrame, timeStart, timeEnd, energy, detectorDistance, fileArray, snapshotCapillary, currentMachine, tocollect, pars):
#        try:
#            print "[ISPyB] Request for saveFrameSetAfter " + str(sampleCode)
#            if (self.client is None):
#                self.__initWebservice()
#            specimenId = self.getSpecimenIdBySampleCode(sampleCode)
#            if specimenId is None:
#                specimenId = -1
#            self.client.service.saveFrameAfter(self.selectedExperimentId, specimenId, sampleCode, exposureTemperature, storageTemperature, timePerFrame, timeStart, timeEnd, energy, detectorDistance, fileArray, snapshotCapillary, currentMachine, tocollect, pars)
#        except Exception:
#            print Exception
#            print "[ISPyB] error", sys.exc_info()[0]
#            traceback.print_exc()

    ### Mode: before, after, sample    
    def saveFrameSet(self, mode, sampleCode, exposureTemperature, storageTemperature, timePerFrame, timeStart, timeEnd, energy, detectorDistance, fileArray, snapshotCapillary, currentMachine, tocollect, pars, concentration, ispybSEUtemperature):
        try:
            print "[ISPyB] Request for saveFrameSet " + str(mode) + " " + str(sampleCode)
            if (self.client is None):
                self.__initWebservice()
            #specimenId = self.getSpecimenIdBySampleCode(sampleCode)
            print "[ISPyB] tocollect[concentration]: " + str(concentration)
            print "[ISPyB] toCollect.SEUtemperature " + str(exposureTemperature)
            print "[ISPyB] toCollect.SEUtemperature " + str(ispybSEUtemperature)

            #print "[ISPyB] exposureTemperature: " + str(tocollect["SEUtemperature"])
            specimenId = self.getSpecimenIdBySampleCodeConcentrationAndSEU(sampleCode, concentration, ispybSEUtemperature)
            print "[ISPyB] Specimen found: " + str(specimenId)
            if specimenId is None:
                specimenId = -1

            self.client.service.saveFrame(mode,
                                          self.selectedExperimentId,
                                          specimenId,
                                          sampleCode,
                                          exposureTemperature,
                                          storageTemperature,
                                          timePerFrame,
                                          timeStart,
                                          timeEnd,
                                          energy,
                                          detectorDistance,
                                          fileArray,
                                          snapshotCapillary,
                                          currentMachine,
                                          str(tocollect),
                                          str(pars),
                                          pars["beamCenterX"],
                                          pars["beamCenterY"],
                                          pars["radiationRelative"],
                                          pars["radiationAbsolute"],
                                          pars["pixelSizeX"],
                                          pars["pixelSizeY"],
                                          pars["normalisation"],
                                          tocollect["transmission"]
                                          )
        except Exception:
            print "[ISPyB] error", sys.exc_info()[0]
            #traceback.print_exc()

    def getPlatesByPlateGroupId(self, plateGroupId, experimentId):
        plates = []
        for experiment in self.experiments:
            if experiment.experiment.experimentId == experimentId:
                experimentPlates = experiment.getPlates()
                for plate in experimentPlates:
                    if plate.plategroup3VO is not None:
                        if plate.plategroup3VO.plateGroupId == plateGroupId:
                            plates.append(plate)
        return plates

    def getRobotXMLByExperimentId(self, experimentId):
        self.selectedExperimentId = experimentId
        if (self.client is None):
            self.__initWebservice()
        for experiment in self.experiments:
            plates = []
            if experiment.experiment.experimentId is experimentId:
                self.selectedExperimentId = experimentId
                for plate in experiment.getPlates():
                    plates.append(plate.samplePlateId)
                return self.client.service.getRobotXMLByPlateIds(experimentId, plates)
        return None

    def getPlateGroupByExperimentId(self, experimentId):
        self.selectedExperimentId = experimentId
        for experiment in self.experiments:
            if experiment.experiment.experimentId == experimentId:
                print experiment.experiment.experimentId
                #It works but I don't know how to deserialize in bricks side
                #return str(experiment.getPlateGroups())
                groups = experiment.getPlateGroups()
                names = []
                for group in groups:
                    names.append([group.name, group.plateGroupId])
                return names
        return []

    def getRobotXMLByPlateGroupId(self, plateGroupId, experimentId):
        plates = self.getPlatesByPlateGroupId(plateGroupId, experimentId)
        ids = []
        for plate in plates:
            ids.append(plate.samplePlateId)
        xml = self.client.service.getRobotXMLByPlateIds(experimentId, str(ids))
        self.emit("onSuccess", "getRobotXMLByPlateGroupId", xml)

    def createExperiment(self, proposalCode, proposalNumber, samples, storageTemperature, mode, extraflowTime):
        try:
            if (self.client is None):
                self.__initWebservice()
        except Exception:
            print "[ISPyB] It has been not possible to connect with ISPyB. No connection"
            raise Exception
            return
        try:
            self.experiment = None
            self.selectedExperimentId = None
            print "[ISPyB] Request to ISPyB: create new experiment for proposal " + str(proposalCode) + str(proposalNumber)
            experiment = self.client.service.createExperiment(proposalCode, proposalNumber, str(samples), storageTemperature, mode, extraflowTime)
            print "[ISPyB] Experiment Created: " + str(experiment.experimentId)
            self.selectedExperimentId = experiment.experimentId
            self.experiment = Experiment(experiment)
            self.experiments.append(Experiment(experiment))
            print "[ISPyB] selectedExperimentId: " + str(self.selectedExperimentId)
            #print experiment
        except Exception:
            print Exception
            print "[ISPyB] error", sys.exc_info()[0]
            raise Exception
            #traceback.print_exc()

class Experiment:
    def __init__(self, experiment):
        self.experiment = experiment

    def getPlates(self):
        return self.experiment.samplePlate3VOs

    def getPlateGroups(self):
        plates = self.getPlates()
        print plates
        dict = {}
        plateGroups = []
        for plate in plates:
            print str(plate)
            if hasattr(plate, 'plategroup3VO'):
                print "contiene plategroup3VO"
                if not dict.has_key(plate.plategroup3VO.name):
                    print "plate.plategroup3VO.name"
                    if plate.plategroup3VO is not None:
                        plateGroups.append(plate.plategroup3VO)
                    dict[plate.plategroup3VO.name] = True
        return plateGroups

if __name__ == "__main__":
    import sys
    biosaxs = BiosaxsClient("mx1438", "Rfo4-73")
    biosaxs.getExperimentNamesByProposalCodeNumber("mx", "1438")
    #experiment = biosaxs.getExperimentById(345)
    biosaxs.selectedExperimentId = 345
    print biosaxs.getSpecimenIdBySampleCode("bsa_25C")

