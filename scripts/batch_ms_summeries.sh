#!/bin/sh

cd /home/mot/py/


./

./mot.py processDirectory '/home/mot/data/source/Glass.Bead.Tests/' 2018-05-03 '/home/mot/data/exports/batchTest'
./mot.py processDirectory "/home/mot/data/source/Water.NaOH.Oil.Sand/"  2018-05-03 '/home/mot/data/exports/batchTest'
./mot.py processDirectory "/home/mot/data/source/Bitumen.Water/" 2018-05-03 '/home/mot/data/exports/batchTest'
./mot.py processDirectory "/home/mot/data/source/Bitumen.Test.Sand.Water/" 2018-05-03 '/home/mot/data/exports/batchTest'
./mot.py processDirectory "/home/mot/data/source/Water.Test.Sand/" 2018-05-03 '/home/mot/data/exports/batchTest'
./mot.py processDirectory "/home/mot/data/source/Water.Clay.Test.Sand" 2018-05-03 '/home/mot/data/exports/batchTest'
./mot.py processDirectory "/home/mot/data/source/Bubbles-BU-2018-03-01/" 2018-05-03 '/home/mot/data/exports/batchTest'
# ./mot.py processDirectory "/home/mot/data/source/BU-2018-02-05/" 2018-05-03 '/home/mot/data/exports/batchTest'