#/*##########################################################################
# Copyright (C) 2004-2012 European Synchrotron Radiation Facility
#
# This file is part of the PyMca X-ray Fluorescence Toolkit developed at
# the ESRF by the Software group.
#
# This toolkit is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# PyMca is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# PyMca; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# PyMca follows the dual licensing model of Riverbank's PyQt and cannot be
# used as a free plugin for a non-free program.
#
# Please contact the ESRF industrial unit (industry@esrf.fr) if this license
# is a problem for you.
#############################################################################*/
#
# Imported from PyMCA 11/7 2012 Staffan Ohlsson
# removed version less than version >= 4.0.0 of
#  QTVERSION = qt.qVersion() 
# removed QtBlissGraphWindow Class since not needed

import copy
import sys
import time
import numpy

from PyMca import PyMcaQt as qt

QString = qt.QString


from PyQt4 import Qwt5


from PyMca.PyMca_Icons import IconDict

DEBUG = 0
USE_SPS_LUT = 1
if USE_SPS_LUT:
    try:
        from PyMca import spslut
        COLORMAPLIST = [spslut.GREYSCALE, spslut.REVERSEGREY, spslut.TEMP,
                        spslut.RED, spslut.GREEN, spslut.BLUE, spslut.MANY]
    except ImportError:
        print( "QtBlissGraph importing spslut directly" )
        try:
            import spslut
            COLORMAPLIST = [spslut.GREYSCALE, spslut.REVERSEGREY, spslut.TEMP,
                        spslut.RED, spslut.GREEN, spslut.BLUE, spslut.MANY]
        except ImportError:
            USE_SPS_LUT = 0
#import arrayfns
qt.QCursor.ArrowCursor = qt.Qt.ArrowCursor
qt.QCursor.UpArrowCursor = qt.Qt.UpArrowCursor
qt.QCursor.WaitCursor = qt.Qt.WaitCursor
qt.QCursor.CrossCursor = qt.Qt.CrossCursor
qt.QCursor.SizeVerCursor = qt.Qt.SizeVerCursor
qt.QCursor.SizeHorCursor = qt.Qt.SizeHorCursor
qt.QCursor.PointingHandCursor = qt.Qt.PointingHandCursor

if not USE_SPS_LUT:
    # from scipy.pilutil
    def bytescale( data, cmin = None, cmax = None, high = 255, low = 0 ):
        if data.dtype == numpy.uint8:
            return data
        high = high - low
        if cmin is None:
            cmin = min( numpy.ravel( data ) )
        if cmax is None:
            cmax = max( numpy.ravel( data ) )
        scale = high * 1.0 / ( cmax - cmin or 1 )
        bytedata = ( ( data * 1.0 - cmin ) * scale + 0.4999 ).astype( numpy.uint8 )
        return bytedata + numpy.asarray( low ).astype( numpy.uint8 )

    def fuzzypalette():
        #calculare bit mapdef
        # In order to make more easy the reckonings, all the calculations
        # will be done in normalized values and later we translate them to
        # practical values (here we describe the limits of these real values)
        init_num_indexed_color = 0
        end_num_indexed_color = 255
        total_indexed_colors = end_num_indexed_color - init_num_indexed_color
        init_range_color = 0
        end_range_color = 255
        total_range_color = end_range_color - init_range_color

        # We will deal with the colors in this schem like if they were
        # fuzzy variables, so we will represent them like trapezoids
        # that are centered in the crisp value
        fuzziness = 0.75
        slope_factor = 4  # We always suppose that 2*(1.0/slope)<fuzziness

        # Settings for the pallette
        R_center = 0.75
        G_center = 0.5
        B_center = 0.25

        myColorMap = []
        for i in range( init_num_indexed_color, end_num_indexed_color + 1 ):
            normalized_i = float( i ) / total_indexed_colors
            R_value = init_range_color + int( trapezoid_fuction( R_center,
                    fuzziness, slope_factor, normalized_i ) * total_range_color )
            G_value = init_range_color + int( trapezoid_fuction( G_center,
                    fuzziness, slope_factor, normalized_i ) * total_range_color )
            B_value = init_range_color + int( trapezoid_fuction( B_center,
                    fuzziness, slope_factor, normalized_i ) * total_range_color )
            myColorMap.append( qt.qRgb( R_value, G_value, B_value ) )
        return myColorMap

    def trapezoid_fuction( center, fuzziness, slope, point_to_calculate ):
        init_point = center - ( fuzziness / 2.0 )
        end_point = center + ( fuzziness / 2.0 )
        triangular_margin = 1.0 / slope  # We supposse that the highness
                                  # is normalized to 1
        if ( point_to_calculate < init_point ):
            value = 0
        elif ( point_to_calculate < ( init_point + triangular_margin ) ):
            value = ( point_to_calculate - init_point ) * slope
        elif ( point_to_calculate < ( end_point - triangular_margin ) ):
            value = 1
        elif ( point_to_calculate < end_point ):
            value = ( end_point - point_to_calculate ) * slope
        else:
            value = 0
        return value


class QtBlissGraphContainer( qt.QWidget ):
    def __init__( self, parent = None, name = 'Container', fl = 0, *args, **kw ):
        qt.QWidget.__init__( self, parent )
        if 0:
            self.layout = qt.QVBoxLayout( self )
        else:
            self.layout = qt.QHBoxLayout( self )
        self.graph = QtBlissGraph( self, *args, **kw )
        self.layout.addWidget( self.graph )

GRAPHEVENT = qt.QEvent.User


class GraphCustomEvent( qt.QEvent ):
    def __init__( self, dict = None ):
        if dict is None:
            dict = {}
        self.dict = dict
        qt.QEvent.__init__( self, GRAPHEVENT )

class CrappyMouseEvent:
    def __init__( self, types, x, y, button ):
        self.info = ( types, x, y, button )

    def type( self ):
        return self.info[0]

    def pos( self ):
        return self

    def x( self ):
        return self.info[1]

    def y( self ):
        return self.info[2]

    def button( self ):
        return self.info[3]


