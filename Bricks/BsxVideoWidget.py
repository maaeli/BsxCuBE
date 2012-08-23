import logging
import sys, time

from PyQt4 import QtCore, Qt

__category__ = "BsxCuBE"

class BsxVideoWidget(Qt.QWidget):

    def __init__(self, *args, **kargs):

        self.refreshRate = 50

        self.image = None
        self.beamLocation = [0, 0, 0, 0]
        self.tempBeamLocation = None
        self.currentLiquidPositionList = []
        self.updateDate = ""
        self.updateTime = ""
        self.imageFormat = "JPG"


        Qt.QWidget.__init__(self, *args, **kargs)

        self.vBoxLayout = Qt.QVBoxLayout()

        self.imageLabel = Qt.QLabel(self)
        self.imageLabel.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding)
        self.imageLabel.setScaledContents(True)
        self.vBoxLayout.addWidget(self.imageLabel)

        self.snapshotPushButton = Qt.QPushButton("Snapshot", self)
        Qt.QObject.connect(self.snapshotPushButton, Qt.SIGNAL("clicked()"), self.snapshotPushButtonClicked)
        self.vBoxLayout.addWidget(self.snapshotPushButton)

        self.setLayout(self.vBoxLayout)

        self.setMouseTracking(True)

        self.imagePainter = Qt.QPainter()

        self.updateTimer = QtCore.QTimer(self)
        self.lastBeamUpdate = 0
        self.beamUpdateInterval = 1
        QtCore.QObject.connect(self.updateTimer, QtCore.SIGNAL('timeout()'), self.update)

        self.__isDrawing = False
        self.__isDefining = False
        self.__isMovingAll = False

        self.__isMovingHorizontalUp = False
        self.__isHorizontalUp = False
        self.__isMovingHorizontalDown = False
        self.__isHorizontalDown = False

        self.__isMovingVerticalLeft = False
        self.__isVerticalLeft = False
        self.__isMovingVerticalRight = False
        self.__isVerticalRight = False

        self.__moveDiagonalUpLeft = False
        self.__isDiagonalUpLeft = False
        self.__moveDiagonalDownLeft = False
        self.__isDiagonalDownLeft = False

        self.__moveDiagonalUpRight = False
        self.__isDiagonalUpRight = False
        self.__moveDiagonalDownRight = False
        self.__isDiagonalDownRight = False

        self.__isInside = False
        self.__moveLocation = []

    def setAutoRefreshRate(self, rate):
        self.refreshRate = rate

    def setAutoRefresh(self, flag):
        if flag == True:
            self.updateTimer.start(self.refreshRate)
        else:
            self.updateTimer.stop()

    def getCurrentLiquidPosition(self):
        return self.currentLiquidPositionList

    def getCurrentBeamLocation(self):
        return self.beamLocation

    def setBeamLocation(self, pos):
        self.beamLocation = pos

    def getNewImage(self):
        return self.image

    def snapshotPushButtonClicked(self):

        filterList = ["Portable Network Graphics (*.png)", "Windows Bitmap (*.bmp)", "Joint Photographics Experts Group (*.jpg)"]
        qFileDialog = Qt.QFileDialog(self, "Save image", ".")
        qFileDialog.setAcceptMode(Qt.QFileDialog.AcceptSave)
        qFileDialog.setFilters(filterList)

        if not qFileDialog.exec_():    #  Cancel button or nothing selected
            return

        if qFileDialog.selectedNameFilter() == filterList[0]:
            imgFormat = "PNG"
        elif qFileDialog.selectedNameFilter() == filterList[1]:
            imgFormat = "BMP"
        else:
            imgFormat = "JPG"

        fileName = str(qFileDialog.selectedFiles()[0])

        if not fileName.upper().endswith("." + format):
            fileName += "." + imgFormat
        if Qt.QPixmap.grabWidget(self.imageLabel).save(fileName, imgFormat):
            Qt.QMessageBox.information(self, "Info", "Image was successfully saved in file '" + fileName + "'!")
        else:
            Qt.QMessageBox.critical(self, "Error", "Error when trying to save image to file '" + fileName + "'!")

    def update(self):
        # update all
        self.updateDate = time.strftime("%Y/%m/%d")
        self.updateTime = time.strftime("%H:%M:%S")

        # get beam and liquid position with different update time than image
        timeFromLastBeamUpdate = int(time.time()) - self.lastBeamUpdate

        if timeFromLastBeamUpdate >= self.beamUpdateInterval :
            self.lastBeamUpdate = int(time.time())
            try:
                self.currentLiquidPositionList = self.getCurrentLiquidPosition()

                # update beam position unless we are drawing it
                if not self.__isDrawing:
                    self.beamLocation = self.getCurrentBeamLocation()
            except Exception, e:
                self.exceptionCallback(e)
                return

        # get new image
        try:
            self.image = self.getNewImage()
        except Exception, e:
            # transmit exception to upper layer (brick)
            self.exceptionCallback(e)
        else:
            if self.image is not None:
                self.updateFrame()

    def exceptionCallback(self, exception):
        pass

    def displayImage(self, image, imgFormat = "JPG"):
        self.image = image
        self.imageFormat = imgFormat
        self.updateFrame()

    def updateFrame(self):
        #TODO: Need to clean this - Should not appear since 22/8 2012 SO
        if type(self.image).__name__ == "list":
            logging.error("Got a list instead of a numpy.ndarray as image" + str(self.image))
            return
        self.imagePixmap = Qt.QPixmap()
        self.imagePixmap.loadFromData(self.image, self.imageFormat)

        self.imagePainter.begin(self.imagePixmap)

        # Date and time
        self.imagePainter.setPen(QtCore.Qt.green)
        self.imagePainter.drawText(5, 15, self.updateDate)
        self.imagePainter.drawText(5, 30, self.updateTime)

        # Liquid position
        if self.currentLiquidPositionList is not None:
            for currentLiquidPosition in self.currentLiquidPositionList:
                self.imagePainter.drawLine(currentLiquidPosition, 0, currentLiquidPosition, self.imageLabel.height())

        # Beam position       
        beam = self.beamLocation
        if beam and len(beam) == 4:
            self.imagePainter.setPen(QtCore.Qt.red)
            self.imagePainter.drawRect(beam[0], beam[1], beam[2] - beam[0], beam[3] - beam[1])

        # Temp beam position
        if self.tempBeamLocation:
            tbeam = self.tempBeamLocation
            self.imagePainter.setPen(QtCore.Qt.blue)
            self.imagePainter.drawRect(tbeam[0], tbeam[1], tbeam[2] - tbeam[0], tbeam[3] - tbeam[1])

        self.imagePainter.end()
        self.imageLabel.setPixmap(self.imagePixmap)

    def drawBeam(self, beam):
        self.beamLocation = beam
        self.updateFrame()

    def mouseDoubleClickEvent(self, pEvent):

        if pEvent.button() != 1:
            return

        x = pEvent.x()
        y = pEvent.y()

        if self.__isDrawing:
            self.__endDrawing()
        else:
            self.__startDrawing(x, y)
        #TODO: What is going on? SO 9/3
        return

        self.__isDefining = True
        self.__isMovingAll = False

        self.__isMovingHorizontalUp = False
        self.__isHorizontalUp = False
        self.__isMovingHorizontalDown = False
        self.__isHorizontalDown = False

        self.__isMovingVerticalLeft = False
        self.__isVerticalLeft = False
        self.__isMovingVerticalRight = False
        self.__isVerticalRight = False

        self.__moveDiagonalUpLeft = False
        self.__isDiagonalUpLeft = False
        self.__moveDiagonalDownLeft = False
        self.__isDiagonalDownLeft = False

        self.__moveDiagonalUpRight = False
        self.__isDiagonalUpRight = False
        self.__moveDiagonalDownRight = False
        self.__isDiagonalDownRight = False

        self.__isInside = False
        self.__moveLocation = []

    def mousePressEvent(self, pEvent):

        if pEvent.button() != 1:
            return

        x = pEvent.x()
        y = pEvent.y()

        if self.__isDrawing:
            self.tempBeamLocation = [x, y, x, y]

        #TODO: Understand this return SO 1/6 2012
        return

        if self.__isInside:
            self.__moveLocation = [x - self.beamLocation[0], y - self.beamLocation[1], self.beamLocation[2] - x, self.beamLocation[3] - y]
            self.__isMovingAll = True
            self.__isDrawing = True
        elif self.__isDiagonalUpLeft:
            self.__isMovingDiagonalUpLeft = True
            self.__isDrawing = True
        elif self.__isDiagonalDownRight:
            self.__isMovingDiagonalDownRight = True
            self.__isDrawing = True
        elif self.__isDiagonalUpRight:
            self.__isMovingDiagonalUpRight = True
            self.__isDrawing = True
        elif self.__isDiagonalDownLeft:
            self.__isMovingDiagonalDownLeft = True
            self.__isDrawing = True
        elif self.__isHorizontalUp:
            self.__isMovingHorizontalUp = True
            self.__isDrawing = True
        elif self.__isHorizontalDown:
            self.__isMovingHorizontalDown = True
            self.__isDrawing = True
        elif self.__isVerticalLeft:
            self.__isMovingVerticalLeft = True
            self.__isDrawing = True
        elif self.__isVerticalRight:
            self.__isMovingVerticalRight = True
            self.__isDrawing = True
        else:
            self.unsetCursor()

    def mouseMoveEvent(self, pEvent):

        x = pEvent.x()
        y = pEvent.y()

        if self.tempBeamLocation:
            self.tempBeamLocation = [self.tempBeamLocation[0], self.tempBeamLocation[1], x, y]
            self.updateFrame()
        #TODO: Why is there a return here??? SO 9/3
        return

        if self.__isDefining:
            self.tempBeamLocation = [self.tempBeamLocation[0], self.tempBeamLocation[1], x, y]
            self.updateFrame()
        elif self.__isMovingAll:
            self.tempBeamLocation = [x - self.__moveLocation[0], y - self.__moveLocation[1], x + self.__moveLocation[2], y + self.__moveLocation[3]]
            self.updateFrame()
        elif self.__isMovingHorizontalUp:
            self.tempBeamLocation = [self.tempBeamLocation[0], y, self.tempBeamLocation[2], self.tempBeamLocation[3]]
            self.updateFrame()
        elif self.__isMovingHorizontalDown:
            self.tempBeamLocation = [self.tempBeamLocation[0], self.tempBeamLocation[1], self.tempBeamLocation[2], y]
            self.updateFrame()
        elif self.__isMovingVerticalLeft:
            self.tempBeamLocation = [x, self.tempBeamLocation[1], self.tempBeamLocation[2], self.tempBeamLocation[3]]
            self.updateFrame()
        elif self.__isMovingVerticalRight:
            self.tempBeamLocation = [self.tempBeamLocation[0], self.tempBeamLocation[1], x, self.tempBeamLocation[3]]
            self.updateFrame()
        elif self.beamLocation is not None:
            if self.beamLocation[0] > self.beamLocation[2]:
                drawBeginX = self.beamLocation[2]
                drawEndX = self.beamLocation[0]
            else:
                drawBeginX = self.beamLocation[0]
                drawEndX = self.beamLocation[2]

            if self.beamLocation[1] > self.beamLocation[3]:
                drawBeginY = self.beamLocation[3]
                drawEndY = self.beamLocation[1]
            else:
                drawBeginY = self.beamLocation[1]
                drawEndY = self.beamLocation[3]

            self.__isInside = (x > drawBeginX and x < drawEndX and y > drawBeginY and y < drawEndY)
            self.__isHorizontalUp = (y == drawBeginY)
            self.__isHorizontalDown = (y == drawEndY)
            self.__isVerticalLeft = (x == drawBeginX)
            self.__isVerticalRight = (x == drawEndX)
            self.__isDiagonalUpLeft = (self.__isHorizontalUp   and self.__isVerticalLeft)
            self.__isDiagonalDownLeft = (self.__isHorizontalDown and self.__isVerticalLeft)
            self.__isDiagonalUpRight = (self.__isHorizontalUp   and self.__isVerticalRight)
            self.__isDiagonalDownRight = (self.__isHorizontalDown and self.__isVerticalRight)

            if self.__isInside:
                self.setCursor(Qt.Qt.SizeAllCursor)
            elif self.__isDiagonalUpLeft or self.__isDiagonalDownRight:
                self.setCursor(Qt.Qt.SizeFDiagCursor)
            elif self.__isDiagonalUpRight or self.__isDiagonalDownLeft:
                self.setCursor(Qt.Qt.SizeBDiagCursor)
            elif self.__isHorizontalUp or self.__isHorizontalDown:
                self.setCursor(Qt.Qt.SizeVerCursor)
            elif self.__isVerticalLeft or self.__isVerticalRight:
                self.setCursor(Qt.Qt.SizeHorCursor)
            else:
                self.unsetCursor()

    def mouseReleaseEvent(self, pEvent):

        if self.tempBeamLocation:
            tbeam = self.tempBeamLocation
            if tbeam[0] != tbeam[2] or tbeam[1] != tbeam[3]:
                self.setCursor(Qt.Qt.ArrowCursor)
                if self.acceptTempBeamLocation():
                    if tbeam[0] > tbeam[2]:
                        x = tbeam[0]
                        tbeam[0] = tbeam[2]
                        tbeam[2] = x

                    if tbeam[1] > tbeam[3]:
                        y = tbeam[1]
                        tbeam[1] = tbeam[3]
                        tbeam[3] = y

                    self.setBeamLocation(tbeam)

            self.__endDrawing()

            self.updateFrame()
        #TODO: what is going on?
        return

        if self.__isDefining or self.__isMovingAll or self.__isMovingHorizontalUp or self.__isMovingHorizontalDown or self.__isMovingVerticalLeft or self.__isMovingVerticalRight:

            self.__isMovingAll = False
            self.__isMovingHorizontalUp = False
            self.__isMovingHorizontalDown = False
            self.__isMovingVerticalLeft = False
            self.__isMovingVerticalRight = False

            self.updateFrame()

    def __startDrawing(self, x, y):
        self.setCursor(Qt.Qt.CrossCursor)
        self.__isDrawing = True
        self.tempBeamLocation = [x, y, x, y]

    def __endDrawing(self):
        self.setCursor(Qt.Qt.ArrowCursor)
        self.__isDrawing = False
        self.tempBeamLocation = None

    def acceptTempBeamLocation(self):

        if Qt.QMessageBox.question(self, "Info", "Do you accept this position as where the beam is located?", \
              Qt.QMessageBox.Yes, Qt.QMessageBox.No, Qt.QMessageBox.NoButton) == Qt.QMessageBox.Yes:
            return True
        else:
            return False


if __name__ == '__main__':

    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = "images/luzern.jpg"
    app = Qt.QApplication(sys.argv)

    win = Qt.QMainWindow()
    wid = BsxVideoWidget(win)
    win.setCentralWidget(wid)
    wid.setWindowTitle('Video Widget')
    wid.displayImage(open(filename).read())
    wid.drawBeam([40, 70, 130, 200])
    wid.setAutoRefreshRate(100)
    wid.setAutoRefresh(True)
    win.show()

    sys.exit(app.exec_())

