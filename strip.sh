# !sh
#
cat pye_core.py pye_gen.py | sed "s/\ *#.*$//" | sed "/^$/d" >pye.py
cat pye_xbee.py pye_gen.py | sed "s/\ *#.*$//" | sed "/^$/d" >pye_x3.py
cat shebang pye_core.py pye_ux.py >pye
chmod +x pye
cat pye_core.py pye_win.py >pye_win
../micropython/mpy-cross/mpy-cross -O3 -o pye.mpy pye.py
../micropython/mpy-cross/mpy-cross -O3 -o pye_x3.mpy -msmall-int-bits=31 pye_x3.py
#
