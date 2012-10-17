from Framework4.Control.Core.CObject import CObjectBase, Slot
from suds.client import Client
from suds.transport.http import HttpAuthenticated

class BiosaxsClient(CObjectBase):
    signals = []
    slots = [
             Slot("getExperimentNamesByProposalCodeNumber"),
             Slot("setUser"),
             Slot("getRobotXMLByExperimentId")
             ]

    def init(self):
        self.URL = 'http://pcantolinos:8080/ispyb-ejb3/ispybWS/ToolsForBiosaxsWebService?wsdl'
        self.selectedExperimentId = None

    def __initWebservice(self, user, password):
        self.user = user #"mx1438"
        self.password = password #"Rfo4-73"
        self.httpAuthenticatedToolsForAutoprocessingWebService = HttpAuthenticated(username = self.user, password = self.password)
        self.client = Client(self.URL, transport = self.httpAuthenticatedToolsForAutoprocessingWebService)
        self.experiments = []
        self.response = None


    def setUser(self, user, password):
        self.__initWebservice(user, password)

    #Return list containing [["ExperimentName1", "experimentId1"], ["ExperimentName2", "experimentId2"]]
    def getExperimentNames(self):
#        print "------------ Getting experiment Names"
        experimentNames = []
        for experiment in self.experiments:
            experimentNames.append([experiment.experiment.name, experiment.experiment.experimentId])
        return experimentNames

    def getExperimentNamesByProposalCodeNumber(self, code, number):
        response = self.client.service.findExperimentByProposalCode(code, number)
        self.experiments = []
        for experiment in response:
            self.experiments.append(Experiment(experiment))
        return self.getExperimentNames()


    def getExperimentsByProposalId(self, proposalId):
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


    def saveFrameSet(self, sampleCode, exposureTemperature, storageTemperature, timePerFrame, timeStart, timeEnd, energy, detectorDistance, fileArray, snapshotCapillary, currentMachine):
        print "Sample code: " + sampleCode
        print "SpecimenId: " + str(self.getSpecimenIdBySampleCode(sampleCode))
        print "ExperimentId: " + str(self.selectedExperimentId)
        print fileArray
        specimenId = self.getSpecimenIdBySampleCode(sampleCode)
        if specimenId is None:
            specimenId = -1
        self.client.service.saveFrameSet(self.selectedExperimentId, str(self.getSpecimenIdBySampleCode(sampleCode)), sampleCode, exposureTemperature, storageTemperature, timePerFrame, timeStart, timeEnd, energy, detectorDistance, fileArray, snapshotCapillary, currentMachine)

        #print str(response)
        #return str(response)
        #return experiments

#    def getExperiments(self, user, password, code, number):
#        self.response = self.client.service.findExperimentByProposalCode(code, number)
#        self.experimentIds = []
#        for experiment in self.response:
#            self.experimentIds.append([experiment.name, experiment.experimentId])
#            self.experiments.append(Experiment(experiment))
#        return self.experimentIds



    def getRobotXMLByExperimentId(self, experimentId):
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
