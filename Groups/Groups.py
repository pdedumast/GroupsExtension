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

        """
        Collapsible part for input/output parameters for Groups CLI
        """
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

        # CheckBox. If checked, Group Box parameters will be enabled
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

        # Selection of the property we want to use (option: -x, then --filter)
        self.specifyPropertySelector = ctk.ctkCheckableComboBox()
        self.specifyPropertySelector.addItems(("C","H","Kappa1","S","K","Kappa2","DPhi","DTheta"))
        self.paramQFormLayout.addRow(qt.QLabel("Properties name to use:"), self.specifyPropertySelector)

        # Weights of each property - Choices on 2 lines (option: ??, then -w)
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

        # Selection of the directory which contains each spherical model (option: -??, then --landmarkDir)
        self.landmarkDirectorySelector = ctk.ctkDirectoryButton()
        self.paramQFormLayout.addRow(qt.QLabel("Landmark Directory:"), self.landmarkDirectorySelector)

        # Specification of the SPHARM decomposition degree (option: -d)
        self.degreeSpharm = ctk.ctkSliderWidget()
        self.degreeSpharm.minimum = 0
        self.degreeSpharm.maximum = 50
        self.degreeSpharm.value = 5        # initial value
        self.degreeSpharm.setDecimals(0)
        self.paramQFormLayout.addRow(qt.QLabel("Degree of SPHARM decomposition:"), self.degreeSpharm)

        # Maximum iteration (option: ??, then --maxIter)
        self.maxIter = qt.QSpinBox()
        self.maxIter.minimum = 0            # Check the range authorized
        self.maxIter.maximum = 100000
        self.maxIter.value = 10000
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


        #### SET PARAMETERS - test
        self.inputModelsDirectorySelector.directory = "/Users/prisgdd/Desktop/Example/Mesh"
        self.inputPropertyDirectorySelector.directory = "/Users/prisgdd/Desktop/Example/attributes"
        self.outputDirectorySelector.directory = "/Users/prisgdd/Desktop/OUTPUTGROUPS"

        # self.landmarkDirectorySelector.directory = "/Users/prisgdd/Desktop/Example/landmark"
        self.sphericalModelsDirectorySelector.directory = "/Users/prisgdd/Desktop/Example/sphere"

        self.maxIter.value = 5

    ## Function cleanup(self):
    def cleanup(self):
        pass

    ## Function onSelect(self):
    # Check if each directory (Models, Property, Output) have been choosen.
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

    ## Function onSelect(self):
    # Enable associated weights
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
    # Enable the parameter Group Box if check boc checked
    def onCheckBoxParam(self):
        if self.enableParamCB.checkState():
            self.parametersGroupBox.setEnabled(True)
        else:
            self.parametersGroupBox.setEnabled(False)

    ## Function onApplyButtonClicked(self):
        # Update every parameters
        # Check directories are ok
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
            logic.runGroups(modelsDir = self.modelsDirectory, propertyDir = self.propertyDirectory, sphereDir = self.sphereDirectory, outputDir = self.outputDirectory)

        else:
            # ----- Creation of string for the specified properties and their values -----

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

            d = self.degreeSpharm.value
            m = self.maxIter.value