class QtBlissGraph( Qwt5.QwtPlot ):
    def __init__( self, *args, **kw ):
        Qwt5.QwtPlot.__init__( self, *args )
        #font = self.parent().font()
        #font.setFamily(qt.QString('Helvetica'))
        #self.setFont(font)
        self.plotLayout().setMargin( 0 )
        self.plotLayout().setCanvasMargin( 0 )
        self.setAutoReplot( False )
        self.plotLayout().setAlignCanvasToScales( True )
        #self.setCanvasLineWidth(0)
        #self.setTitle('QtBlissGraph')
        self.setTitle( '   ' )
        self.setAxisTitle( Qwt5.QwtPlot.xBottom, "x" )
        self.setAxisTitle( Qwt5.QwtPlot.yLeft, "y" )
        #On windows there are problems with the first plot when passing to log
        self.__firstplot = 1
        self.__timer = time.time()
        #legend
        legend = Qwt5.QwtLegend()
        legend.setItemMode( Qwt5.QwtLegend.ClickableItem )
        if 'LegendPos'in kw:
            self.insertLegend( legend, kw['LegendPos'] )
        else:
            self.insertLegend( legend, Qwt5.QwtPlot.BottomLegend )
        usecrosscursor = kw.get( 'usecrosscursor', False )
        self.__uselegendmenu = 0
        self.__legendrename = False
        if 'uselegendmenu' in kw:
            if kw['uselegendmenu']:
                self.__uselegendmenu = 1
                if 'legendrename' in kw:
                    if kw['legendrename']:
                        self.__legendrename = True

        if 'keepimageratio' in kw:
            self.__keepimageratio = 1
        else:
            self.__keepimageratio = 0
        self.legendmenu = None
        self.enableZoom( True )
        self.__defaultPlotPoints = False
        self.__defaultPlotLines = True
        self._zooming = 0
        self._selecting = 0
        self.__zoomback = 1
        self.__markermode = 0
        self.__markermoving = 0
        self._xImageMirror = 0
        self._yImageMirror = 1
        self.markersdict = {}
        self.curves = {}
        self.curveslist = []
        self.__activecurves = []
        self.__oldcursor = self.canvas().cursor().shape()
        #colors
        self.colorslist = ['blue', 'red', 'green', 'pink', 'brown',
                           'orange', 'violet', 'yellow']
        self.colors = {}
        self.colors['blue'] = qt.QColor( 0, 0, 0xFF )
        self.colors['red'] = qt.QColor( 0xFF, 0, 0 )
        self.colors['yellow'] = qt.QColor( 0xFF, 0xFF, 0 )
        self.colors['black'] = qt.QColor( 0, 0, 0 )
        self.colors['green'] = qt.QColor( 0, 0xFF, 0 )
        self.colors['white'] = qt.QColor( 0xFF, 0xFF, 0xFF )
        # added colors #
        self.colors['pink'] = qt.QColor( 255, 20, 147 )
        self.colors['brown'] = qt.QColor( 165, 42, 42 )
        self.colors['orange'] = qt.QColor( 255, 165, 0 )
        self.colors['violet'] = qt.QColor( 148, 0, 211 )

        self.__activecolor = self.colors['black']
        #self.__activecolor = self.colors['blue']

        #styles
        ##self.styleslist=['line','spline','steps','sticks','none']
        self.styleslist = ['line', 'steps', 'sticks', 'none']
        self.styles = {}
        self.styles['line'] = Qwt5.QwtPlotCurve.Lines
        ##self.styles['spline'] = Qwt5.QwtPlotCurve.Spline
        self.styles['steps'] = Qwt5.QwtPlotCurve.Steps
        self.styles['sticks'] = Qwt5.QwtPlotCurve.Sticks

        self.styles['none'] = Qwt5.QwtPlotCurve.NoCurve
        #symbols
        self.symbolslist = ['cross', 'ellipse', 'xcross', 'none']
        self.symbols = {}
        self.symbols['cross'] = Qwt5.QwtSymbol.Cross
        self.symbols['ellipse'] = Qwt5.QwtSymbol.Ellipse
        self.symbols['xcross'] = Qwt5.QwtSymbol.XCross
        #latest API
        self.symbols['none'] = Qwt5.QwtSymbol.NoSymbol
        #types
        self.linetypeslist = ['solid', 'dot', 'dash', 'dashdot', 'dashdotdot']
        self.linetypes = {}
        self.linetypes['solid'] = qt.Qt.SolidLine
        self.linetypes['dash'] = qt.Qt.DashLine
        self.linetypes['dashdot'] = qt.Qt.DashDotLine
        self.linetypes['dashdotdot'] = qt.Qt.DashDotDotLine
        self.linetypes['dot'] = qt.Qt.DotLine
        #grid
        self.grid = None
        #color counter
        self.color = 0
        #symbol counter
        self.symbol = 0
        #line type
        self.linetype = 0
        #width
        if sys.platform == "win32":
            self.linewidth = 1
            self.__activelinewidth = 1
        else:
            self.linewidth = 2
            self.__activelinewidth = 2

        #perhaps this should be somewhere else
        self.plotImage = None
        self.onlyoneactive = 1
        self.xAutoScale = True
        self.yAutoScale = True
        self.panningMode = False
        #connections and functions
        self.zoomStack = []
        self.zoomStack2 = []
        self.connect( self, qt.SIGNAL( "legendClicked(QwtPlotItem *)" ),
                     self._legendClicked )

        #replot
        self.__logx1 = 0
        self.__logy1 = 0
        self.__logy2 = 0
        #self.plotimage()
        self.replot()

        self.selectionPicker = None

        if sys.platform == "win32":
            #this get rid of ugly black rectangles during painting
            self.canvas().setAttribute( qt.Qt.WA_PaintOnScreen, False )
        self.picker = MyPicker( self.canvas() )
        self.connect( self.picker,
             qt.SIGNAL( 'MouseMoved(const QMouseEvent&)' ),
             self.onMouseMoved )
        self.connect( self.picker,
             qt.SIGNAL( 'MousePressed(const QMouseEvent&)' ),
             self.onMousePressed )
        self.connect( self.picker,
             qt.SIGNAL( 'MouseReleased(const QMouseEvent&)' ),
             self.onMouseReleased )
        self.connect( self.picker,
             qt.SIGNAL( 'PanningSignal' ),
             self.onPanningSignal )
        self.picker.setSelectionFlags( Qwt5.QwtPicker.DragSelection |
                                      Qwt5.QwtPicker.RectSelection )

        self.picker.setRubberBand( Qwt5.QwtPicker.NoRubberBand )
        self.picker.setRubberBandPen( qt.QPen( qt.Qt.green ) )
        self.picker.setEnabled( 1 )

        if usecrosscursor:
            self.crossPicker = Qwt5.QwtPlotPicker( 
                    Qwt5.QwtPlot.xBottom,
                    Qwt5.QwtPlot.yLeft,
                    Qwt5.QwtPicker.PointSelection,
                    Qwt5.QwtPlotPicker.CrossRubberBand,
                    Qwt5.QwtPicker.AlwaysOff,
                    self.canvas() )
            self.crossPicker.setRubberBandPen( qt.QPen( qt.Qt.red ) )
            self.crossPicker.setTrackerMode( Qwt5.QwtPicker.ActiveOnly )
            self.crossPicker.setEnabled( 1 )

    def setPickerSelectionModeOn( self, mode, max_points = 0 ):
        if self._zooming:
            raise ValueError( "Cannot enter selection mode while zooming" )
        if self.__markermode:
            raise ValueError( "Cannot enter selection mode being in marker mode" )

        #initialize the picker if needed
        if self.selectionPicker is None:
            self.selectionPicker = Qwt5.QwtPicker( self.canvas() )
            pen = qt.QPen( qt.Qt.green )
            pen.setWidth( 2 )
            self.selectionPicker.setRubberBandPen( pen )
            #be ready for the signals
            self.connect( self.selectionPicker,
                         qt.SIGNAL( 'selected(const QwtPolygon &)' ),
                         self.pickerSelectedSlot )
            self.connect( self.selectionPicker,
                         qt.SIGNAL( 'changed(const QwtPolygon &)' ),
                         self.pickerChangedSlot )
            self.connect( self.selectionPicker,
                         qt.SIGNAL( 'appended(const QPoint &)' ),
                         self.pickerAppendedSlot )
            self.connect( self.selectionPicker,
                         qt.SIGNAL( 'moved(const QPoint &)' ),
                         self.pickerMovedSlot )

        if mode.upper() == "POINT":
            self.selectionPicker.setRubberBand( Qwt5.QwtPicker.CrossRubberBand )
            self.selectionPicker.setTrackerMode( Qwt5.QwtPicker.AlwaysOn )
            self.selectionPicker.setSelectionFlags( 
                Qwt5.QwtPicker.DragSelection | Qwt5.QwtPicker.PointSelection )
        elif mode.upper() in ["VLINE", "VERTICAL"]:
            self.selectionPicker.setRubberBand( Qwt5.QwtPicker.VLineRubberBand )
            self.selectionPicker.setTrackerMode( Qwt5.QwtPicker.AlwaysOn )
            self.selectionPicker.setSelectionFlags( 
                Qwt5.QwtPicker.DragSelection | Qwt5.QwtPicker.PointSelection )
        elif mode.upper() in ["HLINE", "HORIZONTAL"]:
            self.selectionPicker.setRubberBand( Qwt5.QwtPicker.HLineRubberBand )
            self.selectionPicker.setTrackerMode( Qwt5.QwtPicker.AlwaysOn )
            self.selectionPicker.setSelectionFlags( 
                Qwt5.QwtPicker.DragSelection | Qwt5.QwtPicker.PointSelection )
        elif mode.upper() == "LINE":
            self.selectionPicker.setRubberBand( Qwt5.QwtPicker.PolygonRubberBand )
            self.selectionPicker.setTrackerMode( Qwt5.QwtPicker.AlwaysOn )
            self.selectionPicker.setSelectionFlags( 
                Qwt5.QwtPicker.DragSelection | Qwt5.QwtPicker.PolygonSelection )
        elif mode.upper() == "RECTANGLE":
            self.selectionPicker.setRubberBand( Qwt5.QwtPicker.RectRubberBand )
            self.selectionPicker.setTrackerMode( Qwt5.QwtPicker.AlwaysOn )
            self.selectionPicker.setSelectionFlags( 
                Qwt5.QwtPicker.DragSelection | Qwt5.QwtPicker.RectSelection )
        elif mode.upper() == "POLYGON":
            self.selectionPicker.setRubberBand( Qwt5.QwtPicker.PolygonRubberBand )
            self.selectionPicker.setTrackerMode( Qwt5.QwtPicker.AlwaysOn )
            self.selectionPicker.setSelectionFlags( 
                Qwt5.QwtPicker.DragSelection | Qwt5.QwtPicker.PolygonSelection )
        else:
            raise ValueError( "Unknown selection mode %s" % mode )
        self._selectionMode = mode
        self._maximumSelectionPoints = max_points
        self.picker.setEnabled( 0 )
        self.selectionPicker.setEnabled( 1 )

    def setPickerSelectionModeOff( self ):
        if self.selectionPicker is not None:
            self.selectionPicker.setEnabled( 0 )
        self.picker.setEnabled( 1 )

    def _emitSelectionPickerSignal( self, event, polygon = None ):
        if DEBUG:
            print( "_emitSelectionPickerSignal %s" % event )
        if polygon is None:
            polygon = self.selectionPicker.selection()
        npoints = polygon.size()
        xList = []
        yList = []
        oldy = None
        oldx = None
        for i in range( npoints ):
            point = polygon.point( i )
            xpixel = point.x()
            ypixel = point.y()
            x = self.invTransform( Qwt5.QwtPlot.xBottom, xpixel )
            y = self.invTransform( Qwt5.QwtPlot.yLeft, ypixel )
            if i == 0:
                xList = [x]
                yList = [y]
                xpixelList = [xpixel]
                ypixelList = [ypixel]
            elif ( xpixel != oldx ) and ( ypixel != oldy ):
                xList.append( x )
                yList.append( y )
                xpixelList.append( xpixel )
                ypixelList.append( ypixel )
            oldx = xpixel
            oldy = ypixel
        ddict = {'event': event,
                 'mode': self._selectionMode.upper(),
                 'maxpoints': self._maximumSelectionPoints,
                 'x': xList,
                 'y': yList,
                 'xpixel': xpixelList,
                 'ypixel': ypixelList,
                 'xcurve': None,
                 'ycurve': None}
        #let the calling program replot
        #self.replot()

        self.emit( qt.SIGNAL( "PolygonSignal" ), ( ddict ) )

    def pickerSelectedSlot( self, *var ):
        if DEBUG:
            print( "Polygon Selected" )
            print( var )
            print( "Forcing = %d" % self.forced )
        self._emitSelectionPickerSignal( "PolygonSelected",
                                        polygon = var[0] )

    def pickerChangedSlot( self, *var ):
        if DEBUG:
            print( "pickerChangedSlot" )
            print( "Polygon Changed" )
            print( "Number of points = %d", var[0].size() )

    def pickerMovedSlot( self, *var ):
        if DEBUG:
            print( "pickerMovedSlot" )
            print( "point", var[0].x(), var[0].y() )
        self._emitSelectionPickerSignal( "PolygonMoved" )

    def pickerAppendedSlot( self, *var ):
        polygon = self.selectionPicker.selection()
        npoints = polygon.size()
        if DEBUG:
            print( "pickerAppendedSlot" )
            print( "point", var[0].x(), var[0].y() )
            print( "Currently npoints = %d" % npoints )
        self.forced = 0
        if self._selectionMode.upper() == "LINE":
            if npoints > 1:
                #check that I already have two distinct points
                oldx = None
                oldy = None
                for i in range( polygon.size() ):
                    point = polygon.point( i )
                    x = point.x()
                    y = point.y()
                    if i > 0:
                        if x != oldx:
                            if y != oldy:
                                #I have two points
                                self.forced = 1
                                break
                    else:
                        oldx = x
                        oldy = y
                if self.forced:
                    result = self.selectionPicker.end( True )
                    if not result:
                        print( "Error forcing result!" )
                    return
        self._emitSelectionPickerSignal( "PolygonAppended" )

    def setx1timescale( self, on = 0 ):
        if on:
            self.setAxisScaleDraw( Qwt5.QwtPlot.xBottom, TimeScaleDraw() )
        else:
            self.setAxisScaleDraw( Qwt5.QwtPlot.xBottom, Qwt5.QwtScaleDraw() )

    def ToggleLogY( self ):
        if DEBUG:
            print( "use toggleLogY" )
        return self.toggleLogY()

    def toggleLogY( self ):
        if self.__logy1:
            self.__logy1 = 0
            self.__logy2 = 0
            if self.yAutoScale:
                self.setAxisAutoScale( Qwt5.QwtPlot.yLeft )
                self.setAxisAutoScale( Qwt5.QwtPlot.yRight )
            self.setAxisScaleEngine( Qwt5.QwtPlot.yLeft,
                                    Qwt5.QwtLinearScaleEngine() )
            self.setAxisScaleEngine( Qwt5.QwtPlot.yRight,
                                    Qwt5.QwtLinearScaleEngine() )
        else:
            self.__logy1 = 1
            self.__logy2 = 1
            self.enableAxis( Qwt5.QwtPlot.yLeft )
            self.enableAxis( Qwt5.QwtPlot.yRight )
            if self.yAutoScale:
                self.setAxisAutoScale( Qwt5.QwtPlot.yLeft )
                self.setAxisAutoScale( Qwt5.QwtPlot.yRight )
            self.setAxisScaleEngine( Qwt5.QwtPlot.yLeft,
                                    Qwt5.QwtLog10ScaleEngine() )
            self.setAxisScaleEngine( Qwt5.QwtPlot.yRight,
                                    Qwt5.QwtLog10ScaleEngine() )
        self.replot()
        if self.checky1scale() or self.checky2scale():
            self.replot()

    def toggleLogX( self ):
        if self.__logx1:
            self.__logx1 = 0
            if self.xAutoScale:
                self.setAxisAutoScale( Qwt5.QwtPlot.xBottom )
            self.setAxisScaleEngine( Qwt5.QwtPlot.xBottom,
                                    Qwt5.QwtLinearScaleEngine() )
        else:
            self.__logx1 = 1
            self.enableAxis( Qwt5.QwtPlot.xBottom )
            if self.xAutoScale:
                self.setAxisAutoScale( Qwt5.QwtPlot.xBottom )
            self.setAxisScaleEngine( Qwt5.QwtPlot.xBottom,
                                    Qwt5.QwtLog10ScaleEngine() )
        self.replot()
        if self.checky1scale() or self.checky2scale():
            self.replot()

    def zoomReset( self ):
        if self.yAutoScale:
            self.setAxisAutoScale( Qwt5.QwtPlot.yLeft )
            self.setAxisAutoScale( Qwt5.QwtPlot.yRight )

        if self.xAutoScale:
            self.setAxisAutoScale( Qwt5.QwtPlot.xTop )
            self.setAxisAutoScale( Qwt5.QwtPlot.xBottom )

        #the above part is enough is there are some curves
        #but is not enough is there is just an image
        if len( self.zoomStack ):
            autoreplot = self.autoReplot()
            self.setAutoReplot( False )
            if len( self.zoomStack ):
                xmin, xmax, ymin, ymax = self.zoomStack[0]
                if self.xAutoScale:
                    self.setAxisScale( Qwt5.QwtPlot.xBottom, xmin, xmax )
                if self.yAutoScale:
                    self.setAxisScale( Qwt5.QwtPlot.yLeft, ymax, ymin )
                xmin, xmax, ymin, ymax = self.zoomStack2[0]
                if self.axisEnabled( Qwt5.QwtPlot.xTop ):
                    if self.xAutoScale:
                        self.setAxisScale( Qwt5.QwtPlot.xTop, xmin, xmax )
                if self.axisEnabled( Qwt5.QwtPlot.yRight ):
                    if self.yAutoScale:
                        self.setAxisScale( Qwt5.QwtPlot.yRight, ymax, ymin )
            self.setAutoReplot( autoreplot )

        self.zoomStack = []
        self.zoomStack2 = []

        self.replot()
        if self.checky1scale() or self.checky2scale():
            self.replot()

    def ResetZoom( self ):
        if DEBUG:
            print( "ResetZoom kept for compatibility, use zoomReset" )
        self.zoomReset()

    def enableZoom( self, flag = True ):
        self.__zoomEnabled = flag
        if flag:
            self._selecting = False

    def isZoomEnabled( self ):
        if self.__zoomEnabled:
            return True
        else:
            return False

    def setPanningMode( self, flag = False ):
        self.panningMode = flag

    def isPanningModeEnabled( self ):
        return self.panningMode

    def enableSelection( self, flag = True ):
        self._selecting = flag
        if flag:
            self.__zoomEnabled = False

    def checky2scale( self ):
        flag = 0
        if len( self.curves.keys() ):
            flag = 1
            for key in self.curves.keys():
                if self.curves[key]['maptoy2']:
                    flag = 0
                    break
            if flag:
                ymax = self.canvasMap( Qwt5.QwtPlot.yLeft ).s2()
                ymin = self.canvasMap( Qwt5.QwtPlot.yLeft ).s1()
                self.setAxisScale( Qwt5.QwtPlot.yRight, ymin, ymax )
        return flag

    def checky1scale( self ):
        flag = 0
        if len( self.curves.keys() ):
            flag = 1
            for key in self.curves.keys():
                if not self.curves[key]['maptoy2']:
                    flag = 0
                    break
            if flag:
                ymax = self.canvasMap( Qwt5.QwtPlot.yRight ).s2()
                ymin = self.canvasMap( Qwt5.QwtPlot.yRight ).s1()
                self.setAxisScale( Qwt5.QwtPlot.yLeft, ymax, ymin )
        return flag

    def pixmapPlot( self, pixmap, size, xmirror = None, ymirror = None ):
        if xmirror is None:
            xmirror = self._xImageMirror
        if ymirror is None:
            ymirror = self._yImageMirror
        if self.plotImage is None:
            self.plotImage = Qwt5PlotImage( self )
        self.plotImage.setPixmap( pixmap, size,
                                 xmirror = xmirror, ymirror = ymirror )

    def imagePlot( self, data = None, colormap = None,
                xmirror = None, ymirror = None ):
        if data is not None:
            #get the current limits
            xmin = self.canvasMap( Qwt5.QwtPlot.xBottom ).s1()
            xmax = self.canvasMap( Qwt5.QwtPlot.xBottom ).s2()
            ymin = self.canvasMap( Qwt5.QwtPlot.yLeft ).s1()
            ymax = self.canvasMap( Qwt5.QwtPlot.yLeft ).s2()
            if self.plotImage is None:
                self.plotImage = Qwt5PlotImage( self )
            if xmirror is None:
                xmirror = self._xImageMirror
            if ymirror is None:
                ymirror = self._yImageMirror
            if len( self.curveslist ):
                self.plotImage.setData( data, ( xmin, xmax ),
                                       ( ymin, ymax ),
                                       colormap = colormap,
                                       xmirror = xmirror,
                                       ymirror = ymirror )
            else:
                #let the scale be governed by the image
                self.plotImage.setData( data, None, None,
                                       colormap = colormap,
                                       xmirror = xmirror,
                                       ymirror = ymirror )
                self.replot()
                xmin = self.canvasMap( Qwt5.QwtPlot.xBottom ).s1()
                xmax = self.canvasMap( Qwt5.QwtPlot.xBottom ).s2()
                ymin = self.canvasMap( Qwt5.QwtPlot.yLeft ).s1()
                ymax = self.canvasMap( Qwt5.QwtPlot.yLeft ).s2()
            self.imageratio = ( ymax - ymin ) / ( xmax - xmin )

    def plotimage( self, *var, **kw ):
        if DEBUG:
            print( "plotimage obsolete, use imagePlot instead" )
        return self.imagePlot( *var, **kw )


    def removeImage( self, legend = None ):
        self.plotImage.detach()
        self.plotImage = None

    def onPanningSignal( self, ddict ):
        if not self.panningMode:
            return
        if len( self.zoomStack ) == 0:
            return
        xmin, xmax = self.getX1AxisLimits()
        ymin, ymax = self.getY1AxisLimits()
        deltaX = 0.1 * ( xmax - xmin )
        deltaY = 0.1 * ( ymax - ymin )
        maxX = max( self.zoomStack[0][0], self.zoomStack[0][1] )
        minX = min( self.zoomStack[0][0], self.zoomStack[0][1] )
        maxY = max( self.zoomStack[0][2], self.zoomStack[0][3] )
        minY = min( self.zoomStack[0][2], self.zoomStack[0][3] )
        if ddict['direction'] == 'up':
            ymin = ymin + deltaY
            ymax = ymax + deltaY
            if ( ymax > maxY ):
                ymax = maxY
            if ( ymin >= maxY ):
                return
            self.setY1AxisLimits( ymin, ymax )
        elif ddict['direction'] == 'down':
            ymin = ymin - deltaY
            ymax = ymax - deltaY
            if ( ymin < minY ):
                ymin = minY
            if ( ymax <= minY ):
                return
            self.setY1AxisLimits( ymin, ymax )
        elif ddict['direction'] == 'right':
            xmin = xmin + deltaX
            xmax = xmax + deltaX
            if ( xmax > maxX ):
                xmax = maxX
            if ( xmin >= maxX ):
                return
            self.setX1AxisLimits( xmin, xmax )
        elif ddict['direction'] == 'left':
            xmin = xmin - deltaX
            xmax = xmax - deltaX
            if ( xmin < minX ):
                xmin = minX
            if ( xmax <= minX ):
                return
            self.setX1AxisLimits( xmin, xmax )
        self.replot()

    def onMouseMoved( self, event ):
        #method to be overwritten
        if DEBUG:
            print( "onMouseMoved, event = ", event )
        xpixel = event.pos().x()
        ypixel = event.pos().y()
        x = self.invTransform( Qwt5.QwtPlot.xBottom, xpixel )
        y = self.invTransform( Qwt5.QwtPlot.yLeft, ypixel )
        if self.__markermode:
            if self.__markermoving in self.markersdict.keys():
                xmarker = self.markersdict[self.__markermoving]['xmarker']
                if xmarker:
                    self.setMarkerXPos( 
                        self.markersdict[self.__markermoving]['marker'], x )
                else:
                    self.setMarkerYPos( 
                        self.markersdict[self.__markermoving]['marker'], y )
                ddict = {}
                ddict['event'] = "markerMoving"
                ddict['marker'] = self.__markermoving
                ddict['x'] = x
                ddict['y'] = y

                self.emit( qt.SIGNAL( "QtBlissGraphSignal" ), ( ddict ) )
                self.replot()
            else:
                ( marker, distance ) = self.closestMarker( xpixel, ypixel )
                if ( marker is not None ) and distance < 4:
                    if marker is None:
                        pass
                    elif marker not in self.markersdict.keys():
                        print( "Wrong Marker selection" )
                    else:
                        if not ( 'xmarker' in self.markersdict[marker] ):
                            self.markersdict[marker]['xmarker'] = True
                        else:
                            xmarker = self.markersdict[marker]['xmarker']
                        if self.markersdict[marker]['followmouse']:
                            if ( self.canvas().cursor().shape() != qt.QCursor.SizeHorCursor ) and \
                               ( self.canvas().cursor().shape() != qt.QCursor.SizeVerCursor ):
                                self.__oldcursor = self.canvas().cursor().shape()
                            if xmarker:
                                #for x marker
                                self.canvas().setCursor( qt.QCursor( qt.QCursor.SizeHorCursor ) )
                            else:
                                #for y marker
                                self.canvas().setCursor( qt.QCursor( qt.QCursor.SizeVerCursor ) )
                        else:
                            #the marker is selectable because we are in markermode
                            if ( self.canvas().cursor().shape() != qt.QCursor.SizeHorCursor ) and \
                               ( self.canvas().cursor().shape() != qt.QCursor.SizeVerCursor ) and \
                               ( self.canvas().cursor().shape() != qt.QCursor.PointingHandCursor ):
                                self.__oldcursor = self.canvas().cursor().shape()
                            self.canvas().setCursor( qt.QCursor( qt.QCursor.PointingHandCursor ) )
                else:
                    self.canvas().setCursor( qt.QCursor( self.__oldcursor ) )
        #as default, export the mouse in graph coordenates
        ddict = {'event':'MouseAt',
              'x':x,
              'y':y,
              'xpixel':xpixel,
              'ypixel':ypixel,
              'xcurve':None,
              'ycurve':None}

        if self.__activecurves is not None:
            if len( self.__activecurves ):
                if self.__activecurves[0] in self.curves.keys():
                    curve = self.curves[self.__activecurves[0]]["curve"]
                    p = curve.closestPoint( qt.QPoint( xpixel, ypixel ) )
                    ddict['xcurve'] = curve.x( p[0] )
                    ddict['ycurve'] = curve.y( p[0] )
                    ddict['point'] = p[0]
                    ddict['distance'] = p[1]



        self.emit( qt.SIGNAL( 'QtBlissGraphSignal' ), ( ddict ) )

    def onMousePressed( self, e ):
        #method to be overwritten
        if DEBUG:
            print( "onMousePressed, event = ", e.pos().x(), e.pos().y() )
        self.movingmarker = 0
        if qt.Qt.LeftButton == e.button():
            # Python semantics: self.pos = e.pos() does not work; force a copy
            #decide zooming or marker
            self._zooming = self.__zoomEnabled
            self.xpos = e.pos().x()
            self.ypos = e.pos().y()
            self.__timer = time.time()
            if self.__markermode:
                if len( self.markersdict.keys() ):
                    xpixel = e.pos().x()
                    ypixel = e.pos().y()
                    x = self.invTransform( Qwt5.QwtPlot.xBottom, xpixel )
                    y = self.invTransform( Qwt5.QwtPlot.yLeft, ypixel )
                    ( marker, distance ) = self.closestMarker( xpixel, ypixel )
                    if ( marker is not None ) and distance < 4:
                        if marker not in self.markersdict.keys():
                            print( "Wrong Marker selection" )
                        else:
                            if not ( 'xmarker' in self.markersdict[marker] ):
                                self.markersdict[marker]['xmarker'] = True
                            else:
                                xmarker = self.markersdict[marker]['xmarker']
                            if self.markersdict[marker]['followmouse']:
                                self.__markermoving = marker
                                if xmarker:
                                    self.setMarkerXPos( 
                                        self.markersdict[marker]['marker'], x )
                                else:
                                    self.setMarkerYPos( 
                                        self.markersdict[marker]['marker'], y )
                        self._zooming = 0

            if self._zooming:
                self.enableOutline( 1 )
                self.setOutlinePen( qt.QPen( qt.Qt.black ) )
                self.picker.setRubberBand( Qwt5.QwtPicker.RectRubberBand )
                if self.zoomStack == []:
                    self.zoomState = ( 
                            self.canvasMap( Qwt5.QwtPlot.xBottom ).s1(),
                            self.canvasMap( Qwt5.QwtPlot.xBottom ).s2(),
                            self.canvasMap( Qwt5.QwtPlot.yLeft ).s2(),
                            self.canvasMap( Qwt5.QwtPlot.yLeft ).s1() )
                if self.zoomStack2 == []:
                    self.zoomState2 = ( 
                            self.canvasMap( Qwt5.QwtPlot.xTop ).s1(),
                            self.canvasMap( Qwt5.QwtPlot.xTop ).s2(),
                            self.canvasMap( Qwt5.QwtPlot.yRight ).s2(),
                            self.canvasMap( Qwt5.QwtPlot.yRight ).s1() )
            elif self._selecting:
                self.enableOutline( 1 )
                self.setOutlinePen( qt.QPen( qt.Qt.black ) )
                self.picker.setRubberBand( Qwt5.QwtPicker.RectRubberBand )
        elif qt.Qt.RightButton == e.button():
            self._zooming = 0
        # fake a mouse move to show the cursor position
        self.onMouseMoved( e )

    def onMouseReleased( self, e ):
        #method to be overwritten
        if DEBUG:
            print( "onMouseRealeased, event = ", e )

        if qt.Qt.LeftButton == e.button():
            #this is to solve a strange problem under darwin platform
            #where the signals were sent twice
            if self.__timer == -1:
                return
            etime = time.time() - self.__timer
            self.__timer = -1
            if ( etime < 0.2 ) and ( ( self.xpos - e.pos().x() ) == 0 ) and ( ( self.xpos - e.pos().x() ) == 0 ):
                self._zooming = 0
                xpixel = e.pos().x()
                ypixel = e.pos().y()
                x = self.invTransform( Qwt5.QwtPlot.xBottom, xpixel )
                y = self.invTransform( Qwt5.QwtPlot.yLeft, ypixel )
                ddict = {}
                ddict['event'] = "MouseClick"
                ddict['x'] = x
                ddict['xpixel'] = xpixel
                ddict['y'] = y
                ddict['ypixel'] = ypixel

                self.emit( qt.SIGNAL( "QtBlissGraphSignal" ), ( ddict ) )
            if self._zooming:
                xmin0 = min( self.xpos, e.pos().x() )
                xmax0 = max( self.xpos, e.pos().x() )
                ymin0 = min( self.ypos, e.pos().y() )
                ymax0 = max( self.ypos, e.pos().y() )
                self.picker.setRubberBand( Qwt5.QwtPicker.NoRubberBand )
                xmin = self.invTransform( Qwt5.QwtPlot.xBottom, xmin0 )
                xmax = self.invTransform( Qwt5.QwtPlot.xBottom, xmax0 )
                ymin = self.invTransform( Qwt5.QwtPlot.yLeft, ymin0 )
                ymax = self.invTransform( Qwt5.QwtPlot.yLeft, ymax0 )
                if self.plotImage is not None:
                    # prevent problem of misaligned image
                    xmin = int( xmin )
                    xmax = int( xmax )
                    ymin = int( ymin )
                    ymax = int( ymax )
                graphXMin, graphXMax = self.getX1AxisLimits()
                if xmin < graphXMin:
                    xmin = graphXMin
                if xmax > graphXMax:
                    xmax = graphXMax
                if self.isY1AxisInverted():
                    graphYMax, graphYMin = self.getY1AxisLimits()
                else:
                    graphYMin, graphYMax = self.getY1AxisLimits()
                if ymax < ymin:
                    if ymax < graphYMin:
                        ymax = graphYMin
                    if ymin > graphYMax:
                        ymin = graphYMax
                else:
                    if ymin < graphYMin:
                        ymin = graphYMin
                    if ymax > graphYMax:
                        ymax = graphYMax
                if xmin == xmax or ymin == ymax:
                    self._zooming = 0
                    return
                if self.__keepimageratio:
                    ysize = abs( ymin - ymax )
                    xsize = abs( xmin - xmax )
                    a = min( xsize, ysize )
                    xsize = a
                    ysize = a * self.imageratio
                    xmin = int( 0.5 * ( xmin + xmax ) - 0.5 * xsize )
                    xmax = xmin + xsize - 1
                    ymin = int( 0.5 * ( ymin + ymax ) - 0.5 * ysize )
                    ymax = ymin + round( ysize ) - 1
                self.zoomStack.append( self.zoomState )
                self.zoomState = ( xmin, xmax, ymin, ymax )
                self.enableOutline( 0 )
                autoreplot = self.autoReplot()
                self.setAutoReplot( False )
                self.setAxisScale( Qwt5.QwtPlot.xBottom, xmin, xmax )
                self.setAxisScale( Qwt5.QwtPlot.yLeft, ymax, ymin )
                if self.axisEnabled( Qwt5.QwtPlot.xTop ):
                    xmin = self.invTransform( Qwt5.QwtPlot.xTop, xmin0 )
                    xmax = self.invTransform( Qwt5.QwtPlot.xTop, xmax0 )
                    self.setAxisScale( Qwt5.QwtPlot.xTop, xmin, xmax )
                if self.axisEnabled( Qwt5.QwtPlot.yRight ):
                    ymin = self.invTransform( Qwt5.QwtPlot.yRight, ymin0 )
                    ymax = self.invTransform( Qwt5.QwtPlot.yRight, ymax0 )
                    self.setAxisScale( Qwt5.QwtPlot.yRight, ymax, ymin )
                self.zoomStack2.append( self.zoomState2 )
                self.zoomState2 = ( xmin, xmax, ymin, ymax )
                self.setAutoReplot( autoreplot )
                self.replot()
                #zooming is over
                self._zooming = 0
                ddict = {}
                ddict['event'] = "MouseZoom"
                ddict['xmin'] = min( xmin, xmax )
                ddict['xpixel_min'] = min( xmin0, xmax0 )
                ddict['ymin'] = min( ymin, ymax )
                ddict['ypixel_min'] = min( ymin0, ymax0 )
                ddict['xmax'] = max( xmin, xmax )
                ddict['xpixel_max'] = max( xmin0, xmax0 )
                ddict['ymax'] = max( ymin, ymax )
                ddict['ypixel_max'] = max( ymin0, ymax0 )


                self.emit( qt.SIGNAL( "QtBlissGraphSignal" ), ( ddict ) )
            elif self._selecting:
                xmin0 = min( self.xpos, e.pos().x() )
                xmax0 = max( self.xpos, e.pos().x() )
                ymin0 = min( self.ypos, e.pos().y() )
                ymax0 = max( self.ypos, e.pos().y() )
                self.picker.setRubberBand( Qwt5.QwtPicker.NoRubberBand )
                xmin = self.invTransform( Qwt5.QwtPlot.xBottom, xmin0 )
                xmax = self.invTransform( Qwt5.QwtPlot.xBottom, xmax0 )
                ymin = self.invTransform( Qwt5.QwtPlot.yLeft, ymin0 )
                ymax = self.invTransform( Qwt5.QwtPlot.yLeft, ymax0 )
                self.enableOutline( 0 )
                self.replot()
                ddict = {}
                ddict['event'] = "MouseSelection"
                ddict['xmin'] = min( xmin, xmax )
                ddict['xpixel_min'] = min( xmin0, xmax0 )
                ddict['ymin'] = min( ymin, ymax )
                ddict['ypixel_min'] = min( ymin0, ymax0 )
                ddict['xmax'] = max( xmin, xmax )
                ddict['xpixel_max'] = max( xmin0, xmax0 )
                ddict['ymax'] = max( ymin, ymax )
                ddict['ypixel_max'] = max( ymin0, ymax0 )

                self.emit( qt.SIGNAL( "QtBlissGraphSignal" ), ( ddict ) )
            else:
                if self.__markermode:
                    if len( self.markersdict.keys() ):
                        xpixel = e.pos().x()
                        ypixel = e.pos().y()
                        ( marker, distance ) = self.closestMarker( xpixel, ypixel )
                        if marker is None:
                            pass
                        elif marker not in self.markersdict.keys():
                            print( "Wrong Marker selection" )
                        else:
                            ddict = {}
                            if self.markersdict[marker]['followmouse']:
                                ddict['event'] = "markerMoved"
                            else:
                                ddict['event'] = "markerSelected"
                            ddict['distance'] = distance
                            ddict['marker'] = marker
                            x = self.markersdict[marker]['marker'].xValue()
                            y = self.markersdict[marker]['marker'].yValue()
                            ddict['x'] = x
                            ddict['xpixel'] = xpixel
                            ddict['y'] = y
                            ddict['ypixel'] = ypixel
                            self.emit( qt.SIGNAL( "QtBlissGraphSignal" ),
                                          ( ddict ) )
                    else:
                        #print "not in marker mode"
                        pass
                    self.__markermoving = 0
        elif qt.Qt.RightButton == e.button():
            if self.__zoomback:
                autoreplot = self.autoReplot()
                self.setAutoReplot( False )
                if len( self.zoomStack ):
                    xmin, xmax, ymin, ymax = self.zoomStack.pop()
                    self.setAxisScale( Qwt5.QwtPlot.xBottom, xmin, xmax )
                    self.setAxisScale( Qwt5.QwtPlot.yLeft, ymax, ymin )
                    xmin, xmax, ymin, ymax = self.zoomStack2.pop()
                    if self.axisEnabled( Qwt5.QwtPlot.xTop ):
                        self.setAxisScale( Qwt5.QwtPlot.xTop, xmin, xmax )
                    if self.axisEnabled( Qwt5.QwtPlot.yRight ):
                        self.setAxisScale( Qwt5.QwtPlot.yRight, ymax, ymin )
                    self.replot()
                self.setAutoReplot( autoreplot )
            return

    def enablezoomback( self ):
        self.__zoomback = 1

    def disablezoomback( self ):
        self.__zoomback = 0

    def enablemarkermode( self ):
        self.__markermode = 1

    def disablemarkermode( self ):
        self.__markermode = 0

    def setmarkerfollowmouse( self, marker, boolean ):
        if marker in self.markersdict.keys():
            if boolean:
                self.markersdict[marker]['followmouse'] = 1
            else:
                self.markersdict[marker]['followmouse'] = 0

    def __legendsetactive( self ):
        self.setactivecurve( self.__activelegendname )

    def __legendmaptoy1( self ):
        self.mapToY1( self.__activelegendname )
        self.setactivecurve( self.getactivecurve( justlegend = 1 ) )

    def __legendmaptoy2( self ):
        self.mapToY2( self.__activelegendname )
        self.setactivecurve( self.getactivecurve( justlegend = 1 ) )

    def __legendTogglePoints( self ):
        self.togglePoints( self.__activelegendname )
        self.setactivecurve( self.getactivecurve( justlegend = 1 ) )

    def __legendToggleLine( self ):
        self.toggleLine( self.__activelegendname )
        self.setactivecurve( self.getactivecurve( justlegend = 1 ) )

    def setDefaultPlotPoints( self, value ):
        if value:
            self.__defaultPlotPoints = True
            for key in self.curves.keys():
                curve = self.curves[key]['curve']
                symbol = curve.symbol()
                if symbol.style() == self.symbols['none']:
                    self.togglePoints( key )
        else:
            self.__defaultPlotPoints = False
            for key in self.curves.keys():
                curve = self.curves[key]['curve']
                symbol = curve.symbol()
                if symbol.style() != self.symbols['none']:
                    self.togglePoints( key )
            if self.__defaultPlotLines == False:
                self.setDefaultPlotLines( True )

    def setDefaultPlotLines( self, value ):
        if value:
            self.__defaultPlotLines = True
            for key in self.curves.keys():
                curve = self.curves[key]['curve']
                if curve.style() == Qwt5.QwtPlotCurve.NoCurve:
                    self.toggleLine( key )
        else:
            self.__defaultPlotLines = False
            for key in self.curves.keys():
                curve = self.curves[key]['curve']
                if curve.style() != Qwt5.QwtPlotCurve.NoCurve:
                    self.toggleLine( key )
            if self.__defaultPlotPoints == False:
                self.setDefaultPlotPoints( True )

    def togglePoints( self, key ):
        if key not in self.curves.keys():
            if DEBUG:print( "curve %s does not exists" % key )
            return
        curve = self.curves[key]['curve']
        pen = curve.pen()
        symbol = curve.symbol()
        if symbol.style() == self.symbols['none']:
            if self.curves[key] ["symbol"] not in [self.symbols['none'], None]:
                newsymbol = self.curves[key] ["symbol"]
            else:
                #newsymbol = self.symbols['ellipse']
                #newsymbol = Qwt5.QwtSymbol.XCross  # good
                #newsymbol = Qwt5.QwtSymbol.Cross   # good
                newsymbol = Qwt5.QwtSymbol.Ellipse  # good (at least on windows)
            newsymbol = Qwt5.QwtSymbol( newsymbol,
                                  qt.QBrush( pen.color() ),
                                  pen,
                                  qt.QSize( 5, 5 ) )
        else:
            newsymbol = self.symbols['none']
            newsymbol = Qwt5.QwtSymbol( newsymbol,
                                  qt.QBrush( pen.color() ),
                                  pen,
                                  qt.QSize( 5, 5 ) )
        curve.setSymbol( newsymbol )

    def toggleLine( self, key ):
        if key not in self.curves.keys():
            if DEBUG:print( "curve %s does not exists" % key )
            return
        curve = self.curves[key]['curve']
        linetype = curve.style()
        pen = curve.pen()
        if curve.style() == Qwt5.QwtPlotCurve.NoCurve:
            color = self.curves[key] ["pen"]
            linetype = self.curves[key] ["linetype"]
            pen.setColor( color )
            pen.setWidth( self.linewidth )
            pen.setStyle( linetype )
            curve.setStyle( Qwt5.QwtPlotCurve.Lines )
        else:
            curve.setStyle( Qwt5.QwtPlotCurve.NoCurve )

    def __legendremovesignal( self ):
        if DEBUG: print( "__legendremovesignal" )
        self.__removecurveevent = {}
        self.__removecurveevent['event'] = "RemoveCurveEvent"
        self.__removecurveevent['legend'] = self.__activelegendname

    def __legendrenamesignal( self ):
        if DEBUG: print( "__legendrenamesignal" )
        import RenameCurveDialog
        dialog = RenameCurveDialog.RenameCurveDialog( self,
                                                     self.__activelegendname,
                                                     self.curveslist )
        ret = dialog.exec_()
        if ret:
            newlegend = dialog.getText()
            self.__renamecurveevent = {}
            self.__renamecurveevent['event'] = "RenameCurveEvent"
            self.__renamecurveevent['legend'] = self.__activelegendname
            self.__renamecurveevent['newlegend'] = newlegend

    def customEvent( self, event ):
        if 'legend'in event.dict:
            self.emit( qt.SIGNAL( 'QtBlissGraphSignal' ), ( event.dict ) )
        else:
            newevent = CrappyMouseEvent( event.dict['event'],
                                        event.dict['x'],
                                        event.dict['y'],
                                        event.dict['button'] )
            if event.dict['event'] == qt.QEvent.MouseMove:
                self.onMouseMoved( newevent )
            elif event.dict['event'] == qt.QEvent.MouseButtonPress:
                self.onMousePressed( newevent )
            elif event.dict['event'] == qt.QEvent.MouseButtonRelease:
                self.onMouseReleased( newevent )

    def maptoy1( self, keyorindex ):
        print( "maptoy1 deprecated, use mapToY1" )
        self.mapToY1( keyorindex )

    def mapToY1( self, keyorindex ):
        if type( keyorindex ) in [type( unicode( " " ) ), type( " " ), type( str( " " ) )]:
            if keyorindex in self.curveslist:
                index = self.curveslist.index( keyorindex ) + 1
                key = keyorindex
            else:
                return -1
        elif keyorindex > 0:
            index = keyorindex
            key = self.curveslist[index - 1]
        else:
            return -1
        if not self.axisEnabled( Qwt5.QwtPlot.yLeft ):
            self.enableAxis( Qwt5.QwtPlot.yLeft, 1 )
        self.curves[key]["maptoy2"] = 0
        self.setCurveYAxis( index, Qwt5.QwtPlot.yLeft )

    def maptoy2( self, keyorindex ):
        print( "maptoy2 deprecated, use mapToY2" )
        self.mapToY2( keyorindex )

    def mapToY2( self, keyorindex ):
        if type( keyorindex ) in [type( unicode( " " ) ), type( " " ), type( str( " " ) )]:
            if keyorindex in self.curveslist:
                index = self.curveslist.index( keyorindex ) + 1
                key = keyorindex
            else:
                return -1
        elif keyorindex > 0:
            index = keyorindex
            key = self.curveslist[index - 1]
        else:
            return -1
        if not self.axisEnabled( Qwt5.QwtPlot.yRight ):
            self.enableAxis( Qwt5.QwtPlot.yRight, 1 )
        self.curves[key]["maptoy2"] = 1
        self.setCurveYAxis( index, Qwt5.QwtPlot.yRight )

    def setCurveYAxis( self, index, axis ):
        self.curves[self.curveslist[index - 1]]['curve'].setYAxis( axis )


    def _legendClicked( self, itemorindex ):
        self.legendClicked( itemorindex )


    def legendClicked( self, item, index = None ):
        legendtext = qt.safe_str( item.title().text() )
        if self.onlyoneactive:
            self.setactivecurve( legendtext )
        else:
            self.toggleCurve( legendtext )

    def legendclicked( self, index ):
        if DEBUG:
            print( "legendclicked with index = ", index )

        listindex = 0
        for curve in self.curveslist:
            if self.curves[curve]['curve'] == index:
                legendtext = curve
                listindex = self.curveslist.index( legendtext ) + 1
                if DEBUG:
                    print( "legendclicked with name = ", legendtext )
                break

        if listindex > 0:
            if self.onlyoneactive:
                self.setactivecurve( legendtext )
            else:
                self.toggleCurve( legendtext )

        legend = self.legend()
        n = legend.itemCount()

        if n > 1:
            if 0:
                for i in range( n ):
                    item = self.legend().findItem( i + 1 )
