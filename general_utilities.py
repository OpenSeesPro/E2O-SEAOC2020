# -*- coding: utf-8 -*-
"""
Created on Sun Aug  2 16:37:56 2020

@author: asinghania
"""
import time

def start_time():
    print('Started at: ' + time.strftime('%a, %d %b %Y %H:%M:%S PST', time.localtime()))
    return time.time()

def end_time(start_time, final=True):
    end_time    = time.time()
    (mins, secs)= divmod(round(end_time - start_time, 0), 60)
    print('OpenSees Model Created!\nTime Elapsed: ' + str(mins) + ' minute(s) ' + str(secs), 'second(s).\n')
    if final:
        print('Finished at: ' + time.strftime('%a, %d %b %Y %H:%M:%S PST', time.localtime()))
    return