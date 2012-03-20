import logging
import re, ast
from copy import copy

#  Default values
sample_pars = {
     'type':            ['Sample', str],
     'plate':           [-1, int],
     'row':             [-1, int],
     'well':            [-1, int],
     'title':           ["", str],
     'buffername' :     ["", str],
     'enable':          [True, ast.literal_eval],
     'concentration':   [0.0, float],
     'comments' :       ["", str],
     'code' :           ["", str],
     'viscosity'  :     ['Low', str],
     'transmission' :   [100.0, float],
     'volume':          [10, int],
     'SEUtemperature':  [20, float],
     'flow':            [False, ast.literal_eval],
     'recuperate':      [False, ast.literal_eval],
     'waittime':        [0.0, float],
}

general_pars = {
     'sampleType'           :  ['Green', str],
     'storageTemperature'   :  [25, float],
     'extraFlowTime'        :  [0, int],
     'optimization'         :  [0, int],
     'initialCleaning'      :  [False, ast.literal_eval],
     'bufferMode'           :  [0, int],
}

def valdict(indict, idx):
    a = {}
    for key in indict:
        a[key] = indict[key][idx]
    return a


class Sample:

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
        if copysample:
            self.__dict__ = copy (copysample.__dict__)
        else:
            self.__dict__.update(valdict(sample_pars, 0))

    def isBuffer(self):
        return self.type == "Buffer"

    def getTitle(self):
        return "P%(plate)s-%(row)s:%(well)s" % self.__dict__

    def xmlFormat(self, format = "xmlline"):
        if format == "xmlline":
            return self.__xmlformat % self.__dict__
        else:
            return self.__xmlformat % self.__dict__

class CollectPars(list):
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
        self.__dict__.update(valdict(general_pars, 0))

        self.sampleList = SampleList()
        self.bufferList = SampleList()

        if filename:
            self.loadFromXML(filename)

    def xmlFormat(self, format = "xmlline"):
        if format == "xmlline":
            return self.__xmlformat % self.__dict__
        else:
            return self.__xmlformat % self.__dict__

    def loadFromXML(self, filename):
        bufstr = open(filename).read()
        self.searchXML(bufstr , self)

    def searchXML(self, xmlstr, destobj):
        retag = re.compile('\<(?P<key>.*?)\>(?P<value>.*?)\<\/(?P=key)\>', re.DOTALL | re.MULTILINE)

        cursor = 0
        mat = retag.search(xmlstr, cursor)

        while mat :
            foundkey = mat.group('key')
            if foundkey in ['bsxcube', 'general', 'collectpars', 'sampledesc' ]:   # Do nothing. Go deeper only
                self.searchXML(mat.group('value'), destobj)
            elif foundkey in ['Sample', 'Buffer']:  # create sample and add to list. pass object to continue deeper
                sample = Sample()
                self.searchXML(mat.group('value'), sample)
                sample.type = foundkey
                print sample.type
                if foundkey == 'Buffer':
                    self.bufferList.append(sample)
                else:
                    self.sampleList.append(sample)
            elif foundkey == 'history':
                self.history = mat.group('value')
            elif foundkey in sample_pars:
                try:
                    destobj.__dict__[foundkey] = sample_pars[foundkey][1](mat.group('value'))
                except Exception, e:
                    print "problem interpreting ", foundkey
                    print " value is ", mat.group('value')
                    logging.getLogger().error("Got Exception: " + str(e) + "When interpreting value")
            elif foundkey in general_pars:
                try:
                    destobj.__dict__[foundkey] = general_pars[foundkey][1](mat.group('value'))
                except Exception, e:
                    print "problem interpreting ", foundkey
                    print " value is ", mat.group('value')
                    logging.getLogger().error("Got Exception: " + str(e) + "When interpreting value")
            cursor = mat.end()
            mat = retag.search(xmlstr, cursor)

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
    pars = CollectPars('/data/id14eh3/inhouse/saxs_pilatus/Sandra/Dps1_DNAcomplexes/Dps1complexes.xml')
    for sample in pars.sampleList:
        print sample.SEUtemperature
    print pars
