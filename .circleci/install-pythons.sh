set -x
set -e

BUILDROOT=$HOME/heartbot
export PYTHONZ_ROOT=$BUILDROOT/.pythonz

if [[ ! -e .pythonz ]]; then
    wget -O - https://raw.github.com/saghul/pythonz/master/pythonz-install | bash

    declare -a pythons=("2.6.9" "2.7.9" "3.2.6", "3.3.6", "3.4.2")
    for i in "${pythons[@]}"
    do
        $BUILDROOT/.pythonz/bin/pythonz install "$i"
        ln -s "$BUILDROOT/.pythonz/pythons/CPython-$i/bin/python${i:0:3}" ~/bin/
    done

fi
