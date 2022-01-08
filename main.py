# BMX2OSU by sxturndev

# Imports
import os, sys
import PyQt5.QtWidgets as qtw
from PyQt5.QtCore import QProcess

convertTo7k = False
convertSounds = False

dirname = os.path.dirname(__file__)
inputPath = ''
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
        self.openFolder = qtw.QPushButton('Open Folder')
        self.folderInput = qtw.QLineEdit()
        top.addWidget(self.openFolder)
        top.addWidget(self.folderInput)

        self.openFolder.clicked.connect(get_input)
        
        # Options layout
        options = qtw.QVBoxLayout()
        self.include7k = qtw.QCheckBox(text='Include 7k Version')
        self.convertAudio = qtw.QCheckBox(text='Convert Audio to .mp3 (Removes keysounds)')
        options.addWidget(self.include7k)
        options.addWidget(self.convertAudio)

        # Github link and Convert button layout
        bottom = qtw.QHBoxLayout()
        github = qtw.QLabel('<a href=\"https://github.com/sxturndev/bmx2osu\">Github</a>')
        github.setOpenExternalLinks(True)
        spacer = qtw.QSpacerItem(0, 0, qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Minimum)
        self.convert = qtw.QPushButton('Convert')
        bottom.addWidget(github)
        bottom.addItem(spacer)
        bottom.addWidget(self.convert)
        
        self.convert.clicked.connect(convert)

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


def ui_state(enabled: bool):
    mw.openFolder.setEnabled(enabled)
    mw.folderInput.setEnabled(enabled)
    mw.convertAudio.setEnabled(enabled)
    mw.include7k.setEnabled(enabled)
    mw.convert.setEnabled(enabled)


# Pipe stdout and stderr
def handle_stdout(process):
    line = process.readAllStandardOutput().data().decode('utf-8').strip()
    mw.logger(line)


def handle_stderr(process):
    line = process.readAllStandardError().data().decode('utf-8').strip()
    mw.logger(line)


# Open file dialog
def get_input():
    global inputPath
    dir = qtw.QFileDialog.getExistingDirectory(
        parent=mw,
        caption='Open Song Directory',
    )
    inputPath = dir
    mw.folderInput.setText(inputPath)


def convert():
    if (inputPath == ''):
        mw.logger('No input path selected!')
        return
    if not (os.access(outputPath, os.F_OK)):
        mw.logger('Output folder doesn\'t exist... Creating.')
        os.mkdir(outputPath)
    if (len(os.listdir(outputPath)) != 0):
        mw.logger('Files exist in output folder!')
        return

    mw.logger(f'Input path: {inputPath}')
    mw.logger(f'Output path: {outputPath}\n')
    mw.logger('CONVERTING to .OSU\n-----------------------')

    # Disable UI when starting processing
    ui_state(False)

    bmt = QProcess()
    bmt.readyReadStandardOutput.connect(lambda: handle_stdout(bmt))
    bmt.readyReadStandardError.connect(lambda: handle_stderr(bmt))
    bmt.start('bmt.exe', ['-i', inputPath, '-o', outputPath, '-type', 'osu'])

    bmt.finished.connect(finish_processing)


def finish_processing():
    global convertTo7k, convertSounds
    mw.logger('\nFinished converting with bmtranslator\n')

    convertTo7k = mw.include7k.isChecked()
    convertSounds = mw.convertAudio.isChecked()

    folders = os.listdir(outputPath)
    if (len(folders) == 0):
        mw.logger('No folders found in output!')
        return

    songs = []
    for folder in folders:
        songs.append(os.path.join(outputPath, folder))
    
    for song in songs:
        mw.logger('Processing: ' + os.path.basename(song) + "\n")
        if convertTo7k:
            convert7k(song)
        if convertSounds:
            convertAudio(song)
        zipToOsz(song)
    ui_state(True)


def convert7k(song):
    mw.logger('CONVERTING TO 7K\n-----------------------')


def convertAudio(song):
    mw.logger('CONVERTING AUDIO\n-----------------------')


def zipToOsz(song):
    mw.logger('ZIPPING TO .OSZ\n-----------------------')

    mw.logger('\n\nFINISHED')


app = qtw.QApplication([])
app.setStyle('Fusion')
mw = MainWindow()
mw.resize(400, 400)
sys.exit(app.exec_())

