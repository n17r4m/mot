# Multiple Object Tracking

This documentation is not currently well maintained and may be out of date.

The basic structure of this project is in to two parts.

The first, is found in py/ and is a robust collection
of python analysis modules.

The second, in webui/ is a browser based GUI which ties the python
tools together into task-based workflows.

## Running

All of the python commands in py/commands can be accessed through
the top level mot.py utility. 

e.g.: 
cd mot/py
./mot.py detect some/video.avi 2017-10-24 Experiment24 "Ran extra hot 90deg C"


To start the webui, enter the directory and type

meteor

## Dependancies

- numpy
- skvideo
- skimage
- tensorflow 
- meteor

