import Queue
import PyTango
import threading
import time


if __name__ == '__main__' :
    class javaServerTask( threading.Thread ):
        def __init__( self, device_name, task_name, *args ):
            threading.Thread.__init__( self )
            self.device_name = device_name
            self.task_name = task_name
            self.args = args
            self.result = None

            self.start()

        def run( self ):
            device = PyTango.DeviceProxy( self.device_name )
            method = getattr( device, self.task_name )
            task_id = method( *self.args )

            while device.isTaskRunning( task_id ):
                time.sleep( 0.5 )

            try:
                r = device.checkTaskResult( task_id )
            except PyTango.DevFailed, traceback:
                task_error = traceback[0]
                error_msg = str( task_error.desc ).replace( "Task error: ", "" )
                self.result = Exception( error_msg )
            except Exception, err:
                self.result = Exception( str( err ) )
            else:
                self.result = r

        def get_result( self ):
            """Raise an exception if an error occured, otherwise return value"""
            self.join() #wait end of run()
            if isinstance( self.result, Exception ):
                raise Exception( self.result )
            else:
                return self.result

task = javaServerTask( "bm29/bssc/1", "measureConcentration", ["1", "1", "1"] )

t0 = time.time()
print "starting thread"
print task.get_result()
print "(took %s seconds)" % ( time.time() - t0 )

