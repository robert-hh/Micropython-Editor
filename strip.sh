# !sh
cpp -D BASIC -D WIPY -D DEFINES pye.py | sed "s/#.*$//" | sed "/^$/d" >wipye.py
cpp -D BASIC -D WIPY -D DEFINES -D INDENT pye.py | sed "s/#.*$//" | sed "/^$/d" >wipye_indt.py
cpp -D BASIC -D WIPY -D DEFINES -D REPLACE pye.py | sed "s/#.*$//" | sed "/^$/d" >wipye_rplc.py
cpp -D BASIC -D WIPY -D DEFINES -D SCROLL pye.py | sed "s/#.*$//" | sed "/^$/d" >wipye_scrl.py
cpp -D BASIC -D WIPY -D DEFINES -D BRACKET pye.py | sed "s/#.*$//" | sed "/^$/d" >wipye_brkt.py
cpp -D BASIC -D PYBOARD -D DEFINES -D BRACKET pye.py | sed "s/#.*$//" | sed "/^$/d" >pemin.py
cpp -D PYBOARD -D DEFINES pye.py | sed "s/#.*$//" | sed "/^$/d" >pe.py
cpp -D LINUX -D SCROLL -D DEFINES pye.py | sed "s/#.*$//" | sed "/^$/d" >pex.py
cat shebang pex.py >pye
chmod +x pye
rm pex.py
#
cpp -D BASIC -D WIPY -D DEFINES pye2.py | sed "s/#.*$//" | sed "/^$/d" >wipye2.py
cpp -D PYBOARD -D DEFINES pye2.py | sed "s/#.*$//" | sed "/^$/d" >pe2.py
cpp -D LINUX -D SCROLL pye2.py | grep -v "^# .*$" >pex2.py
cat shebang pex2.py >pye2
chmod +x pye2
rm pex2.py
#
cpp -D BASIC -D WIPY -D DEFINES pye_vt.py | sed "s/#.*$//" | sed "/^$/d" >wipyt.py
cpp -D PYBOARD -D DEFINES pye_vt.py | sed "s/#.*$//" | sed "/^$/d" >pet.py

