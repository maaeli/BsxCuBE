from Framework4.Control.Core.CObject import CObjectBase, Slot, Signal
from suds.client import Client
from suds.transport.http import HttpAuthenticated
import time

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

    def __initWebservice(self):

        self.httpAuthenticatedToolsForAutoprocessingWebService = HttpAuthenticated(username = self.user, password = self.password)
        self.client = Client(self.URL, transport = self.httpAuthenticatedToolsForAutoprocessingWebService, cache = None)
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



    def getExperimentsByProposalId(self, proposalId):
        if (self.client is None):
             self.__initWebservice()

        response = self.client.service.findExperimentByPosposalId(3124)
        self.experiments = []
        for experiment in response:
            self.experiments.append(Experiment(experiment))
        return self.getExperimentNames()

    def test(self):
        print "----------------> TEST"

    def getSpecimenIdBySampleCode(self, sampleCode):
        for experiment in self.experiments:
            if experiment.experiment.experimentId is self.selectedExperimentId:
                for sample in experiment.experiment.samples:
                    for specimen in sample.specimen3VOs:
                        if specimen.code == sampleCode:
                            return specimen.specimenId
        return None


    def saveFrameSetBefore(self, sampleCode, exposureTemperature, storageTemperature, timePerFrame, timeStart, timeEnd, energy, detectorDistance, fileArray, snapshotCapillary, currentMachine):
        if (self.client is None):
             self.__initWebservice()
        specimenId = self.getSpecimenIdBySampleCode(sampleCode)
        if specimenId is None:
            specimenId = -1
        self.client.service.saveFrameBefore(self.selectedExperimentId, specimenId, sampleCode, exposureTemperature, storageTemperature, timePerFrame, timeStart, timeEnd, energy, detectorDistance, fileArray, snapshotCapillary, currentMachine)

    def saveFrameSetAfter(self, sampleCode, exposureTemperature, storageTemperature, timePerFrame, timeStart, timeEnd, energy, detectorDistance, fileArray, snapshotCapillary, currentMachine):
        if (self.client is None):
             self.__initWebservice()
        specimenId = self.getSpecimenIdBySampleCode(sampleCode)
        if specimenId is None:
            specimenId = -1
        self.client.service.saveFrameAfter(self.selectedExperimentId, specimenId, sampleCode, exposureTemperature, storageTemperature, timePerFrame, timeStart, timeEnd, energy, detectorDistance, fileArray, snapshotCapillary, currentMachine)

    def saveFrameSet(self, sampleCode, exposureTemperature, storageTemperature, timePerFrame, timeStart, timeEnd, energy, detectorDistance, fileArray, snapshotCapillary, currentMachine):
        if (self.client is None):
             self.__initWebservice()
        specimenId = self.getSpecimenIdBySampleCode(sampleCode)
        if specimenId is None:
            specimenId = -1
        self.client.service.saveFrame(self.selectedExperimentId, specimenId, sampleCode, exposureTemperature, storageTemperature, timePerFrame, timeStart, timeEnd, energy, detectorDistance, fileArray, snapshotCapillary, currentMachine)

    def getRobotXMLByExperimentId(self, experimentId):
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


class Experiment:
    def __init__(self, experiment):
        self.experiment = experiment

    def getPlates(self):
        return self.experiment.samplePlate3VOs

    def getPlateGroups(self, experiment):
        plates = self.getPlates()
        dict = {}
        plateGroups = []
        for plate in plates:
            if hasattr(plate, 'plategroup3VO'):
                if not dict.has_key(plate.plategroup3VO.name):
                    plateGroups.append(plate.plategroup3VO)
                    dict[plate.plategroup3VO.name] = True
        return plateGroups