#TODO: DEBUG - next line is not right - No ClickFocus
#                    item.setFocusPolicy(qt.QWidget.ClickFocus)
            else:
                for curve in self.curves.keys():
                    item = self.legend().findItem( self.curves[curve] ["curve"] )


    def setactivecolor( self, color ):
        if color != self.__activecolor:
            if color in self.colors.keys():
                if color in self.colorslist:
                    colorindex = self.colorslist.index( color )
                    colorbuffer = self.__activecolor
                    self.__activecolor = color
                    self.colorslist[colorindex] = colorbuffer
        return self.__activecolor

    def setactivelinewidth( self, linewidth ):
        self.__activelinewidth = linewidth
        return self.__activelinewidth

    def xlabel( self, label = None ):
        if DEBUG:print( "xlabel deprecated, use x1Label" )
        return self.x1Label( label )

    def x1Label( self, label = None ):
        # set axis titles
        if label is None:
            return self.axisTitle( Qwt5.QwtPlot.xBottom ).text()
        else:
            return self.setAxisTitle( Qwt5.QwtPlot.xBottom, label )

    def ylabel( self, label = None ):
        if DEBUG:"print ylabel deprecated, use y1Label"
        self.y1Label( label )

    def y1Label( self, label = None ):
        # set axis titles
        if label is None:
            return self.axisTitle( Qwt5.QwtPlot.yLeft ).text()
        else:
            return self.setAxisTitle( Qwt5.QwtPlot.yLeft, label )


    # TODO fred still necessary ?
    def enableOutline( self, value ):
        pass

    # TODO fred still necessary ?
    def setOutlinePen( self, value ):
        pass

    # TODO fred still necessary ?
    def setOutlineStyle( self, value ):
        pass

    def removeCurve( self, key ):
        return self.delcurve( key )

    def setAutoLegend( self, value ):
        print( "setAutoLegend: Not available in Qwt5, use setDisplayPolicy)" )
        return

    # TODO fred there is return and useless code in this method
    def enableLegend( self, value ):
        #print "Not available in Qwt5, use setDisplayPolicy)"
        if value:
            self.legend().show()
            return
            #TODO: Not reached
            #self.legend().setDisplayPolicy( self.legend().AutoIdentifier, 3 )
        else:
            self.legend().hide()
            return
            #TODO:  Not reached 
            # self.legend().setDisplayPolicy( self.legend().NoIdentifier, 3 )


    def legendItemSlot( self, ddict ):
        if ddict['event'] == "leftMousePressed": return self.setactivecurve( ddict['legend'] )
        if ddict['event'] != "rightMouseReleased": return
        if not self.__uselegendmenu: return
        self.__activelegendname = ddict['legend']
        self.__event = None
        self.__removecurveevent = None
        self.__renamecurveevent = None
        if self.legendmenu is None:
            self.legendmenu = qt.QMenu()
            self.legendmenu.addAction( QString( "Set Active" ), self.__legendsetactive )
            self.legendmenu.addSeparator()
            self.legendmenu.addAction( QString( "Map to y1" ) , self.__legendmaptoy1 )
            self.legendmenu.addAction( QString( "Map to y2" ) , self.__legendmaptoy2 )
            self.legendmenu.addSeparator()
            self.legendmenu.addAction( QString( "Toggle Points" ) ,
                                   self.__legendTogglePoints )
            self.legendmenu.addAction( QString( "Toggle Line" ) ,
                                   self.__legendToggleLine )
            self.legendmenu.addSeparator()
            self.legendmenu.addAction( QString( "Remove curve" ) , self.__legendremovesignal )
            if self.__legendrename:
                self.legendmenu.addAction( QString( "Rename curve" ) ,
                                           self.__legendrenamesignal )

        self.legendmenu.exec_( self.cursor().pos() )

        if self.__removecurveevent is not None:
            event = GraphCustomEvent()
            event.dict['event' ] = "RemoveCurveEvent"
            event.dict['legend'] = self.__removecurveevent['legend']
            qt.QApplication.postEvent( self, event )

        if self.__renamecurveevent is not None:
            event = GraphCustomEvent()
            event.dict['event' ] = "RenameCurveEvent"
            event.dict['legend'] = self.__renamecurveevent['legend']
            event.dict['newlegend'] = self.__renamecurveevent['newlegend']
            qt.QApplication.postEvent( self, event )

    def newcurve( self, *var, **kw ):
        if DEBUG: print( "newcurve obsolete, use newCurve instead" )
        return self.newCurve( *var, **kw )

    def newCurve( self, key, x = None, y = None, logfilter = 0, curveinfo = None,
                 maptoy2 = False, **kw ):
        if key not in self.curves.keys():
            self.curveinit( key, **kw )
            n = self.legend().itemCount()
            if n > 0:
                item = self.legend().find( self.curves[key]['curve'] )
                self.connect( item, qt.SIGNAL( "MyQwt5LegendItemSignal" ),
                                 self.legendItemSlot )
        else:
            #curve already exists
            pass
        if curveinfo is None:
            self.curves[key]['curveinfo'] = {}
        else:
            self.curves[key]['curveinfo'] = copy.deepcopy( curveinfo )
        if y is not None:
            if len( y ):
                if isinstance( y, numpy.ndarray ):
                    if y.shape == ( len( y ), 1 ):
                        y.shape = [len( y ), ]
                if x is None:
                    x = numpy.arange( len( y ) )
                if logfilter:
                    i1 = numpy.nonzero( y > 0.0 )[0]
                    x = numpy.take( x, i1 )
                    y = numpy.take( y, i1 )
            if len( y ):
                ymin = min( y )
            else:
                self.delcurve( key )
                return
                #if len(self.curves.keys()) != 1:
                #    self.delcurve(key)
                #    return
            self.setCurveData( self.curves[key]['curve'], x, y )
            if 'baseline' in kw:
                if logfilter:
                    ybase = numpy.take( kw['baseline'], i1 )
                    i1 = numpy.nonzero( ybase <= 0 )[0]
                    for i in i1:
                        ybase[i] = ymin
                else:
                    ybase = kw['baseline']
                self.curves[key]['curve'].setbaseline( ybase )
            if 'regions' in kw:
                regions = []
                for region in kw['regions']:
                    region0 = min( region[0], region[1] )
                    region1 = max( region[0], region[1] )
                    i1 = numpy.min( numpy.nonzero( x >= region0 )[0], 0 )
                    i2 = numpy.max( numpy.ravel( numpy.nonzero( x <= region1 )[0] ) )
                    regions.append( [int( i1 ), int( i2 )] )
                self.curves[key]['curve'].setregions( regions )
            if maptoy2:
                self.mapToY2( key )
            if len( self.curves.keys() ) == 1:
                #set the active curve
                #self.legendclicked(1)
                curves_keys = []
                for tmpKey in self.curves.keys():
                    curves_keys.append( tmpKey )
                self.setactivecurve( curves_keys[0] )
        else:
            self.delcurve( key )

    def setxofy( self, legend ):
        if legend in self.curves.keys():
            self.setCurveOptions( self.curves[legend]['curve'], Qwt5.QwtPlotCurve.Xfy )

    def clearCurve( self, key ):
        return self.delcurve( key )

    def delcurve( self, key ):
        index = None
        if key in self.curves.keys():
            del_index = self.curves[key]['curve']
            del self.curves[key]
        if key in self.curveslist:
            index = self.curveslist.index( key )
            del self.curveslist[index]
        if index is not None:
            try:
                del_index.detach()
            except:
                print( "del_index = ", del_index, "error" )
        if not len( self.curves.keys() ):
            self.clearcurves()
            dict = {}
            dict['event' ] = "SetActiveCurveEvent"
            dict['legend'] = None
            dict['index' ] = -1
            self.emit( qt.SIGNAL( 'QtBlissGraphSignal' ), ( dict ) )
        elif self.__activecurves is not None:
            if key in self.__activecurves:
                del self.__activecurves[self.__activecurves.index( key )]
                if self.__activecurves == []:
                    dict = {}
                    dict['event' ] = "SetActiveCurveEvent"
                    dict['legend'] = None
                    dict['index' ] = -1

                    self.emit( qt.SIGNAL( 'QtBlissGraphSignal' ), ( dict ) )

    def clearcurves( self ):
        if DEBUG:
            print( "Deprecation: Please use clearCurves instead" )
        return self.clearCurves()

    def clearCurves( self ):
        for key in list( self.curves.keys() ):
            self.delcurve( key )
        self.__activecurves = []
        #color counter
        self.color = 0
        #symbol counter
        self.symbol = 0
        #line type
        self.linetype = 0
        #TODO: this code is useless
        if 0:
            self.removeMarkers() #necessary because clear() will get rid of them
            self.clear()         #this deletes also plot items in Qwt5!
        else:                    #try to remove just the curves
            self.replot()

    def hideGrid( self ):
        self.removeGrid()

    def removeGrid( self ):
        if self.grid is not None:
            self.grid.detach()

    def showGrid( self ):
        if self.grid is None:
            self.grid = Qwt5.QwtPlotGrid()
            self.grid.enableYMin( False )
            self.grid.setMajPen( qt.QPen( qt.Qt.black,
                                0,
                                self.linetypes['dot'] ) )
            self.grid.setMinPen( qt.QPen( qt.Qt.gray,
                                0,
                                self.linetypes['dot'] ) )
        self.grid.attach( self )

    def removeCurves( self ):
        for key in self.curves.keys():
            self.delcurve( key )

    def removeMarkers( self ):
        keylist = list( self.markersdict.keys() )
        for key in keylist:
            try:
                self.markersdict[key]['marker'].detach()
            except:
                if DEBUG:print( "It had been already destroyed" )
            del self.markersdict[key]

    def closestMarker( self, xpixel, ypixel ):
        x = self.invTransform( Qwt5.QwtPlot.xBottom, xpixel )
        y = self.invTransform( Qwt5.QwtPlot.yLeft, ypixel )
        ( marker, distance ) = ( None, None )
        xmarker = True
        for key in list( self.markersdict.keys() ):
            if marker is None:
                marker = key
                if self.markersdict[key]['marker'].lineStyle() == Qwt5.QwtPlotMarker.HLine:
                    #ymarker
                    distance = abs( y - self.markersdict[key]['marker'].yValue() )
                    xmarker = False
                else:
                    #xmarker
                    distance = abs( x - self.markersdict[key]['marker'].xValue() )
                    xmarker = True
            else:
                if self.markersdict[key]['marker'].lineStyle() == Qwt5.QwtPlotMarker.HLine:
                    #ymarker
                    distancew = abs( y - self.markersdict[key]['marker'].yValue() )
                    xmarker = False
                else:
                    #xmarker
                    distancew = abs( x - self.markersdict[key]['marker'].xValue() )
                    xmarker = True
                if distancew < distance:
                    distance = distancew
                    marker = key
        #this distance is in x coordenates
        #but I decide on distance in pixels ...
        if distance is not None:
            if xmarker:
                x1pixel = abs( self.invTransform( Qwt5.QwtPlot.xBottom, xpixel + 4 ) - x ) / 4.0
                distance = distance / x1pixel
            else:
                y1pixel = abs( self.invTransform( Qwt5.QwtPlot.xBottom, ypixel + 4 ) - y ) / 4.0
                distance = distance / y1pixel
        return ( marker, distance )

    def toggleCurve( self, keyorindex ):
        if type( keyorindex ) in [type( unicode( " " ) ), type( " " ), type( str( " " ) )]:
            if keyorindex in self.curveslist:
                index = self.curveslist.index( keyorindex ) + 1
                key = keyorindex
            else:
                return -1
        elif keyorindex > 0:
            index = keyorindex
            key = self.curveslist[index - 1]
        else:
            return -1
        if key in self.__activecurves:
            del self.__activecurves[self.__activecurves.index( key )]
            color = self.curves[key] ["pen"]
            linetype = self.curves[key] ["linetype"]
            pen = qt.QPen( color, self.linewidth, linetype )
            self.setCurvePen( self.curves[key]['curve'], pen )
        else:
            linetype = self.curves[key] ["linetype"]
            pen = qt.QPen( self.__activecolor, self.__activelinewidth, linetype )
            self.setCurvePen( self.curves[key]['curve'], pen )
            self.__activecurves.append( key )
        #plot just that curve?
        self.drawCurve( index, 0, -1 )

    def getactivecurve( self, justlegend = 0 ):
        if DEBUG: print( "Deprecation warning: QtBlissGraph getactivecurve" )
        return self.getActiveCurve( justlegend )


    def getActiveCurve( self, justlegend = 0 ):
        #check the number of curves
        curves_keys = list( self.curves.keys() )
        if len( curves_keys ) > 1:
            if not len( self.__activecurves ):
                if justlegend:return None
                else:return None, None, None
            else:
                legend = self.__activecurves[0]
        elif  len( curves_keys ) == 1:
            legend = curves_keys[0]
        else:
            if justlegend:return None
            else: return None, None, None
        if legend in curves_keys:
            if justlegend:
                return legend
            index = self.curves[legend]['curve']
            x = []
            y = []
            print( "QtBlissGraph: get curve data to be implemented" )
            return legend, numpy.array( x ).astype( numpy.float ), numpy.array( y ).astype( numpy.float )
        else:
            return None, None, None

    def getcurveinfo( self, legend ):
        if legend is None:
            return {}
        ddict = {}
        if legend in self.curves.keys():
            ddict = copy.deepcopy( self.curves[legend]['curveinfo'].copy() )
        return ddict

    def setactivecurve( self, keyorindex ):
        if DEBUG: print( "Deprecation warning: QtBlissGraph setactivecurve" )
        return self.setActiveCurve( keyorindex )

    def setActiveCurve( self, keyorindex ):
        if keyorindex is None:
            return -1
        try:
            tmp_int = int(keyorindex)
        except :
            keyorindex = str(keyorindex)
        else:
            keyorindex = tmp_int
            
        if type( keyorindex ) in [type( unicode( " " ) ), type( " " ), type( str( " " ) )]:
            if keyorindex in self.curves.keys():
                #index = self.curveslist.index(keyorindex) + 1
                index = self.curves[keyorindex]['curve']
                key = keyorindex
            else:
                return -1
        elif keyorindex > 0:
            index = keyorindex
            key = self.curveslist[index - 1]
        else:
            return -1
        for ckey in  self.__activecurves:
            del self.__activecurves[self.__activecurves.index( ckey )]
            if ckey in self.curves.keys():
                color = self.curves[ckey] ["pen"]
                linetype = self.curves[ckey] ["linetype"]
                pen = qt.QPen( color, self.linewidth, linetype )
                if ( self.curves[ckey]['curve'].pen().style() != qt.Qt.NoPen ):
                    self.setCurvePen( self.curves[ckey]['curve'], pen )
        linetype = self.curves[key] ["linetype"]
        pen = qt.QPen( self.__activecolor, self.__activelinewidth, linetype )
        if ( self.curves[key]['curve'].pen().style() != qt.Qt.NoPen ):
            self.setCurvePen( self.curves[key]['curve'], pen )
        self.__activecurves.append( key )

        n = self.legend().itemCount()
        if n > 1:
            if 0:
                for i in range( n ):
                        item = self.legend().findItem( i + 1 )
                        #TODO: DEBUG - next line is not right - No ClickFocus
