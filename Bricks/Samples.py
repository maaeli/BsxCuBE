import logging
import types
import copy
from lxml import etree

logger = logging.getLogger("Samples")

def node_to_members(node, obj):
    for tag, value in [(x.tag, x.text) for x in node.getchildren()]:
        if value in ("false", "true"):
            # to avoid Alejandro changing stuff on his side,
            # convert those to booleans
            value = bool(value.title())
        else:
            try:
               value = int(value)
            except ValueError:
               try:
                 value = float(value)
               except ValueError:
                 pass
        setattr(obj, tag, value)


def Sample(copysample = None):
  if copysample:
    return copy.deepcopy(copysample)
  else:
    return _Sample()


class _Sample:
    __xmlformat = """
<%(type)s>
  <sampledesc>
     <plate>%(plate)s</plate>
     <row>%(row)s</row>
     <well>%(well)s</well>
     <flow>%(flow)s</flow>
     <buffername>%(buffername)s</buffername>
  </sampledesc>
  <collectpars>
    <enable>%(enable)s</enable>
    <concentration>%(concentration)s</concentration>
    <comments>%(comments)s</comments>
    <code>%(code)s</code>
    <viscosity>%(viscosity)s</viscosity>
    <transmission>%(transmission)s</transmission>
    <volume>%(volume)s</volume>
    <SEUtemperature>%(SEUtemperature)s</SEUtemperature>
    <flow>%(flow)s</flow>
    <recuperate>%(recuperate)s</recuperate>
    <waittime>%(waittime)s</waittime>
  </collectpars>
</%(type)s>
    """
    def __init__(self, copysample = None):
        # Default Values
        self.type = 'Sample'
        self.plate = -1
        self.row = -1
        self.well = -1
        self.title = ""
        self.buffername = ""
        self.enable = True
        self.concentration = 0.0
        self.comments = ""
        self.code = ""
        self.viscosity = 'Low'
        self.transmission = 100.0
        self.volume = 10
        self.SEUtemperature = 4
        self.flow = False
        self.recuperate = False
        self.waittime = 0.0

    def isBuffer(self):
        return self.type == "Buffer"

    def getTitle(self):
        return "P%(plate)s-%(row)s:%(well)s" % self.__dict__

    def xmlFormat(self, format = "xmlline"):
        if format == "xmlline":
            return self.__xmlformat % self.__dict__
        else:
            return self.__xmlformat % self.__dict__


class CollectPars:
    __xmlformat = """
<general>
     <sampleType>%(sampleType)s</sampleType>
     <storageTemperature>%(storageTemperature)s</storageTemperature>
     <extraFlowTime>%(extraFlowTime)s</extraFlowTime>
     <optimization>%(optimization)s</optimization>
     <initialCleaning>%(initialCleaning)s</initialCleaning>
     <bufferMode>%(bufferMode)s</bufferMode>
</general>
    """
    def __init__(self, filename = None):
        # initialize
        self.sampleType = 'Green'
        self.storageTemperature = 25
        self.extraFlowTime = 0
        self.optimization = 0
        self.initialCleaning = False
        self.bufferMode = 0

        self.sampleList = SampleList()
        self.bufferList = SampleList()
        self.history = ""

        if filename:
            self.loadFromXML(filename)

    def xmlFormat(self, format = "xmlline"):
        if format == "xmlline":
            return self.__xmlformat % self.__dict__
        else:
            return self.__xmlformat % self.__dict__

    def loadFromXML(self, filename):
        # filename can be a string, in this case the file is opened then read,
        # or 'filename' can be a file object
        if type(filename) == types.StringType:
            bufstr = open(filename).read()
        else:
            bufstr = filename.read()
            bufstr = bufstr.replace("\000", "")
        self.searchXML(bufstr , self)

    def searchXML(self, xmlstr, destobj):
        xml_tree = etree.fromstring(xmlstr)
        for tag, value in [(x.tag, x.text) for x in xml_tree.xpath("//general/*")]:
            setattr(self, tag, value)
        buffers = xml_tree.xpath("//Buffer")
        for buffer in buffers:
            sample = Sample()
            sample.type = "Buffer"
            self.bufferList.append(sample)
            # let's consider there is only one sampledesc and collectpars per buffer
            node_to_members(buffer.xpath("./sampledesc")[0], sample)
            node_to_members(buffer.xpath("./collectpars")[0], sample)
        samples = xml_tree.xpath("//Sample")
        for sample_node in samples:
            sample = Sample()
            sample.type = "Sample"
            self.sampleList.append(sample)
            # let's consider there is only one sampledesc and collectpars per sample
            node_to_members(buffer.xpath("./sampledesc")[0], sample)
            node_to_members(sample_node.xpath("./sampledesc")[0], sample)
            node_to_members(sample_node.xpath("./collectpars")[0], sample)

    def save(self, filename, history, format = "xml"):
        # start
        bufstr = "<bsxcube>"

        # general pars
        bufstr += self.xmlFormat()

        # samples and buffers
        for localBuffer in self.bufferList:
            bufstr += localBuffer.xmlFormat()
        for localSample in self.sampleList:
            bufstr += localSample.xmlFormat()

        # then history
        bufstr += "\n<history>\n"
        bufstr += history
        bufstr += "\n</history>\n"

        # end
        bufstr += "</bsxcube>"

        open(filename, "w").write(bufstr)

class SampleList(list):
    def sortSEUtemp(self):
        self.sort(self.cmpSEUtemp)
    def sortCode(self):
        self.sort(self.cmpCode)
    def sortCodeAndSEU(self):
        self.sort(self.cmpCodeAndSEU)

    def cmpSEUtemp(self, a, b):
        return cmp(a.SEUtemperature, b.SEUtemperature)
    def cmpCode(self, a, b):
        return cmp(a.code, b.code)
    def cmpCodeAndSEU(self, a, b):
        if a.code == b.code:
            return cmp(a.SEUtemperature, b.SEUtemperature)
        else:
            return cmp(a.code, b.code)

if __name__ == '__main__':
    pars = CollectPars('/data/bm29/inhouse/Test/robot.xml')
    for sample in pars.sampleList:
        print sample.SEUtemperature
    print pars
