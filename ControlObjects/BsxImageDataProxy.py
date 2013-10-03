from Framework4.Control.Core.CObject import CObjectBase, Signal, Slot
import logging, os, types
import traceback
import numpy
import pprint

class BsxImageDataProxy( CObjectBase ):
    signals = [Signal( 'new_curves_data' ),
               Signal( 'erase_curve' )]
    slots = [Slot( 'load_files' )]

    def init( self ):
        logging.debug( "<BsxImageDataProxy> Created" )

    def load_files( self, filenames ):
        if type( filenames ) is types.ListType:
            for filename in filenames:
                try:
                    self.load_single_file( filename )
                except:
                    logging.debug( "Problem opening file %s", filename )
        else:
            try:
                self.load_single_file( filenames )
            except:
                logging.debug( traceback.format_exc() )
                logging.debug( "Problem opening file %s", filenames )

    def load_single_file( self, filename ):
        if not os.path.exists( filename ):
            return

        data = numpy.loadtxt( filename )
       
        self.display_data(filename, data[:,0], data[:,1])

    def display_data(self, name, x, y):
        self.emit( 'erase_curve', name )

        # remove negative values, for Log scale
        mask = y>0 
     
        self.emit( 'new_curves_data', { name: [x[mask], y[mask]] } )

    def erase_curves( self ):
        self.emit( 'erase_curve', None )
