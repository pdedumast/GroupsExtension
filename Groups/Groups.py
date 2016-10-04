import os, sys
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging


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

        # Selection of the directory containing the input models (option: -i, then --surfaceDir)
        self.inputModelsDirectorySelector = ctk.ctkDirectoryButton()
        self.ioQFormLayout.addRow(qt.QLabel("Input Models Directory:"), self.inputModelsDirectorySelector)

        # Selection of the input directory containing the property files from SPHARM (txt files) (option: -p, then --propertyDir)
        self.inputPropertyDirectorySelector = ctk.ctkDirectoryButton()
        self.ioQFormLayout.addRow(qt.QLabel("Input Property directory:"), self.inputPropertyDirectorySelector)

        # Selection of the output directory for Groups (option: -o, then --outputDir)
        self.outputDirectorySelector = ctk.ctkDirectoryButton()
        self.ioQFormLayout.addRow(qt.QLabel("Output directory:"), self.outputDirectorySelector)

        # CheckBox. If checked, Group Box parameters will be enabled
        self.enableParamCB = ctk.ctkCheckBox()
        self.enableParamCB.setText("Personalize parameters")
        self.ioQFormLayout.addRow(self.enableParamCB)

        # Connections
        self.inputModelsDirectorySelector.connect("directoryChanged(const QString &)", self.onSelect)
        self.inputPropertyDirectorySelector.connect("directoryChanged(const QString &)", self.onSelect)
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
        self.specifyPropertySelector.addItems(("C","H","Kappa1","T","K","Kappa2"))
        self.paramQFormLayout.addRow(qt.QLabel("Properties name to use:"), self.specifyPropertySelector)

        # Weights of each property - Choices on 2 lines (option: ??, then -w)
        self.weightLayout = qt.QVBoxLayout(self.parametersGroupBox)

        self.weightline1 = qt.QHBoxLayout(self.parametersGroupBox)  # Line 1
        self.weightLayout.addLayout(self.weightline1)
        self.weightline2 = qt.QHBoxLayout(self.parametersGroupBox)  # Line 2
        self.weightLayout.addLayout(self.weightline2)

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
        self.labelT = qt.QLabel("T")
        self.weightline2.addWidget(self.labelT)
        self.weightT = ctk.ctkDoubleSpinBox()
        self.weightT.enabled = False
        self.weightT.value = 1
        self.weightline2.addWidget(self.weightT)

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

        # Selection of the directory which contains each spherical model (option: -alignedSphere, then --sphereDir)
        self.sphericalModelsDirectorySelector = ctk.ctkDirectoryButton()
        self.paramQFormLayout.addRow("Spherical Models Directory:", self.sphericalModelsDirectorySelector)

        # Maximum iteration (option: ??, then --maxIter)
        self.maxIter = qt.QSpinBox()
        self.maxIter.minimum = 0            # Check the range authorized
        self.maxIter.maximum = 100000
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
        self.outputDirectory = str(self.outputDirectorySelector.directory)

        # Check if each directory has been choosen
        self.applyButton.enabled = self.modelsDirectory != "." and self.propertyDirectory != "." and self.outputDirectory != "."

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
            self.weightT.enabled = not self.weightT.enabled

        if self.specifyPropertySelector.currentIndex == 4:
            self.weightK.enabled = not self.weightK.enabled

        if self.specifyPropertySelector.currentIndex == 5:
            self.weightKappa2.enabled = not self.weightKappa2.enabled


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

        if not self.enableParamCB.checkState():
            logic.runGroups(self.modelsDirectory, self.propertyDirectory, self.outputDirectory)

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

            if self.weightT.enabled:
                if self.propertyValue != "":
                    self.propertyValue = self.propertyValue + ","
                    self.property = self.property + ","

                self.propertyValue = self.propertyValue + str(self.weightT.value)
                self.property = self.property + "T.txt"

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

            if self.property == "":
                self.property = 0
            if self.propertyValue == "":
                self.propertyValue = 0

            print self.propertyValue
            print self.property

            if self.landmarkDirectorySelector.directory == ".":
                landmark = 0
            else:
                landmark = self.landmarkDirectorySelector.directory

            if self.sphericalModelsDirectorySelector.directory == ".":
                sphereDir = 0
            else:
                sphereDir = self.sphericalModelsDirectorySelector.directory


            logic.runGroups(self.modelsDirectory, self.propertyDirectory, self.outputDirectory, self.property, self.propertyValue, landmark, self.degreeSpharm.value, sphereDir, self.maxIter.value)


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


    ## Functiun runGroups(...)
    #
    #
    def runGroups(self, modelsDir, propertyDir, outputDir, properties=0, propValues=0, landmark=0, degree=0, sphereDir=0, maxIter=0):
        print "--- function runGroups() ---"

        """
        Calling Groups CLI
            Arguments:
             -i: Directory with input models
             -p: Property folder (txt files from SPHARM)
             -o: Output directory
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
        arguments.append("-i")
        arguments.append(modelsDir)
        arguments.append("-p")
        arguments.append(propertyDir)
        arguments.append("-o")
        arguments.append(outputDir)

        if properties:
            arguments.append("-x")
            arguments.append(properties)
        if propValues:
            arguments.append("-w")
            arguments.append(propValues)

        if landmark:
            arguments.append("-landmarkDir")
            arguments.append(landmark)
        if degree:
            arguments.append("-d")
            arguments.append(degree)
        if sphereDir:
            arguments.append("-sphereDir")
            arguments.append(sphereDir)
        if maxIter:
            arguments.append("-maxIter")
            arguments.append(maxIter)

        print arguments

        # # ----- Call to the CLI -----
        # process = qt.QProcess()
        # print "Calling " + os.path.basename(groups)
        # process.start(groups, arguments)
        # process.waitForStarted()
        # print "state: " + str(process.state())
        # process.waitForFinished()
        # print "error: " + str(process.error())

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
