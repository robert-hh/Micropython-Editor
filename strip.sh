# !sh
cpp -D BASIC -D WIPY -D DEFINES pye.py | sed "s/#.*$//" | sed "/^$/d" >wipye.py
cpp -D BASIC -D PYBOARD -D DEFINES pye.py | sed "s/#.*$//" | sed "/^$/d" >pemin.py
cpp -D PYBOARD -D DEFINES pye.py | sed "s/#.*$//" | sed "/^$/d" >pe.py
cpp -D LINUX pye.py | grep -v "^# .*$" >pex.py
cpp -D PYBOARD pye.py | grep -v "^# .*$" >peb.py
cat shebang pex.py >pye
chmod +x pye

