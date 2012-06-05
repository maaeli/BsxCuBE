from Framework4.Control.Core.CObject import CObjectBase, Signal, Slot


class Login(CObjectBase):

    signals = [Signal("loggedIn")]

    slots = [Slot("loginTry")]


    def __init__(self, *args, **kwargs):
        CObjectBase.__init__(self, *args, **kwargs)



    def init(self):
        pass

    def loginTry(self, userAndPassword):
        print "Got a try of login"
        #TODO! check login and send signal
