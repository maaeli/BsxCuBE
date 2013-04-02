from Framework4.Control.Core.CObject import CObjectBase, Slot, Signal
from suds.client import Client
from suds.transport.http import HttpAuthenticated
import traceback
import sys



class BiosaxsClient( CObjectBase ):
    signals = [
               Signal( "onSuccess" ),
               Signal( "onError" )
               ]
    slots = [
             Slot( "getExperimentNamesByProposalCodeNumber" ),
             Slot( "setUser" ),
             Slot( "getRobotXMLByExperimentId" )
             ]

    def init( self ):
        self.client = None

        #Test machine
        self.URL = 'http://ispyvalid.esrf.fr:8080/ispyb-ejb3/ispybWS/ToolsForBiosaxsWebService?wsdl'
        print "ISPyB Server: " + self.URL
        #Alejandro's local machine
        #self.URL = 'http://pcantolinos:8080/ispyb-ejb3/ispybWS/ToolsForBiosaxsWebService?wsdl'
        self.selectedExperimentId = None

        #Login information
        self.user = None
        self.password = None
        self.proposalType = None
        self.proposalNumber = None


        self.timeout = 5
        self.experiments = None

    def __initWebservice( self ):

        self.httpAuthenticatedToolsForAutoprocessingWebService = HttpAuthenticated( username = self.user, password = self.password )
        self.client = Client( self.URL, transport = self.httpAuthenticatedToolsForAutoprocessingWebService, cache = None, timeout = self.timeout )
        self.experiments = []
        self.response = None


    def setUser( self, user, password, proposalType, proposalNumber ):
        self.user = user #"mx1438"
        self.password = password #"Rfo4-73"
        self.proposalType = proposalType
        self.proposalNumber = proposalNumber

    #Return list containing [["ExperimentName1", "experimentId1"], ["ExperimentName2", "experimentId2"]]
    def getExperimentNames( self ):
#        print "------------ Getting experiment Names"
        experimentNames = []
        for experiment in self.experiments:
            experimentNames.append( [experiment.experiment.name, experiment.experiment.experimentId] )
        return experimentNames

    def getExperimentNamesByProposalCodeNumber( self, code, number ):
        if ( self.client is None ):
            self.__initWebservice()
        response = self.client.service.findExperimentByProposalCode( code, number )
        self.experiments = []
        for experiment in response:
            self.experiments.append( Experiment( experiment ) )
        experimentNames = self.getExperimentNames()
        self.emit( "onSuccess", "getExperimentNamesByProposalCodeNumber", experimentNames )
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



    def getSpecimenIdBySampleCode( self, sampleCode ):
        print "[ISPyB] getSpecimenIdBySampleCode " + str( sampleCode )
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

    # Return an array of samples which a given concentration
    def getSpecimensByConcentration( self, concentration ):
        print "[ISPyB] getSpecimenByConcentration: " + str( concentration )
        if self.experiment is None:
            print "[ISPyB] Experiment is None"
            return None
        if self.selectedExperimentId is None:
            print "[ISPyB] Experiment is None"
            return None

        samples = []
        for experiment in self.experiments:
            if experiment.experiment.experimentId == self.selectedExperimentId:
                for sample in experiment.experiment.samples:
                    if ( float( sample.concentration ) ) == ( float( concentration ) ):
                        samples.append( sample )
        return samples


    def getBufferIdByAcronym( self, bufferName ):
        for myBuffer in self.experiment.getBuffers():
            if bufferName == myBuffer.acronym:
                return myBuffer.bufferId
        return None

    #It looks for a code in the comments that identifies the measurments
    # [1] This is a comment
    # ---
    #  |_ Id
    def getMeasurementIdByCommentId( self, commentId ):
        try:
            for experiment in self.experiments:
                if experiment.experiment.experimentId == self.selectedExperimentId:
                    for sample in experiment.experiment.samples:
                        for specimen in sample.specimen3VOs:
                            if str( specimen.comment ).find( "[" + str( commentId ) + "]" ) != -1:
                                return specimen.specimenId
        except:
            traceback.print_exc()
            raise Exception
        return -1

    def getMeasurementIdBySampleCodeConcentrationAndSEU( self, sampleCode, concentration, seu, bufferName ):
        try:
            print "[ISPyB] getMeasurementIdBySampleCodeConcentrationAndSEU " + str( sampleCode ) + " " + str( concentration ) + " " + str( seu ) + " " + str( bufferName )
            if self.experiment is None:
                print "[ISPyB] Experiment is None"
                return None
            if self.selectedExperimentId is None:
                print "[ISPyB] Experiment is None"
                return None
            bufferId = self.getBufferIdByAcronym( bufferName )
            print "[ISPyB] bufferId " + str( bufferId )
            for experiment in self.experiments:
                #print experiment.experiment.experimentId
                if experiment.experiment.experimentId == self.selectedExperimentId:
                    samples = self.getSpecimensByConcentration( concentration )
                    for sample in samples:
                        if sample.bufferId == bufferId:
                            for specimen in sample.specimen3VOs:
                                if ( float( specimen.exposureTemperature ) == float( seu ) and ( str( specimen.code ) == str( sampleCode ) ) ):
                                    return specimen.specimenId
        except Exception:
            print "[ISPyB] error"
            traceback.print_exc()
            raise Exception
        print "[ISPyB] Measurement not found with conc: %s SEU: %s and sampleCode:%s" % ( str( concentration ), str( seu ), str( sampleCode ) )
        return -1
