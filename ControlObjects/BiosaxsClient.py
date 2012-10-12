from Framework4.Control.Core.CObject import CObjectBase, Slot
from suds.client import Client
from suds.transport.http import HttpAuthenticated

class BiosaxsClient(CObjectBase):
    signals = []
    slots = [Slot("getRobotXML")]

    def init(self):
        print "-"*20, "Hello, ISPyB Control object is initializing...."
        self.user = "mx1438"
        self.password = "Rfo4-73"
        self.httpAuthenticatedToolsForAutoprocessingWebService = HttpAuthenticated(username = self.user, password = self.password)
        self.client = Client('http://pcantolinos:8080/ispyb-ejb3/ispybWS/ToolsForBiosaxsWebService?wsdl', transport = self.httpAuthenticatedToolsForAutoprocessingWebService)
        self.experimentIds = []
        self.experiments = []
        self.response = None

    def getExperiments(self, user, password, code, number):
        self.response = self.client.service.findExperimentByProposalCode(code, number)
        self.experimentIds = []
        for experiment in self.response:
            self.experimentIds.append([experiment.name, experiment.experimentId])
            self.experiments.append(Experiment(experiment))
        return self.experimentIds


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
