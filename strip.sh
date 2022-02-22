# !sh
#
cat pye_core.py pye_gen.py | sed "s/\ *#.*$//" | sed "/^$/d" >pye.py
cat pye_xbee.py pye_gen.py | sed "s/\ *#.*$//" | sed "/^$/d" >pye_x3.py
cat shebang pye_core.py pye_ux.py >pye
chmod +x pye
cat pye_core.py pye_win.py >pye_win
mpy-cross -o pye.mpy -O3 pye.py
mpy-cross -o pye_x3.mpy -mno-unicode -msmall-int-bits=31 -O3 pye_x3.py
#