#Testing git hub

    ### Mode: before, after, sample    
    def saveFrameSet( self, mode, sampleCode, exposureTemperature, storageTemperature, timePerFrame, timeStart, timeEnd, energy, detectorDistance, fileArray, snapshotCapillary, currentMachine, tocollect, pars, specimenId ):
        try:
            print "[ISPyB] Request for saveFrameSet " + str( mode ) + " " + str( sampleCode )
            if ( self.client is None ):
                self.__initWebservice()

            #specimenId = self.getMeasurementIdBySampleCodeConcentrationAndSEU(sampleCode, concentration, ispybSEUtemperature, bufferName)
            print "[ISPyB] Specimen: " + str( specimenId )
            if specimenId is None:
                specimenId = -1

            self.client.service.saveFrame( mode,
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
                                          str( tocollect ),
                                          str( pars ),
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

    def getPlatesByPlateGroupId( self, plateGroupId, experimentId ):
        plates = []
        for experiment in self.experiments:
            if experiment.experiment.experimentId == experimentId:
                experimentPlates = experiment.getPlates()
                for plate in experimentPlates:
                    if plate.plategroup3VO is not None:
                        if plate.plategroup3VO.plateGroupId == plateGroupId:
                            plates.append( plate )
        return plates

    def getRobotXMLByExperimentId( self, experimentId ):
        self.selectedExperimentId = experimentId
        if ( self.client is None ):
            self.__initWebservice()
        for experiment in self.experiments:
            plates = []
            if experiment.experiment.experimentId is experimentId:
                self.selectedExperimentId = experimentId
                for plate in experiment.getPlates():
                    plates.append( plate.samplePlateId )
                return self.client.service.getRobotXMLByPlateIds( experimentId, plates )
        return None

    def getPlateGroupByExperimentId( self, experimentId ):
        self.selectedExperimentId = experimentId
        for experiment in self.experiments:
            if experiment.experiment.experimentId == experimentId:
                print experiment.experiment.experimentId
                #It works but I don't know how to deserialize in bricks side
                #return str(experiment.getPlateGroups())
                groups = experiment.getPlateGroups()
                names = []
                for group in groups:
                    names.append( [group.name, group.plateGroupId] )
                return names
        return []

    def getRobotXMLByPlateGroupId( self, plateGroupId, experimentId ):
        plates = self.getPlatesByPlateGroupId( plateGroupId, experimentId )
        ids = []
        for plate in plates:
            ids.append( plate.samplePlateId )
        xml = self.client.service.getRobotXMLByPlateIds( experimentId, str( ids ) )
        self.emit( "onSuccess", "getRobotXMLByPlateGroupId", xml )

    def createExperiment( self, proposalCode, proposalNumber, samples, storageTemperature, mode, extraflowTime ):
        try:
            if ( self.client is None ):
                self.__initWebservice()
        except Exception:
            print "[ISPyB] It has been not possible to connect with ISPyB. No connection"
            raise Exception
        try:
            self.experiment = None
            self.selectedExperimentId = None
            print "[ISPyB] Request to ISPyB: create new experiment for proposal " + str( proposalCode ) + str( proposalNumber )
            experiment = self.client.service.createExperiment( proposalCode, proposalNumber, str( samples ), storageTemperature, mode, extraflowTime )
            if ( experiment is None ):
                print "[ISPyB] ISPyB could not create the experiment from robot file"
                raise Exception

            print "[ISPyB] Experiment Created: " + str( experiment.experimentId )
            self.selectedExperimentId = experiment.experimentId
            self.experiment = Experiment( experiment )
            self.experiments.append( Experiment( experiment ) )
            print "[ISPyB] selectedExperimentId: " + str( self.selectedExperimentId )
            #print experiment
        except Exception:
            print "[ISPyB] handled error"
            traceback.print_exc()
            raise Exception
            #traceback.print_exc()

class Experiment:
    def __init__( self, experiment ):
        self.experiment = experiment

    def getBuffers( self ):
        return self.experiment.buffer3VOs

    def getPlates( self ):
        return self.experiment.samplePlate3VOs

    def getPlateGroups( self ):
        plates = self.getPlates()
        print plates
        dict = {}
        plateGroups = []
        for plate in plates:
            print str( plate )
            if hasattr( plate, 'plategroup3VO' ):
                print "contiene plategroup3VO"
                if not dict.has_key( plate.plategroup3VO.name ):
                    print "plate.plategroup3VO.name"
                    if plate.plategroup3VO is not None:
                        plateGroups.append( plate.plategroup3VO )
                    dict[plate.plategroup3VO.name] = True
        return plateGroups

if __name__ == "__main__":
    biosaxs = BiosaxsClient( "mx1438", "Rfo4-73" )
    biosaxs.getExperimentNamesByProposalCodeNumber( "mx", "1438" )
    #experiment = biosaxs.getExperimentById(345)
    biosaxs.selectedExperimentId = 345
    print biosaxs.getSpecimenIdBySampleCode( "bsa_25C" )

