from lib.Process import *

success = []
failure = []


try:
    test = ["Hello!", "World!"]
    a = Iter(test).results()
    assert(test == a)
except:
    failure.append(test)
else:
    success.append(test)




print("\n\nTest Success!")
print(success)

print("\n\nTest Failure. :9")
print(failure)



