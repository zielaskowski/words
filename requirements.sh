#!/bin/bash
pipreqs --no-pin --force
packages=$(cat requirements.txt | paste -s -d,)
rm ./requirements.txt
pipdeptree -p $packages > requirements.txt
pipdeptree -p $packages --graph-output jpg > requirements.jpg