#                       item.setFocusPolicy(qt.QWidget.ClickFocus)
            else:
                for curve in self.curves.keys():
                    if DEBUG:
                        print( "findItem also missing" )

        self.replot()
        dict = {}
        dict['event' ] = "SetActiveCurveEvent"
        dict['legend'] = key
        dict['index' ] = index

        self.emit( qt.SIGNAL( 'QtBlissGraphSignal' ), ( dict ) )
        return 0

    def setmarkercolor( self, marker, color, label = None ):
        if marker not in self.markersdict.keys():
            print( "ERROR, returning" )
            return -1
        if color in self.colors.keys():
            pen = self.colors[color]
        else:
            pen = self.colors[self.colorslist[0]]
        self.markersdict[marker]['marker'].setLinePen( qt.QPen( pen, 0, qt.Qt.SolidLine ) )
        if label is not None:
            self.markersdict[marker]['marker'].setLabel( Qwt5.QwtText( label ) )

        return 0

    def curveinit( self, key, symbol = None, line = None, **kw ):
        self.curves[key] = {}
        #self.curves[key] =  self.insertCurve(key)
        if len( kw.keys() ):
            curve = BlissCurve( key, **kw )
            curve.attach( self )
            self.curves[key] ["curve"] = curve
            blissCurve = True
        else:
            curve = self.insertCurve( key )
            blissCurve = False
            self.curves[key] ["curve"] = curve
        self.curves[key] ["name"] = QString( qt.safe_str( key ) )
        self.curveslist.append( key )
        self.curves[key] ["symbol"] = self.getnewsymbol()
        if symbol is not None:
            if symbol in self.symbols.keys():
                self.curves[key] ["symbol"] = self.symbols[symbol]
            elif symbol == 'o':
                self.curves[key] ["symbol"] = self.symbols['ellipse']
            elif symbol == 'x':
                self.curves[key] ["symbol"] = self.symbols['xcross']
            elif symbol == '+':
                self.curves[key] ["symbol"] = self.symbols['cross']
        elif self.__defaultPlotPoints:
            self.curves[key] ["symbol"] = self.symbols['ellipse']

        self.curves[key] ["maptoy2"] = 0
        color = self.colors[self.colorslist[self.color]]
        linetype = self.linetypes[self.linetypeslist[self.linetype]]
        self.linetypeslist = ['solid', 'dot', 'dash', 'dashdot', 'dashdotdot']

        if line is not None:
            if line in self.linetypes.keys():
                linetype = self.linetypes[line]
            elif line == '-':
                linetype = self.linetypes['solid']
            elif line == '.':
                linetype = self.linetypes['dot']
            elif line == '--':
                linetype = self.linetypes['dash']
            elif line == '-.':
                linetype = self.linetypes['dashdot']
            elif line == '-..':
                linetype = self.linetypes['dashdotdot']

        self.curves[key] ["pen"] = color
        pen = qt.QPen( color, self.linewidth, linetype )
        self.curves[key] ["linetype"] = linetype
        self.curves[key] ["curveinfo"] = {}
        self.getnewpen()
        self.setCurvePen( self.curves[key]['curve'], pen )

        if symbol is not None:
            self.togglePoints( key )

        if blissCurve:
            return

        if line is None:
            if self.__defaultPlotLines:
                curve.setStyle( Qwt5.QwtPlotCurve.Lines )
            else:
                curve.setStyle( Qwt5.QwtPlotCurve.NoCurve )


    def insertCurve( self, key ):
        curve = MyQwt5PlotCurve( key )
        curve.attach( self )
        return curve

    def setCurvePen( self, curve, pen ):
        symbol = curve.symbol()
        symbol.setPen( pen )
        brush = symbol.brush()
        brush.setColor( pen.color() )
        curve.symbol().setBrush( brush )
        curve.setPen( pen )

    def setCurveData( self, curve, x, y ):
        curve.setData( x, y )

    def insertLineMarker( self, key, position ):
        m = Qwt5.QwtPlotMarker()
        m.setLabel( Qwt5.QwtText( key ) )
        try:
            m.setLabelAlignment( position )
        except:
            #print "marker label error"
            m.setLabelAlignment( qt.Qt.AlignLeft | qt.Qt.AlignTop )
        m.attach( self )
        return m

    def setMarkerYPos( self, m, value ):
        if m in self.markersdict.keys():
            m = self.markersdict[m]['marker']
        return m.setYValue( value )

    def setMarkerXPos( self, m, value ):
        if m in self.markersdict.keys():
            m = self.markersdict[m]['marker']
        return m.setXValue( value )

    def getnewpen( self ):
        self.color = self.color + 1
        if self.color > ( len( self.colorslist ) - 1 ):
            self.color = 0
            self.linetype += 1
            if self.linetype > ( len( self.linetypeslist ) - 1 ):
                self.linetype = 0
        return

    def getnewstyle( self ):
        return self.linetype

    def getnewsymbol( self ):
        return

    def getcurveaxes( self, key ):
        if type( key ) == type( " " ):
            if key in self.curveslist:
                index = self.curveslist.index( key ) + 1
            else:
                return -1, -1
        elif key > 0:
            index = key
        else:
            return -1, -1
        x = self.curveXAxis( index )
        y = self.curveXAxis( index )
        return x, y

    def getX1AxisLimits( self ):
        #get the current limits
        xmin = self.canvasMap( Qwt5.QwtPlot.xBottom ).s1()
        xmax = self.canvasMap( Qwt5.QwtPlot.xBottom ).s2()
        return xmin, xmax

    def getx1axislimits( self ):
        if DEBUG:
            print( "getx1axislimits deprecated, use getX1AxisLimits instead" )
        return self.getX1AxisLimits()

    def getY1AxisLimits( self ):
        #get the current limits
        ymin = self.canvasMap( Qwt5.QwtPlot.yLeft ).s1()
        ymax = self.canvasMap( Qwt5.QwtPlot.yLeft ).s2()
        return ymin, ymax

    def getY2AxisLimits( self ):
        if not self.axisEnabled( Qwt5.QwtPlot.yRight ):
            return self.getY1AxisLimits()
        #get the current limits
        ymin = self.canvasMap( Qwt5.QwtPlot.yRight ).s1()
        ymax = self.canvasMap( Qwt5.QwtPlot.yRight ).s2()
        return ymin, ymax

    def gety1axislimits( self ):
        if DEBUG:
            print( "gety1axislimits deprecated, use getY1AxisLimits instead" )
        return self.getY1AxisLimits()

    def setX1AxisInverted( self, flag ):
        self.axisScaleEngine( Qwt5.QwtPlot.xBottom ).setAttribute( Qwt5.QwtScaleEngine.Inverted,
                                                               flag )

    def setY1AxisInverted( self, flag ):
        self.axisScaleEngine( Qwt5.QwtPlot.yLeft ).setAttribute( Qwt5.QwtScaleEngine.Inverted,
                                                             flag )

    def isX1AxisInverted( self ):
        return self.axisScaleEngine( Qwt5.QwtPlot.xBottom ).    \
                                   testAttribute( Qwt5.QwtScaleEngine.Inverted )

    def isY1AxisInverted( self ):
        return self.axisScaleEngine( Qwt5.QwtPlot.yLeft ).    \
                                   testAttribute( Qwt5.QwtScaleEngine.Inverted )

    def isY2AxisInverted( self ):
        return self.axisScaleEngine( Qwt5.QwtPlot.yRight ).    \
                                   testAttribute( Qwt5.QwtScaleEngine.Inverted )

    def setY2AxisInverted( self, flag ):
        self.axisScaleEngine( Qwt5.QwtPlot.yRight ).setAttribute( Qwt5.QwtScaleEngine.Inverted,
                                                              flag )

    def setx1axislimits( self, *var, **kw ):
        if DEBUG:
            print( "setx1axislimits deprecated, use setX1AxisLimits instead" )
        return self.setX1AxisLimits( *var, **kw )

    def setX1AxisLimits( self, xmin, xmax, replot = None ):
        if replot is None: replot = True
        if self.__logx1:
            if xmin <= 0:
                xmin = 1
            if xmax <= 0:
                xmax = xmin + 1
        self.setAxisScale( Qwt5.QwtPlot.xBottom, xmin, xmax )
        if replot:self.replot()

    def sety1axislimits( self, *var, **kw ):
        if DEBUG:
            print( "sety1axislimits deprecated, use setY1AxisLimits instead" )
        return self.setY1AxisLimits( *var, **kw )

    def setY1AxisLimits( self, ymin, ymax, replot = None ):
        if replot is None: replot = True
        if self.__logy1:
            if ymin <= 0:
                ymin = 1
            #else:
            #    ymin = log(ymin)
            if ymax <= 0:
                ymax = ymin + 1
            #else:
            #    ymax = log(ymax)
        self.setAxisScale( Qwt5.QwtPlot.yLeft, ymin, ymax )
        if replot:self.replot()

    def sety2axislimits( self, *var ):
        if DEBUG:print( "Deprecation warning: use setY2AxisLimits instead" )
        return self.setY2AxisLimits( *var )

    def setY2AxisLimits( self, ymin, ymax, replot = None ):
        if not self.axisEnabled( Qwt5.QwtPlot.yRight ): return
        if replot is None: replot = True
        if self.__logy2:
            if ymin <= 0:
                ymin = 1
            #else:
            #    ymin = log(ymin)
            if ymax <= 0:
                ymax = ymin + 1
            #else:
            #    ymax = log(ymax)
        self.setAxisScale( Qwt5.QwtPlot.yRight, ymin, ymax )
        if replot:self.replot()

    def insertx1marker( self, *var, **kw ):
        if DEBUG:print( "insertx1marker deprecated, use insertX1Marker" )
        return self.insertX1Marker( *var, **kw )

    def inserty1marker( self, *var, **kw ):
        if DEBUG:print( "inserty1marker deprecated, use insertY1Marker" )
        return self.insertY1Marker( *var, **kw )

    def insertX1Marker( self, *var, **kw ):
        if len( var ) < 1:
            return -1
        elif len( var ) == 1:
            x = var[0]
            y = None
        else:
            x = var[0]
            y = var[1]
        if 'label' in kw:
            label = kw['label']
        else:
            label = ""
        if 'noline' in kw:
            noline = kw['noline']
        else:
            noline = False

        mX = Qwt5.QwtPlotMarker()
        mX.setLabel( Qwt5.QwtText( label ) )
        mX.setLabelAlignment( qt.Qt.AlignRight | qt.Qt.AlignTop )
        if not noline:
            mX.setLineStyle( Qwt5.QwtPlotMarker.VLine )
        marker = id( mX )

        if marker == 0:
            print( "Error inserting marker!!!!" )
            return -1
        if y is None:
            mX.setXValue( x )
        else:
            mX.setXValue( x )
            mX.setYValue( y )
        if marker in self.markersdict.keys():
            self.markersdict[marker]['marker'] = mX
        else:
            self.markersdict[marker] = {}
            self.markersdict[marker]['marker'] = mX
            self.markersdict[marker]['followmouse'] = 0
        self.markersdict[marker]['xmarker'] = True
        mX.attach( self )
        return marker

    def insertY1Marker( self, *var, **kw ):
        if len( var ) < 1:
            return -1
        elif len( var ) == 1:
            y = var[0]
            x = None
        else:
            x = var[0]
            y = var[1]
        if 'label' in kw:
            label = kw['label']
        else:
            label = ""

        mX = Qwt5.QwtPlotMarker()
        mX.setLabel( Qwt5.QwtText( label ) )
        mX.setLabelAlignment( qt.Qt.AlignRight | qt.Qt.AlignTop )
        mX.setLineStyle( Qwt5.QwtPlotMarker.HLine )
        marker = id( mX )

        if marker == 0:
            print( "Error inserting marker!!!!" )
            return -1
        if x is None:
            mX.setYValue( y )
        else:
            mX.setXValue( x )
            mX.setYValue( y )
        if marker in self.markersdict.keys():
            self.markersdict[marker]['marker'] = mX
        else:
            self.markersdict[marker] = {}
            self.markersdict[marker]['marker'] = mX
            self.markersdict[marker]['followmouse'] = 0
        self.markersdict[marker]['xmarker'] = False
        mX.attach( self )
        return marker

    def setx1markerpos( self, marker, x, y = None ):
        if marker in self.markersdict.keys():
            marker = self.markersdict[marker]['marker']

        if y is None:
            self.setMarkerXPos( marker, x )
        else:
            self.setMarkerPos( marker, x, y )

    def clearmarkers( self ):
        if DEBUG:print( "Deprecation warning: use clearMarkers instead" )
        return self.clearMarkers()

    def clearMarkers( self ):
        self.removeMarkers()
        self.markersdict = {}

    def removeMarker( self, marker ):
        if marker in self.markersdict.keys():
            self.markersdict[marker]['marker'].detach()
            del self.markersdict[marker]
        else:
            for m in self.markersdict.keys():
                if id( self.markersdict[m] ) == id( marker ):
                    marker.detach()
                    del self.markersdict[m]
                    break

    def removemarker( self, marker ):
        print( "Deprecation warning: use removeMarker instead" )
        return self.removeMarker( marker )


    def printps( self ):
        printer = qt.QPrinter()
        printDialog = qt.QPrintDialog( printer, self )
        if printDialog.exec_():
            try:
                painter = qt.QPainter()
                if not( painter.begin( printer ) ):
                    return 0
                dpiy = printer.logicalDpiY()
                margin = int( ( 2 / 2.54 ) * dpiy ) #2cm margin
                body = qt.QRect( 0.5 * margin,
                                margin,
                                printer.width() - 1 * margin,
                                printer.height() - 2 * margin )
                fil = Qwt5.QwtPlotPrintFilter()
                fil.setOptions( fil.PrintAll )
                fil.apply( self )
                self.print_( painter, body )
            finally:
                painter.end()

