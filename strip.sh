# !sh
#
cat pye.py pye_gen.py | sed "s/\ *#.*$//" | sed "/^$/d" >pye_mp.py
cat pye_xbee.py pye_gen.py | sed "s/\ *#.*$//" | sed "/^$/d" >pye_x3.py
cat shebang pye.py pye_ux.py >pye
chmod +x pye
mpy-cross -o pye_mp.mpy pye_mp.py
mpy-cross -o pye_x3.mpy -mno-unicode -msmall-int-bits=31 pye_x3.py
#
