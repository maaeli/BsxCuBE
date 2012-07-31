from xml.dom.minidom import parse, parseString
from suds.client import Client
from suds.transport.http import HttpAuthenticated
from suds.sax.date import DateTime




class BiosaxsClient:
	def __init__(self, user, password):
		self.user = user
		self.password = password
		self.httpAuthenticatedToolsForAutoprocessingWebService = HttpAuthenticated(username=self.user, password=self.password)		
		self.client = Client('http://pcantolinos:8080/ispyb-ejb3/ispybWS/ToolsForBiosaxsWebService?wsdl', transport = self.httpAuthenticatedToolsForAutoprocessingWebService)

	def getExperimentsByProposalId(self, id):
		response = self.client.service.findExperimentByPosposalId(415)
		experiments = []
		for experiment in response:
			experiments.append(Experiment(experiment))
		return experiments

	def getRobotXMLByPlateIds(self, experimentId, ids):
		textIds = ''
		for id in ids:
			textIds = str(id) + " " + textIds

		response = self.client.service.getRobotXMLByPlateIds(experimentId, textIds)
		return response


class Experiment:
	def __init__(self, experiment):
		self.experiment = experiment
		print 'creating experiment'

        def getPlates(self):
		return self.experiment.samplePlate3VOs



