#!/usr/bin/python

import numpy as np

boxes = np.random.choice(range(100), size=100, replace=False)
inmates = range(100)
lucky = []


print("boxes:", boxes)
print("inmates", inmates)

print("------------")


# The director of a prison offers 100 death row prisoners, who are numbered 
# from 1 to 100, a last chance. A room contains a cupboard with 100 drawers. 
# The director randomly puts one prisoner's number in each closed drawer. 
# The prisoners enter the room, one after another. Each prisoner may open 
# and look into 50 drawers in any order. The drawers are closed again afterwards.
# If, during this search, every prisoner finds his number in one of the drawers, 
# all prisoners are pardoned. If just one prisoner does not find his number, all 
# prisoners die. Before the first prisoner enters the room, the prisoners may 
# discuss strategy—but may not communicate once the first prisoner enters to 
# look in the drawers. What is the prisoners' best strategy?


for prisoner in inmates:
    
    print("Hi, Im prisoner", prisoner)
    choices = len(boxes) / 2
    og = prisoner
    
    while choices >= 1:

        pick = boxes[prisoner]
        
        if pick == og:
            print("Hi, Im lucky prisoner", prisoner)
            lucky.append(prisoner)
            break
        else:
            print("I choose", prisoner, "picked", pick)
            prisoner = pick
        choices -= 1

if len(lucky) == 100:
    print("Prisoners escape!")

print("halts.", lucky)