class Qwt5PlotImage( Qwt5.QwtPlotItem ):
    def __init__( self, parent, palette = None ):
        Qwt5.QwtPlotItem.__init__( self )
        self.xyzs = None
        self.attach( parent )
        self.image = None
        if not USE_SPS_LUT:
            if palette is None:
                self.palette = fuzzypalette()
            else:
                self.palette = palette

    def draw( self, painter, xMap, yMap, lgx1 = 0, lgy1 = 0 ):
        """Paint image to zooming to xMap, yMap

        Calculate (x1, y1, x2, y2) so that it contains at least 1 pixel,
        and copy the visible region to scale it to the canvas.
        """
        # calculate y1, y2
        if self.image is None:
            return
        if lgy1:
            if yMap.s1() <= 1:
                yMaps1 = 0.0
            else:
                yMaps1 = pow( 10., yMap.s1() )
            yMaps2 = pow( 10., yMap.s2() )
        else:
            yMaps2 = yMap.s2()
            yMaps1 = yMap.s1()
        if DEBUG:
            print( "working drawImage xMap,yMap", \
                        xMap.s1(), xMap.s2(), yMaps1, yMaps2 )

        y1 = y2 = self.image.height()
        y1 *= ( self.yMap.s2() - yMaps2 )
        y1 /= ( self.yMap.s2() - self.yMap.s1() )
        y1 = max( 0, int( y1 ) )
        y2 *= ( self.yMap.s2() - yMaps1 )
        y2 /= ( self.yMap.s2() - self.yMap.s1() )
        y2 = min( self.image.height(), int( y2 + 0.5 ) )
        # calculate x1, x1
        x1 = x2 = self.image.width()
        #x1 *= (self.xMap.d2() - xMap.d2())
        x1 *= ( xMap.s1() - self.xMap.s1() )
        x1 /= ( self.xMap.s2() - self.xMap.s1() )
        x1 = max( 0, int( x1 ) )
        x2 *= ( xMap.s2() - self.xMap.s1() )
        x2 /= ( self.xMap.s2() - self.xMap.s1() )
        x2 = min( self.image.width(), int( x2 + 0.5 ) )
        # copy
        image = self.image.copy( x1, y1, x2 - x1, y2 - y1 )
        # zoom
        image = image.scaled( xMap.p2() - xMap.p1() + 1, yMap.p1() - yMap.p2() + 1 )
        # draw
        painter.drawImage( xMap.p1(), yMap.p2(), image )

    def setData( self, xyzs, xScale = None, yScale = None, colormap = None,
                xmirror = 0, ymirror = 1 ):
        self.xyzs = xyzs
        shape = xyzs.shape
        if colormap is not None:
            if len( colormap ) < 7:
                colormap.append( spslut.LINEAR )
        if xScale is None:
            xRange = ( 0, shape[1] )
        else:
            xRange = xScale * 1

        if yScale is None:
            yRange = ( 0, shape[0] )
        else:
            yRange = yScale * 1

        if self.plot().isX1AxisInverted():
            self.xMap = Qwt5.QwtScaleMap( 0, shape[0], xRange[1], xRange[0] )
            self.plot().setAxisScale( Qwt5.QwtPlot.xBottom, xRange[1], xRange[0] )
        else:
            self.xMap = Qwt5.QwtScaleMap( 0, shape[0], xRange[0], xRange[1] )
            self.plot().setAxisScale( Qwt5.QwtPlot.xBottom, xRange[0], xRange[1] )

        if self.plot().isY1AxisInverted():
            self.yMap = Qwt5.QwtScaleMap( 0, shape[1], yRange[1], yRange[0] )
            self.plot().setAxisScale( Qwt5.QwtPlot.yLeft, yRange[1], yRange[0] )
        else:
            self.yMap = Qwt5.QwtScaleMap( 0, shape[1], yRange[0], yRange[1] )
            self.plot().setAxisScale( Qwt5.QwtPlot.yLeft, yRange[0], yRange[1] )

        if not USE_SPS_LUT:
            #calculated palette
            self.image = Qwt5.toQImage( bytescale( self.xyzs ) ).mirrored( xmirror, ymirror )
            for i in range( 0, 256 ):
                self.image.setColor( i, self.palette[i] )

        else:
            if colormap is None:
                ( image_buffer, size, minmax ) = spslut.transform( self.xyzs, ( 1, 0 ),
                                         ( spslut.LINEAR, 3.0 ), "BGRX", spslut.TEMP,
                                          1, ( min( numpy.ravel( self.xyzs ) ), max( numpy.ravel( self.xyzs ) ) ) )
            else:
                ( image_buffer, size, minmax ) = spslut.transform( self.xyzs, ( 1, 0 ),
                                         ( colormap[6], 3.0 ),
                                         "BGRX", COLORMAPLIST[int( qt.safe_str( colormap[0] ) )],
                                          colormap[1], ( colormap[2], colormap[3] ) )

            self.image = qt.QImage( image_buffer, size[0], size[1],
                                       qt.QImage.Format_RGB32 ).mirrored( xmirror,
                                                                        ymirror )
            self.image_buffer = image_buffer

    def setPixmap( self, pixmap, size = None, xScale = None, yScale = None,
                  xmirror = 0, ymirror = 1 ):
        #I have to receive an array
        selectedTypes = [type( "" )]
        if sys.version > '2.6':
            selectedTypes.append( type( eval( 'b""' ) ) )
        if type( pixmap ) in selectedTypes:
            shape = size
        else:
            shape = size
       #     shape = pixmap.shape
       #     if len(shape) == 1:
       #         shape = (shape[0], 1)
        if xScale is None:
            xRange = ( 0, shape[0] )
        else:
            xRange = xScale * 1

        if yScale is None:
            yRange = ( 0, shape[1] )
        else:
            yRange = yScale * 1

        if self.plot().isX1AxisInverted():
            self.xMap = Qwt5.QwtScaleMap( 0, shape[0], xRange[1], xRange[0] )
            self.plot().setAxisScale( Qwt5.QwtPlot.xBottom, xRange[1], xRange[0] )
        else:
            self.xMap = Qwt5.QwtScaleMap( 0, shape[0], xRange[0], xRange[1] )
            self.plot().setAxisScale( Qwt5.QwtPlot.xBottom, xRange[0], xRange[1] )

        if self.plot().isY1AxisInverted():
            self.yMap = Qwt5.QwtScaleMap( 0, shape[1], yRange[1], yRange[0] )
            self.plot().setAxisScale( Qwt5.QwtPlot.yLeft, yRange[1], yRange[0] )
        else:
            self.yMap = Qwt5.QwtScaleMap( 0, shape[1], yRange[0], yRange[1] )
            self.plot().setAxisScale( Qwt5.QwtPlot.yLeft, yRange[0], yRange[1] )


        if type( pixmap ) in selectedTypes:
            self.image = qt.QImage( pixmap,
                               size[0],
                               size[1],
                               qt.QImage.Format_RGB32 ).mirrored( xmirror,
                                                                ymirror )
        else:
            self.image = qt.QImage( pixmap.tostring(),
                               size[0],
                               size[1],
                               qt.QImage.Format_RGB32 ).mirrored( xmirror,
                                                                ymirror )
        self.image_buffer = pixmap


