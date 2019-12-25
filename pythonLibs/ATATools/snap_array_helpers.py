#!/usr/bin/python

"""
    This module contains array helpers.
"""

import sys
import ast

def string_to_numeric_array(string):

    arr = []
    arr.append(eval('[%s]' % string))
    return arr[0]


# Convert a string, like "[0,0,0,1,1],[0,0,0,0,0]" to an array
def string_to_array(string):

    arr = []
    had_brackets = True;
    string = string.replace("],[","<temp>")
    if(string[0] != '['):
        had_brackets = False;
        string = "['" + string + "']"
    else:
        string = string.replace("[", "['")
        string = string.replace("]", "']")
    string = string.replace(",", "','")
    string = string.replace("<temp>", "'],['")
    arr.append(eval('[%s]' % string))

    if(had_brackets):
        return arr[0]
    return arr[0][0]

def dict_keys_to_array(dic, do_sort):

    if(do_sort == False):
        return list(dic.keys())
    else:
        newList = [];
        for key, value in sorted(dic.iteritems(), key=lambda (k,v): (v,k)):
            newList.append(key)
        return newList

def flatten(arr):

    return sum(arr, [])

def array_to_string(arr):

    return str(arr).replace("'", "").replace("[", "").replace("]", "").replace(" ", "")

def dict_values_to_array(dic):

    groups = []
    for k,v in dic.iteritems():
        groups.append(v)
    return groups

def dict_values_to_string(dic, cleanup):

    if(cleanup == True):
        return str(dict_values_to_array(dic)).replace("[[", "[").replace("]]","]").replace("'","").replace(" ","")
    return str(dict_values_to_array(dic))
    #return array_to_string(dict_values_to_array(dic))

def run_tests():

    #arr = "[0,0,0,1,1],[0,0,0,0,0],[0,1,1,0,0],[1,0,0,0]";
    #print string_to_array(arr)
    print string_to_array("casa,vira,taua,moon")
    #print flatten(string_to_array("casa,vira,taua,moon"))
    print string_to_array("[2j,2d,4k,1d,2f,5h,3j,3e],[2a,2b,2e,3l,1f,5c,4l,4g]");
    print "Flatten: %s" % flatten(string_to_array("[2j,2d,4k,1d,2f,5h,3j,3e],[2a,2b,2e,3l,1f,5c,4l,4g]"))
    print string_to_numeric_array("[1000.0,2000,3000],[1000.0,2000,3000]")
    print sum(string_to_numeric_array("[1000.0,2000,3000],[1000.0,2000,3000]"), [])
    print "Flatten: %s" % flatten(string_to_numeric_array("[1000.0,2000,3000],[1000.0,2000,3000]"))

    print string_to_numeric_array("1000.0,2000,3000")
    print string_to_numeric_array("")
    print string_to_numeric_array("[]")
    print string_to_array("2j,2d,2f,4k,3e,3j,5h,1d")
    testList =  ['2j', '2d', '2f', '4k', '3e', '3j', '5h', '1d']
    print "Unflattened: %s" % testList
    print "Flatten: %s" % flatten(string_to_array(str(testList).replace("'", "")))


    snaps = {
            "snap0" : "2a,2b,2e,3l,1f,5c,4l,4g",
            "snap1" : "2j,2d,4k,1d,2f,5h,3j,3e",
            #"snap2" : "1ax,1bx,1gx,1hx,2kx,2mx,3dx,4jx,1ay,1by,1gy,1hy,2ky,2my,3dy,4jy"
        }
    snapList = dict_keys_to_array(snaps, True)
    print(str(snapList))
    snapList = dict_keys_to_array(snaps, False)
    print(str(snapList))

if __name__== "__main__":

    import sys

    def print_help():
        print "Syntax: %s test" % (sys.argv[0],)
        sys.exit()


    if len(sys.argv) <= 1:
        print_help()

    if(sys.argv[1] == "test"):
        print "Running tests..."
        run_tests()
        sys.exit()
    else:
        print_help()



