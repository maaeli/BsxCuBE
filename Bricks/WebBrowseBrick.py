import logging
from Framework4.GUI import Core
from Framework4.GUI.Core import Property, Connection, Signal, Slot
from PyQt4 import QtCore, QtGui, Qt
from PyQt4.QtWebKit import QWebView

from PyQt4.QtCore import QUrl


__category__ = "BsxCuBE"



class WebBrowseBrick( Core.BaseBrick ):

    properties = {"url": Property( "string", "URL", "", "urlChanged" )}

    connections = {"login": Connection( "Login object",
                                        [Signal( "loggedIn", "loggedIn" )],
                                        [],
                                        "connectionToLogin" )}

    signals = []
    slots = [Slot( "setURL" )]


    def __init__( self, *args, **kargs ):
        Core.BaseBrick.__init__( self, *args, **kargs )

    def init( self ):
        self.webViewer = QWebView()
        self.urlBlank = "about:blank"
        mainLayout = Qt.QHBoxLayout( self.brick_widget )
        mainLayout.addWidget( self.webViewer )
        self.brick_widget.setLayout( mainLayout )
        self.brick_widget.setStyleSheet( "border:1px solid;" )
        self.brick_widget.setSizePolicy( Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding )

    def urlChanged( self, url ):
        self.urlConfig = url

    def setUrl( self, url ):
        #TODO:DEBUG 
        print "got url %s" % url
        self.urlConfig = url

   # When connected to Login, then block the brick
    def connectionToLogin( self, pPeer ):
        if pPeer is not None:
            self.brick_widget.setEnabled( False )
            self.webViewer.load( QUrl( self.urlBlank ) )

    # Logged In : True or False 
    def loggedIn( self, pValue ):
        self.brick_widget.setEnabled( pValue )
        if pValue:
            self.webViewer.load( QUrl( self.urlConfig ) )
        else:
            self.webViewer.load( QUrl( self.urlBlank ) )

