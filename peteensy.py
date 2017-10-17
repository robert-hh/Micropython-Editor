#
# wrapper for Teensy 3.5 and 3.6
#
import pe
def pye(*files):
        from pyb import USB_VCP
        USB_VCP().setinterrupt(-1)
        pe.pye(*files)
        USB_VCP().setinterrupt(3)

