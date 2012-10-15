from Framework4.Control.Core.CObject import CObjectBase, Slot
from suds.client import Client
from suds.transport.http import HttpAuthenticated

class BiosaxsClient(CObjectBase):
    signals = []
    slots = [
             Slot("getRobotXML"),
             Slot("getExperimentNamesByProposalCodeNumber"),
             Slot("setUser"),
             Slot("getRobotXMLByExperimentId")
             ]

    def init(self):
        self.URL = 'http://pcantolinos:8080/ispyb-ejb3/ispybWS/ToolsForBiosaxsWebService?wsdl'
        self.user = "mx1438"
        self.password = "Rfo4-73"
        self.httpAuthenticatedToolsForAutoprocessingWebService = HttpAuthenticated(username = self.user, password = self.password)
        self.client = Client(self.URL, transport = self.httpAuthenticatedToolsForAutoprocessingWebService)

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
        print "------------ Getting experiment Names"
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

#        sampleCode = "BSA__B1__30"
#        exposureTemperature = "exposureTemperature"
#        storageTemperature = "storageTemperature"
#        timePerFrame = "timePerFrame"
#        timeStart = ""
#        timeEnd = ""
#        energy = "energy"
#        detectorDistance = "detectorDistance"
#        fileArray = "['/data/bm29/inhouse/Test/raw/jj_058_00001.dat', '/data/bm29/inhouse/Test/raw/jj_058_00002.dat', '/data/bm29/inhouse/Test/raw/jj_058_00003.dat']"
#        snapshotCapillary = "snapshotCapillar"
#        currentMachine = "currentMachine"
#
#        self.client = BiosaxsClient('mx1438', 'Rfo4-73')
#        self.client.saveFrameSet(self.experiment.experiment.experimentId, sampleCode, exposureTemperature, storageTemperature, timePerFrame,timeStart, timeEnd, energy, detectorDistance,  fileArray, snapshotCapillary, currentMachine)

    def test(self):
        print "----------------> TEST"

    def saveFrameSet(self, experimentId, sampleCode, exposureTemperature, storageTemperature, timePerFrame, timeStart, timeEnd, energy, detectorDistance, fileArray, snapshotCapillary, currentMachine):
        self.client.service.saveFrameSet(experimentId, sampleCode, exposureTemperature, storageTemperature, timePerFrame, timeStart, timeEnd, energy, detectorDistance, fileArray, snapshotCapillary, currentMachine)

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
                print "Experiment found with id " + str(experimentId)
                for plate in experiment.getPlates():
                    plates.append(plate.samplePlateId)
                print plates
                return self.client.service.getRobotXMLByPlateIds(experimentId, plates)
        return None

#        return Noneself.client.service.getRobotXMLByPlateIds(self.experiments[currentIndex].experiment.experimentId, plates)

    def getRobotXML(self, currentIndex):
        plates = []
        for  plate in self.experiments[currentIndex].getPlates():
            plates.append(plate.samplePlateId)
        return self.client.service.getRobotXMLByPlateIds(self.experiments[currentIndex].experiment.experimentId, plates)



class Experiment:
    def __init__(self, experiment):
        self.experiment = experiment
        print 'creating experiment ' + experiment.name

    def getPlates(self):
        return self.experiment.samplePlate3VOs
