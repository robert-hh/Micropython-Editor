# !sh
#
cpp -D MICROPYTHON pye.py | sed "s/#.*$//" | sed "/^$/d" >pye_mp.py
cat shebang <(cpp -D LINUX       pye.py | sed "s/#.*$//" | sed "/^$/d") >pye
chmod +x pye
#
