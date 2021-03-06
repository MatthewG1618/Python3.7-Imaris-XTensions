# Filament Analysis
#
# Written by Matthew J. Gastinger
#
# Aug 2020 - Imaris 9.6.0
#
#
    #<CustomTools>
        #<Menu>
            #<Submenu name="Filaments Functions">
                #<Item name="Filament Analysis19 beta" icon="Python3">
                    #<Command>Python3XT::XT_MJG_Filament_Analysis19_beta(%i)</Command>
                #</Item>
            #</Submenu>
       #</Menu>
       #<SurpassTab>
           #<SurpassComponent name="bpFilaments">
               #<Item name="Filament Analysis19 beta" icon="Python3">
                   #<Command>Python3XT::XT_MJG_Filament_Analysis19_beta(%i)</Command>
               #</SurpassComponent>
           #</SurpassTab>
    #</CustomTools>
#
#  Description:
#       This XTension will do several things:
#       1)Place spots at each point along the filament, allowing for
#           visualizing and measuring the instensity along the dendrites
#       2)Find synaptic bouton(varicosities) along dendrite segments, place
#           a spot at that point.
#       3)Place spots at each of hte following places:
#           beginning point,
#           dendrite branch,
#           dendrite terminal point,
#           Spine Attachment point
#           Spine terminal point
#       4)Generate a duplicate of the filament object with NEW statistics
#           Dendrite mean intensity (for each channel)
#           Spine intensity (not just the spine head, the whole spine)
#           Bouton(varicosity) number per dendrite segment
#           Bouton density
#           Spot Detection within a certain distance of filament
#           Spot Density

#Python Dependancies:
    # numpy
    # tkinter
    # scipy
    # operator
    # itertools
    # statistics import mean
    # functools import reduce



import numpy as np
import time
import random


# GUI imports
import tkinter as tk
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tkinter import simpledialog
#import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from scipy.signal import peak_widths
from scipy.spatial.distance import cdist
from scipy.spatial.distance import pdist
from operator import add
from operator import itemgetter
import operator
import itertools
from statistics import mean
from functools import reduce
import collections