class MyPicker( Qwt5.QwtPicker ):
    def __init__( self, parent ):
        self._keyPressed = None
        self.__mouseToBeMoved = True
        Qwt5.QwtPicker.__init__( self, parent )

    def widgetMousePressEvent( self, event ):
        if DEBUG:
            print ( "mouse press" )

        self.emit( qt.SIGNAL( "MousePressed(const QMouseEvent&)" ), event )
        Qwt5.QwtPicker.widgetMousePressEvent( self, event )

    def widgetMouseReleaseEvent( self, event ):
        if DEBUG:
            print ( "mouse release" )
        self.emit( qt.SIGNAL( "MouseReleased(const QMouseEvent&)" ), event )
        Qwt5.QwtPicker.widgetMouseReleaseEvent( self, event )

    def widgetMouseDoubleClickEvent( self, event ):
        if DEBUG:
            print ( "mouse doubleclick" )

        self.emit( qt.SIGNAL( "MouseDoubleClicked(const QMouseEvent&)" ), event )
        Qwt5.QwtPicker.widgetMouseDoubleClickEvent( self, event )

    def widgetMouseMoveEvent( self, event ):
        if DEBUG:
            print ( "mouse move" )
        self.__mouseToBeMoved = False

        self.emit( qt.SIGNAL( "MouseMoved(const QMouseEvent&)" ), event )
        Qwt5.QwtPicker.widgetMouseMoveEvent( self, event )

    def widgetKeyPressEvent( self, event ):
        if DEBUG:
            print ( "Key Pressed" )
        self._keyPressed = event.key()
        if self._keyPressed in [qt.Qt.Key_Left,
                                qt.Qt.Key_Right,
                                qt.Qt.Key_Up,
                                qt.Qt.Key_Down]:
            self.__mouseToBeMoved = True
        Qwt5.QwtPicker.widgetKeyPressEvent( self, event )

    def widgetKeyReleaseEvent( self, event ):
        if DEBUG:
            print ( "Key Released" )

        if self.__mouseToBeMoved:
            if self._keyPressed in [qt.Qt.Key_Left,
                                    qt.Qt.Key_Right,
                                    qt.Qt.Key_Up,
                                    qt.Qt.Key_Down]:
                ddict = {}
                ddict['event'] = 'PanningSignal'
                if self._keyPressed == qt.Qt.Key_Left:
                    ddict['direction'] = 'left'
                elif self._keyPressed == qt.Qt.Key_Right:
                    ddict['direction'] = 'right'
                elif self._keyPressed == qt.Qt.Key_Up:
                    ddict['direction'] = 'up'
                elif self._keyPressed == qt.Qt.Key_Down:
                    ddict['direction'] = 'down'

                self.emit( qt.SIGNAL( "PanningSignal" ), ddict )
        self._keyPressed = None
        self.__mouseToBeMoved = False
        Qwt5.QwtPicker.widgetKeyReleaseEvent( self, event )

