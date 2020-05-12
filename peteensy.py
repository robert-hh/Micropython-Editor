#
# wrapper for Teensy 3.5 and 3.6
#
import pye_mp
def pye(*files):
        from pyb import USB_VCP
        USB_VCP().setinterrupt(-1)
        pye_mp.pye(*files)
        USB_VCP().setinterrupt(3)