import ImarisLib
aImarisId=0
def XT_MJG_Filament_Analysis19_beta(aImarisId):
    # Create an ImarisLib object
    vImarisLib = ImarisLib.ImarisLib()
    # Get an imaris object with id aImarisId
    vImarisApplication = vImarisLib.GetApplication(aImarisId)
    # Get the factory
    vFactory = vImarisApplication.GetFactory()
    # Get the currently loaded dataset
    vImage = vImarisApplication.GetDataSet()
    # Get the Surpass scene
    vSurpassScene = vImarisApplication.GetSurpassScene()

    vSurfaces = vFactory.ToSurfaces(vImarisApplication.GetSurpassSelection())
    vSpots = vFactory.ToSpots(vImarisApplication.GetSurpassSelection())
    vFilaments = vFactory.ToFilaments(vImarisApplication.GetSurpassSelection())

    ############################################################################
    global Entry2, NamesSurfaces, NamesSpots

    NamesSurfaces=[]
    NamesSpots=[]
    NamesFilaments=[]
    NamesaFilamentIndex=[]
    NamesSurfaceIndex=[]
    NamesSpotsIndex=[]

    vSurpassSurfaces = 0
    vSurpassSpots = 0
    vSurpassFilaments = 0
    vNumberSurpassItems=vImarisApplication.GetSurpassScene().GetNumberOfChildren()
    for vChildIndex in range(0,vNumberSurpassItems):
        vDataItem=vSurpassScene.GetChild(vChildIndex)
        IsSurface=vImarisApplication.GetFactory().IsSurfaces(vDataItem)
        IsSpot=vImarisApplication.GetFactory().IsSpots(vDataItem)
        IsFilament=vImarisApplication.GetFactory().IsFilaments(vDataItem)
        if IsSurface:
            vSurpassSurfaces = vSurpassSurfaces+1
            NamesSurfaces.append(vDataItem.GetName())
            NamesSurfaceIndex.append(vChildIndex)
        elif IsSpot:
            vSurpassSpots = vSurpassSpots+1
            NamesSpots.append(vDataItem.GetName())
            NamesSpotsIndex.append(vChildIndex)
        elif IsFilament:
            vSurpassFilaments = vSurpassFilaments+1
            NamesFilaments.append(vDataItem.GetName(),)
            NamesaFilamentIndex.append(vChildIndex)
    ############################################################################

    #Dialog window
    ############################################################################
    window = tk.Tk()
    window.title('Filament Analysis')
    window.geometry('300x280')
    window.attributes("-topmost", True)

    ##################################################################
    #Set input in center on screen
    # Gets the requested values of the height and widht.
    windowWidth = window.winfo_reqwidth()
    windowHeight = window.winfo_reqheight()
    # Gets both half the screen width/height and window width/height
    positionRight = int(window.winfo_screenwidth()/2 - windowWidth/2)
    positionDown = int(window.winfo_screenheight()/2 - windowHeight/2)
    # Positions the window in the center of the page.
    window.geometry("+{}+{}".format(positionRight, positionDown))
    ##################################################################

    def Filament_options():
        global vOptionIntensity, vOptionFilamentToSpots,vOptionFilamentToSpotsMerge,vOptionBoutonThreshold, vOptionBoutonHeight
        global vOptionFilamentBoutonDetection, vOptionFilamentBoutoDetecionThreshold, vOptionFilamentCloseToSpots, vOptionFilamentToSpotsFill
        global vOptionFilamentSpotThreshold, NamesSpots, NamesSurfaces
        if (var1.get() == 0) and (var2.get() == 0) and (var4.get() == 0) and (var5.get() ==0):
            messagebox.showerror(title='Filament Analysis menu',
                             message='Please Select ONE Analysis')
            window.mainloop()

        vOptionIntensity=var1.get()
        vOptionFilamentToSpots=var2.get()
        vOptionFilamentToSpotsMerge=var3.get()
        vOptionFilamentToSpotsFill=var6.get()
        vOptionFilamentBoutonDetection=var4.get()
        # vOptionSpotsDistanceAlongFilament=var7.get()
        vOptionFilamentCloseToSpots=var5.get()
        vOptionFilamentSpotThreshold=[float(Entry2.get())]

        if NamesSpots==[] and vOptionFilamentCloseToSpots==1:
            messagebox.showerror(title='Spot Selection',
                             message='Please Create Spots Object!!')
            window.mainloop()

        if vOptionFilamentBoutonDetection==1 and (var4Low.get()+var4Med.get()+var4High.get())>1:
            messagebox.showerror(title='Filament Analysis menu',
                             message='Choose one Sensitivity')
            window.mainloop()

        if (var4.get() == 1) and (var4Low.get() == 1):
            vOptionBoutonThreshold=20
            vOptionBoutonHeight=0.5
        elif (var4.get() == 1) and (var4Med.get() == 1):
            vOptionBoutonThreshold=10
            vOptionBoutonHeight=.25
        elif (var4.get() == 1) and (var4High.get() == 1):
            vOptionBoutonThreshold=5
            vOptionBoutonHeight=0

        if (var2.get() == 0) and (var3.get() == 1):
            vOptionFilamentToSpots=1
        window.destroy()

    var1 = tk.IntVar(value=0)
    var2 = tk.IntVar(value=0)
    var3 = tk.IntVar(value=0)
    var4 = tk.IntVar(value=0)
    var5 = tk.IntVar(value=0)
    var6 = tk.IntVar(value=0)
    var4Low=tk.IntVar(value=0)
    var4Med=tk.IntVar(value=1)
    var4High=tk.IntVar(value=0)
    # var7= tk.IntVar(value=0)

    tk.Label(window, font="bold", text='Choose Analysis Options!').grid(row=0,column=0, padx=75,sticky=W)
    tk.Checkbutton(window, text='Measure Intensity of Dendrite',
                    variable=var1, onvalue=1, offvalue=0).grid(row=1, column=0, padx=40,sticky=W)
    tk.Checkbutton(window, text='Export Filament as a Spots object',
                    variable=var2, onvalue=1, offvalue=0).grid(row=2, column=0, padx=40,sticky=W)
    tk.Checkbutton(window, text='Fill Spots',
                    variable=var6, onvalue=1, offvalue=0).grid(row=4, column=0, padx=80,sticky=W)
    tk.Checkbutton(window, text='Merge all Filaments',
                    variable=var3, onvalue=1, offvalue=0).grid(row=3, column=0, padx=80,sticky=W)
    tk.Checkbutton(window, text='Detect Boutons (varicosities)',
                    variable=var4, onvalue=1, offvalue=0).grid(row=5, column=0, padx=40,sticky=W)

    tk.Checkbutton(window, text='Low',
                    variable=var4Low, onvalue=1, offvalue=0).grid(row=6, column=0, padx=80,sticky=W)
    tk.Checkbutton(window, text='Med',
                    variable=var4Med, onvalue=1, offvalue=0).grid(row=6, column=0, padx=130,sticky=W)
    tk.Checkbutton(window, text='High (sensitivity)',
                    variable=var4High, onvalue=1, offvalue=0).grid(row=6, column=0, padx=180,sticky=W)

    tk.Checkbutton(window, text='Find Spots Close to Filaments',
                    variable=var5, onvalue=1, offvalue=0).grid(row=7, column=0, padx=40,sticky=W)
    Entry2=Entry(window,justify='center',width=8)
    Entry2.grid(row=8, column=0, padx=80, sticky=W)
    Entry2.insert(0, '0.5')
    tk.Label(window, text='um (distance threshold)').grid(row=8,column=0, padx=130, sticky=W)

    btn = Button(window, text="Analyze Filament", bg='blue', fg='white', command=Filament_options)
    btn.grid(column=0, row=9, sticky=W, padx=100, pady=5)


    window.mainloop()

    ############################################################################
    ############################################################################
    #Open Surpass menu to Select Spots Object
    if vOptionFilamentCloseToSpots==1:

        #####################################################
        #Making the Listbox for the Surpass menu
        main = tk.Tk()
        main.title("Surpass menu")
        main.geometry("+50+150")
        frame = ttk.Frame(main, padding=(3, 3, 12, 12))
        frame.grid(column=0, row=0, sticky=(N, S, E, W))
        main.attributes("-topmost", True)

        #################################################################
        #Set input in center on screen
        # Gets the requested values of the height and widht.
        windowWidth = main.winfo_reqwidth()
        windowHeight = main.winfo_reqheight()
        # Gets both half the screen width/height and window width/height
        positionRight = int(main.winfo_screenwidth()/2 - windowWidth/2)
        positionDown = int(main.winfo_screenheight()/2 - windowHeight/2)
        # Positions the window in the center of the page.
        main.geometry("+{}+{}".format(positionRight, positionDown))
        ##################################################################
        names = StringVar()
        names.set(NamesSpots)
        lstbox = Listbox(frame, listvariable=names, selectmode=MULTIPLE, width=20, height=10)
        lstbox.grid(column=0, row=0, columnspan=2)
        def select():
            global ObjectSelection
            ObjectSelection = list()
            selection = lstbox.curselection()
            for i in selection:
                entrada = lstbox.get(i)
                ObjectSelection.append(entrada)
        #Test for the correct number selected
            if len(ObjectSelection)!=1:
                messagebox.showerror(title='Surface menu',
                                      message='Please Choose 1 Spots')
                main.mainloop()
            else:
                main.destroy()

        btn = ttk.Button(frame, text="Choose Spots Object", command=select)
        btn.grid(column=1, row=1)
        #Selects the top items in the list
        lstbox.selection_set(0)
        main.mainloop()
    ####################################################################
    # get the Selected Spots in Surpass Scene
        vDataItem=vSurpassScene.GetChild(NamesSpotsIndex[(NamesSpots.index( ''.join(map(str, ObjectSelection[0]))))])
        vSpots=vImarisApplication.GetFactory().ToSpots(vDataItem)
    ####################################################################
    #Test if scene has Spots object
     #get the spot coordinates
        vSpotsColocPositionsXYZ = vSpots.GetPositionsXYZ()
        vSpotsColocRadius = vSpots.GetRadiiXYZ()
        vSpotsColocTimeIndices = vSpots.GetIndicesT()
        vSpotsColocCount = len(vSpotsColocRadius)
        vSpotsId = vSpots.GetIds()
    ####################################################################
    ####################################################################

    #Get Image properties
    vDataMin = (vImage.GetExtendMinX(),vImage.GetExtendMinY(),vImage.GetExtendMinZ())
    vDataMax = (vImage.GetExtendMaxX(),vImage.GetExtendMaxY(),vImage.GetExtendMaxZ())
    vDataSize = (vImage.GetSizeX(),vImage.GetSizeY(),vImage.GetSizeZ())
    vSizeT = vImage.GetSizeT()
    vSizeC = vImage.GetSizeC()
    aXvoxelSpacing= (vDataMax[0]-vDataMin[0])/vDataSize[0]
    aYvoxelSpacing= (vDataMax[1]-vDataMin[1])/vDataSize[1]
    aZvoxelSpacing = round((vDataMax[2]-vDataMin[2])/vDataSize[2],3)
    vSmoothingFactor=aXvoxelSpacing*2

    #Get the Current Filament Object
    vNumberOfFilaments=vFilaments.GetNumberOfFilaments()
    vFilamentIds= vFilaments.GetIds()

    #Generate Surpass Scene folder locations

    #Create a new folder object for Filament to Spots
    #Generate new Factory for Surpass Scene objects
    vNewSpotsDendritesFolder = vImarisApplication.GetFactory().CreateDataContainer()
    vNewSpotsSpinesFolder =vImarisApplication.GetFactory().CreateDataContainer()
    vNewSpotsDendritesFolder.SetName('Filament to Spots (dendrite) -- ' + vFilaments.GetName())
    vNewSpotsSpinesFolder.SetName('Spines to Spots -- ' + vFilaments.GetName())

    #Create a new folder object for Filament Intensity
    vNewIntensityFolder=vImarisApplication.GetFactory().CreateDataContainer()
    vNewIntensityFolder.SetName(vFilaments.GetName() + 'Filament Intensity -')
    vOriginalSpotsFromFilament=vImarisApplication.GetFactory().CreateSpots()

    #Create a new folder object for Bouton Spots
    vNewSpotsBoutons = vImarisApplication.GetFactory().CreateSpots()
    # vNewSpotsvNewSpotsAlongFilament = vImarisApplication.GetFactory().CreateSpots()
    vNewSpotsAnalysisFolder =vImarisApplication.GetFactory().CreateDataContainer()
    vNewSpotsAnalysisFolder.SetName('Filament Analysis -- ' + vFilaments.GetName())

    #Preset variable lists
    vTotalSpotsDendrite=[]
    vTotalSpotsDendriteTime=[]
    vTotalSpotsDendriteRadius=[]
    vTotalSpotsSpine=[]
    vTotalSpotsSpineRadius=[]
    vTotalSpotsSpineTime=[]
    wAllSegmentIds=[]
    TotalSegmentIndex=[]
    wCompleteFilamentTimeIndex=[]
    wCompleteDendriteTimeIndex=[]
    wCompleteSpineTimeIndex=[]
    vBoutonPositionAll=[]
    vBoutonRadiusAll=[]
    vStatisticFilamentBoutonsPerDendrite=[]
    wCompleteFilamentNumberBoutons=[]
    vAllColocDensityPerDendrite=[]
    vFilamentCountActual=0
    wCompleteDendriteSegmentIds=[]
    wCompleteSpineSegmentIds=[]
    wCompleteDendriteBranchIntCenter=[]
    wCompleteDendriteBranchIntMean=[]
    wCompleteSpineBranchIntCenter=[]
    wCompleteSpineBranchIntMean=[]
    vStatisticDendriteBranchIntMean=[]
    vStatisticDendriteBranchIntCenter=[]
    vStatisticSpineBranchIntMean=[]
    vStatisticSpineBranchIntCenter=[]
    wNumberOfSpotsPerDendrite=[]
    wNumberOfSpotsPerSpine=[]
    wCompleteShortestDistanceToFilament=[]
    wCompleteShortestDistanceToALLFilaments=[]
    wCompleteShortestDistanceToSpine=[]
    wNewSpotsOnFilamentAll=[]
    wNewSpotsOnFilament=[]
    wNewSpotsOnFilamentRadius=[]
    wNewSpotsOnFilamentTime=[]
    wCompleteSpotDistAlongFilamentStat=[]
    wCompleteSpotDistAlongFilamentPosX=[]
    wCompleteSpotDistAlongFilamentPosY=[]
    wCompleteBoutonDistAlongFilamentStat=[]
    wCompleteBoutonDistAlongFilamentPosX=[]
    wCompleteBoutonDistAlongFilamentPosY=[]
    wCompleteSpotsonSpine=[]
    wCompleteSpotsonDendrite=[]
    wCompleteSpotsonFilament=[]
    wCompleteNumberSpotsPerFilament=[]
    wCompleteNumberSpotsonSpinePerFilament=[]
    wCompleteNumberSpotsonDendritePerFilament=[]
    wFilamentIntensityMean=[]
    wFilamentIntensityCenter=[]
    IsRealFilament=[]
    wSpotsAllIndex=[]
    SegmentCountALL=0

    aFilamentIndex=0
    qIsSpines=False
    ###############################################################################
    ###############################################################################
    #Progress Bar for Dendrites
    # if vNumberOfFilaments>10:
    # Create the master object
    master = tk.Tk()
    # Create a progressbar widget
    progress_bar = ttk.Progressbar(master, orient="horizontal",
                                  mode="determinate", maximum=100, value=0)
    progress_bar2 = ttk.Progressbar(master, orient="horizontal",
                                  mode="determinate", maximum=100, value=0)
    # And a label for it
    label_1 = tk.Label(master, text="Dendrite Progress Bar ")
    label_2 = tk.Label(master, text="Filament Progress Bar ")
    # Use the grid manager
    label_1.grid(row=0, column=0,pady=10)
    label_2.grid(row=1, column=0,pady=10)

    progress_bar.grid(row=0, column=1)
    progress_bar2.grid(row=1, column=1)

    master.geometry('250x100')
    master.attributes("-topmost", True)
    #################################################################
    #Set input in center on screen
    # Gets the requested values of the height and widht.
    windowWidth = master.winfo_reqwidth()
    windowHeight = master.winfo_reqheight()
    # Gets both half the screen width/height and window width/height
    positionRight = int(master.winfo_screenwidth()/2 - windowWidth/2)
    positionDown = int(master.winfo_screenheight()/2 - windowHeight/2)
    # Positions the window in the center of the page.
    master.geometry("+{}+{}".format(positionRight, positionDown))
    ##################################################################
    # Necessary, as the master object needs to draw the progressbar widget
    # Otherwise, it will not be visible on the screen
    master.update()
    progress_bar['value'] = 0
    master.update()
    ###############################################################################
    ###############################################################################
    if vNumberOfFilaments>50:
        qisVisible=messagebox.askquestion("Processing Warning - Large Number of Filaments",
                                      'Do you wish to Hide Imaris Application?\n'
                                      ' This will increase processing speed\n''\n'
                                      'Close Progress window to CANCEL script')
        if qisVisible=='yes':
                vImarisApplication.SetVisible(0)

    try:
        ###############################################################################
        zEmptyfilaments=[]
        for aFilamentIndex in range(vNumberOfFilaments):
            vFilamentsRadius = vFilaments.GetRadii(aFilamentIndex)
            if len(vFilamentsRadius)==1:
                zEmptyfilaments.append(int(aFilamentIndex))
        vFilamentIds=[v for i,v in enumerate(vFilamentIds) if i not in zEmptyfilaments]

        ###############################################################################
        ###############################################################################
        #Loop each Filament
        for aFilamentIndex in range(vNumberOfFilaments):
            vFilamentsIndexT = vFilaments.GetTimeIndex(aFilamentIndex)
            vFilamentsXYZ = vFilaments.GetPositionsXYZ(aFilamentIndex)
            vFilamentsRadius = vFilaments.GetRadii(aFilamentIndex)
        #Test if the time point has empty filament matrix or filament start
        #point and nothing more
            if len(vFilamentsRadius)==1:
                continue
            vFilamentCountActual=vFilamentCountActual+1

            vFilamentsEdgesSegmentId = vFilaments.GetEdgesSegmentId(aFilamentIndex)
        #Find unique values of variable using set, the copnvert back to list
            vSegmentIds=list(set(vFilamentsEdgesSegmentId))
            vNumberOfDendriteBranches = len(vSegmentIds)#total number dendrite segments
            vNumberOfFilamentPoints= len(vFilamentsRadius)#including starting point
            vFilamentTimeIndex=[vFilamentsIndexT]*len(vFilamentsRadius)#for filament spot creation
            vFilamentsEdges = vFilaments.GetEdges(aFilamentIndex)
            vTypes = vFilaments.GetTypes(aFilamentIndex)
            vBeginningVertex = vFilaments.GetBeginningVertexIndex(aFilamentIndex)
            if max(vTypes)==1:
                qIsSpines=True
            #Get Filament stats
            vAllFilamentStatistics = vFilaments.GetStatistics()
            vAllFilamentStatNames = vAllFilamentStatistics.mNames
            vAllFilamentStatValues = vAllFilamentStatistics.mValues
            vAllFilamentStatIds = vAllFilamentStatistics.mIds
            vAllFilamentIndexDendriteLength=[i for i,val in enumerate(vAllFilamentStatNames)
                                              if val==('Dendrite Length')]
            if len(vAllFilamentIndexDendriteLength)>1:
                vAllFilamentDendriteLength=list(itemgetter(*vAllFilamentIndexDendriteLength)(vAllFilamentStatValues))
                vAllFilamentDendriteLengthIds=list(itemgetter(*vAllFilamentIndexDendriteLength)(vAllFilamentStatIds))
            else:
                vAllFilamentDendriteLength=[x[1] for x in enumerate(vAllFilamentStatValues)
                                        if x[0] in vAllFilamentIndexDendriteLength]
                vAllFilamentDendriteLengthIds=[x[1] for x in enumerate(vAllFilamentStatIds)
                                        if x[0] in vAllFilamentIndexDendriteLength]

            tmpUniq = {} # temp
            vAllFilamentDendriteLength = [tmpUniq.setdefault(i,i) for i in vAllFilamentDendriteLength if i not in tmpUniq]
            tmpUniq = {} # temp
            vAllFilamentDendriteLengthIds = [tmpUniq.setdefault(i,i) for i in vAllFilamentDendriteLengthIds if i not in tmpUniq]


        ###############################################################################
        ###############################################################################
        #Calculating Mean Intensity
            if vOptionIntensity==1:
            #Adjusting the All Filament Points that fall outside the edge of the volume for
            #Spot placement and calculation of Intensities
                xAdj = list(list(zip(*vFilamentsXYZ))[0])
                yAdj = list(list(zip(*vFilamentsXYZ))[1])
                zAdj = list(list(zip(*vFilamentsXYZ))[2])
                # xAdj=[i+0.001 if i <= vDataMin[0] else i for i in xAdj]
                # xAdj=[i-0.001 if i >= vDataMax[0] else i for i in xAdj]
                # xAdj=[i+0.001 if i <= vDataMin[1] else i for i in yAdj]
                # xAdj=[i-0.001 if i >= vDataMax[1] else i for i in yAdj]
                # xAdj=[i+0.001 if i <= vDataMin[2] else i for i in zAdj]
                # xAdj=[i-0.001 if i >= vDataMax[2] else i for i in zAdj]
                vFilamentsXYZAdj=[list(l) for l in zip(xAdj, yAdj, zAdj)]
                vOriginalSpotsFromFilament.Set(vFilamentsXYZAdj, vFilamentTimeIndex, vFilamentsRadius)

            #Get New adjusted spots intensity values
                vAllFilamentSpotsStatistics = vOriginalSpotsFromFilament.GetStatistics()
                vAllFilamentSpotsStatNames = vAllFilamentSpotsStatistics.mNames
                vAllFilamentSpotsStatValues = vAllFilamentSpotsStatistics.mValues
                vAllFilamentSpotsStatIds = vAllFilamentSpotsStatistics.mIds
                vAllFilamentSpotsIndexIntCnt=[i for i,val in enumerate(vAllFilamentSpotsStatNames)
                                              if val==('Intensity Center')]

                vAllFilamentSpotsIntCnt=list(itemgetter(*vAllFilamentSpotsIndexIntCnt)(vAllFilamentSpotsStatValues))
                vAllFilamentSpotsIndexIntMean=[i for i,val in enumerate(vAllFilamentSpotsStatNames)
                                              if val==('Intensity Mean')]
                vAllFilamentSpotsIntMean=list(itemgetter(*vAllFilamentSpotsIndexIntMean)(vAllFilamentSpotsStatValues))
                #for missing spots
                vAllFilamentSpotsIndexDiameter=[i for i,val in enumerate(vAllFilamentSpotsStatNames)
                                              if val==('Diameter X')]
                vAllFilamentSpotsIds=list(itemgetter(*vAllFilamentSpotsIndexDiameter)(vAllFilamentSpotsStatIds))

                vAllFilamentSpotsIdsIntensity=list(itemgetter(*vAllFilamentSpotsIndexIntCnt)(vAllFilamentSpotsStatIds))
        #Find Intensity spot Ids only
                vAllFilamentSpotsIdsIntensity=vAllFilamentSpotsIdsIntensity[0:int(len(vAllFilamentSpotsIdsIntensity)/(vSizeC))]

        ###############################################################################
                vAllFilamentSpotsIntCntChannels=[]
                vAllFilamentSpotsIntMeanChannels=[]
            #Split spot intensity on channel basis
                if vSizeC>1:
                    for c in range (vSizeC):
                        wNumber1=int(0*c+c*len(vAllFilamentSpotsIndexIntCnt)/vSizeC)
                        wNumber2=int(len(vAllFilamentSpotsIndexIntCnt)/vSizeC+len(vAllFilamentSpotsIndexIntCnt)/vSizeC*c)
                        vAllFilamentSpotsIntCntChannels.extend([vAllFilamentSpotsIntCnt[wNumber1:wNumber2]])
                        vAllFilamentSpotsIntMeanChannels.extend([vAllFilamentSpotsIntMean[wNumber1:wNumber2]])
                else:
                    vAllFilamentSpotsIntCntChannels.extend([vAllFilamentSpotsIntCnt[0:len(vAllFilamentSpotsIndexIntCnt)]])
                    vAllFilamentSpotsIntMeanChannels.extend([vAllFilamentSpotsIntMean[0:len(vAllFilamentSpotsIndexIntCnt)]])
        ###############################################################################
        ###############################################################################
    #Find Starting point and terminal point indices
    # Efficient Python program to print all non-
    # repeating elements.
            def firstNonRepeating(arr, n):
                global wFilamentTerminalPointIndex, x
                wFilamentTerminalPointIndex=[]
                # Insert all array elements in hash
                # table
                mp={}
                for i in range(n):
                    if arr[i] not in mp:
                        mp[arr[i]]=0
                    mp[arr[i]]+=1

                # Traverse through map only and
                for x in mp:
                    if (mp[x]== 1):
                        # print(x,end=" ")
                        wFilamentTerminalPointIndex.append(x)
            #Flatten Filament edges
            # arr = vFilamentsEdges1DAll=reduce(operator.concat, vFilamentsEdges)
            arr = reduce(operator.concat, vFilamentsEdges)

            n = len(arr)
        #run function firstNonRepeating to find Terminal Indices
            firstNonRepeating(arr, n)
        #Remove Beginning Vertex
            # wStartingIndex=[i for i in range(len(wFilamentTerminalPointIndex))
            #                                if wFilamentTerminalPointIndex[i] == vBeginningVertex]
            # del wFilamentTerminalPointIndex[[i for i in range(len(wFilamentTerminalPointIndex))
            #                                if wFilamentTerminalPointIndex[i] == vBeginningVertex][0]]

        # Find Branch point Indices
            wFilamentBranchPointIndex=[x for x, y in collections.Counter(arr).items() if y > 2]
        #Extract the Filament Point Position from the determined indices
            if len(wFilamentTerminalPointIndex) > 1:
                wFilamentTerminalPoints=list(itemgetter(*wFilamentTerminalPointIndex)(vFilamentsXYZ))
                if wFilamentBranchPointIndex!=[]:
                    wFilamentBranchPoints=list(itemgetter(*wFilamentBranchPointIndex)(vFilamentsXYZ))
            else:
                wFilamentTerminalPoints=[x[1] for x in enumerate(vFilamentsXYZ)
                              if x[0] in wFilamentTerminalPointIndex]
                if wFilamentBranchPointIndex!=[]:
                    wFilamentBranchPoints=[x[1] for x in enumerate(vFilamentsXYZ)
                              if x[0] in wFilamentBranchPointIndex]
        ###############################################################################
        ###############################################################################




            vAllSegmentsPerFilamentRadiusWorkingInserts=[]
            vAllSegmentsPerFilamentPositionsWorkingInserts=[]
            vAllSegmentsTypesPerFilamentWorkingInserts=[]
            vAllSegmentIdsPerFilamentInserts=[]
            vAllNewSpotsBoutonsPositionXYZ=[]
            vAllNewSpotsBoutonsRadius=[]
            vSegmentBranchLength=[]
            vStatisticBoutonWidth=[]
            wDendriteSegmentIds=[]
            wSpineSegmentIds=[]
            wShortestDistanceToSegment=[]
            zReOrderedFilamentPointIndex=[]
            zReOrderedFilamentPositions=[]
            zReOrderedFilamentRadius=[]
            zReOrderedFilamentPointIndexWorking=[]
            zReOrderedFilamentPositionsWorking=[]
            zReOrderedFilamentRadiusWorking=[]
            zReorderedvSegmentIds=[]
            zReorderedvSegmentType=[]
            wSpotsAllIndexPerFilament=[]
            wCompleteSpotDistAlongFilamentStatWorking=[]
            vBranchIndex=0
            dcount=0
            scount=0
        #Loop through dendrite segments, terminal segements and spine segments
            for vBranchIndex in range (vNumberOfDendriteBranches):
                SegmentCountALL=SegmentCountALL+1
                zReOrderedFilamentPointIndexWorking=[]
                zReOrderedFilamentPositionsWorking=[]
                zReOrderedFilamentRadiusWorking=[]
        #Set the ID for dendrite segment
                vSegmentIdWorking = vSegmentIds[vBranchIndex]
                #Isolate all edges for the working segment
                vSegmentWorkingPointIndex=[i for i in range(len(vFilamentsEdgesSegmentId))
                                           if vFilamentsEdgesSegmentId[i] == vSegmentIdWorking]
                if len(vSegmentWorkingPointIndex)>1:
                    vSegmentEdgesWorking=list(itemgetter(*vSegmentWorkingPointIndex)(vFilamentsEdges))
                else:
                    vSegmentEdgesWorking=[x[1] for x in enumerate(vFilamentsEdges)
                                  if x[0] in vSegmentWorkingPointIndex]

                #Find unique edge indices using "set" and convert back to list
                vEdgesUniqueWorking=list(set(x for l in vSegmentEdgesWorking for x in l))

                #Collate all segmentsIds
                wAllSegmentIds.append(vSegmentIdWorking)
           #Find current Working Dendrite segment parts
                vSegmentPositionsWorking=list(itemgetter(*vEdgesUniqueWorking)(vFilamentsXYZ))
                vSegmentRadiusWorking=list(itemgetter(*vEdgesUniqueWorking)(vFilamentsRadius))
                vSegmentTypesWorking=list(itemgetter(*vEdgesUniqueWorking)(vTypes))

                #Unit length number of points that make it up
                vSegmentBranchLength.append(len(vEdgesUniqueWorking))

                #Collate all SegmentId by Type (dendrtie or spine)
                if max(vSegmentTypesWorking)==0:
                    wDendriteSegmentIds.append(vSegmentIdWorking)
                else:
                    wSpineSegmentIds.append(vSegmentIdWorking)


        ###############################################################################
        #Calculate the  Intensity values on per dendrite basis
        #generate dendrite intensity values by averageing all spots for each segment, per channel
                if vOptionIntensity==1:
                    vSegmentIndexWorking=[]
                    for i in range (len(vSegmentRadiusWorking)):
                        xFindX = list(list(zip(*[(index_,sub_list.index(vSegmentPositionsWorking[i][0]))\
                             for index_, sub_list in enumerate(vFilamentsXYZ)\
                             if vSegmentPositionsWorking[i][0] in sub_list]))[0])
                        xFindY = list(list(zip(*[(index_,sub_list.index(vSegmentPositionsWorking[i][1]))\
                             for index_, sub_list in enumerate(vFilamentsXYZ)\
                             if vSegmentPositionsWorking[i][1] in sub_list]))[0])
                        xFindZ = list(list(zip(*[(index_,sub_list.index(vSegmentPositionsWorking[i][2]))\
                             for index_, sub_list in enumerate(vFilamentsXYZ)\
                             if vSegmentPositionsWorking[i][2] in sub_list]))[0])
                        vSegmentIndexWorking.append(max(list(set(xFindX) & set(xFindY) & set(xFindZ))))

                    #ids of the original spots
                    xFinalIds=[vAllFilamentSpotsIds[i] for i in vSegmentIndexWorking]
                    #match that id with id from FilamentSpotsID list, return index
                    xFinalFilamentIndex=([i for i, e in enumerate(vAllFilamentSpotsIdsIntensity) if e in set(xFinalIds)])
                    if xFinalFilamentIndex==[]:
                        #grab last measured intensity and add that here
                        if vStatisticDendriteBranchIntCenter==[] or vStatisticSpineBranchIntCenter==[]:#first in the list
                            xFinalValue=0.0001#unique value likley to be found in real data
                            if max(vSegmentTypesWorking)==1:
                                qIsSpines=True
                                for t in range (vSizeC):
                                        vStatisticSpineBranchIntCenter.append(xFinalValue)
                                        vStatisticSpineBranchIntMean.append(xFinalValue)
                            else:
                                for t in range (vSizeC):
                                    vStatisticDendriteBranchIntCenter.append(xFinalValue)
                                    vStatisticDendriteBranchIntMean.append(xFinalValue)
                        else:
                            if max(vSegmentTypesWorking)==1:
                                qIsSpines=True
                                for t in range (vSizeC):
                                        vStatisticSpineBranchIntCenter.append(vStatisticSpineBranchIntCenter[-1])
                                        vStatisticSpineBranchIntMean.append(vStatisticSpineBranchIntMean[-1])
                            else:
                                for t in range (vSizeC):
                                    vStatisticDendriteBranchIntCenter.append(vStatisticDendriteBranchIntCenter[-1])
                                    vStatisticDendriteBranchIntMean.append(vStatisticDendriteBranchIntMean[-1])

                    #Collate Intensity measures
                    else:
                        if max(vSegmentTypesWorking)==1:
                            qIsSpines=True
                            for t in range (vSizeC):
                                vStatisticSpineBranchIntCenter.append(mean([vAllFilamentSpotsIntCntChannels[t][index] for index in xFinalFilamentIndex]))
                                vStatisticSpineBranchIntMean.append(mean([vAllFilamentSpotsIntMeanChannels[t][index] for index in xFinalFilamentIndex]))
                        else:
                            for t in range (vSizeC):
                                vStatisticDendriteBranchIntCenter.append(mean([vAllFilamentSpotsIntCntChannels[t][index] for index in xFinalFilamentIndex]))
                                vStatisticDendriteBranchIntMean.append(mean([vAllFilamentSpotsIntMeanChannels[t][index] for index in xFinalFilamentIndex]))

        ###############################################################################
        ###############################################################################
        #find gaps in the dendrite length and fill with extra spots
        #For bouton detect and Spots display
                if vOptionFilamentToSpotsFill==1 or vOptionFilamentBoutonDetection==1 or vOptionFilamentCloseToSpots==1 or vOptionIntensity==1:
        ###########################
        ###########################
        #ReOrder segment
                #Reordering
                #flattten list
                    zNum=reduce(operator.concat, vSegmentEdgesWorking)
                    #Test for perfect edge sequence, no reordereding needed
                    # sorted_list_diffs = sum(np.diff(sorted(np.unique(zNum).tolist())))
                    # if sorted_list_diffs == (len(np.unique(zNum).tolist()) - 1):
                    #     zReOrderedFilamentPointIndex.append(np.unique(zNum).tolist())
                    #     zReOrderedFilamentPositions.extend(vSegmentPositionsWorking)
                    #     continue
                    # if zNum == sorted(zNum):
                    #     zReOrderedFilamentRadiusWorking=vSegmentRadiusWorking[:]
                    #     zReOrderedFilamentPositionsWorking=vSegmentPositionsWorking[:]
                    #     zReorderedvSegmentIds.extend([vSegmentIdWorking]*len(vSegmentRadiusWorking))
                    #     zReorderedvSegmentType.extend([max(vSegmentTypesWorking)]*len(vSegmentRadiusWorking))
                    # else:
                    #find duplicates
                    zDup=[zNum[i] for i in range(len(zNum)) if not i == zNum.index(zNum[i])]
                    #find individuals - start and end index
                    zIndiv=list(set(zNum).difference(zDup))

                    zStartIndex=zIndiv[0]
                    zEndIndex=zIndiv[1]
                    zReOrderedFilamentPointIndexWorking.append(zStartIndex)
                    zReOrderedFilamentPositionsWorking.append(vFilamentsXYZ[zStartIndex])
                    zReOrderedFilamentRadiusWorking.append(vFilamentsRadius[zStartIndex])

                #start of loop for each dendrite segment
                    for k in range (len(vSegmentRadiusWorking)-1):
                        if k==0:
                            #find nested list index that contains StartIndex (5,1)--next point is (5,0)
                            #convert tuple to list
                            zEdgesNext=list(reduce(operator.concat, [(index_,sub_list.index(zStartIndex))\
                                 for index_, sub_list in enumerate(vSegmentEdgesWorking)\
                                 if zStartIndex in sub_list]))

                            #find next segment index delete previous one
                            if zEdgesNext[1]==1:
                                zNextSegmentIndex=vSegmentEdgesWorking[zEdgesNext[0]][0]#next index in sequence
                                vSegmentEdgesWorking.pop(zEdgesNext[0])#remove list of list
                            else:
                                zNextSegmentIndex=vSegmentEdgesWorking[zEdgesNext[0]][1]#next index in sequence
                                vSegmentEdgesWorking.pop(zEdgesNext[0])#remove list of list
                            #collate segment indices
                            zReOrderedFilamentPointIndexWorking.append(zNextSegmentIndex)
                            zReOrderedFilamentPositionsWorking.append(vFilamentsXYZ[zNextSegmentIndex])
                            zReOrderedFilamentRadiusWorking.append(vFilamentsRadius[zNextSegmentIndex])

                        else:
                           #find nested list index that contains NextIndex
                           #convert tuple to list
                            zEdgesNext=list(reduce(operator.concat, [(index_,sub_list.index(zNextSegmentIndex))\
                                 for index_, sub_list in enumerate(vSegmentEdgesWorking)\
                                 if zNextSegmentIndex in sub_list]))

                            if zEdgesNext[1]==1:
                                zNextSegmentIndex=vSegmentEdgesWorking[zEdgesNext[0]][0]#next index in sequence
                                vSegmentEdgesWorking.pop(zEdgesNext[0])#remove list of list
                            else:
                                zNextSegmentIndex=vSegmentEdgesWorking[zEdgesNext[0]][1]#next index in sequence
                                vSegmentEdgesWorking.pop(zEdgesNext[0])#remove list of list

                            zReOrderedFilamentPointIndexWorking.append(zNextSegmentIndex)
                            zReOrderedFilamentPositionsWorking.append(vFilamentsXYZ[zNextSegmentIndex])
                            zReOrderedFilamentRadiusWorking.append(vFilamentsRadius[zNextSegmentIndex])
                        zReorderedvSegmentIds.extend([vSegmentIdWorking]*len(vSegmentRadiusWorking))
                        zReorderedvSegmentType.extend([max(vSegmentTypesWorking)]*len(vSegmentRadiusWorking))

        ##############################################################################
        ##############################################################################
        #fill spots in filament point gaps
                    # if(zNum != sorted(zNum)):
                    vSegmentRadiusWorkingInserts=zReOrderedFilamentRadiusWorking[:]
                    vSegmentPositionsWorkingInserts=zReOrderedFilamentPositionsWorking[:]
                    if max(vSegmentTypesWorking)==0:
                        for loop in range (3):#loop through 3 times
                            i=0
                            while i<=(len(vSegmentPositionsWorkingInserts)-2):
                                vFillFilamentPairDist=pdist([vSegmentPositionsWorkingInserts[i],vSegmentPositionsWorkingInserts[i+1]])
                                vFillFilamentRadialSum=vSegmentRadiusWorkingInserts[i]+vSegmentRadiusWorkingInserts[i+1]
                                if vFillFilamentPairDist>vFillFilamentRadialSum:
                #insert Radius at next spot
                                    vSegmentRadiusWorkingInserts[i+1:i+1]=[vFillFilamentRadialSum/2]
                                    vSegmentPositionsWorkingInserts[i+1:i+1]=[np.divide(np.add(vSegmentPositionsWorkingInserts[i+1],
                                                                                                vSegmentPositionsWorkingInserts[i]),2).tolist()]
                                i=i+1
                    vAllSegmentsPerFilamentRadiusWorkingInserts.extend(vSegmentRadiusWorkingInserts)
                    vAllSegmentsPerFilamentPositionsWorkingInserts.extend(vSegmentPositionsWorkingInserts)
                    vAllSegmentsTypesPerFilamentWorkingInserts.extend([max(vSegmentTypesWorking)]*len(vSegmentRadiusWorkingInserts))
                    vAllSegmentIdsPerFilamentInserts.extend([vSegmentIdWorking]*len(vSegmentRadiusWorkingInserts))

        ###############################################################################
        ###############################################################################
        # Detect VaricositiesBoutons based on the radius of filled spot list
                if vOptionFilamentBoutonDetection==1 and max(vSegmentTypesWorking)==0:
                    peaks, _ = find_peaks(vSegmentRadiusWorkingInserts, height=vOptionBoutonHeight)
                    # peakwidths=peak_widths(vSegmentRadiusWorkingInserts,peaks)

                    #Grab Bouton dendrite working positions/radius from the detected Peak indices
                    if len(peaks)>1:
                        vNewSpotsBoutonsPositionXYZ=list(itemgetter(*peaks)(vSegmentPositionsWorkingInserts))
                        vNewSpotsBoutonsRadius=list(itemgetter(*peaks)(vSegmentRadiusWorkingInserts))
                    else:
                        vNewSpotsBoutonsPositionXYZ=[x[1] for x in enumerate(vSegmentPositionsWorkingInserts)
                                  if x[0] in peaks]
                        vNewSpotsBoutonsRadius=[x[1] for x in enumerate(vSegmentRadiusWorkingInserts)
                                  if x[0] in peaks]

            #Compile all boutons per dendrite for filament statistic
                    if peaks.size>0:
                        vStatisticFilamentBoutonsPerDendrite.append(len(vNewSpotsBoutonsRadius))
                    else:
                        vStatisticFilamentBoutonsPerDendrite.append(0)
                    vAllNewSpotsBoutonsPositionXYZ.extend(vNewSpotsBoutonsPositionXYZ)
                    vAllNewSpotsBoutonsRadius.extend(vNewSpotsBoutonsRadius)
         #############################
         # #Add Bouton Statistics to Filament object
            #Concatonate all boutons from all "real" filaments
                    if vBranchIndex==vNumberOfDendriteBranches-1:#Do when last dendrite branch is processed for filament
                        TotalSegmentIndex.extend(wAllSegmentIds)
                        #Add Spot for each bouton - ALL Filaments
                        vBoutonPositionAll.extend(vAllNewSpotsBoutonsPositionXYZ)
                        vBoutonRadiusAll.extend(vAllNewSpotsBoutonsRadius)
                        #number of Boutons per Filament for new Filament level stat
                        wCompleteFilamentNumberBoutons.append(len(vAllNewSpotsBoutonsRadius))

        ###############################################################################
        ###############################################################################
            #Spot to fIlament analysis
                if vOptionFilamentCloseToSpots==1:
                    if max(vSegmentTypesWorking)==1:
                        scount=scount+1
                    else:
                        dcount=dcount+1
            #Get all spots from same time index as current filament DO NOT need to do every branch index
                    vSpotsColocPositionsWorkingIndex = [i for i in range(len(vSpotsColocRadius))
                                            if vSpotsColocTimeIndices[i] == vFilamentsIndexT]
                    if len(vSpotsColocPositionsWorkingIndex)>1:
                        vSpotsColocPositionsWorking=list(itemgetter(*vSpotsColocPositionsWorkingIndex)(vSpotsColocPositionsXYZ))
                        vSpotsColocRadiusWorking=list(itemgetter(*vSpotsColocPositionsWorkingIndex)(vSpotsColocRadius))
                    else:
                        vSpotsColocPositionsWorking=[x[1] for x in enumerate(vSpotsColocPositionsXYZ)
                                  if x[0] in vSpotsColocPositionsWorkingIndex]
                        vSpotsColocRadiusWorking=[x[1] for x in enumerate(vSpotsColocRadius)
                                  if x[0] in vSpotsColocPositionsWorkingIndex]

            #Isolate spots on dendrites and spines
                    if max(vSegmentTypesWorking)==0:
                        #Find Spots "close" to current Filament min value per row in array
                        wSpotToFilamentDistanceArray=cdist(vSpotsColocPositionsWorking,vSegmentPositionsWorkingInserts)
                        #Adjust distance measure based on filament point radius and spot radius
                        wSpotToFilamentDistanceArray=wSpotToFilamentDistanceArray-vSegmentRadiusWorkingInserts-[max(vSpotsColocRadiusWorking[0])]*len(vSegmentRadiusWorkingInserts)
                        #per dendrite segment - dista of each spot to working dendrite segment
                        wShortestDistanceToSegment=wSpotToFilamentDistanceArray.min(axis=1)
                        wShortestDistanceToSegment[wShortestDistanceToSegment<0]=0
                        #SpotIndex for those the are less than threshold per dendrite segment
                        wSpotsIndexPerSegment = [i for i,val in enumerate(wShortestDistanceToSegment)
                                                  if val<=vOptionFilamentSpotThreshold]
                        #Collating dendrite segments
                        if dcount==1:
                            wCompleteShortestDistanceToFilament=wShortestDistanceToSegment
                        else:
                            wCompleteShortestDistanceToFilament=np.column_stack((wCompleteShortestDistanceToFilament,wShortestDistanceToSegment))

                        #Calculate spot density per segment
                        wCurrentIndexDendrite=[i for i,val in enumerate(vAllFilamentDendriteLengthIds)
                                                  if val==vSegmentIdWorking]
                        wCurrentDendriteLength=[x[1] for x in enumerate(vAllFilamentDendriteLength)
                                                if x[0] in wCurrentIndexDendrite]
                        #QUantify spots per dendrite
                        wNumberOfSpotsPerDendrite.append(np.count_nonzero(wShortestDistanceToSegment <= vOptionFilamentSpotThreshold))
                        vAllColocDensityPerDendrite.append(np.count_nonzero(wShortestDistanceToSegment <= vOptionFilamentSpotThreshold)/wCurrentDendriteLength[0]*10)
                    else:
                        #Find Spots "close" to current Filament min value per row in array
                        wSpotToFilamentDistanceArray=cdist(vSpotsColocPositionsWorking,vSegmentPositionsWorkingInserts)
                        #Adjust distance measure based on filament point radius and spot radius
                        wSpotToFilamentDistanceArray=wSpotToFilamentDistanceArray-vSegmentRadiusWorkingInserts-[max(vSpotsColocRadiusWorking[0])]*len(vSegmentRadiusWorkingInserts)
                        #per dendrite segment - dista of each spot to working dendrite segment
                        wShortestDistanceToSegment=wSpotToFilamentDistanceArray.min(axis=1)
                        wShortestDistanceToSegment[wShortestDistanceToSegment<0]=0
                        #SpotIndex for those the are less than threshold per dendrite segment
                        wSpotsIndexPerSegment = [i for i,val in enumerate(wShortestDistanceToSegment)
                                                  if val<=vOptionFilamentSpotThreshold]
                        #Collating spine segments
                        if scount==1:
                            wCompleteShortestDistanceToSpine=wShortestDistanceToSegment
                        else:
                            wCompleteShortestDistanceToSpine=np.column_stack((wCompleteShortestDistanceToSpine,wShortestDistanceToSegment))
                        #Quantify spot per spine
                        wNumberOfSpotsPerSpine.append(np.count_nonzero(wShortestDistanceToSegment <= vOptionFilamentSpotThreshold))

                    wShortestDistanceToSegment=[]
                    wSpotToFilamentDistanceArray=[]
                    wSpotsAllIndex.extend(wSpotsIndexPerSegment)
                    wSpotsAllIndexPerFilament.extend(wSpotsIndexPerSegment)
                    wSpotsIndexPerSegment=[]

        #Progress bar for dendrite segments
                progress_bar['value'] = int((vBranchIndex+1)/vNumberOfDendriteBranches*100) #  % out of 100
                master.update()

        ###############################################################################
        ###############################################################################
        #After Each Filament
        #Find distance along Filament for all boutons
        #     if vOptionFilamentBoutonDetection==1 and any(vStatisticFilamentBoutonsPerDendrite):
        #         wNewFilamentsEdges=list(vFilamentsEdges)
        #         wNewFilamentsRadius=list(vFilamentsRadius)
        #         wNewFilamentsXYZ=list(vFilamentsXYZ)
        #         wNewFilamentsTypes=list(vTypes)
        #         #Create array of distance measures
        #         vAllNewSpotsBoutonsPositionXYZ=[[(i-.01) for i in row] for row in vAllNewSpotsBoutonsPositionXYZ]

        #         wSpotToAllFilamentDistanceArray=cdist(vAllNewSpotsBoutonsPositionXYZ,vFilamentsXYZ)
        #         #Find Closet distance to nearest Filament point
        #         wSpotsFilamentClosestDistance=wSpotToAllFilamentDistanceArray.min(axis=1)
        #         #For each spot, find index on filament of closest point
        #         wSpotsFilamentClosestDistancePointIndex=np.argmin(wSpotToAllFilamentDistanceArray, axis=1)
        #         wSpotsIndex = [i for i,val in enumerate(wSpotsFilamentClosestDistance)
        #                                       if val<=vOptionFilamentSpotThreshold]
        #         #loop for each spot within threshold
        #         #append new filament and create list of new spots
        #         for i in range (len(wSpotsIndex)):
        #             wNewSpotsOnFilament.append(vAllNewSpotsBoutonsPositionXYZ[wSpotsIndex[i]])
        #             wNewSpotsOnFilamentRadius.append(vAllNewSpotsBoutonsRadius[wSpotsIndex[i]])
        #             wNewFilamentsXYZ.append(vAllNewSpotsBoutonsPositionXYZ[wSpotsIndex[i]])
        #             wNewFilamentsRadius.append(1)
        #             wNewFilamentsEdges.append([wSpotsFilamentClosestDistancePointIndex[wSpotsIndex[i]],len(vFilamentsRadius)+i])
        #             wNewFilamentsTypes.append(1)

        #         vNewFilament=vImarisApplication.GetFactory().CreateFilaments()
        #         vNewFilament.AddFilament(wNewFilamentsXYZ, wNewFilamentsRadius, wNewFilamentsTypes, wNewFilamentsEdges, vFilamentsIndexT)
        #         vNewFilament.SetBeginningVertexIndex(0, 0)

        # #Grab New Filament Spine Statistics for attachment point distance.
        #         vNewFilamentStatistics = vNewFilament.GetStatistics()
        #         vNewFilamentStatNames = vNewFilamentStatistics.mNames
        #         vNewFilamentStatValues = vNewFilamentStatistics.mValues
        #         vNewFilamentSpineAttPtDistIndex=[i for i,val in enumerate(vNewFilamentStatNames)
        #                                           if val==('Spine Attachment Pt Distance')]
        #         vNewFilamentSpineAttPtPosXIndex=[i for i,val in enumerate(vNewFilamentStatNames)
        #                                           if val==('Spine Attachment Pt Position X')]
        #         vNewFilamentSpineAttPtPosYIndex=[i for i,val in enumerate(vNewFilamentStatNames)
        #                                           if val==('Spine Attachment Pt Position Y')]
        #         if len(vNewFilamentSpineAttPtDistIndex)>1:
        #             vNewFilamentSpineAttPtDist=list(itemgetter(*vNewFilamentSpineAttPtDistIndex)(vNewFilamentStatValues))
        #             vNewFilamentSpineAttPtPosX=list(itemgetter(*vNewFilamentSpineAttPtPosXIndex)(vNewFilamentStatValues))
        #             vNewFilamentSpineAttPtPosY=list(itemgetter(*vNewFilamentSpineAttPtPosYIndex)(vNewFilamentStatValues))
        #         else:
        #             vNewFilamentSpineAttPtDist=[x[1] for x in enumerate(vNewFilamentStatValues)
        #                                    if x[0] in vNewFilamentSpineAttPtDistIndex]
        #             vNewFilamentSpineAttPtPosX=[x[1] for x in enumerate(vNewFilamentStatValues)
        #                                     if x[0] in vNewFilamentSpineAttPtPosXIndex]
        #             vNewFilamentSpineAttPtPosY=[x[1] for x in enumerate(vNewFilamentStatValues)
        #                                     if x[0] in vNewFilamentSpineAttPtPosYIndex]

        #         #Collate all spots for each filament
        #         wCompleteBoutonDistAlongFilamentStat.append(vNewFilamentSpineAttPtDist)
        #         wCompleteBoutonDistAlongFilamentPosX.append(vNewFilamentSpineAttPtPosX)
        #         wCompleteBoutonDistAlongFilamentPosY.append(vNewFilamentSpineAttPtPosY)

        ###############################################################################
        ###############################################################################
        #After each Filament
        ###############################################################################
        # #Find Spot close to filament and measure distance along path to starting point
        # #Make spot position conect to filament as spine attachment point
            if vOptionFilamentCloseToSpots==1:
                #find duplicates and remove
                wSpotsAllIndexPerFilament=list(set(wSpotsAllIndexPerFilament))
                #number spots on dendrites and spines together
                wCompleteNumberSpotsPerFilament.append(len(wSpotsAllIndexPerFilament))
                #Calculate number of spots on spines and dendrites Per Filament
                wCompleteNumberSpotsonSpinePerFilament.append(sum(wNumberOfSpotsPerSpine))
                wCompleteNumberSpotsonDendritePerFilament.append(sum(wNumberOfSpotsPerDendrite))

                if wSpotsAllIndexPerFilament!=[]:
                    for i in range (len(wSpotsAllIndexPerFilament)):
                        wNewSpotsOnFilament.append(vSpotsColocPositionsWorking[wSpotsAllIndexPerFilament[i]])
                        wNewSpotsOnFilamentAll.append(vSpotsColocPositionsWorking[wSpotsAllIndexPerFilament[i]])
                        wNewSpotsOnFilamentRadius.append(vSpotsColocRadiusWorking[wSpotsAllIndexPerFilament[i]])

                    if vBeginningVertex !=-1:
                        wNewFilamentsEdges=list(vFilamentsEdges)
                        wNewFilamentsRadius=list(vFilamentsRadius)
                        wNewFilamentsXYZ=list(vFilamentsXYZ)
                        wNewFilamentsTypes=list(vTypes)

                        #Create array of distance measures to original filament points
                        wSpotToAllFilamentDistanceArrayOriginal=cdist(vSpotsColocPositionsWorking,vFilamentsXYZ)
                        wSpotToAllFilamentDistanceArrayOriginal=wSpotToAllFilamentDistanceArrayOriginal- vFilamentsRadius -[max(vSpotsColocRadiusWorking[0])]*len(vFilamentsRadius)

                        #For each spot, find index on filament of closest point
                        wSpotsFilamentClosestDistancePointIndex=np.argmin(wSpotToAllFilamentDistanceArrayOriginal, axis=1)

                        #test is spine attachment point is branch point, if so add one
                        for i in range (len(wSpotsFilamentClosestDistancePointIndex)):
                            if wSpotsFilamentClosestDistancePointIndex[i] in wFilamentBranchPointIndex or wSpotsFilamentClosestDistancePointIndex[i] in wFilamentTerminalPointIndex:
                                wSpotNearest = cdist([vSpotsColocPositionsWorking[i]],vFilamentsXYZ)
                                wSpotNearest = wSpotNearest - vFilamentsRadius -[max(vSpotsColocRadiusWorking[0])]*len(vFilamentsRadius)
                                wSpotsNearestIndex=np.argpartition(wSpotNearest, 2)
                                wSpotsFilamentClosestDistancePointIndex[i]=wSpotsNearestIndex[0][1]
                                if wSpotsFilamentClosestDistancePointIndex[i] in wFilamentBranchPointIndex or wSpotsFilamentClosestDistancePointIndex[i] in wFilamentTerminalPointIndex:
                                    wSpotsFilamentClosestDistancePointIndex[i]=wSpotsNearestIndex[0][2]
                                if wSpotsFilamentClosestDistancePointIndex[i] in wFilamentBranchPointIndex or wSpotsFilamentClosestDistancePointIndex[i] in wFilamentTerminalPointIndex:
                                    wSpotsFilamentClosestDistancePointIndex[i]=wSpotsNearestIndex[0][3]

                        #loop for each spot within threshold
                        #append new filament and create list of new spots
                        for i in range (len(wSpotsAllIndexPerFilament)):
                            wNewFilamentsXYZ.append(vSpotsColocPositionsWorking[wSpotsAllIndexPerFilament[i]])
                            wNewFilamentsRadius.append(1)
                            wNewFilamentsEdges.append([wSpotsFilamentClosestDistancePointIndex[wSpotsAllIndexPerFilament[i]],len(vFilamentsRadius)+i])
                            wNewFilamentsTypes.append(1)

                        vNewFilament=vImarisApplication.GetFactory().CreateFilaments()
                        vNewFilament.AddFilament(wNewFilamentsXYZ, wNewFilamentsRadius, wNewFilamentsTypes, wNewFilamentsEdges, vFilamentsIndexT)
                        vNewFilament.SetBeginningVertexIndex(0, 0)

                #Grab New Filament Spine Statistics for attachment point distance.
                        vNewFilamentStatistics = vNewFilament.GetStatistics()
                        vNewFilamentStatNames = vNewFilamentStatistics.mNames
                        vNewFilamentStatValues = vNewFilamentStatistics.mValues
                        vNewFilamentStatIds = vNewFilamentStatistics.mIds
                        vNewFilamentSpineAttPtDistIndex=[i for i,val in enumerate(vNewFilamentStatNames)
                                                          if val==('Spine Attachment Pt Distance')]
                        vNewFilamentSpinePtPosXIndex=[i for i,val in enumerate(vNewFilamentStatNames)
                                                          if val==('Spine Terminal Pt Position X')]
                        if len(vNewFilamentSpineAttPtDistIndex)>1:
                            vNewFilamentSpineAttPtDist=list(itemgetter(*vNewFilamentSpineAttPtDistIndex)(vNewFilamentStatValues))
                            vNewFilamentSpinePtPosX=list(itemgetter(*vNewFilamentSpinePtPosXIndex)(vNewFilamentStatValues))
                            vNewFilamentStatIdsPosX=list(itemgetter(*vNewFilamentSpinePtPosXIndex)(vNewFilamentStatIds))
                            vNewFilamentStatIdsDist=list(itemgetter(*vNewFilamentSpineAttPtDistIndex)(vNewFilamentStatIds))
                        else:
                            vNewFilamentSpineAttPtDist=[x[1] for x in enumerate(vNewFilamentStatValues)
                                                    if x[0] in vNewFilamentSpineAttPtDistIndex]
                            vNewFilamentSpinePtPosX=[x[1] for x in enumerate(vNewFilamentStatValues)
                                                      if x[0] in vNewFilamentSpinePtPosXIndex]
                            vNewFilamentStatIdsDist=[x[1] for x in enumerate(vNewFilamentStatIds)
                                                    if x[0] in vNewFilamentSpineAttPtDistIndex]
                            vNewFilamentStatIdsPosX=[x[1] for x in enumerate(vNewFilamentStatIds)
                                                    if x[0] in vNewFilamentSpinePtPosXIndex]

                        #Collate all spots for each filament
                        for i in range (len(wSpotsAllIndexPerFilament)):
                            wCompleteSpotDistAlongFilamentStat.append(vNewFilamentSpineAttPtDist[vNewFilamentStatIdsDist.index(vNewFilamentStatIdsPosX[vNewFilamentSpinePtPosX.index(wNewSpotsOnFilament[i][0])])])
                            wCompleteSpotDistAlongFilamentStatWorking.append(vNewFilamentSpineAttPtDist[vNewFilamentStatIdsDist.index(vNewFilamentStatIdsPosX[vNewFilamentSpinePtPosX.index(wNewSpotsOnFilament[i][0])])])
                else:
                    vNewSpotsvNewSpotsAlongFilament = vImarisApplication.GetFactory().CreateSpots()
                    vNewSpotsvNewSpotsAlongFilament.SetName('NO Colocalized Spots -- FilamentId:' + str(vFilamentIds[vFilamentCountActual-1]))
                    vNewSpotsAnalysisFolder.AddChild(vNewSpotsvNewSpotsAlongFilament, -1)

            #################################################################################
                #Create a new Coloc Spots Object
                if len(wSpotsAllIndexPerFilament) != []:
                    vNewSpotsvNewSpotsAlongFilament = vImarisApplication.GetFactory().CreateSpots()
                    vNewSpotsvNewSpotsAlongFilament.SetName('Colocalized Spots -- FilamentId:' + str(vFilamentIds[vFilamentCountActual-1]))
                    vNewSpotsOnFilamentIndex=[vFilamentsIndexT]*len(wNewSpotsOnFilamentRadius)
                    zRandomColor=((random.uniform(0, 1)) * 256 * 256 * 256 )
                    vNewSpotsvNewSpotsAlongFilament.SetColorRGBA(zRandomColor)
                    vNewSpotsvNewSpotsAlongFilament.Set(wNewSpotsOnFilament, vNewSpotsOnFilamentIndex, [i[0] for i in wNewSpotsOnFilamentRadius])
                    vNewSpotsAnalysisFolder.AddChild(vNewSpotsvNewSpotsAlongFilament, -1)
                    vImarisApplication.GetSurpassScene().AddChild(vNewSpotsAnalysisFolder, -1);
        ############################################
                    ##ADD new Stat distance to starting points to new Spots objects
                    vNewSpotsOnFilamentIndex=[vFilamentsIndexT+1]*len(wSpotsAllIndexPerFilament)
                    vSpotsvIds=list(range(len(wSpotsAllIndexPerFilament)))
                    vSpotsStatUnits=['um']*len(wSpotsAllIndexPerFilament)
                    vSpotsStatFactors=(['Spot']*len(wSpotsAllIndexPerFilament), [str(x) for x in vNewSpotsOnFilamentIndex] )
                    vSpotsStatFactorName=['Category','Time']

                #Combine distance measure per filament (spine and dendrite)
                    if qIsSpines==True:
                        wCompleteFinalperFilament=np.column_stack((wCompleteShortestDistanceToFilament,wCompleteShortestDistanceToSpine))
                    else:
                        wCompleteFinalperFilament=wCompleteShortestDistanceToFilament
                    #Collate each Filament together for closest distance to all spots
                    if vFilamentCountActual==1:
                        wCompleteShortestDistanceToALLFilaments=wCompleteFinalperFilament
                    else:
                        wCompleteShortestDistanceToALLFilaments=np.column_stack((wCompleteShortestDistanceToALLFilaments,wCompleteFinalperFilament))


                    if len(wCompleteSpotDistAlongFilamentStatWorking) == 0:
                        #find shortest distance for Coloc spots to Dendrite
                        if SegmentCountALL>1:
                            vColocSpotToFilamentDistanceOnly = wCompleteFinalperFilament.min(axis=1)[wCompleteFinalperFilament.min(axis=1) <= vOptionFilamentSpotThreshold].tolist()
                        else:
                            vColocSpotToFilamentDistanceOnly = wCompleteFinalperFilament[wCompleteFinalperFilament<=vOptionFilamentSpotThreshold].tolist()
                        vSpotsStatNames=[' Shortest Distance to Filament']*len(wSpotsAllIndexPerFilament)
                        vNewSpotsvNewSpotsAlongFilament.AddStatistics(vSpotsStatNames, vColocSpotToFilamentDistanceOnly,
                                                      vSpotsStatUnits, vSpotsStatFactors,
                                                      vSpotsStatFactorName, vSpotsvIds)
                    else:
                        vSpotsStatNames=[' Distance to Starting Point']*len(wSpotsAllIndexPerFilament)
                        vNewSpotsvNewSpotsAlongFilament.AddStatistics(vSpotsStatNames, wCompleteSpotDistAlongFilamentStatWorking,
                                                  vSpotsStatUnits, vSpotsStatFactors, vSpotsStatFactorName, vSpotsvIds)
                        if SegmentCountALL>1:
                            vColocSpotToFilamentDistanceOnly = wCompleteFinalperFilament.min(axis=1)[wCompleteFinalperFilament.min(axis=1) <= vOptionFilamentSpotThreshold].tolist()
                        else:
                            vColocSpotToFilamentDistanceOnly = wCompleteFinalperFilament[wCompleteFinalperFilament<=vOptionFilamentSpotThreshold].tolist()
                        vSpotsStatNames=[' Shortest Distance to Filament']*len(vColocSpotToFilamentDistanceOnly)
                        vNewSpotsvNewSpotsAlongFilament.AddStatistics(vSpotsStatNames, vColocSpotToFilamentDistanceOnly,
                                                      vSpotsStatUnits, vSpotsStatFactors,
                                                      vSpotsStatFactorName, vSpotsvIds)
                        # if scount>1:
                        #     vColocSpotToSpineDistanceOnly = wCompleteShortestDistanceToSpine.min(axis=1)[wCompleteShortestDistanceToSpine.min(axis=1) <= vOptionFilamentSpotThreshold].tolist()
                        # else:
                        #     vColocSpotToSpineDistanceOnly = wCompleteShortestDistanceToSpine[wCompleteShortestDistanceToSpine<=vOptionFilamentSpotThreshold].tolist()
                        # vSpotsStatNames=[' Shortest Distance to Spine']*len(wSpotsAllIndexPerFilament)
                        # vNewSpotsvNewSpotsAlongFilament.AddStatistics(vSpotsStatNames, vColocSpotToSpineDistanceOnly,
                        #                               vSpotsStatUnits, vSpotsStatFactors,
                        #                               vSpotsStatFactorName, vSpotsvIds)

                wSpotsAllIndexPerFilament=[]
                wNewSpotsOnFilamentRadius=[]
                wNewSpotsOnFilament=[]

        ###############################################################################
        ###############################################################################
        #After Each Filament collate spots to Display
        # Convert the Filament points into Spots
            if vOptionFilamentToSpots==1:# and vOptionFilamentToSpotsMerge==0:
                vNewSpotsDendrites = vImarisApplication.GetFactory().CreateSpots()
                vNewSpotsSpines = vImarisApplication.GetFactory().CreateSpots()

                for c  in range (2): #loop twice for each filamant, 0=dendrite 1=spine, and generate a
                    if vOptionFilamentToSpotsFill==0:
                        #find index for dendrites and spines
                        vTypeIndex=[i for i,val in enumerate(vTypes) if val==c]
                       #Grab all type object from Filament object
                        vSegmentPositionsWorking=[vFilamentsXYZ[i] for i in vTypeIndex]
                        vSegmentRadiusWorking=[vFilamentsRadius[i] for i in vTypeIndex]
                        vDendritevTypesWorking=[vTypes[i] for i in vTypeIndex]
                        vTimeIndex=[vFilamentsIndexT]*len(vSegmentRadiusWorking)
                    else:#Use Filled spots for display
                        vTypeIndex=[i for i,val in enumerate(vAllSegmentsTypesPerFilamentWorkingInserts) if val==c]
                    #Grab all type object from Filament object
                        vSegmentPositionsWorking=[vAllSegmentsPerFilamentPositionsWorkingInserts[i] for i in vTypeIndex]
                        vSegmentRadiusWorking=[vAllSegmentsPerFilamentRadiusWorkingInserts[i] for i in vTypeIndex]
                        vDendritevTypesWorking=[vAllSegmentsTypesPerFilamentWorkingInserts[i] for i in vTypeIndex]
                        vTimeIndex=[vFilamentsIndexT]*len(vSegmentRadiusWorking)

                    #Collate all filaments into one
                    if vOptionFilamentToSpotsMerge==1:
                        vTotalSpotsDendrite.extend(vSegmentPositionsWorking)
                        vTotalSpotsDendriteRadius.extend(vSegmentRadiusWorking)
                        vTotalSpotsDendriteTime.extend(vTimeIndex)
                        if c==1 and vSegmentPositionsWorking != []:
                            qSpinesPresent=True
                            vTotalSpotsSpine.extend(vSegmentPositionsWorking)
                            vTotalSpotsSpineRadius.extend(vSegmentRadiusWorking)
                            vTotalSpotsSpineTime.extend(vTimeIndex)

                    if vOptionFilamentToSpotsMerge==0:
                        if c==0: #Do first look for dendrites
                            vNewSpotsDendrites.Set(vSegmentPositionsWorking, vTimeIndex, vSegmentRadiusWorking)
                            zRandomColor=((random.uniform(0, 1)) * 256 * 256 * 256 )
                            vNewSpotsDendrites.SetColorRGBA(zRandomColor)
                            vNewSpotsDendrites.SetName(str(vFilaments.GetName())+" dendrite_ID:"+ str(vFilamentIds[vFilamentCountActual-1]))
                            #Add new surface to Surpass Scene
                            vNewSpotsDendrites.SetVisible(0)
                            vNewSpotsDendritesFolder.AddChild(vNewSpotsDendrites, -1)
                        else:
                            if qIsSpines==True:#test second loop if spines exist, if not do not make spine spots object
                                vNewSpotsSpines.Set(vSegmentPositionsWorking, vTimeIndex, vSegmentRadiusWorking)
                                zRandomColor=((random.uniform(0, 1)) * 256 * 256 * 256 )
                                vNewSpotsSpines.SetColorRGBA(zRandomColor)
                                vNewSpotsSpines.SetName(str(vFilaments.GetName())+" Spine_ID:"+ str(vFilamentIds[vFilamentCountActual-1]))
                                vNewSpotsSpines.SetVisible(0)
                                vNewSpotsSpinesFolder.AddChild(vNewSpotsSpines, -1)

                        #After the last Spot creation Place the folders
                        if aFilamentIndex+1==vNumberOfFilaments:
                            vImarisApplication.GetSurpassScene().AddChild(vNewSpotsDendritesFolder, -1)
                            if qIsSpines == True:
                                vImarisApplication.GetSurpassScene().AddChild(vNewSpotsSpinesFolder, -1)

        ###############################################################################
        ###############################################################################
            #After each filament
            #Find overall Filament Intensity from SPots vNewSpotsDendrites
            if vOptionIntensity==1:
                vNewSpotsDendrites = vImarisApplication.GetFactory().CreateSpots()
                vTimeIndex=[vFilamentsIndexT]*len(vAllSegmentsPerFilamentRadiusWorkingInserts)
                vNewSpotsDendrites.Set(vAllSegmentsPerFilamentPositionsWorkingInserts, vTimeIndex, vAllSegmentsPerFilamentRadiusWorkingInserts)
                vNewSpotsFilamentStatistics = vNewSpotsDendrites.GetStatistics()
                vNewSpotsFilamentStatNames = vNewSpotsFilamentStatistics.mNames
                vNewSpotsFilamentStatValues = vNewSpotsFilamentStatistics.mValues
                vNewSpotsFilamentIndexCenter=[i for i,val in enumerate(vNewSpotsFilamentStatNames)
                                                  if val==('Intensity Mean')]
                vNewSpotsFilamentIndexMean=[i for i,val in enumerate(vNewSpotsFilamentStatNames)
                                                  if val==('Intensity Center')]
                vNewSpotsIntensityMean=list(itemgetter(*vNewSpotsFilamentIndexMean)(vNewSpotsFilamentStatValues))
                vNewSpotsIntensityCenter=list(itemgetter(*vNewSpotsFilamentIndexCenter)(vNewSpotsFilamentStatValues))

        #Spilt Intensity by channels and calculate average
                if vSizeC>1:
                    for c in range (vSizeC):
                        wNumber1=int( c*len(vNewSpotsFilamentIndexMean)/vSizeC)
                        wNumber2=int(len(vNewSpotsFilamentIndexMean)/vSizeC+len(vNewSpotsFilamentIndexMean)/vSizeC*c)
                        wFilamentIntensityCenter.append(mean(vNewSpotsIntensityCenter[wNumber1:wNumber2]))
                        wFilamentIntensityMean.append(mean(vNewSpotsIntensityMean[wNumber1:wNumber2]))
                else:
                    wFilamentIntensityCenter.append(mean(vNewSpotsIntensityCenter[0:len(vNewSpotsFilamentIndexMean)]))
                    wFilamentIntensityMean.append(mean(vNewSpotsIntensityMean[0:len(vNewSpotsFilamentIndexMean)]))

        ###############################################################################
        ###############################################################################
        #After Each Filament collate SegmentIds fro dendrites and spines
            wCompleteDendriteSegmentIds.extend(wDendriteSegmentIds)
            wCompleteSpineSegmentIds.extend(wSpineSegmentIds)
            wCompleteFilamentTimeIndex.extend([vFilamentsIndexT+1]*vFilamentCountActual)
            wCompleteDendriteTimeIndex.extend([vFilamentsIndexT+1]*len(wDendriteSegmentIds))
            wCompleteSpineTimeIndex.extend([vFilamentsIndexT+1]*len(wSpineSegmentIds))

        ###############################################################################
        ###############################################################################
            progress_bar2['value'] = int((aFilamentIndex+1)/vNumberOfFilaments*100) #  % out of 100
            master.update()
        master.destroy()
        master.mainloop()
        ###############################################################################
        ###############################################################################
        #After last Filament in Bouton Statistics
        #create new Bouton spot object and Filament Statistic
        if vOptionFilamentBoutonDetection==1:
            if vAllNewSpotsBoutonsRadius==[]:
                vNewSpotsBoutons.SetName(' NO Boutons Found')
                vNewSpotsBoutonsTimeIndex=[vFilamentsIndexT]*len(vBoutonRadiusAll)
                vNewSpotsBoutons.Set(vBoutonPositionAll, vNewSpotsBoutonsTimeIndex, vBoutonRadiusAll)
                vNewSpotsAnalysisFolder.AddChild(vNewSpotsBoutons, -1)
            else:
                vNewSpotsBoutonsTimeIndex=[vFilamentsIndexT]*len(vBoutonRadiusAll)
                vNewSpotsBoutons.SetName('Detected Varicosities (Boutons)')
                vNewSpotsBoutons.SetColorRGBA(18000)
                vNewSpotsBoutons.Set(vBoutonPositionAll, vNewSpotsBoutonsTimeIndex, vBoutonRadiusAll)
                vNewSpotsAnalysisFolder.AddChild(vNewSpotsBoutons, -1)

                # #ADD Spot to Filament Distance statistic.
                # vSpotsvIds=list(range(len(vBoutonRadiusAll)))
                # vSpotsStatUnits=['um']*len(vBoutonRadiusAll)
                # vSpotsStatFactors=(['Spot']*len(vBoutonRadiusAll),
                #                       ['1']*(len(vBoutonRadiusAll)))
                # vSpotsStatFactorName=['Category','Time']
                # vSpotsStatNames=[' Distance to StartingPoint']*len(vBoutonRadiusAll)
                # vNewSpotsBoutons.AddStatistics(vSpotsStatNames, list(itertools.chain(*wCompleteBoutonDistAlongFilamentStat)),
                #                               vSpotsStatUnits, vSpotsStatFactors,
                #                               vSpotsStatFactorName, vSpotsvIds)

        ###############################################################################
            #Add Filament Bouton Statistics

            vFilamentStatvIds=list(range(len(vAllFilamentDendriteLength)))
            vFilamentStatUnits=['']*(len(vAllFilamentDendriteLength))
            vFilamentStatFactors=(['Dendrite']*len(vAllFilamentDendriteLength), [str(x) for x in wCompleteDendriteTimeIndex] )
            vFilamentStatFactorName=['Category','Time']
        #######################
            vFilamentStatNames=[' Dendrite Bouton Number']*(len(vAllFilamentDendriteLength))
            vFilaments.AddStatistics(vFilamentStatNames, vStatisticFilamentBoutonsPerDendrite,
                                  vFilamentStatUnits, vFilamentStatFactors,
                                  vFilamentStatFactorName, wCompleteDendriteSegmentIds)
        #######################
            vFilamentStatUnits=['']*(len(vAllFilamentDendriteLength))
            vNewStatBoutonDensityPerSegment=[vStatisticFilamentBoutonsPerDendrite[i] / vAllFilamentDendriteLength[i] for i in range(len(vAllFilamentDendriteLength))]
            vFilamentStatNames=[' Dendrite Bouton Density (per um)']*(len(vNewStatBoutonDensityPerSegment))
            vFilaments.AddStatistics(vFilamentStatNames, vNewStatBoutonDensityPerSegment,
                                  vFilamentStatUnits, vFilamentStatFactors,
                                  vFilamentStatFactorName, wCompleteDendriteSegmentIds)
        ###############################################################################
        ###############################################################################
        #After last Filament in Scene generate intensity statistics
        if vOptionIntensity==1:
        #Reorder reshape intensity stats
            wCompleteDendriteBranchIntCenter = [[] for _ in range(vSizeC)]
            for index, item in enumerate(vStatisticDendriteBranchIntCenter):
                wCompleteDendriteBranchIntCenter[index % vSizeC].append(item)
            wCompleteDendriteBranchIntMean = [[] for _ in range(vSizeC)]
            for index, item in enumerate(vStatisticDendriteBranchIntMean):
                wCompleteDendriteBranchIntMean[index % vSizeC].append(item)

            if qIsSpines==True:
                wCompleteSpineBranchIntCenter = [[] for _ in range(vSizeC)]
                for index, item in enumerate(vStatisticSpineBranchIntCenter):
                    wCompleteSpineBranchIntCenter[index % vSizeC].append(item)
                wCompleteSpineBranchIntMean = [[] for _ in range(vSizeC)]
                for index, item in enumerate(vStatisticSpineBranchIntMean):
                    wCompleteSpineBranchIntMean[index % vSizeC].append(item)


        #######################
        #Test if the first value is equal to 0.0001 the fixed value if the first dendrite
        #has no intensity spots.
            if any(0.0001 in x for x in wCompleteDendriteBranchIntMean)==True:
                x=1
            if any(0.0001 in x for x in wCompleteSpineBranchIntMean)==True:
                x=1
        ########################
            vFilamentStatvIds=list(range(len(wCompleteDendriteSegmentIds)))
            vFilamentStatUnits=['']*(len(wCompleteDendriteSegmentIds))
            vFilamentStatFactors=(['Dendrite']*len(wCompleteDendriteSegmentIds), [str(x) for x in wCompleteDendriteTimeIndex] )

            vFilamentStatFactorName=['Category','Time']
        #######################
            for c in range (vSizeC):
                vFilamentStatNames=[' Dendrite Intensity Mean ch' + str(c+1)]*(len(wCompleteDendriteSegmentIds))
                vFilaments.AddStatistics(vFilamentStatNames, wCompleteDendriteBranchIntMean[c],
                                      vFilamentStatUnits, vFilamentStatFactors,
                                      vFilamentStatFactorName, wCompleteDendriteSegmentIds)
                #######################
                vFilamentStatNames=[' Dendrite Intensity Center ch' + str(c+1)]*(len(wCompleteDendriteSegmentIds))
                vFilaments.AddStatistics(vFilamentStatNames, wCompleteDendriteBranchIntCenter[c],
                                      vFilamentStatUnits, vFilamentStatFactors,
                                      vFilamentStatFactorName, wCompleteDendriteSegmentIds)
            if wSpineSegmentIds!=[]:
                vSpineStatvIds=list(range(len(wCompleteSpineSegmentIds)))
                vSpineStatUnits=['']*(len(wCompleteSpineSegmentIds))
                vSpineStatFactors=(['Spine']*len(wCompleteSpineSegmentIds), [str(x) for x in wCompleteSpineTimeIndex] )

                vSpineStatFactorName=['Category','Time']
                for c in range (vSizeC):
                    vFilamentStatNames=[' Spine Intensity Mean ch' + str(c+1)]*(len(wCompleteSpineSegmentIds))
                    vFilaments.AddStatistics(vFilamentStatNames, wCompleteSpineBranchIntMean[c],
                                          vSpineStatUnits, vSpineStatFactors,
                                          vSpineStatFactorName, wCompleteSpineSegmentIds)
                    #######################
                    vFilamentStatNames=[' Spine Intensity Center Mean ch' + str (c+1)]*(len(wCompleteSpineSegmentIds))
                    vFilaments.AddStatistics(vFilamentStatNames, wCompleteSpineBranchIntCenter[c],
                                          vSpineStatUnits, vSpineStatFactors,
                                          vFilamentStatFactorName, wCompleteSpineSegmentIds)

        ###############################################################################
        ###############################################################################
        #After last Filament - Processing end of Filament to Spots Merge
        if vOptionFilamentToSpots==1 and vOptionFilamentToSpotsMerge==1:
            vNewSpotsDendrites = vImarisApplication.GetFactory().CreateSpots()
            vNewSpotsDendrites.Set(vTotalSpotsDendrite, vTotalSpotsDendriteTime, vTotalSpotsDendriteRadius)
            vNewSpotsDendrites.SetName(str(vFilaments.GetName())+" All Dendrites")
            #Add new surface to Surpass Scene
            vNewSpotsDendritesFolder.AddChild(vNewSpotsDendrites, -1)
            vImarisApplication.GetSurpassScene().AddChild(vNewSpotsDendritesFolder, -1)
            if qSpinesPresent==True:
                vNewSpotsSpines = vImarisApplication.GetFactory().CreateSpots()
                vNewSpotsSpines.Set(vTotalSpotsSpine, vTotalSpotsSpineTime, vTotalSpotsSpineRadius)
                vNewSpotsSpines.SetName(str(vFilaments.GetName())+" All Spines")
                 #Add new surface to Surpass Scene
                vNewSpotsSpinesFolder.AddChild(vNewSpotsSpines, -1)
                vImarisApplication.GetSurpassScene().AddChild(vNewSpotsSpinesFolder, -1)
        ###############################################################################
        ###############################################################################
        #After the last Filament - Spot to fIlament Stats
        if vOptionFilamentCloseToSpots==1:
            #ADD Spot to Filament Distance statistic.
            vSpotsStatUnits=['um']*len(vSpotsColocRadius)
            vSpotsStatFactors=(['Spot']*len(vSpotsColocRadius), [str(x) for x in [i+1 for i in vSpotsColocTimeIndices]] )
            vSpotsStatFactorName=['Category','Time']
            vSpotsStatNames=[' Shortest Distance to Filament']*len(vSpotsColocRadius)
            vSpots.SetName(vSpots.GetName()+' -- Analyzed')

            wCompleteShortestDistanceStat=[]
            # Get the minimum values of each column i.e. along axis 0
            if SegmentCountALL>1:
                wCompleteShortestDistanceStat = np.amin(wCompleteShortestDistanceToALLFilaments, axis=1).tolist()
            else:
                wCompleteShortestDistanceStat=wCompleteShortestDistanceToALLFilaments.tolist()
            vSpots.AddStatistics(vSpotsStatNames, wCompleteShortestDistanceStat,
                                          vSpotsStatUnits, vSpotsStatFactors,
                                          vSpotsStatFactorName, vSpotsId)

        ###########
            #ADD Spot number&Density to Filament Distance statistic.
            vFilamentStatvIds=list(range(len(wCompleteDendriteSegmentIds)))
            vFilamentStatUnits=['']*(len(wCompleteDendriteSegmentIds))
            vFilamentStatFactors=(['Dendrite']*len(wCompleteDendriteSegmentIds), [str(x) for x in wCompleteDendriteTimeIndex] )
            vFilamentStatFactorName=['Category','Time']
            vFilamentStatNames=[' Dendrite Coloc Number Spots']*(len(wCompleteDendriteSegmentIds))
            vFilaments.AddStatistics(vFilamentStatNames, wNumberOfSpotsPerDendrite,
                                          vFilamentStatUnits, vFilamentStatFactors,
                                          vFilamentStatFactorName, wCompleteDendriteSegmentIds)

            vNewStatSpotColocDensityPerDendrite=[(wNumberOfSpotsPerDendrite[i]*10) / vAllFilamentDendriteLength[i] for i in range(len(vAllFilamentDendriteLength))]
            vFilamentStatNames=[' Dendrite Coloc Spot Density (per 10um)']*(len(wCompleteDendriteSegmentIds))
            vFilaments.AddStatistics(vFilamentStatNames, vAllColocDensityPerDendrite,
                                          vFilamentStatUnits, vFilamentStatFactors,
                                          vFilamentStatFactorName, wCompleteDendriteSegmentIds)
            #Spine Stat
            if wNumberOfSpotsPerSpine!=[]:
                vFilamentStatvIds=list(range(len(wCompleteSpineSegmentIds)))
                vFilamentStatUnits=['']*(len(wCompleteSpineSegmentIds))
                vFilamentStatFactorName=['Category','Time']
                vFilamentStatFactors=(['Spine']*len(wCompleteSpineSegmentIds), [str(x) for x in wCompleteSpineTimeIndex] )
                vFilamentStatNames=[' Spine Coloc Number Spots']*len(wCompleteSpineSegmentIds)
                vFilaments.AddStatistics(vFilamentStatNames, wNumberOfSpotsPerSpine,
                                          vFilamentStatUnits, vFilamentStatFactors,
                                          vFilamentStatFactorName, wCompleteSpineSegmentIds)
        ###############################################################################
        ###############################################################################
        #Produce Report the Filament level stats
        vFilamentStatUnits=['']*vFilamentCountActual
        vFilamentStatFactors=(['Filament']*vFilamentCountActual, [str(x) for x in wCompleteFilamentTimeIndex] )
        vFilamentStatFactorName=['Category','Time']

        if vOptionIntensity==1:
            #Reshape reorder filament Intensity stats
            wCompleteFilamentIntCenter = [[] for _ in range(vSizeC)]
            for index, item in enumerate(wFilamentIntensityCenter):
                wCompleteFilamentIntCenter[index % vSizeC].append(item)
            wCompleteFilamentIntMean = [[] for _ in range(vSizeC)]
            for index, item in enumerate(wFilamentIntensityMean):
                wCompleteFilamentIntMean[index % vSizeC].append(item)
            for c in range (vSizeC):
                vFilamentStatNames=[' Filament IntensityMean ch' + str(c+1)]*vFilamentCountActual
                vFilaments.AddStatistics(vFilamentStatNames, wCompleteFilamentIntMean[c],
                                          vFilamentStatUnits, vFilamentStatFactors,
                                          vFilamentStatFactorName, vFilamentIds)
                vFilamentStatNames=[' Filament IntensityCenter ch' + str(c+1)]*vFilamentCountActual
                vFilaments.AddStatistics(vFilamentStatNames, wCompleteFilamentIntCenter[c],
                                          vFilamentStatUnits, vFilamentStatFactors,
                                          vFilamentStatFactorName, vFilamentIds)
        if vOptionFilamentBoutonDetection==1:
            vFilamentStatNames=[' Filament Number Boutons']*vFilamentCountActual
            vFilaments.AddStatistics(vFilamentStatNames, wCompleteFilamentNumberBoutons,
                                      vFilamentStatUnits, vFilamentStatFactors,
                                      vFilamentStatFactorName, vFilamentIds)
        if vOptionFilamentCloseToSpots==1:
            vFilamentStatNames=[' Filament Number Coloc Spots']*vFilamentCountActual
            vFilaments.AddStatistics(vFilamentStatNames, wCompleteNumberSpotsPerFilament,
                                      vFilamentStatUnits, vFilamentStatFactors,
                                      vFilamentStatFactorName, vFilamentIds)
            vFilamentStatNames=[' Filament Number Coloc Spots on Dendrites']*vFilamentCountActual
            vFilaments.AddStatistics(vFilamentStatNames, wCompleteNumberSpotsonDendritePerFilament,
                                      vFilamentStatUnits, vFilamentStatFactors,
                                      vFilamentStatFactorName, vFilamentIds)
            if qIsSpines==True:
                vFilamentStatNames=[' Filament Number Coloc Spots on Spines']*vFilamentCountActual
                vFilaments.AddStatistics(vFilamentStatNames, wCompleteNumberSpotsonSpinePerFilament,
                                          vFilamentStatUnits, vFilamentStatFactors,
                                          vFilamentStatFactorName, vFilamentIds)

        ###################################################################################
        ###################################################################################
        #Apply SpotAnalysis folder to Surpass scene
        if vOptionFilamentCloseToSpots==1 or vOptionFilamentBoutonDetection==1:
            vImarisApplication.GetSurpassScene().AddChild(vNewSpotsAnalysisFolder, -1)

        if vOptionFilamentBoutonDetection==1 or vOptionFilamentCloseToSpots==1 or vOptionIntensity==1:
            vFilaments.SetName(vFilaments.GetName()+' -- Analyzed')
            vImarisApplication.GetSurpassScene().AddChild(vFilaments, -1)

        if vOptionFilamentCloseToSpots==1:
            vSpots.SetVisible(0)

        # # #Adjust Visibility
        # if vOptionFilamentToSpots==1 and vOptionFilamentCloseToSpots==1 or vOptionFilamentBoutonDetection==1:
        #     vNewSpotsDendritesFolder.SetVisible(0)
        #     vNewSpotsSpinesFolder.SetVisible(0)

        if vNumberOfFilaments>50 and vOptionFilamentCloseToSpots==1 or vOptionIntensity==1:
            vImarisApplication.SetVisible(1)

    except:
        vImarisApplication.SetVisible(1)



