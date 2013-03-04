import os
from Framework4.GUI.Core import BaseBrick, Property, PropertyGroup, Connection, Signal, Slot
from PyQt4 import Qt, QtCore, QtGui
import types
import time
from PyMca import PyMcaQt as qt
from PyQt4 import Qwt5 as qwt
from QtBlissGraph import QtBlissGraph

import logging

__category__ = "BsxCuBE"

class BsxGraphBrick( BaseBrick ):


    properties = {"title": Property( "string", "Title", "", "titleChanged", "untitled" ),
                  "lineWidth": Property( "integer", "Line width", "", "lineWidthChanged", 1 ),

                  "enableGrid": Property( "boolean", "Enable grid", "", "enableGridChanged", False ),
                  "enableZoom": Property( "boolean", "Enable zoom", "", "enableZoomChanged", False ),

                  #"showSaveButton": Property("boolean", "Show save button", "", "showSaveButtonChanged", True),
                  "showPrintButton": Property( "boolean", "Show print button", "", "showPrintButtonChanged", True ),
                  "showScaleButton": Property( "boolean", "Show scale button", "", "showScaleButtonChanged", True ),
                  "showGridButton": Property( "boolean", "Show grid button", "", "showGridButtonChanged", True ),

                  "yAxisLabel": Property( "string", "Y axis label", "", "yAxisLabelChanged", "" ),
                  "y2AxisLabel": Property( "string", "Y2 axis label", "", "y2AxisLabelChanged", "" ),
                  "xAxisLabel": Property( "string", "X axis label", "", "xAxisLabelChanged", "" ),
                  "titleFontSize": Property( "combo", "Title font size", "", "titleFontSizeChanged", "14", ["8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24"] ),
                  "axisFontSize": Property( "combo", "Axis font size", "", "axisFontSizeChanged", "8", ["6", "7", "8", "9", "10", "11", "12"] ),
                  "defaultScale": Property( "combo", "Default scale", "", "defaultScaleChanged", "linear", ["linear", "logarithmic"] ),
                  "timeOnXAxis": Property( "boolean", "Time on X axis", "", "timeOnXAxisChanged", False ),
                  "timeElapsedTime": Property( "boolean", "Elapsed time", "", "timeElapsedTimeChanged", True ),
                  "windowSize": Property( "integer", "Window size", "", "windowSizeChanged", "3600" )}

    connections = { "Y": Connection( "Y axis values provider"
                                       , [ Signal( "update", "new_y_axis_value" ) ]
                                       , [ ]
                                       , "y_axis_values_provider_connected" ),
                    "Y2": Connection( "Y2 axis values provider"
                                       , [ Signal( "update", "new_y2_axis_value" ) ]
                                       , [ ]
                                       , "y2_axis_values_provider_connected" ),
                    "y_curves": Connection( "Y-mapped curves provider"
                                            , [Signal( 'new_curves_data', 'y_curves_data' ),
                                               Signal( 'erase_curve', 'erase_curve' )]
                                            , []
                                            , 'y_curves_provider_connected' ),
                    "y2_curves": Connection( "Y2-mapped curves provider"
                                            , [Signal( 'new_curves_data', 'y2_curves_data' ),
                                               Signal( 'erase_curve', 'erase_curve' )]
                                            , []
                                            , 'y2_curves_provider_connected' ),
                    'y_scan': Connection( 'Y scan provider'
                                         , [Signal( 'new_scan', 'new_scan' ),
                                            Signal( 'new_point', 'new_value' )]
                                         , []
                                         , 'y_scan_provider_connected' ),
                    'y2_scan': Connection( 'Y2 scan provider'
                                         , [Signal( 'new_scan', 'new_scan' ),
                                            Signal( 'new_point', 'new_value' )]
                                         , []
                                         , 'y2_scan_provider_connected' ),
                    }



    def __init__( self, *args, **kargs ):
        BaseBrick.__init__( self, *args, **kargs )


    def init( self ):
        self.__axis_provider = dict()
        self.__curves_by_provider = dict()
        self.graphLayout = Qt.QVBoxLayout()
        self.graphSubLayout = Qt.QHBoxLayout()

        self.qtBlissGraph = QtBlissGraph()
        self.graphLayout.addWidget( self.qtBlissGraph )

        #self.savePushButton = Qt.QPushButton("Save")
        #self.graphSubLayout.addWidget(self.savePushButton)
        #Qt.QObject.connect(self.savePushButton, Qt.SIGNAL("clicked()"), self.savePushButtonClicked)

        self.printPushButton = Qt.QPushButton( "Print" )
        self.graphSubLayout.addWidget( self.printPushButton )
        Qt.QObject.connect( self.printPushButton, Qt.SIGNAL( "clicked()" ), self.printPushButtonClicked )


        self.current_scale = "linear"
        self.scalePushButton = Qt.QPushButton( "Scale" )
        self.scaleMenu = Qt.QMenu( self.scalePushButton )
        self.scaleActionGroup = Qt.QActionGroup( self.scaleMenu )
        self.scaleMenuLinear = Qt.QAction( "Linear", self.scaleActionGroup )
        self.scaleMenuLinear.setCheckable( True )
        self.scaleMenu.addAction( self.scaleMenuLinear )
        self.scaleMenuLogarithmic = Qt.QAction( "Logarithmic", self.scaleActionGroup )
        self.scaleMenuLogarithmic.setCheckable( True )
        self.scaleMenu.addAction( self.scaleMenuLogarithmic )
        Qt.QObject.connect( self.scaleActionGroup, Qt.SIGNAL( "triggered(QAction*)" ), self.scaleActionGroupTriggered )
        self.scalePushButton.setMenu( self.scaleMenu )
        self.graphSubLayout.addWidget( self.scalePushButton )

        self.gridPushButton = Qt.QPushButton( "Grid" )
        self.gridMenu = Qt.QMenu( self.gridPushButton )
        self.gridActionGroup = Qt.QActionGroup( self.gridMenu )
        self.gridMenuEnable = Qt.QAction( "Enable", self.gridActionGroup )
        self.gridMenuEnable.setCheckable( True )
        self.gridMenu.addAction( self.gridMenuEnable )
        self.gridMenuDisable = Qt.QAction( "Disable", self.gridActionGroup )
        self.gridMenuDisable.setCheckable( True )
        self.gridMenuDisable.setChecked( True )
        self.gridMenu.addAction( self.gridMenuDisable )
        Qt.QObject.connect( self.gridActionGroup, Qt.SIGNAL( "triggered(QAction*)" ), self.gridActionGroupTriggered )
        self.gridPushButton.setMenu( self.gridMenu )
        self.graphSubLayout.addWidget( self.gridPushButton )

        self.resetPushButton = Qt.QPushButton( "Reset" )
        self.graphSubLayout.addWidget( self.resetPushButton )
        Qt.QObject.connect( self.resetPushButton, Qt.SIGNAL( "clicked()" ), self.resetPushButtonClicked )

        self.graphLayout.addLayout( self.graphSubLayout )
        self.brick_widget.setLayout( self.graphLayout )

        self.curveData = {}
        self.timeAxisX = False
        self.timeAxisElapsedTime = True
        self.windowSize = None


    def addCurve( self, pCurve ):
        curveName = pCurve["name"]
        maptoy2 = pCurve.get( "maptoy2", False )

        if not curveName in self.curveData:
            self.curveData[curveName] = CurveData( curveName, maptoy2 = maptoy2 )

        self.qtBlissGraph.newCurve( curveName, x = self.curveData[curveName].x, y = self.curveData[curveName].y, maptoy2 = maptoy2 )


    def addPoint( self, pCurveName, x = None, y = None, pTimeOut = False, replot = True ):
        if y is None:
            return
        else:
            y = float( y )

        curveData = self.curveData[pCurveName]

        if self.timeAxisX:
            if self.timeAxisElapsedTime:
                if curveData.t0 is None:
                    # 't0' is the starting time (first point added)
                    curveData.t0 = time.time()
                    curveData.t = curveData.t0
                    t = 0
                else:
                    # 't' is the time elapsed between the new point and the previous one
                    t = time.time() - curveData.t
                    curveData.t += t
            else:
                t = int( time.strftime( "%S" ) ) + int( time.strftime( "%H" ) ) * 3600 + int( time.strftime( "%M" ) ) * 60
                curveData.t = t


            if self.windowSize > 0:
                x = 0
                n0 = len( curveData.x )
                curveData.x = filter( None, [x + self.windowSize > 0 and x - t for x in curveData.x] )
                n = len( curveData.x )

                if n0 > n:
                    curveData.y = curveData.y[n0 - n:]
            else:
                if self.timeAxisElapsedTime:
                    x = curveData.t - curveData.t0
                else:
                    x = curveData.t
        elif x is not None:
            x = float( x )
        else:
            if pTimeOut:
                return

            if len( curveData.x ) > 0:
                x = curveData.x[-1] + 1
            else:
                x = 0

        curveData.x.append( x )
        curveData.y.append( y )

        if self.windowSize:
            if not self.timeAxisX and len( curveData.y ) == self.windowSize:
                del curveData.y[0]
                del curveData.x[0]

        if replot:
            self.qtBlissGraph.newCurve( pCurveName, curveData.x, curveData.y, maptoy2 = curveData.maptoy2 )
            self.qtBlissGraph.replot()


    def removeCurve( self, pCurveName ):
        try:
            del self.curveData[pCurveName]
        except KeyError:
            pass
        else:
            self.qtBlissGraph.newCurve( pCurveName, [], [] )
            pass


    def new_y_axis_value( self, *args, **kwargs ):
        self.new_value( *args, **kwargs )

    def new_y2_axis_value( self, *args, **kwargs ):
        kwargs['maptoy2'] = True
        self.new_value( *args, **kwargs )


    def y_curves_data( self, *args, **kwargs ):
        self.new_value( *args, **kwargs )

    def y2_curves_data( self, *args, **kwargs ):
        kwargs['maptoy2'] = True
        self.new_value( *args, **kwargs )

    def new_value( self, value, sender = None, maptoy2 = False, signal = None, replot = True ):
        if type( value ) == types.DictType:
            #dict in the form {curvename: [[values for x],[values for y]]}
            # call ourselves one time per value pair
            for curve, points in value.iteritems():
                self.erase_curve( curve )
                for ( x, y ) in zip( points[0], points[1] ):
                    self.new_value( ( x, y, curve ), sender = sender, maptoy2 = maptoy2, replot = False )
                curveData = self.curveData[curve]
                self.qtBlissGraph.newCurve( curve, curveData.x, curveData.y, maptoy2 = maptoy2 )
            self.qtBlissGraph.replot()
            return

        # if value is not a dict, proceed as usual
        # it's either a tuple or a discrete value
        if type( value ) == types.TupleType and len( value ) == 3:
            curveName = value[2]
        else:
            curveName = sender.username()

        if sender not in self.__curves_by_provider.keys():
          self.__curves_by_provider[sender] = [curveName]
        else:
          if curveName not in self.__curves_by_provider[sender]:
            self.__curves_by_provider[sender].append( curveName )

        if value is None:
            self.removeCurve( curveName )
        else:
            if not curveName in self.curveData:
                self.addCurve( {"name": curveName, 'maptoy2': maptoy2} )
            if type( value ) == types.TupleType:
                if len( value ) >= 2:
                    self.addPoint( curveName, x = value[0], y = value[1], replot = replot )
            else:
                self.addPoint( curveName, y = value, replot = replot )

    def erase_curve( self, curve_name, sender = None ):
        """If the curve_name is None or empty, erase all curves (created by objects sending data packs)"""
        #logging.debug('%s: erase_curve called with curve_name=%s and sender=%s', self, curve_name, sender)
        #logging.debug('curves by sender: %r', self.__curves_by_provider)
        if curve_name is None:
            if sender is not None:
                for curve in self.__curves_by_provider.get( sender, [] ):
                    #logging.debug('    removing curve %s', curve)
                    self.removeCurve( curve )
        else:
            self.removeCurve( curve_name )

    def new_scan( self, parameters, sender = None ):
        self.erase_curve( None, sender )
        ylabel = parameters.get( 'ylabel', "" )
        xlabel = parameters.get( 'xlabel', "" )
        title = parameters.get( 'title', '' )
        self.qtBlissGraph.setTitle( title )
        self.qtBlissGraph.xlabel( xlabel )
        if self.__axis_provider.get( sender, 'y' ) == 'y':
            self.qtBlissGraph.ylabel( ylabel )
        else:
            self.qtBlissGraph.setAxisTitle( qwt.QwtPlot.yRight, ylabel )

    def y_axis_values_provider_connected( self, provider ):
        pass

    def y2_axis_values_provider_connected( self, provider ):
        pass

    def y_curves_provider_connected( self, provider ):
        pass

    def y2_curves_provider_connected( self, provider ):
        pass

    def y_scan_provider_connected( self, provider ):
        self.__axis_provider[provider] = 'y'

    def y2_scan_provider_connected( self, provider ):
        self.__axis_provider[provider] = 'y2'

    def titleChanged( self, pValue ):
        self.qtBlissGraph.setTitle( pValue )


    def lineWidthChanged( self, pValue ):
        self.qtBlissGraph.setactivelinewidth( pValue )
        self.qtBlissGraph.linewidth = pValue
        self.qtBlissGraph.replot()


    def enableGridChanged( self, pValue ):
        if pValue:
            self.gridMenuEnable.setChecked( True )
            self.qtBlissGraph.showGrid()
        else:
            self.gridMenuDisable.setChecked( True )
            self.qtBlissGraph.hideGrid()
        self.qtBlissGraph.replot()



    def enableZoomChanged( self, pValue ):
        self.qtBlissGraph.enableZoom( pValue )



    def showSaveButtonChanged( self, pValue ):
        pass
        #if self.savePushButton is not None:
        #    self.savePushButton.setVisible(pValue)


    def showPrintButtonChanged( self, pValue ):
        if self.printPushButton is not None:
            self.printPushButton.setVisible( pValue )


    def showScaleButtonChanged( self, pValue ):
        if self.scalePushButton is not None:
            self.scalePushButton.setVisible( pValue )


    def showGridButtonChanged( self, pValue ):
        if self.gridPushButton is not None:
            self.gridPushButton.setVisible( pValue )




    def xAxisLabelChanged( self, pValue ):
        self.qtBlissGraph.xlabel( pValue )



    def yAxisLabelChanged( self, pValue ):
        self.qtBlissGraph.ylabel( pValue )



    def y2AxisLabelChanged( self, pValue ):
        self.qtBlissGraph.setAxisTitle( qwt.QwtPlot.yRight, pValue )



    def titleFontSizeChanged( self, pValue ):
        title = self.qtBlissGraph.title()
        font = title.font()
        font.setPointSize( int( pValue ) )
        title.setFont( font )
        self.qtBlissGraph.setTitle( title )


    def axisFontSizeChanged( self, pValue ):
        titleX = self.qtBlissGraph.axisTitle( qwt.QwtPlot.xBottom )
        titleY = self.qtBlissGraph.axisTitle( qwt.QwtPlot.yLeft )
        titleY2 = self.qtBlissGraph.axisTitle( qwt.QwtPlot.yRight )
        fontX = titleX.font()
        fontY = titleY.font()
        fontY2 = titleY2.font()
        size = int( pValue )
        fontX.setPointSize( size )
        fontY.setPointSize( size )
        fontY2.setPointSize( size )
        titleX.setFont( fontX )
        titleY.setFont( fontY )
        titleY2.setFont( fontY2 )
        self.qtBlissGraph.setAxisFont( qwt.QwtPlot.xBottom, fontX )
        self.qtBlissGraph.setAxisFont( qwt.QwtPlot.yLeft, fontY )
        self.qtBlissGraph.setAxisFont( qwt.QwtPlot.yRight, fontY2 )
        self.qtBlissGraph.setAxisTitle( qwt.QwtPlot.xBottom, titleX )
        self.qtBlissGraph.setAxisTitle( qwt.QwtPlot.yLeft, titleY )
        self.qtBlissGraph.setAxisTitle( qwt.QwtPlot.yRight, titleY2 )

    def timeOnXAxisChanged( self, pValue ):
        self.timeAxisX = pValue
        for curveData in self.curveData.itervalues():
            curveData.clear()
            self.qtBlissGraph.newCurve( str( curveData.objectName() ), x = [], y = [], maptoy2 = curveData.maptoy2 )
        self.setXAxisScale()

    def setXAxisScale( self ):
        if self.timeAxisX:
            self.qtBlissGraph.setx1timescale( True )
            if self.windowSize is not None:
                if self.windowSize <= 0:
                    self.qtBlissGraph.xAutoScale = True
                    #self.graphWidget.setAxisAutoScale(qwt.QwtPlot.xBottom)
                else:
                    self.qtBlissGraph.setX1AxisLimits( 0 - int( self.windowSize ), 0 )
                    #self.graphWidget.setAxisScale(qwt.QwtPlot.xBottom, 0 - self.windowSize, 0)
        else:
            self.qtBlissGraph.setx1timescale( False )
            self.qtBlissGraph.xAutoScale = True
            #self.graphWidget.setAxisAutoScale(qwt.QwtPlot.xBottom)
        self.qtBlissGraph.replot()

    def timeElapsedTimeChanged( self, pValue ):
        self.timeAxisElapsedTime = pValue

    def windowSizeChanged( self, pValue ):
        self.windowSize = pValue
        self.setXAxisScale()

    def savePushButtonClicked( self ):
        fileName = QtGui.QFileDialog.getSaveFileName( self.brick_widget, "Save File", "." )

        print
        print dir( self.qtBlissGraph )
        print

        #pixmap = QtGui.QPixmap(self.qtBlissGraph.plotImage.getPixmap())

        pixmap = QtGui.QPixmap( 500, 500 )

        pixmap.fill( self.qtBlissGraph, 0, 0 )
        pixmap.save( fileName, "PNG" )

    def printPushButtonClicked( self ):
        self.qtBlissGraph.printps()

    def scaleActionGroupTriggered( self, scale_action ):
        if scale_action == self.scaleMenuLinear:
            if self.current_scale != "linear":
              self.current_scale = "linear"
              self.qtBlissGraph.toggleLogY()
        else:
            if self.current_scale == "linear":
                self.current_scale = "logarithmic"
                self.qtBlissGraph.toggleLogY()

    def defaultScaleChanged( self, scale ):
        if scale == "linear":
            self.scaleMenuLinear.setChecked( True )
            self.scaleActionGroupTriggered( self.scaleMenuLinear )
        else:
            #logarithmic
            self.scaleMenuLogarithmic.setChecked( True )
            self.scaleActionGroupTriggered( self.scaleMenuLogarithmic )

    def gridActionGroupTriggered( self, pValue ):
        self.setProperty( "enableGrid", pValue == self.gridMenuEnable )

    def resetPushButtonClicked( self ):
        curve_names = self.curveData.keys()
        for name in curve_names:
            self.erase_curve( name )
        self.qtBlissGraph.replot()




class CurveData( Qt.QObject ):
    def __init__( self, pCurveName, maptoy2 = False ):
        Qt.QObject.__init__( self )
        self.setObjectName( pCurveName )
        self.maptoy2 = maptoy2
        self.clear()


    def clear( self ):
        self.x = []
        self.y = []
        self.t0 = None
        self.t = None


    def addPoint( self, y = None, x = None ):
        self.emit( qt.PYSIGNAL( "addPoint" ), ( str( self.name() ), y, x, False ) )


    def timeout( self ):
        if len( self.y ) > 0:
            self.emit( qt.PYSIGNAL( "addPoint" ), ( str( self.name() ), self.y[-1], None, True ) )
