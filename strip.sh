# !sh
#
cat pye.py pye_std.py | sed "s/\ *#.*$//" | sed "/^$/d" >pye_mp.py
cat shebang pye.py pye_ux.py >pye
chmod +x pye
mpy-cross -o pye_mp.mpy pye_mp.py
#