class MyQwt5PlotCurve( Qwt5.QwtPlotCurve ):
    def __init__( self, key ):
        Qwt5.QwtPlotCurve.__init__( self, key )

    #These two methods to be overloaded to use ANY widget as legend item.
    #Default implementation is a Qwt5LegendItem
    def legendItem( self ):
        if DEBUG:print( "in legend item" )
        #return Qwt5.QwtPlotCurve.legendItem(self)
        return MyQwt5LegendItem( self.plot().legend() )

    def updateLegend( self, legend ):
        if DEBUG:print( "in update legend!" )
        return Qwt5.QwtPlotCurve.updateLegend( self, legend )

class MyQwt5LegendItem( Qwt5.QwtLegendItem ):
    def __init__( self, *var ):
        Qwt5.QwtLegendItem.__init__( self, *var )
        self.legendMenu = None

    def mousePressEvent( self, event ):
        if DEBUG:print( "MyQwt5LegendItem mouse pressed" )
        if event.button() == qt.Qt.LeftButton:
            text = "leftMousePressed"
        elif event.button() == qt.Qt.RightButton:
            text = "rightMousePressed"
        else:
            text = "centralMousePressed"
        self.__emitSignal( text )

    def mouseReleaseEvent( self, event ):
        if DEBUG:print( "MyQwt5LegendItem mouse released" )
        if event.button() == qt.Qt.LeftButton:
            text = "leftMouseReleased"
        elif event.button() == qt.Qt.RightButton:
            text = "rightMouseReleased"
        else:
            text = "centralMouseReleased"
        self.__emitSignal( text )

    def __emitSignal( self, eventText ):
        ddict = {}
        ddict['legend'] = qt.safe_str( self.text().text() )
        ddict['event'] = eventText

        self.emit( qt.SIGNAL( "MyQwt5LegendItemSignal" ), ddict )


