# !sh
#
cpp -D MICROPYTHON pye2.py | sed "s/#.*$//" | sed "/^$/d" >pye2_mp.py
cpp -D LINUX       pye2.py | sed "s/#.*$//" | sed "/^$/d" >pex2.py
cat shebang pex2.py >pye2
chmod +x pye2
rm pex2.py
#
cpp -D MICROPYTHON pye.py | sed "s/#.*$//" | sed "/^$/d" >pye_mp.py
cpp -D LINUX       pye.py | sed "s/#.*$//" | sed "/^$/d" >pex.py
cat shebang pex.py >pye
chmod +x pye
rm pex.py
mpy-cross -o wipye.mpy pye_mp.py
#


