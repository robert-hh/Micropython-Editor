# !sh
#
cpp -D MICROPYTHON -D VT100 pye.py | sed "s/\ *#.*$//" | sed "/^$/d" >pye_mp.py
cat shebang <(cpp -D LINUX -D VT100 pye.py | sed "s/\ *#.*$//" | sed "/^$/d") >pye
chmod +x pye
mpy-cross -o pye_mp.mpy pye_mp.py
#
