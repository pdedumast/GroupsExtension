import os, sys
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

import shutil

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
        self.parent.categories = ["Quantification"]
        self.parent.dependencies = []
        self.parent.contributors = ["Priscille de Dumast (University of Michigan), Ilwoo Lyu (UNC), Hamid Ali (UNC)"]
        self.parent.helpText = """
        ...
    """
        self.parent.acknowledgementText = """
        ...
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
        self.ioQFormLayout.addRow(qt.QLabel("Input Property Directory:"), self.inputPropertyDirectorySelector)

        # Selection of the directory which contains each spherical model (option: --sphereDir)
        self.sphericalModelsDirectorySelector = ctk.ctkDirectoryButton()
        self.ioQFormLayout.addRow("Spherical Models Directory:", self.sphericalModelsDirectorySelector)

        # Selection of the output directory for Groups (option: --outputDir)
        self.outputDirectorySelector = ctk.ctkDirectoryButton()
        self.ioQFormLayout.addRow(qt.QLabel("Output Directory:"), self.outputDirectorySelector)

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
        self.specifyPropertySelector.addItems(("medialMeshArea","medialMeshPartialArea","medialMeshRadius","medialMeshPartialRadius","paraPhi","paraTheta"))
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
        self.labelArea = qt.QLabel("medialMeshArea")
        self.weightline1.addWidget(self.labelArea)
        self.weightArea = ctk.ctkDoubleSpinBox()
        self.weightArea.enabled = False
        self.weightArea.value = 1
        self.weightline1.addWidget(self.weightArea)

        self.labelPartialArea = qt.QLabel("medialMeshPartialArea")
        self.weightline1.addWidget(self.labelPartialArea)
        self.weightPartialArea = ctk.ctkDoubleSpinBox()
        self.weightPartialArea.enabled = False
        self.weightPartialArea.value = 1
        self.weightline1.addWidget(self.weightPartialArea)

        # Fill out second line
        self.labelRadius = qt.QLabel("medialMeshRadius")
        self.weightline2.addWidget(self.labelRadius)
        self.weightRadius = ctk.ctkDoubleSpinBox()
        self.weightRadius.enabled = False
        self.weightRadius.value = 1
        self.weightline2.addWidget(self.weightRadius)

        self.labelPartialRadius = qt.QLabel("medialMeshPartialRadius")
        self.weightline2.addWidget(self.labelPartialRadius)
        self.weightPartialRadius = ctk.ctkDoubleSpinBox()
        self.weightPartialRadius.enabled = False
        self.weightPartialRadius.value = 1
        self.weightline2.addWidget(self.weightPartialRadius)

        # Fill out third line
        self.labelparaPhi = qt.QLabel("paraPhi")
        self.weightline3.addWidget(self.labelparaPhi)
        self.weightparaPhi = ctk.ctkDoubleSpinBox()
        self.weightparaPhi.enabled = False
        self.weightparaPhi.value = 1
        self.weightline3.addWidget(self.weightparaPhi)

        self.labelparaTheta = qt.QLabel("paraTheta")
        self.weightline3.addWidget(self.labelparaTheta)
        self.weightparaTheta = ctk.ctkDoubleSpinBox()
        self.weightparaTheta.enabled = False
        self.weightparaTheta.value = 1
        self.weightline3.addWidget(self.weightparaTheta)

        self.paramQFormLayout.addRow("Weight of each property:", self.weightLayout)

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

        self.errorLabel = qt.QLabel("Error: Invalide inputs")
        self.errorLabel.hide()
        self.errorLabel.setStyleSheet("color: rgb(255, 0, 0);")
        self.ioQVBox.addWidget(self.errorLabel)


        # Connections
        self.applyButton.connect('clicked(bool)', self.onApplyButtonClicked)

        # ----- Add vertical spacer ----- #
        self.layout.addStretch(1)


        #### SET PARAMETERS - for test!!
        self.inputModelsDirectorySelector.directory = "/Users/prisgdd/Desktop/TestPipeline/inputGroups/Mesh"
        self.inputPropertyDirectorySelector.directory = "/Users/prisgdd/Desktop/TestPipeline/inputGroups/attributes"
        self.outputDirectorySelector.directory = "/Users/prisgdd/Desktop/TestPipeline/outputGroups"
        self.sphericalModelsDirectorySelector.directory = "/Users/prisgdd/Desktop/TestPipeline/inputGroups/sphere"
        self.degreeSpharm.value = 15
        self.maxIter.value = 1000

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

        # Hide error message if printed
        self.errorLabel.hide()

    ## Function onSpecifyPropertyChanged(self):
    # Enable/Disable associated weights
    def onSpecifyPropertyChanged(self):
        if self.specifyPropertySelector.currentIndex == 0:
            self.weightArea.enabled = not self.weightArea.enabled

        if self.specifyPropertySelector.currentIndex == 1:
            self.weightPartialArea.enabled = not self.weightPartialArea.enabled

        if self.specifyPropertySelector.currentIndex == 2:
            self.weightRadius.enabled = not self.weightRadius.enabled

        if self.specifyPropertySelector.currentIndex == 3:
            self.weightPartialRadius.enabled = not self.weightPartialRadius.enabled

        if self.specifyPropertySelector.currentIndex == 4:
            self.weightparaPhi.enabled = not self.weightparaPhi.enabled

        if self.specifyPropertySelector.currentIndex == 5:
            self.weightparaTheta.enabled = not self.weightparaTheta.enabled

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
            endGroup = logic.runGroups(modelsDir=self.modelsDirectory, propertyDir=self.propertyDirectory, sphereDir=self.sphereDirectory, outputDir=self.outputDirectory)

        else:
            # ----- Creation of string for the specified properties and their values ----- #
            self.property = ""
            self.propertyValue = ""

            if self.weightArea.enabled:
                self.propertyValue = self.propertyValue + str(self.weightArea.value)
                self.property = self.property + "medialMeshArea.txt"

            if self.weightPartialArea.enabled:
                if self.propertyValue != "":
                    self.propertyValue = self.propertyValue + ","
                    self.property = self.property + ","

                self.propertyValue = self.propertyValue + str(self.weightPartialArea.value)
                self.property = self.property + "medialMeshPartialArea.txt"

            if self.weightRadius.enabled:
                if self.propertyValue != "":
                    self.propertyValue = self.propertyValue + ","
                    self.property = self.property + ","

                self.propertyValue = self.propertyValue + str(self.weightRadius.value)
                self.property = self.property + "medialMeshRadius.txt"

            if self.weightPartialRadius.enabled:
                if self.propertyValue != "":
                    self.propertyValue = self.propertyValue + ","
                    self.property = self.property + ","

                self.propertyValue = self.propertyValue + str(self.weightPartialRadius.value)
                self.property = self.property + "medialMeshPartialRadius.txt"

            if self.weightparaPhi.enabled:
                if self.propertyValue != "":
                    self.propertyValue = self.propertyValue + ","
                    self.property = self.property + ","

                self.propertyValue = self.propertyValue + str(self.weightparaPhi.value)
                self.property = self.property + "paraPhi.txt"

            if self.weightparaTheta.enabled:
                if self.propertyValue != "":
                    self.propertyValue = self.propertyValue + ","
                    self.property = self.property + ","

                self.propertyValue = self.propertyValue + str(self.weightparaTheta.value)
                self.property = self.property + "paraTheta.txt"

            if self.property == "" and self.propertyValue == "":                         # Si aucune propriete selectionnee
                self.property = 0
                self.propertyValue = 0

            d = int(self.degreeSpharm.value)
            m = int(self.maxIter.value)

            endGroup = logic.runGroups(modelsDir = self.modelsDirectory, propertyDir = self.propertyDirectory,
                                    sphereDir = self.sphereDirectory, outputDir = self.outputDirectory, properties = self.property,
                                    propValues = self.propertyValue, degree = d, maxIter = m)

        ## Groups didn't run because of invalid inputs
        if not endGroup:
            self.errorLabel.show()

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
    def runGroups(self, modelsDir, propertyDir, sphereDir, outputDir, properties=0, propValues=0, degree=0, maxIter=0):
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
             -d: Degree of deformation field
             --maxIter: Maximum number of iteration
        """

        #####################################################################################
        ## ----- Check if directories contents correctly match with models Directory ----- ##
        # For each shape, files should have the same name, with different extension.
        #       Mesh: [name].vtk
        #       Properties: 8 x [name].vtk.[prop].txt
        #       Sphere: [name].txt.vtk
