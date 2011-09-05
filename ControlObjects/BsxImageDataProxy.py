
from Framework4.Control.Core.CObject import CObjectBase, Signal, Slot
from specfile import Specfile

import logging, os, types

class BsxImageDataProxy(CObjectBase):

    signals = [Signal('new_curves_data'),
               Signal('erase_curve')]

    slots = [Slot('load_files')]

    def init(self):
        logging.debug("<BsxImageDataProxy> Created")

    def load_files(self, filenames):
    
        if type(filenames) is types.ListType:
            for filename in filenames:
                try:
                   self.load_single_file(filename)
                except:    
                   logging.debug("problem opening file %s" % filename)  
        else:
            try:
                self.load_single_file(filenames)
            except:    
                logging.debug("problem opening files %s" % filenames)  
            
    def load_single_file(self, filename):

        if not os.path.exists(filename):
            return

        try:
           spec_file = Specfile(filename)
        except:
           spec_file = None

        if spec_file and  spec_file.scanno() > 0:
            #  we take the data of first scan in file. There should only be one
            data = spec_file[0].data()
            self.emit('new_curves_data', { filename: data })

    def erase_curves(self):
        self.emit('erase_curve', None) 
