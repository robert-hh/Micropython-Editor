# !sh
#
cpp -D MICROPYTHON pye2.py | sed "s/#.*$//" | sed "/^$/d" >pye2_mp.py
cat shebang <(cpp -D LINUX       pye2.py | sed "s/#.*$//" | sed "/^$/d") >pye2
chmod +x pye2
#
cpp -D MICROPYTHON pye.py | sed "s/#.*$//" | sed "/^$/d" >pye_mp.py
cat shebang <(cpp -D LINUX       pye.py | sed "s/#.*$//" | sed "/^$/d") >pye
chmod +x pye
mpy-cross -o pye_mp.mpy pye_mp.py
#