# if file[len(file)-len(suffixSphere):] == suffixSphere:
        

        ## Preparation of the reference list (from modelsDir)
        listModelsDir = os.listdir(modelsDir)
        listModelsName = list()
        if listModelsDir.count(".DS_Store"):
            listModelsDir.remove(".DS_Store")
        if not len(listModelsDir):
            return False


        # Get the list of all basename + check if they are all vtk files
        for i in range(0, len(listModelsDir)):
            modelsExtension = "_surfSPHARM_procalign.vtk"
            listModelsName.append( listModelsDir[i][:len(listModelsDir[i])-len(modelsExtension)] )
            print "model num " + str(i) + " : " + listModelsName[i]

        ## Check other directories
        listPropertyDir = os.listdir(propertyDir)
        listPropertyName = list()
        if listPropertyDir.count(".DS_Store"):
            listPropertyDir.remove(".DS_Store")
        # There should be 6 files for each one in modelsDir
        for i in range(0, len(listPropertyDir)):
            listPropertyName.append(str(('_').join(listPropertyDir[i].split('_')[:-2])))
        for file in listModelsName:
            if listPropertyName.count(file) != 6:
                print "Properties. Not enough properties for " + str(file)
                return False        


        listSphereDir = os.listdir(sphereDir)
        listSphereName = list()
        if listSphereDir.count(".DS_Store"):
            listSphereDir.remove(".DS_Store")
        # There should be the same basename files
        suffix = "_surf_para.vtk"
        for i in range(0, len(listSphereDir)): 
            end = listSphereDir[i][len(listSphereDir[i])-len(suffix):]
            print end
            if end == suffix:
                print "suffix OK"
                listSphereName.append('_'.join(listSphereDir[i].split('_')[:-2]))
            else:
                print "else suff"
                listSphereName.append('_'.join(listSphereDir[i].split('_')[:-1]))
            print "name sphare :: " + listSphereName[i]

        for file in listModelsName:
            if listSphereName.count(file) != 1:
                print "Sphere. Wrong correspondence between name files " + str(file)
                return False

        # Get the list of all basename + check if they are all vtk files
        # for i in range(0, len(listModelsDir)):
        #     extension = listModelsDir[i].split('.')[-1]
        #     if extension == 'vtk':
        #         listModelsName.append('.'.join(listModelsDir[i].split('.')[:-1]))

        # ## Check other directories
        # listPropertyDir = os.listdir(propertyDir)
        # listPropertyName = list()
        # if listPropertyDir.count(".DS_Store"):
        #     listPropertyDir.remove(".DS_Store")
        # # There should be 8 files for each one in modelsDir
        # listPropertyName = ['.'.join(file.split('.')[:-3]) for file in listPropertyDir]
        # for file in listModelsName:
        #     if listPropertyName.count(file) != 6:
        #         print "Properties. Not enough properties for " + str(file)
        #         return False

        # listSphereDir = os.listdir(sphereDir)
        # listSphereName = list()
        # if listSphereDir.count(".DS_Store"):
        #     listSphereDir.remove(".DS_Store")
        # # There should be the same basename files
        # listSphereName = ['.'.join(file.split('.')[:-2]) for file in listSphereDir]
        # for file in listModelsName:
        #     if listSphereName.count(file) != 1:
        #         print "Sphere. Wrong correspondence between name files " + str(file)
        #         return False

        ############################################
        # ----- Creation of the command line ----- #

        # Avec le make package
        # self.moduleName = "Groups"
        # scriptedModulesPath = eval('slicer.modules.%s.path' % self.moduleName.lower())
        # scriptedModulesPath = os.path.dirname(scriptedModulesPath)
        
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
            arguments.append("medialMeshArea.txt,medialMeshPartialArea.txt,medialMeshRadius.txt,medialMeshPartialRadius.txt,paraPhi.txt,paraTheta.txt")
            arguments.append("-w")
            arguments.append("1.0,1.0,1.0,1.0,1.0,1.0")

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
        self.process.setProcessChannelMode(qt.QProcess.MergedChannels)

        # print "Calling " + os.path.basename(groups)
        self.process.start(groups, arguments)
        self.process.waitForStarted()
        # # print "state: " + str(self.process.state())
        self.process.waitForFinished(-1)
        # print "error: " + str(self.process.error())

        processOutput = str(self.process.readAll())
        sizeProcessOutput = len(processOutput)

        finStr = processOutput[sizeProcessOutput - 10:sizeProcessOutput]
        print "finStr : " + finStr
        if finStr == "All done!":
            return False

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

        ## Prepare data & paths
        self.initialPath = "/Users/prisgdd/Documents/Projects/GroupsExtension/dataTest/"
        self.localPath = slicer.app.temporaryPath + "/dataTest"

        if os.path.isdir(self.localPath):
            shutil.rmtree(self.localPath)

        shutil.copytree(self.initialPath, self.localPath)

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
        meshDir = self.localPath + "/Mesh"
        propertiesDir = self.localPath + "/attributes"
        landmarkDir = self.localPath + "/landmark"
        sphereDir = self.localPath + "/sphere"
        degree = 5
        maxIter = 1000
        properties = "C.txt,S.txt"
        propertiesValues = "0.5,0.25"
        outputVerif1 = self.localPath + "/outputVerif/outputVerif1"
        outputDir1 = self.localPath + "/outputTest/outputTest1"

        if not os.path.exists(outputDir1):
            os.mkdir(outputDir1)

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
        meshDir = self.localPath + "/Mesh"
        propertiesDir = self.localPath + "/attributes"
        landmarkDir = self.localPath + "/landmark"
        sphereDir = self.localPath + "/sphere"
        degree = 5
        maxIter = 5000
        properties = "C.txt,H.txt,Kappa1.txt,S.txt,K.txt,Kappa2.txt,DPhi.txt,DTheta.txt"
        propertiesValues = "0.2,1.0,0.3,0.25,0.3,0.8,0.1,0.4"
        outputDir2 = self.localPath + "/outputTest/outputTest2"
        outputVerif2 = self.localPath + "/outputVerif/outputVerif2"

        if not os.path.exists(outputDir2):
            os.mkdir(outputDir2)

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
        meshDir = self.localPath + "/Mesh"
        propertiesDir = self.localPath + "/attributes"
        sphereDir = self.localPath + "/sphere"
        degree = 5
        maxIter = 1000
        properties = "C.txt,S.txt"
        propertiesValues = "0.5,0.25"
        outputDir3 = self.localPath + "/outputTest/outputTest3"
        outputVerif3 = self.localPath + "/outputVerif/outputVerif3"

        if not os.path.exists(outputDir3):
            os.mkdir(outputDir3)

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
        meshDir = self.localPath + "/Mesh"
        propertiesDir = self.localPath + "/attributes"
        landmarkDir = self.localPath + "/landmark"
        sphereDir = self.localPath + "/sphere"
        degree = 18
        maxIter = 1000
        outputDir4 = self.localPath + "/outputTest/outputTest4"
        outputVerif4 = self.localPath + "/outputVerif/outputVerif4"

        if not os.path.exists(outputDir4):
            os.mkdir(outputDir4)

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
        meshDir = self.localPath + "/Mesh"
        propertiesDir = self.localPath + "/attributes"
        sphereDir = self.localPath + "/sphere"
        landmarkDir = self.localPath + "/landmark"
        degree = 5
        maxIter = 1000
        properties = "DPhi.txt,C.txt,S.txt,Kappa1.txt"
        propertiesValues = "0.1,0.3"
        outputDir5 = self.localPath + "/outputTest/outputTest5"
        outputVerif5 = self.localPath + "/outputVerif/outputVerif5"

        if not os.path.exists(outputDir5):
            os.mkdir(outputDir5)

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
        meshDir = self.localPath + "/Mesh"
        propertiesDir = self.localPath + "/attributes"
        sphereDir = self.localPath + "/sphere"
        landmarkDir = self.localPath + "/landmark"
        properties = "C.txt,S.txt"
        propertiesValues = "0.5,0.25"
        outputDir6 = self.localPath + "/outputTest/outputTest6"
        outputVerif6 = self.localPath + "/outputVerif/outputVerif6"

        if not os.path.exists(outputDir6):
            os.mkdir(outputDir6)

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