# self, modelsDir, propertyDir, outputDir, properties=0, propValues=0, landmark=0, degree=0, sphereDir=0, maxIter=0

            logic.runGroups(modelsDir = self.modelsDirectory, propertyDir = self.propertyDirectory, sphereDir = self.sphereDirectory, outputDir = self.outputDirectory, properties = self.property, propValues = self.propertyValue, landmark = landmark, degree = d, maxIter = m)


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

    def hasImageData(self, volumeNode):
        """This is an example logic method that
    returns true if the passed in volume
    node has valid image data
    """
        if not volumeNode:
            logging.debug('hasImageData failed: no volume node')
            return False
        if volumeNode.GetImageData() is None:
            logging.debug('hasImageData failed: no image data in volume node')
            return False
        return True

    def isValidInputOutputData(self, inputVolumeNode, outputVolumeNode):
        """Validates if the output is not the same as input
    """
        if not inputVolumeNode:
            logging.debug('isValidInputOutputData failed: no input volume node defined')
            return False
        if not outputVolumeNode:
            logging.debug('isValidInputOutputData failed: no output volume node defined')
            return False
        if inputVolumeNode.GetID() == outputVolumeNode.GetID():
            logging.debug(
                'isValidInputOutputData failed: input and output volume is the same. Create a new volume for output to avoid this error.')
            return False
        return True

    def takeScreenshot(self, name, description, type=-1):
        # show the message even if not taking a screen shot
        slicer.util.delayDisplay(
            'Take screenshot: ' + description + '.\nResult is available in the Annotations module.', 3000)

        lm = slicer.app.layoutManager()
        # switch on the type to get the requested window
        widget = 0
        if type == slicer.qMRMLScreenShotDialog.FullLayout:
            # full layout
            widget = lm.viewport()
        elif type == slicer.qMRMLScreenShotDialog.ThreeD:
            # just the 3D window
            widget = lm.threeDWidget(0).threeDView()
        elif type == slicer.qMRMLScreenShotDialog.Red:
            # red slice window
            widget = lm.sliceWidget("Red")
        elif type == slicer.qMRMLScreenShotDialog.Yellow:
            # yellow slice window
            widget = lm.sliceWidget("Yellow")
        elif type == slicer.qMRMLScreenShotDialog.Green:
            # green slice window
            widget = lm.sliceWidget("Green")
        else:
            # default to using the full window
            widget = slicer.util.mainWindow()
            # reset the type so that the node is set correctly
            type = slicer.qMRMLScreenShotDialog.FullLayout

        # grab and convert to vtk image data
        qpixMap = qt.QPixmap().grabWidget(widget)
        qimage = qpixMap.toImage()
        imageData = vtk.vtkImageData()
        slicer.qMRMLUtils().qImageToVtkImageData(qimage, imageData)

        annotationLogic = slicer.modules.annotations.logic()
        annotationLogic.CreateSnapShot(name, description, type, 1, imageData)


    ## Function runGroups(...)
    #
    #
    def runGroups(self, modelsDir, propertyDir, sphereDir, outputDir, properties=0, propValues=0, landmark=0, degree=0, maxIter=0):
        print "--- function runGroups() ---"

        """
        Calling Groups CLI
            Arguments:
             --surfaceDir: Directory with input models
             --propertyDir: Property folder (txt files from SPHARM)
             --outputDir: Output directory
        """

        # ----- Creation of the command line -----

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


        if properties:
            arguments.append("--filter")
            arguments.append(properties)
        else:       # Si proprietes non precisees
            arguments.append("--filter")
            arguments.append("C.txt,H.txt,Kappa1.txt,S.txt,K.txt,Kappa2.txt,DPhi.txt,DTheta.txt")

        if propValues:
            arguments.append("-w")
            arguments.append(propValues)
        else:
            arguments.append("-w")
            arguments.append("1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0")


        if landmark:
            arguments.append("--landmarkDir")
            arguments.append(landmark)

        if degree:
            arguments.append("-d")
            arguments.append(int(degree))
        else:
            arguments.append("-d")
            arguments.append(5)

        if maxIter:
            arguments.append("--maxIter")
            arguments.append(maxIter)
        else:
            arguments.append("--maxIter")
            # arguments.append(10000)
            arguments.append(10)

        print arguments

        # ----- Call the CLI -----
        self.process = qt.QProcess()
        # self.process.setProcessChannelMode(qt.QProcess.MergedChannels)

        print "Calling " + os.path.basename(groups)
        self.process.start(groups, arguments)
        self.process.waitForStarted()
        # print "state: " + str(self.process.state())
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
        self.setUp()
        self.test_Groups1()

    def test_Groups1(self):
        """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

        self.delayDisplay("Starting the test")
        #
        # first, get some data
        #
        import urllib
        downloads = (
            ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
        )

        for url, name, loader in downloads:
            filePath = slicer.app.temporaryPath + '/' + name
            if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
                logging.info('Requesting download %s from %s...\n' % (name, url))
                urllib.urlretrieve(url, filePath)
            if loader:
                logging.info('Loading %s...' % (name,))
                loader(filePath)
        self.delayDisplay('Finished with download and loading')

        volumeNode = slicer.util.getNode(pattern="FA")
        logic = GroupsLogic()
        self.assertIsNotNone(logic.hasImageData(volumeNode))
        self.delayDisplay('Test passed!')