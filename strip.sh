# !sh
cpp -D MICROPYTHON -D BASIC -D DEFINES -D REPLACE -D INDENT pye_sml.py | sed "s/#.*$//" | sed "/^$/d" >pemin.py
#
cpp -D MICROPYTHON -D DEFINES -D SCROLL -D MOUSE pye2.py | sed "s/#.*$//" | sed "/^$/d" >pe2.py
cpp -D LINUX   -D DEFINES -D SCROLL -D MOUSE pye2.py | grep -v "^# .*$" >pex2.py
cat shebang pex2.py >pye2
chmod +x pye2
rm pex2.py
#
cpp -D MICROPYTHON -D DEFINES -D SCROLL -D MOUSE pye.py | sed "s/#.*$//" | sed "/^$/d" >pe.py
cpp -D LINUX   -D DEFINES -D SCROLL -D MOUSE pye.py | sed "s/#.*$//" | sed "/^$/d" >pex.py
cat shebang pex.py >pye
chmod +x pye
rm pex.py
mpy-cross -o wipye.mpy pe.py
#


