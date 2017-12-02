from lib.Process import *

success = []
failure = []


try: # .results()
    
    test = ["Hello!", "World!"]
    x = list(Iter(test).items())
    assert(x == test)
    
except Exception as e: failure.append((test, e))
else:                  success.append(test)


try: # .items()
    
    test = ["Identity"]
    f = Iter(test).into(F())
    for x in f.items():
        assert(x == test[0])
    
except Exception as e: failure.append((test, e))
else:                  success.append(test)



try:
    
    test = ["Pachinko", *range(5)]
    x = list(
        Iter(test)
        .into(By(5, Delay, 0., 0.01))
        .into(By(5, Delay, 0., 0.01))
        .into(By(5, Delay, 0., 0.01))
        .items())
    
    assert(test[0] in x)
    
except Exception as e: failure.append((test, e))
else:                  success.append(test)



try:
    #             x * 2 = y
    test = [[1,2,3],      [2,4,6]]
    class TimesTwo(F): 
        def do(self, n): self.push(n * 2)
    x = list(Iter(test[0]).into(TimesTwo()).items())
    assert(x == test[1])
    
except Exception as e: failure.append((test, e))
else:                  success.append(test)



try:
    test = ["Split-Merge"]
    x = list(
        Iter(test)
        .sequence()
        .split([F(), F(), F()])
        .merge()
        .items())
    
    assert(x == [test * 3])
    
except Exception as e: failure.append((test, e))
else:                  success.append(test)



try:
    test = ["Split-Merge2"]
    x = list(
        Iter(test)
        .sequence()
        .split([
            By(3, F).into(Delay(0, 0.1)), 
            F().into(Delay(0, 0.1)), 
            F().into(Delay(0, 0.1))
        ])
        .merge()
        .items())
    
    assert(x == [test * 3])
    
except Exception as e: failure.append((test, e))
else:                  success.append(test)







print("\n\nTest Success!")
print(success)

print("\n\nTest Failure. :9")
print(failure)



