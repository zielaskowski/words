#!/bin/bash
# assume app is in ./
# and script is in ./req
# so to reach app we need ../

pipreqs --no-pin --force ../
packages=$(cat ../requirements.txt | paste -s -d,)
pipdeptree -p $packages > requirements.txt
pipdeptree -p $packages --graph-output jpg > requirements.jpg
pyreverse -a1 -s2 -my -o png ../gui.py

pip freeze
# from WIN encoding to utf-8
#file -i requirements.txt
#pipiconv -f utf-16le -t utf-8 requirements.txt -o requirements.txt
