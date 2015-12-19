# !sh
cpp -D BASIC -D WIPY -D DEFINES pye.py | sed "s/#.*$//" | sed "/^$/d" >wipye_sml.py
cpp -D BASIC -D WIPY -D DEFINES -D REPLACE pye.py | sed "s/#.*$//" | sed "/^$/d" >wipye_rplc.py
cpp -D BASIC -D WIPY -D DEFINES -D SCROLL pye.py | sed "s/#.*$//" | sed "/^$/d" >wipye_scrl.py
cpp -D BASIC -D WIPY -D DEFINES -D BRACKET pye.py | sed "s/#.*$//" | sed "/^$/d" >wipye.py
cpp -D BASIC -D PYBOARD -D DEFINES -D BRACKET pye.py | sed "s/#.*$//" | sed "/^$/d" >pemin.py
cpp -D PYBOARD -D DEFINES pye.py | sed "s/#.*$//" | sed "/^$/d" >pe.py
cpp -D LINUX pye.py | grep -v "^# .*$" >pex.py
cpp -D PYBOARD pye.py | grep -v "^# .*$" >peb.py
cat shebang pex.py >pye
chmod +x pye
#
cpp -D BASIC -D WIPY -D DEFINES pye2.py | sed "s/#.*$//" | sed "/^$/d" >wipye2.py
cpp -D PYBOARD -D DEFINES pye2.py | sed "s/#.*$//" | sed "/^$/d" >pe2.py
cpp -D LINUX pye2.py | grep -v "^# .*$" >pex2.py
cat shebang pex2.py >pye2
chmod +x pye2
rm pex2.py
#
