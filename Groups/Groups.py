import os, sys
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

import subprocess

#
# Groups
#

class Groups(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "Groups"  # TODO make this more human readable by adding spaces
        self.parent.categories = ["Correspondence"]
        self.parent.dependencies = []
        self.parent.contributors = ["Priscille de Dumast (University of Michigan), Ilwoo Lyu (UNC), Hamid Ali (UNC)"]
        self.parent.helpText = """
    This is an example of scripted loadable module bundled in an extension.
    It performs a simple thresholding on the input volume and optionally captures a screenshot.
    """
        self.parent.acknowledgementText = """
    This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
    and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
"""  # replace with organization, grant and thanks.


#
# GroupsWidget
#

class GroupsWidget(ScriptedLoadableModuleWidget):
    """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)

        ###################################################################
        ##                                                               ##
        ##  Collapsible part for input/output parameters for Groups CLI  ##
        ##                                                               ##
        ###################################################################

        self.ioCollapsibleButton = ctk.ctkCollapsibleButton()
        self.ioCollapsibleButton.text = "IO"
        self.layout.addWidget(self.ioCollapsibleButton)
        self.ioQVBox = qt.QVBoxLayout(self.ioCollapsibleButton)

        # --------------------------------- #
        # ----- Group Box DIRECTORIES ----- #
        # --------------------------------- #
        self.directoryGroupBox = qt.QGroupBox("Directories")
        self.ioQVBox.addWidget(self.directoryGroupBox)
        self.ioQFormLayout = qt.QFormLayout(self.directoryGroupBox)

        # Selection of the directory containing the input models (option: --surfaceDir)
        self.inputModelsDirectorySelector = ctk.ctkDirectoryButton()
        self.ioQFormLayout.addRow(qt.QLabel("Input Models Directory:"), self.inputModelsDirectorySelector)

        # Selection of the input directory containing the property files from SPHARM (txt files) (option: --propertyDir)
        self.inputPropertyDirectorySelector = ctk.ctkDirectoryButton()
        self.ioQFormLayout.addRow(qt.QLabel("Input Property directory:"), self.inputPropertyDirectorySelector)

        # Selection of the directory which contains each spherical model (option: --sphereDir)
        self.sphericalModelsDirectorySelector = ctk.ctkDirectoryButton()
        self.ioQFormLayout.addRow("Spherical Models Directory:", self.sphericalModelsDirectorySelector)

        # Selection of the output directory for Groups (option: --outputDir)
        self.outputDirectorySelector = ctk.ctkDirectoryButton()
        self.ioQFormLayout.addRow(qt.QLabel("Output directory:"), self.outputDirectorySelector)

        # CheckBox. If checked, Group Box 'Parameters' will be enabled
        self.enableParamCB = ctk.ctkCheckBox()
        self.enableParamCB.setText("Personalize parameters")
        self.ioQFormLayout.addRow(self.enableParamCB)

        # Connections
        self.inputModelsDirectorySelector.connect("directoryChanged(const QString &)", self.onSelect)
        self.inputPropertyDirectorySelector.connect("directoryChanged(const QString &)", self.onSelect)
        self.sphericalModelsDirectorySelector.connect("directoryChanged(const QString &)", self.onSelect)
        self.outputDirectorySelector.connect("directoryChanged(const QString &)", self.onSelect)
        self.enableParamCB.connect("stateChanged(int)", self.onCheckBoxParam)

        # Name simplification (string)
        self.modelsDirectory = str(self.inputModelsDirectorySelector.directory)
        self.propertyDirectory = str(self.inputPropertyDirectorySelector.directory)
        self.outputDirectory = str(self.outputDirectorySelector.directory)

        # -------------------------------- #
        # ----- Group Box PARAMETERS ----- #
        # -------------------------------- #
        self.parametersGroupBox = qt.QGroupBox("Parameters")
        self.ioQVBox.addWidget(self.parametersGroupBox)
        self.paramQFormLayout = qt.QFormLayout(self.parametersGroupBox)
        self.parametersGroupBox.setEnabled(False)

        # Selection of the property we want to use (option: --filter)
        self.specifyPropertySelector = ctk.ctkCheckableComboBox()
        self.specifyPropertySelector.addItems(("C","H","Kappa1","S","K","Kappa2","DPhi","DTheta"))
        self.paramQFormLayout.addRow(qt.QLabel("Properties name to use:"), self.specifyPropertySelector)

        # Weights of each property - Choices on 3 lines (option: -w)
        self.weightLayout = qt.QVBoxLayout(self.parametersGroupBox)
        self.weightline1 = qt.QHBoxLayout(self.parametersGroupBox)  # Line 1
        self.weightLayout.addLayout(self.weightline1)
        self.weightline2 = qt.QHBoxLayout(self.parametersGroupBox)  # Line 2
        self.weightLayout.addLayout(self.weightline2)
        self.weightline3 = qt.QHBoxLayout(self.parametersGroupBox)  # Line 3
        self.weightLayout.addLayout(self.weightline3)

        # Fill out first line
        self.labelC = qt.QLabel("C")
        self.weightline1.addWidget(self.labelC)
        self.weightC = ctk.ctkDoubleSpinBox()
        self.weightC.enabled = False
        self.weightC.value = 1
        self.weightline1.addWidget(self.weightC)

        self.labelH = qt.QLabel("H")
        self.weightline1.addWidget(self.labelH)
        self.weightH = ctk.ctkDoubleSpinBox()
        self.weightH.enabled = False
        self.weightH.value = 1
        self.weightline1.addWidget(self.weightH)

        self.labelKappa1 = qt.QLabel("Kappa1")
        self.weightline1.addWidget(self.labelKappa1)
        self.weightKappa1 = ctk.ctkDoubleSpinBox()
        self.weightKappa1.enabled = False
        self.weightKappa1.value = 1
        self.weightline1.addWidget(self.weightKappa1)

        # Fill out second line
        self.labelS = qt.QLabel("S")
        self.weightline2.addWidget(self.labelS)
        self.weightS = ctk.ctkDoubleSpinBox()
        self.weightS.enabled = False
        self.weightS.value = 1
        self.weightline2.addWidget(self.weightS)

        self.labelK = qt.QLabel("K")
        self.weightline2.addWidget(self.labelK)
        self.weightK = ctk.ctkDoubleSpinBox()
        self.weightK.enabled = False
        self.weightK.value = 1
        self.weightline2.addWidget(self.weightK)

        self.labelKappa2 = qt.QLabel("Kappa2")
        self.weightline2.addWidget(self.labelKappa2)
        self.weightKappa2 = ctk.ctkDoubleSpinBox()
        self.weightKappa2.enabled = False
        self.weightKappa2.value = 1
        self.weightline2.addWidget(self.weightKappa2)

        # Fill out third line
        self.labelDPhi = qt.QLabel("DPhi")
        self.weightline3.addWidget(self.labelDPhi)
        self.weightDPhi = ctk.ctkDoubleSpinBox()
        self.weightDPhi.enabled = False
        self.weightDPhi.value = 1
        self.weightline3.addWidget(self.weightDPhi)

        self.labelDTheta = qt.QLabel("DTheta")
        self.weightline3.addWidget(self.labelDTheta)
        self.weightDTheta = ctk.ctkDoubleSpinBox()
        self.weightDTheta.enabled = False
        self.weightDTheta.value = 1
        self.weightline3.addWidget(self.weightDTheta)

        self.paramQFormLayout.addRow("Weight of each property:", self.weightLayout)

        # Selection of the directory which contains each spherical model (option: --landmarkDir)            ## !!!!!!!!!!!
        self.landmarkDirectorySelector = ctk.ctkDirectoryButton()
        self.paramQFormLayout.addRow(qt.QLabel("Landmark Directory:"), self.landmarkDirectorySelector)

        # Specification of the SPHARM decomposition degree (option: -d)
        self.degreeSpharm = ctk.ctkSliderWidget()
        self.degreeSpharm.minimum = 0
        self.degreeSpharm.maximum = 50
        self.degreeSpharm.value = 5        # initial value
        self.degreeSpharm.setDecimals(0)
        self.paramQFormLayout.addRow(qt.QLabel("Degree of SPHARM decomposition:"), self.degreeSpharm)

        # Maximum iteration (option: --maxIter)
        self.maxIter = qt.QSpinBox()
        self.maxIter.minimum = 0            # Check the range authorized
        self.maxIter.maximum = 100000
        self.maxIter.value = 5000
        self.paramQFormLayout.addRow("Maximum number of iteration:", self.maxIter)

        # Name simplification
        self.property = ""
        self.propertyValue = ""

        # Connections
        self.specifyPropertySelector.connect("checkedIndexesChanged()", self.onSpecifyPropertyChanged)

        # ------------------------------------------ #
        # ----- Apply button to launch the CLI ----- #
        # ------------------------------------------ #
        self.applyButton = qt.QPushButton("Apply")
        self.applyButton.enabled = False
        self.ioQVBox.addWidget(self.applyButton)

        # Connections
        self.applyButton.connect('clicked(bool)', self.onApplyButtonClicked)

        # ----- Add vertical spacer ----- #
        self.layout.addStretch(1)


        #### SET PARAMETERS - for test!!
        self.inputModelsDirectorySelector.directory = "/Users/prisgdd/Desktop/Example/Mesh"
        self.inputPropertyDirectorySelector.directory = "/Users/prisgdd/Desktop/Example/attributes"
        self.outputDirectorySelector.directory = "/Users/prisgdd/Desktop/OUTPUTGROUPS"

        # self.landmarkDirectorySelector.directory = "/Users/prisgdd/Desktop/Example/landmark"
        self.sphericalModelsDirectorySelector.directory = "/Users/prisgdd/Desktop/Example/sphere"
        self.degreeSpharm.value = 10
        self.maxIter.value = 5

    ## Function cleanup(self):
    def cleanup(self):
        pass

    ## Function onSelect(self):
    # Check if each directory (Models, Property, Sphere and Output) have been chosen.
    # If they were, Apply button is enabled to call the CLI
    # Update the simplified names
    def onSelect(self):
        # Update names
        self.modelsDirectory = str(self.inputModelsDirectorySelector.directory)
        self.propertyDirectory = str(self.inputPropertyDirectorySelector.directory)
        self.sphereDirectory = str(self.sphericalModelsDirectorySelector.directory)
        self.outputDirectory = str(self.outputDirectorySelector.directory)

        # Check if each directory has been choosen
        self.applyButton.enabled = self.modelsDirectory != "." and self.propertyDirectory != "." and self.outputDirectory != "." and self.sphereDirectory != "."

    ## Function onSpecifyPropertyChanged(self):
    # Enable/Disable associated weights
    def onSpecifyPropertyChanged(self):
        if self.specifyPropertySelector.currentIndex == 0:
            self.weightC.enabled = not self.weightC.enabled

        if self.specifyPropertySelector.currentIndex == 1:
            self.weightH.enabled = not self.weightH.enabled

        if self.specifyPropertySelector.currentIndex == 2:
            self.weightKappa1.enabled = not self.weightKappa1.enabled

        if self.specifyPropertySelector.currentIndex == 3:
            self.weightS.enabled = not self.weightS.enabled

        if self.specifyPropertySelector.currentIndex == 4:
            self.weightK.enabled = not self.weightK.enabled

        if self.specifyPropertySelector.currentIndex == 5:
            self.weightKappa2.enabled = not self.weightKappa2.enabled

        if self.specifyPropertySelector.currentIndex == 6:
            self.weightDPhi.enabled = not self.weightDPhi.enabled

        if self.specifyPropertySelector.currentIndex == 7:
            self.weightDTheta.enabled = not self.weightDTheta.enabled

    ## Function onCheckBoxParam(self):
    # Enable the parameter Group Box if associated check box is checked
    def onCheckBoxParam(self):
        if self.enableParamCB.checkState():
            self.parametersGroupBox.setEnabled(True)
        else:
            self.parametersGroupBox.setEnabled(False)

    ## Function onApplyButtonClicked(self):
    # Update every parameters to call Groups
    # Check maxIter is an integer
    # Check if parameters group box enabled
    def onApplyButtonClicked(self):
        logic = GroupsLogic()

        # Update names
        self.modelsDirectory = str(self.inputModelsDirectorySelector.directory)
        self.propertyDirectory = str(self.inputPropertyDirectorySelector.directory)
        self.sphereDirectory = str(self.sphericalModelsDirectorySelector.directory)
        self.outputDirectory = str(self.outputDirectorySelector.directory)

        if not self.enableParamCB.checkState():
            logic.runGroups(modelsDir=self.modelsDirectory, propertyDir=self.propertyDirectory, sphereDir=self.sphereDirectory, outputDir=self.outputDirectory)

        else:
            # ----- Creation of string for the specified properties and their values ----- #
            self.property = ""
            self.propertyValue = ""

            if self.weightC.enabled:
                self.propertyValue = self.propertyValue + str(self.weightC.value)
                self.property = self.property + "C.txt"

            if self.weightH.enabled:
                if self.propertyValue != "":
                    self.propertyValue = self.propertyValue + ","
                    self.property = self.property + ","

                self.propertyValue = self.propertyValue + str(self.weightH.value)
                self.property = self.property + "H.txt"

            if self.weightKappa1.enabled:
                if self.propertyValue != "":
                    self.propertyValue = self.propertyValue + ","
                    self.property = self.property + ","

                self.propertyValue = self.propertyValue + str(self.weightKappa1.value)
                self.property = self.property + "Kappa1.txt"

            if self.weightS.enabled:
                if self.propertyValue != "":
                    self.propertyValue = self.propertyValue + ","
                    self.property = self.property + ","

                self.propertyValue = self.propertyValue + str(self.weightS.value)
                self.property = self.property + "S.txt"

            if self.weightK.enabled:
                if self.propertyValue != "":
                    self.propertyValue = self.propertyValue + ","
                    self.property = self.property + ","

                self.propertyValue = self.propertyValue + str(self.weightK.value)
                self.property = self.property + "K.txt"

            if self.weightKappa2.enabled:
                if self.propertyValue != "":
                    self.propertyValue = self.propertyValue + ","
                    self.property = self.property + ","

                self.propertyValue = self.propertyValue + str(self.weightKappa2.value)
                self.property = self.property + "Kappa2.txt"

            if self.weightDPhi.enabled:
                if self.propertyValue != "":
                    self.propertyValue = self.propertyValue + ","
                    self.property = self.property + ","

                self.propertyValue = self.propertyValue + str(self.weightDPhi.value)
                self.property = self.property + "DPhi.txt"

            if self.weightDTheta.enabled:
                if self.propertyValue != "":
                    self.propertyValue = self.propertyValue + ","
                    self.property = self.property + ","

                self.propertyValue = self.propertyValue + str(self.weightDTheta.value)
                self.property = self.property + "DTheta.txt"

            if self.property == "" and self.propertyValue == "":                         # Si aucune propriete selectionnee
                self.property = 0
                self.propertyValue = 0

            if self.landmarkDirectorySelector.directory == ".":
                landmark = 0
            else:
                landmark = str(self.landmarkDirectorySelector.directory)

            d = int(self.degreeSpharm.value)
            m = int(self.maxIter.value)

            logic.runGroups(modelsDir = self.modelsDirectory, propertyDir = self.propertyDirectory,
                            sphereDir = self.sphereDirectory, outputDir = self.outputDirectory, properties = self.property,
                            propValues = self.propertyValue, landmark = landmark, degree = d, maxIter = m)

#
# GroupsLogic
#

class GroupsLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

    ## Function runGroups(...)
    #   Check if directories are ok
    #   Create the command line
    #   Call the CLI Groups
    def runGroups(self, modelsDir, propertyDir, sphereDir, outputDir, properties=0, propValues=0, landmark=0, degree=0, maxIter=0):
        print "--- function runGroups() ---"

        """
        Calling Groups CLI
            Arguments:
             --surfaceDir: Directory with input models
             --propertyDir: Property folder (txt files from SPHARM)
             --sphereDir: Sphere folder
             --outputDir: Output directory
             --filter: Properties to consider
             -w: weights associated with each property
             --landmarkDir: Landmark folder
             -d: Degree of deformation field
             --maxIter: Maximum number of iteration
        """

        #####################################################################################
        ## ----- Check if directories contents correctly match with models Directory ----- ##
        # For each shape, files should have the same name, with different extension.
        #       Mesh: [name].vtk
        #       Properties: 8 x [name].vtk.[prop].txt
        #       Sphere: [name].txt.vtk
        #       landmark: [name].txt


        ## Preparation of the reference list (from modelsDir)
        listModelsDir = os.listdir(modelsDir)
        listModelsName = list()
        if listModelsDir.count(".DS_Store"):
            listModelsDir.remove(".DS_Store")
        if not len(listModelsDir):
            return False
        # Get the list of all basename + check if they are all vtk files
        for i in range(0, len(listModelsDir)):
            extension = listModelsDir[i].split('.')[-1]
            if extension == 'vtk':
                listModelsName.append('.'.join(listModelsDir[i].split('.')[:-1]))

        ## Check other directories
        listPropertyDir = os.listdir(propertyDir)
        listPropertyName = list()
        if listPropertyDir.count(".DS_Store"):
            listPropertyDir.remove(".DS_Store")
        # There should be 8 files for each one in modelsDir
        listPropertyName = ['.'.join(file.split('.')[:-3]) for file in listPropertyDir]
        for file in listModelsName:
            if listPropertyName.count(file) != 8:
                print "Properties. Not enough properties for " + str(file)
                return False

        listSphereDir = os.listdir(sphereDir)
        listSphereName = list()
        if listSphereDir.count(".DS_Store"):
            listSphereDir.remove(".DS_Store")
        # There should be the same basename files
        listSphereName = ['.'.join(file.split('.')[:-2]) for file in listSphereDir]
        for file in listModelsName:
            if listSphereName.count(file) != 1:
                print "Sphere. Wrong correspondence between name files " + str(file)
                return False

        if landmark:
            listLandmarkDir = os.listdir(landmark)
            if listLandmarkDir.count(".DS_Store"):
                listLandmarkDir.remove(".DS_Store")
            listLandmarkName = list()
            ## In each directory there should be files with same basename as in the model repertory
            listNameName = ['.'.join(file.split('.')[:-1]) for file in listLandmarkDir]
            for file in listModelsName:
                if listNameName.count(file) != 1:
                    print "Landmark. Wrong correspondence between name files " + str(file)
                    return False

        ############################################
        # ----- Creation of the command line ----- #

        # # Avec le make package
        # self.moduleName = "Groups"
        # scriptedModulesPath = eval('slicer.modules.%s.path' % self.moduleName.lower())
        # scriptedModulesPath = os.path.dirname(scriptedModulesPath)
        #
        # libPath = os.path.join(scriptedModulesPath)
        # sys.path.insert(0, libPath)
        # groups = os.path.join(scriptedModulesPath, '../hidden-cli-modules/Groups')

        # Sans le make package
        groups = "/Users/prisgdd/Documents/Projects/Groups/GROUPS-build/Groups-build/bin/Groups"

        arguments = list()
        arguments.append("--surfaceDir")
        arguments.append(modelsDir)
        arguments.append("--propertyDir")
        arguments.append(propertyDir)
        arguments.append("--sphereDir")
        arguments.append(sphereDir)
        arguments.append("--outputDir")
        arguments.append(outputDir)

        if properties and propValues:
            # If # of properties and # of weights aren't the same, we cut those at the end
            if properties.count(',') > propValues.count(','):
                while properties.count(',') > propValues.count(','):
                    properties = (','.join(properties.split(',')[:-1]))
            elif propValues.count(',') > properties.count(','):
                while propValues.count(',') > properties.count(','):
                    propValues = (','.join(propValues.split(',')[:-1]))
            arguments.append("--filter")
            arguments.append(properties)
            arguments.append("-w")
            arguments.append(propValues)
        else:       # If no properties specified - Default: each property with weight=1
            arguments.append("--filter")
            arguments.append("C.txt,H.txt,Kappa1.txt,S.txt,K.txt,Kappa2.txt,DPhi.txt,DTheta.txt")
            arguments.append("-w")
            arguments.append("1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0")

        if landmark:
            arguments.append("--landmarkDir")
            arguments.append(landmark)

        if degree:
            arguments.append("-d")
            arguments.append(int(degree))
        else:           # Default: degree=5
            arguments.append("-d")
            arguments.append(5)

        if maxIter:
            arguments.append("--maxIter")
            arguments.append(maxIter)
        else:           # Default: # maximum of iteration = 5000
            arguments.append("--maxIter")
            arguments.append(5000)

        ############################
        # ----- Call the CLI ----- #
        self.process = qt.QProcess()
        # self.process.setProcessChannelMode(qt.QProcess.MergedChannels)

        # print "Calling " + os.path.basename(groups)
        self.process.start(groups, arguments)
        self.process.waitForStarted()
        # # print "state: " + str(self.process.state())
        self.process.waitForFinished(-1)
        # print "error: " + str(self.process.error())

        # processOutput = self.process.readAll()
        # print "processOutput : " + str(processOutput)

        return True


class GroupsTest(ScriptedLoadableModuleTest):
    """
        This is the test case for your scripted module.
        Uses ScriptedLoadableModuleTest base class, available at:
        https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
        """

    def setUp(self):
        """ Do whatever is needed to reset the state - typically a scene clear will be enough.
            """
        slicer.mrmlScene.Clear(0)

    def runTest(self):
        """Run as few or as many tests as needed here.
            """
        self.delayDisplay("Starting the test")
        self.setUp()

        self.delayDisplay("Test 1")
        self.assertTrue(self.test_Groups1())
        self.delayDisplay("Test 2 - All properties")
        self.assertTrue(self.test_Groups2())
        self.delayDisplay("Test 3 - Without landmark")
        self.assertTrue(self.test_Groups3())
        self.delayDisplay("Test 4 - No properties or weights specified")
        self.assertTrue(self.test_Groups4())
        self.delayDisplay("Test 5 - # of properties different from # of weights")
        self.assertTrue(self.test_Groups5())
        self.delayDisplay("Test 6 - No specified values for degree and # of iteration")
        self.assertTrue(self.test_Groups6())

        self.delayDisplay('All test passed!')


    def test_Groups1(self):
        self.delayDisplay('Start test 1')

        ## --- Prepare parameters --- ##
        meshDir = "/Users/prisgdd/Documents/Projects/GroupsExtension/dataTest/Mesh"
        propertiesDir = "/Users/prisgdd/Documents/Projects/GroupsExtension/dataTest/attributes"
        landmarkDir = "/Users/prisgdd/Documents/Projects/GroupsExtension/dataTest/landmark"
        sphereDir = "/Users/prisgdd/Documents/Projects/GroupsExtension/dataTest/sphere"
        degree = 5
        maxIter = 1000
        properties = "C.txt,S.txt"
        propertiesValues = "0.5,0.25"
        outputDir1 = "/Users/prisgdd/Documents/Projects/GroupsExtension/dataTest/outputTest/outputTest1"
        outputVerif1 = "/Users/prisgdd/Documents/Projects/GroupsExtension/dataTest/outputVerif/outputVerif1"

        ## --- Call the CLI --- ##
        # logic = GroupsLogic()
        # logic.runGroups(modelsDir=meshDir, propertyDir=propertiesDir,
        #                 sphereDir=sphereDir, outputDir=outputDir1, properties=properties,
        #                 propValues=propertiesValues, landmark=landmarkDir, degree=degree, maxIter=maxIter)

        ## --- Compare results --- ##
        if self.outputcomparison(outputDir1, outputVerif1, meshDir):
            self.delayDisplay('Test 1 passed!')
            return True
        else:
            return False

    # Test 2 - All properties
    def test_Groups2(self):
        self.delayDisplay('Start test 2')

        ## --- Prepare parameters --- ##
        meshDir = "/Users/prisgdd/Documents/Projects/GroupsExtension/dataTest/Mesh"
        propertiesDir = "/Users/prisgdd/Documents/Projects/GroupsExtension/dataTest/attributes"
        landmarkDir = "/Users/prisgdd/Documents/Projects/GroupsExtension/dataTest/landmark"
        sphereDir = "/Users/prisgdd/Documents/Projects/GroupsExtension/dataTest/sphere"
        degree = 5
        maxIter = 5000
        properties = "C.txt,H.txt,Kappa1.txt,S.txt,K.txt,Kappa2.txt,DPhi.txt,DTheta.txt"
        propertiesValues = "0.2,1.0,0.3,0.25,0.3,0.8,0.1,0.4"
        outputDir2 = "/Users/prisgdd/Documents/Projects/GroupsExtension/dataTest/outputTest/outputTest2"
        outputVerif2 = "/Users/prisgdd/Documents/Projects/GroupsExtension/dataTest/outputVerif/outputVerif2"

        ## --- Call the CLI --- ##
        # logic = GroupsLogic()
        # logic.runGroups(modelsDir=meshDir, propertyDir=propertiesDir,
        #                 sphereDir=sphereDir, outputDir=outputDir2, properties=properties,
        #                 propValues=propertiesValues, landmark=landmarkDir, degree=degree, maxIter=maxIter)

        ## --- Compare results --- ##
        if self.outputcomparison(outputDir2, outputVerif2, meshDir):
            self.delayDisplay('Test 2 passed!')
            return True
        else:
            return False

    # Test 3 - Without landmark
    def test_Groups3(self):
        self.delayDisplay('Start test 3')

        ## --- Prepare parameters --- ##
        meshDir = "/Users/prisgdd/Documents/Projects/GroupsExtension/dataTest/Mesh"
        propertiesDir = "/Users/prisgdd/Documents/Projects/GroupsExtension/dataTest/attributes"
        sphereDir = "/Users/prisgdd/Documents/Projects/GroupsExtension/dataTest/sphere"
        degree = 5
        maxIter = 1000
        properties = "C.txt,S.txt"
        propertiesValues = "0.5,0.25"
        outputDir3 = "/Users/prisgdd/Documents/Projects/GroupsExtension/dataTest/outputTest/outputTest3"

        outputVerif3 = "/Users/prisgdd/Documents/Projects/GroupsExtension/dataTest/outputVerif/outputVerif3"

        ## --- Call the CLI --- ##
        # logic = GroupsLogic()
        # logic.runGroups(modelsDir=meshDir, propertyDir=propertiesDir,
        #                 sphereDir=sphereDir, outputDir=outputDir3, properties=properties,
        #                 propValues=propertiesValues, degree=degree, maxIter=maxIter)

        ## --- Compare results --- ##
        if self.outputcomparison(outputDir3, outputVerif3, meshDir):
            self.delayDisplay('Test 3 passed!')
            return True
        else:
            return False

    # Test 4 - No properties or weights specified"
    def test_Groups4(self):
        self.delayDisplay('Start test 4')

        ## --- Prepare parameters --- ##
        meshDir = "/Users/prisgdd/Documents/Projects/GroupsExtension/dataTest/Mesh"
        propertiesDir = "/Users/prisgdd/Documents/Projects/GroupsExtension/dataTest/attributes"
        landmarkDir = "/Users/prisgdd/Documents/Projects/GroupsExtension/dataTest/landmark"
        sphereDir = "/Users/prisgdd/Documents/Projects/GroupsExtension/dataTest/sphere"
        degree = 18
        maxIter = 1000

        outputDir4 = "/Users/prisgdd/Documents/Projects/GroupsExtension/dataTest/outputTest/outputTest4"

        outputVerif4 = "/Users/prisgdd/Documents/Projects/GroupsExtension/dataTest/outputVerif/outputVerif4"

        ## --- Call the CLI --- ##
        # logic = GroupsLogic()
        # logic.runGroups(modelsDir=meshDir, propertyDir=propertiesDir,
        #                 sphereDir=sphereDir, outputDir=outputDir4, landmark=landmarkDir, degree=degree, maxIter=maxIter)

        ## --- Compare results --- ##
        if self.outputcomparison(outputDir4, outputVerif4, meshDir):
            self.delayDisplay('Test 4 passed!')
            return True
        else:
            return False

    # Test 5 - # of properties different from # of weights
    def test_Groups5(self):
        self.delayDisplay('Start test 5')

        ## --- Prepare parameters --- ##
        meshDir = "/Users/prisgdd/Documents/Projects/GroupsExtension/dataTest/Mesh"
        propertiesDir = "/Users/prisgdd/Documents/Projects/GroupsExtension/dataTest/attributes"
        sphereDir = "/Users/prisgdd/Documents/Projects/GroupsExtension/dataTest/sphere"
        landmarkDir = "/Users/prisgdd/Documents/Projects/GroupsExtension/dataTest/landmark"
        degree = 5
        maxIter = 1000
        properties = "DPhi.txt,C.txt,S.txt,Kappa1.txt"
        propertiesValues = "0.1,0.3"

        outputDir5 = "/Users/prisgdd/Documents/Projects/GroupsExtension/dataTest/outputTest/outputTest5"

        outputVerif5 = "/Users/prisgdd/Documents/Projects/GroupsExtension/dataTest/outputVerif/outputVerif5"

        ## --- Call the CLI --- ##
        # logic = GroupsLogic()
        # logic.runGroups(modelsDir=meshDir, propertyDir=propertiesDir, properties=properties,
        #                 propValues=propertiesValues,
        #                 sphereDir=sphereDir, outputDir=outputDir5, landmark=landmarkDir, degree=degree, maxIter=maxIter)

        ## --- Compare results --- ##
        if self.outputcomparison(outputDir5, outputVerif5, meshDir):
            self.delayDisplay('Test 5 passed!')
            return True
        else:
            return False

    # Test 6 - No specified values for degree and # of iteration
    def test_Groups6(self):
        self.delayDisplay('Start test 6')

        ## --- Prepare parameters --- ##
        meshDir = "/Users/prisgdd/Documents/Projects/GroupsExtension/dataTest/Mesh"
        propertiesDir = "/Users/prisgdd/Documents/Projects/GroupsExtension/dataTest/attributes"
        sphereDir = "/Users/prisgdd/Documents/Projects/GroupsExtension/dataTest/sphere"
        landmarkDir = "/Users/prisgdd/Documents/Projects/GroupsExtension/dataTest/landmark"

        properties = "C.txt,S.txt"
        propertiesValues = "0.5,0.25"

        outputDir6 = "/Users/prisgdd/Documents/Projects/GroupsExtension/dataTest/outputTest/outputTest6"

        outputVerif6 = "/Users/prisgdd/Documents/Projects/GroupsExtension/dataTest/outputVerif/outputVerif6"

        ## --- Call the CLI --- ##
        # logic = GroupsLogic()
        # logic.runGroups(modelsDir=meshDir, propertyDir=propertiesDir,
        #                 sphereDir=sphereDir, outputDir=outputDir6, properties=properties,
        #                 propValues=propertiesValues, landmark=landmarkDir)

        ## --- Compare results --- ##
        if self.outputcomparison(outputDir6, outputVerif6, meshDir):
            self.delayDisplay('Test 6 passed!')
            return True
        else:
            return False

    ## Function outputComparison(...)
    # Compare the expected outputs (outputVerif) with those obtained (outputDir)
    def outputcomparison(self, outputDir, outputVerif, inputDir):
        listFilesOut = os.listdir(outputDir)
        listFilesVerif = os.listdir(outputVerif)

        ## Delete .DS_Store if there is one - for MacOS
        if listFilesOut.count(".DS_Store"):
            listFilesOut.remove(".DS_Store")
        if listFilesVerif.count(".DS_Store"):
            listFilesVerif.remove(".DS_Store")

        ## Check number of outputs
        nbFilesOut = len(listFilesOut)
        nbFilesIn = len(os.listdir(inputDir))
        if nbFilesOut != nbFilesIn:
            print "Wrong number of outputs"
            return False

        ## Check files names
        listFilesOutNames = list()
        listFilesVerifNames = list()
        for i in range(0, len(listFilesOut)):
            listFilesOutNames.append('.'.join(listFilesOut[i].split('.')[:-1]))
            listFilesVerifNames.append('.'.join(listFilesVerif[i].split('.')[:-1]))

            if listFilesOutNames[i] != listFilesVerifNames[i]:
                print "Erreur de noms"
                return False

        ## Compare files contents
        taille = len(listFilesOut)
        for i in range(0, taille):
            fTest = open(outputDir + "/" + listFilesOut[i], "r")
            contenuTest = fTest.read()

            fVerif = open(outputVerif + "/" + listFilesVerif[i], "r")
            contenuVerif = fVerif.read()

            if contenuTest != contenuVerif:
                print "Wrong contents"
                return False

        return True
