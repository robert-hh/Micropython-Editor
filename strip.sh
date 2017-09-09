# !sh
cpp -D BASIC -D WIPY -D DEFINES pye_sml.py | sed "s/#.*$//" | sed "/^$/d" >wipye.py
cpp -D BASIC -D WIPY -D DEFINES -D INDENT pye_sml.py | sed "s/#.*$//" | sed "/^$/d" >wipye_indt.py
cpp -D BASIC -D WIPY -D DEFINES -D REPLACE pye_sml.py | sed "s/#.*$//" | sed "/^$/d" >wipye_rplc.py
#
cpp -D BASIC -D PYBOARD -D DEFINES -D REPLACE -D INDENT pye_sml.py | sed "s/#.*$//" | sed "/^$/d" >pemin.py
#
cpp -D PYBOARD -D DEFINES -D SCROLL -D MOUSE pye2.py | sed "s/#.*$//" | sed "/^$/d" >pe2.py
cpp -D LINUX   -D DEFINES -D SCROLL -D MOUSE pye2.py | grep -v "^# .*$" >pex2.py
cat shebang pex2.py >pye2
chmod +x pye2
rm pex2.py
#
cpp -D PYBOARD -D DEFINES -D SCROLL -D MOUSE pye.py | sed "s/#.*$//" | sed "/^$/d" >pe.py
cpp -D ESP32   -D DEFINES -D SCROLL -D MOUSE pye.py | sed "s/#.*$//" | sed "/^$/d" >pesp.py
cpp -D LINUX   -D DEFINES -D SCROLL -D MOUSE pye.py | sed "s/#.*$//" | sed "/^$/d" >pex.py
cat shebang pex.py >pye
chmod +x pye
rm pex.py
mpy-cross -o wipye.mpy pesp.py
#


