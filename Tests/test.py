from suds.client import Client
from suds.transport.http import HttpAuthenticated

class BiosaxsClient():

    def init(self):
        self.URL = 'http://pcantolinos:8080/ispyb-ejb3/ispybWS/ToolsForBiosaxsWebService?wsdl'
        self.selectedExperimentId = None

    def initWebservice(self, user, password):
        self.init()
        self.user = user #"mx1438"
        self.password = password #"Rfo4-73"
        self.httpAuthenticatedToolsForAutoprocessingWebService = HttpAuthenticated(username = self.user, password = self.password)
        self.client = Client(self.URL, transport = self.httpAuthenticatedToolsForAutoprocessingWebService, cache = None)
        self.experiments = []
        self.response = None


    def setUser(self, user, password):
        self.initWebservice(user, password)

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
        return self.experiments


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

        print self.selectedExperimentId
        print specimenId
        print sampleCode
        self.client.service.saveFrame(self.selectedExperimentId, specimenId, sampleCode, exposureTemperature, storageTemperature, timePerFrame, timeStart, timeEnd, energy, detectorDistance, fileArray, snapshotCapillary, currentMachine)

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

    def getSpecimenIdOfBufferBeforeBySampleCode(self, sampleCode):
        specimenId = self.getSpecimenIdBySampleCode(sampleCode)
        return specimenId

    def saveFrameSetBefore(self):

        self.client.service.test(43, "specimenId", "sampleCode", " exposureTemperature", " storageTemperature", " timePerFrame", " timeStart", " timeEnd", " energy", " detectorDistance", " fileArray", " snapshotCapillary", " currentMachine")

class Experiment:
    def __init__(self, experiment):
        self.experiment = experiment

    def getPlates(self):
        return self.experiment.samplePlate3VOs
if __name__ == '__main__':
    print "exexe"
    biosaxs = BiosaxsClient()
    biosaxs.setUser("mx1438", "Rfo4-73")
    print biosaxs.client
    (biosaxs.getExperimentNamesByProposalCodeNumber("mx", "1438"))
    experiments = biosaxs.experiments
    #print (experiments[1].experiment.samples)
    biosaxs.selectedExperimentId = 43
    print biosaxs.client
    biosaxs.saveFrameSetBefore()
    #print biosaxs.getSpecimenIdOfBufferBeforeBySampleCode("A__B1-1__25")
    #biosaxs.getRobotXMLByExperimentId(43)
    #print biosaxs.getSpecimenIdBySampleCode("A__B1-1__25")
    #print biosaxs.getSpecimenIdBySampleCode("A__B1-1__25")
    #biosaxs.initWebservice(biosaxs.user, biosaxs.password)
    #biosaxs.saveFrameSet("A__B1-1__25", "exposureTemperature", "storageTemperature", "timePerFrame", "timeStart", "timeEnd", "energy", "detectorDistance", "fileArray", "snapshotCapillary", "currentMachine")
