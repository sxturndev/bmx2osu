# BMX2OSU by sxturndev

# Imports
import os, sys
import PyQt5.QtWidgets as qtw
from PyQt5.QtCore import QProcess

convertTo7k = False
convertSounds = False

dirname = os.path.dirname(__file__)
inputPath = os.path.join(dirname, 'input')
outputPath = os.path.join(dirname, 'output')

class MainWindow(qtw.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("BMX2OSU (by sxturndev)")
        layout = qtw.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.converter()
        self.output()
        self.show()

    def converter(self):
        converter = qtw.QVBoxLayout()
        converter.layout().setContentsMargins(10, 10, 10, 0)

        # Open file layout
        top = qtw.QHBoxLayout()
        openFolder = qtw.QPushButton('Open Folder')
        self.fileInput = qtw.QLineEdit()
        top.addWidget(openFolder)
        top.addWidget(self.fileInput)
        
        # Options layout
        options = qtw.QVBoxLayout()
        include7k = qtw.QCheckBox(text='Include 7k Version')
        convertAudio = qtw.QCheckBox(text='Convert Audio to .mp3 (Removes keysounds)')
        options.addWidget(include7k)
        options.addWidget(convertAudio)

        # Github link and Convert button layout
        bottom = qtw.QHBoxLayout()
        github = qtw.QLabel('<a href=\"https://github.com/sxturndev/bmx2osu\">Github</a>')
        github.setOpenExternalLinks(True)
        spacer = qtw.QSpacerItem(0, 0, qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Minimum)
        self.convert = qtw.QPushButton('Convert')
        bottom.addWidget(github)
        bottom.addItem(spacer)
        bottom.addWidget(self.convert)
        
        self.convert.clicked.connect(lambda: convertToOsu(self, inputPath))

        # Add Layouts
        converter.layout().addLayout(top)
        converter.layout().addLayout(options)
        converter.layout().addLayout(bottom)
        self.layout().addLayout(converter)

    def output(self):
        output = qtw.QVBoxLayout()
        output.layout().setContentsMargins(10, 0, 10, 10)

        groupBox = qtw.QGroupBox('Output')
        groupBox.setLayout(qtw.QVBoxLayout())
        self.outputBox = qtw.QTextEdit()
        groupBox.layout().addWidget(self.outputBox)

        output.layout().addWidget(groupBox)
        self.layout().addLayout(output)

    def logger(self, text):
        self.outputBox.append(text)


def handle_stdout(gui, process):
    line = process.readAllStandardOutput().data().decode('utf-8').strip()
    print(line)
    mw.logger(line)


def convertToOsu(gui, path):
    gui.logger('CONVERTING to .OSU\n-----------------------')

    bmt = QProcess()
    bmt.readyReadStandardOutput.connect(lambda: handle_stdout(mw, bmt))
    bmt.start('bmt.exe', ['-i', path, '-o', outputPath, '-type', 'osu'])
    

def convertAudio():
    print('Converting Audio')


def convert7k():
    print('Converting to 7k')


def zipToOsz():
    print('Zipping to .osz')


app = qtw.QApplication([])
app.setStyle('Fusion')
mw = MainWindow()
mw.resize(400, 400)
sys.exit(app.exec_())