class BlissCurve( MyQwt5PlotCurve ):
    def __init__( self, name = "", regions = [[0, -1]], baseline = [] ):
        MyQwt5PlotCurve.__init__( self, name )
        self.regions = regions
        self.setStyle( Qwt5.QwtPlotCurve.Sticks )
        self.baselinedata = baseline
        #self.setOptions(Qwt5.QwtPlotCurve.Xfy)

    def drawFromTo( self, painter, xMap, yMap, a, b ):
        for region in self.regions:
            if len( self.baselinedata ):
                for i in range( int( region[0] ), int( region[1] ) ):
                    #get the point
                    self.setBaseline( self.baselinedata[i] )
                    MyQwt5PlotCurve.drawFromTo( self, painter, xMap, yMap, i, i )
            else:
                MyQwt5PlotCurve.drawFromTo( self, painter, xMap, yMap, region[0], region[1] )

    def setregions( self, regions ):
        self.regions = regions

    def setbaseline( self, baseline ):
        self.baselinedata = baseline

class TimeScaleDraw( Qwt5.QwtScaleDraw ):
    def label( self, value ):
        if int( value ) - value == 0:
            value = abs( int( value ) )
            h = value / 3600
            m = ( value % 3600 ) / 60
            s = value - 3600 * h - 60 * m

            if h == 0 and m == 0:
                r = '%ds' % s
                return Qwt5.QwtText( r )
            else:
                if h == 0:
                    r = '%dm%02ds' % ( m, s )
                    return Qwt5.QwtText( r )
                else:
                    r = '%dh%02dm%02ds' % ( h, m, s )
                    return Qwt5.QwtText( r )
        else:
            return Qwt5.QwtText( '' )


def make0():
    demo = QtBlissGraphContainer( uselegendmenu = 1 )
    demo.resize( 500, 300 )
    # set axis titles
    demo.graph.setAxisTitle( Qwt5.QwtPlot.xBottom, 'x -->' )
    demo.graph.setAxisTitle( Qwt5.QwtPlot.yLeft, 'y -->' )
    demo.graph.uselegendmenu = 1
    # insert a few curves
    cSin = {}
    cCos = {}
    nplots = 10
    for i in range( nplots ):
        # calculate 3 NumPy arrays
        x = numpy.arange( 0.0, 10.0, 0.1 )
        y = 10 * numpy.sin( x + ( i / 10.0 ) * 3.14 )
        z = numpy.cos( x + ( i / 10.0 ) * 3.14 )
        #build a key
        a = "%d" % i
        #plot the data
        cSin[a] = demo.graph.newcurve( 'y = sin(x)' + a, x = x, y = y )
        cCos[a] = demo.graph.newcurve( 'y = cos(x)' + a, x = x, y = z )
    # insert a horizontal marker at y = 0
    mY = demo.graph.inserty1marker( 0.0, 0.0, 'y = 0' )
    demo.graph.setmarkerfollowmouse( mY, True )
    # insert a vertical marker at x = 2 pi
    mX = demo.graph.insertx1marker( 2 * numpy.pi, 0.0, label = 'x = 2 pi' )
    demo.graph.setmarkerfollowmouse( mX, True )
    demo.graph.enablemarkermode()
    demo.graph.canvas().setMouseTracking( True )
    # replot
    #print dir(demo.graph)
    #print dir(demo.graph.curve)
    #print dir(demo.graph.curve(demo.graph.curves['y = sin(x)0']['curve']))
    #print dir(demo.graph.legend())

    #print demo.graph.curve(cSin[a]).dataSize()
    #first = 0
    #last  = 0
    #length,first,last = demo.graph.curve(cSin[a]).verifyRange(first,last)
    #print length,first,last

    #how to retrieve the data
    #print demo.graph.curve(cSin[a]).x
    if 0:
        for i in range( demo.graph.curve( 1 ).dataSize() ):
            print( demo.graph.curve( 1 ).x( i ) )

    demo.graph.replot()
    idata = numpy.arange( 10000. )
    idata.shape = [100, 100]
    demo.graph.imagePlot( idata )
    demo.graph.replot()
    demo.graph.setactivecurve( 'y = sin(x)3' )
    print( demo.graph.getactivecurve() )

    #demo.graph.show()
    demo.show()
    return demo


def main( args ):
    app = qt.QApplication( args )

    demo = make0()
    demo.resize( 500, 300 )
    # set axis titles
    def myslot( ddict ):
        if ddict['event'] == "RemoveCurveEvent":
            #self.removeCurve
            demo.graph.delcurve( ddict['legend'] )
            demo.graph.replot()
            demo.graph.disablemarkermode()
            demo.graph.setPickerSelectionModeOn( "LINE" )
            demo.graph.setTitle( "Line drawing mode is On" )
        if ddict['event'] == "PolygonSelected":
            demo.graph.setTitle( "Marker mode is On" )
            demo.graph.enablemarkermode()
            demo.graph.setPickerSelectionModeOff()
            print( ddict )
    #rescaler = Qwt5.QwtPlotRescaler(demo.graph.canvas())
    #rescaler.setEnabled(True)
    demo.show()
    qt.QObject.connect( demo.graph, qt.SIGNAL( 'QtBlissGraphSignal' ), myslot )
    qt.QObject.connect( demo.graph, qt.SIGNAL( 'PolygonSignal' ), myslot )
    sys.exit( app.exec_() )


# Admire
if __name__ == '__main__':
    main( sys.argv )

