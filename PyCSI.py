# -*- coding: utf-8 -*-
"""
Created on Wed Oct 30 15:10:49 2019

@author: pranchal
"""

import sys
import comtypes.client

def getSapModelFromEtabs(AttachToInstance):
    
    # connect to ETABS
    if AttachToInstance:
        # attach to a running instance of ETABS
        try:
            # get the active ETABS object
            myETABSObject = comtypes.client.GetActiveObject("CSI.ETABS.API.ETABSObject") 
        except (OSError, comtypes.COMError):
            print("No running instance of the program found or failed to attach.")
            sys.exit(-1)    
    
    # create SapModel object
    SapModel        = myETABSObject.SapModel
    myETABSObject   = None
    
    return SapModel

def getSapModelFromSap2000(AttachToInstance):
    
    # connect to ETABS
    if AttachToInstance:
        # attach to a running instance of ETABS
        try:
            # get the active ETABS object
            mySapObject = comtypes.client.GetActiveObject("CSI.SAP2000.API.SapObject") 
        except (OSError, comtypes.COMError):
            print("No running instance of the program found or failed to attach.")
            sys.exit(-1)    
    
    # create SapModel object
    SapModel        = mySapObject.SapModel
    mySapObject   = None
    
    return SapModel