import numpy

def avgindexnumpy(s):
    total = sum(s)
    weightedtotal = 0
    for i in xrange(len(s)):
        weightedtotal += i * s[i]
    return float(weightedtotal) / float(total)

def avgindex(s):
    total = sum(s)
    weightedtotal = 0
    for i in xrange(len(s)):
        weightedtotal += i * s[i]
    return float(weightedtotal) / float(total)

print avgindex([2, 5, 5, 3, 2])
print avgindex([2, 5, 5, 5, 2])
print avgindex([2, 5, 5, 3, 2, 0, 0, 0, 0])
print avgindex([2, 5, 5, 3, 2, 0, 0, 0, 1])
