#--------------------------------------------------
#
#  Filename    : SPEC (SPEC.py)
#  Description :
#  Version     : 1.0
#  Date        : 10/Sep/2009
#  Author      : Ricardo Nogueira (ESRF)
#
#--------------------------------------------------

import os, sys

class SPEC:

    def __init__(self):
        self.__handler = None
        self.__filename = None

    def getFilename(self):
        return self.__filename

    def open(self, pFilename, pMode = "r+"):
        try:
            self.__filename = str(pFilename)
            self.__handler = open(self.__filename, str(pMode))
            return 0
        except:
            return -1

    def close(self):
        try:
            self.__handler.close()
            return 0
        except:
            return -1

    def isValid(self):
        try:
            self.__handler.seek(0)
            if self.__handler.read(2) == "#F":
                return 0
            else:
                return -1
        except:
            return -1

    def getHeader(self, pSplit = False):
        header = []
        try:
            self.__handler.seek(0)
            for line in self.__handler:
                # skip empty lines
                if len(line.strip()) == 0: continue

                if line[:1] == "#":
                    if pSplit:
                        i = line.find("=")
                        if i != -1:
                            header.append([line[1:i].strip(), line[i + 1:-2].strip()])
                    else:
                        header.append(line[1:-2])
                else:
                    break
        except:
            pass
        return header

    def getValues(self):
        result = []
        try:
            self.__handler.seek(0)
            for line in self.__handler:
                if line[:1] != "#":
                    valueList = line.split(" ")
                    tmp = []
                    for value in valueList:
                        try:
                            tmp.append(float(value))
                        except:
                            pass
                    result.append(tmp)
        except:
            pass
        return result

    def write(self, pHeader, pValues):
        try:
            for header in pHeader:
                self.__handler.write("#" + header + "\r\n")
            for value0 in pValues:
                tmp = ""
                count = len(value0)
                for i in range(0, count):
                    if i < count - 1:
                        tmp += str(value0[i]) + "  "
                    else:
                        tmp += str(value0[i]) + " \n"
                self.__handler.write(tmp)
            return 0
        except:
            return -1

    def radiationDamage(self, pValues, pAdder, pCounter, pTolerance = 0):
        flag = 0
        total = 0
        count = 0
        try:
            values = self.getValues()
            total = len(values)
            if total == len(pValues):
                pTolerance = float(pTolerance)
                for i in range(0, total):
                    if float(values[i][0]) == float(pValues[i][0]):
                        y0 = float(pValues[i][1])
                        y1 = float(values[i][1])
                        tolerance = y0 * pTolerance
                        if y1 < y0 - tolerance or y1 > y0 + tolerance:
                            count += 1
                        else:
                            if pAdder is not None:
                                pAdder[i] += y1
                                pCounter[i] += 1
                    else:
                        flag = -1    # different x values
                        break
            else:
                flag = -1    # different x values
        except:
            flag = -2
        return flag, total, count

if __name__ == "__main__":

    spec = SPEC()

    print spec.open("/bliss/users/nogueira/workspace/data/processed/test_001_01.dat")
    print spec.isValid()
    print spec.getHeader()

    spec0 = SPEC()

    print spec0.open("/bliss/users/nogueira/workspace/data/processed/big_test.dat", "w")
    print spec0.write(spec.getHeader(), spec.getValues())
    print spec0.close()

    print spec.close()

