# BMX2OSU by sxturndev

# Imports
import os, sys, math
import PyQt5.QtWidgets as qtw
from PyQt5.QtCore import QProcess

convertTo7k = False
convertSounds = False
overallDifficulty = ''
hpDrainRate = ''

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
        converter.setContentsMargins(10, 10, 10, 0)

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

        diffOptions = qtw.QFormLayout()
        self.od = qtw.QLineEdit()
        self.od.setPlaceholderText('(Default 8.0)')
        self.od.setFixedWidth(75)
        self.hp = qtw.QLineEdit()
        self.hp.setPlaceholderText('(Default 8.5)')
        self.hp.setFixedWidth(75)
        diffOptions.addRow('OD:', self.od)
        diffOptions.addRow('HP:', self.hp)

        options.addWidget(self.include7k)
        options.addWidget(self.convertAudio)
        options.addLayout(diffOptions)

        # Github link and Convert button layout
        bottom = qtw.QHBoxLayout()
        github = qtw.QLabel('<a href=\"https://github.com/sxturndev/bmx2osu\">Github</a>')
        github.setOpenExternalLinks(True)
        spacer = qtw.QSpacerItem(0, 0, qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Minimum)
        self.convert = qtw.QPushButton('Convert')
        self.convert.clicked.connect(convert)

        bottom.addWidget(github)
        bottom.addItem(spacer)
        bottom.addWidget(self.convert)

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
        self.outputBox.setReadOnly(True)
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
    mw.od.setEnabled(enabled)
    mw.hp.setEnabled(enabled)


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
        mw.logger('<font color="red"><b>No input path selected!</b></font>')
        return
    if (len(os.listdir(inputPath)) == 0):
        mw.logger('<font color="red"><b>Nothing found in input folder!</b></font>')
        return
    if not (os.access(outputPath, os.F_OK)):
        mw.logger('<font color="red"><b>Output folder doesn\'t exist... Creating.</b></font>')
        os.mkdir(outputPath)
    if (len(os.listdir(outputPath)) != 0):
        mw.logger('<font color="red"><b>Files exist in output folder!</b></font>')
        return

    mw.logger(f'Input path: {inputPath}')
    mw.logger(f'Output path: {outputPath}\n')
    mw.logger('<b>Starting conversion</b><br>-----------------------')

    # Disable UI when starting processing
    ui_state(False)

    # Add args for bmtranslator
    def args():
        global overallDifficulty, hpDrainRate

        overallDifficulty = mw.od.text()
        hpDrainRate = mw.hp.text()

        args = ['-i', inputPath, '-o', outputPath, '-type', 'osu']
        if overallDifficulty != '':
            args.append('-od')
            args.append(overallDifficulty)
        if hpDrainRate != '':
            args.append('-hp')
            args.append(hpDrainRate)
        mw.logger(f'bmt.exe {" ".join(args)}\n')
        return args

    # Run bmtranslator
    bmt = QProcess()
    bmt.readyReadStandardOutput.connect(lambda: handle_stdout(bmt))
    bmt.readyReadStandardError.connect(lambda: handle_stderr(bmt))
    bmt.start('bmt.exe', args())

    bmt.finished.connect(finish_processing)


def finish_processing():
    global convertTo7k, convertSounds
    mw.logger('<br><font color="green"><b>Finished processing with bmtranslator</b></font><br>-----------------------')
            
    convertTo7k = mw.include7k.isChecked()
    convertSounds = mw.convertAudio.isChecked()

    folders = os.listdir(outputPath)
    if (len(folders) == 0):
        mw.logger('<br><font color="red"><b>No folders found in output! Stopping. Please check your settings and input folder.</b></font>')
        ui_state(True)
        return

    songs = list(map(lambda folder: os.path.join(outputPath, folder), folders))

    for i in range(len(songs)):
        song = songs[i]
        progress = f'[{i+1}/{len(songs)}]'
        mw.logger(f'<font color="blue"><b>{progress} Processing: {os.path.basename(song)}</b></font><br>')

        if convertTo7k:
            convert7k(song)
        if convertSounds:
            convertAudio(song)
        zipToOsz(song)

    mw.logger('<br><br><font size="5">FINISHED</b></font>')
    ui_state(True)


def convert7k(song):
    folderName = os.path.basename(song)
    mw.logger(f'<b>* Converting {folderName} to 7 keys. *</b>')
    difficulties = list(filter(lambda x: os.path.splitext(x)[1] == '.osu', os.listdir(song)))
    difficulties = list(map(lambda x: os.path.join(song, x), difficulties))
    total = len(difficulties)

    mw.logger(f'Found {total} charts to convert.\n')
    for i in range(total):
        diff = difficulties[i]
        diffName = os.path.basename(diff)
        progress = f'[{i+1}/{total}]'
        mw.logger(f'<b>{progress}</b> Converting {diffName} to 7key...')

        # Read File
        file = open(diff, 'r', encoding='utf-8')
        lines = file.read().splitlines()
        tpIndex = lines.index('[TimingPoints]')
        hitObjIndex = lines.index('[HitObjects]')
        data = lines[:tpIndex]
        timingPoints = lines[tpIndex:hitObjIndex]
        notes = lines[hitObjIndex:]
        lines.clear()
        file.close()

        # Edit metadata
        for i in range(len(data)):
            if data[i].startswith('Version'):
                split = data[i].split(':')
                data[i] = f'Version:[7K] {split[1]}'
                mw.logger(f'Set version to: [7K] {split[1]}')
            if data[i].startswith('CircleSize'):
                data[i] = 'CircleSize: 7'
                mw.logger('Set key count to 7.')
                break
        
        # Move scratch note sound to storyboard
        def moveToStoryboard(note):
            isLongNote = False
            time = note[2]
            hitSample = note[len(note) - 1].split(':')

            if (int(hitSample[0]) > 3):
                isLongNote = True
            
            if isLongNote:
                newEvent = 'Sample,{},0,"{}",100'.format(time, hitSample[5])  
            else:
                newEvent = 'Sample,{},0,"{}",100'.format(time, hitSample[4])

            data.append(newEvent)

        # Note conversion
        # Set i to 1 to skip [HitObjects]
        i = 1 
        scratchRemoved = 0
        while i < len(notes):
            note = notes[i].split(',')
            columnIndex = math.floor(int(note[0]) * 8 / 512)
            newColumn = ['36', '109', '182', '256', '329', '402', '475']

            if columnIndex == 0:
                notes.pop(i)
                i -= 1
                moveToStoryboard(note)
                scratchRemoved += 1
            if (columnIndex >= 1 and columnIndex <= 7):
                note[0] = newColumn[columnIndex-1]
                notes[i] = ','.join(note)
            i += 1
        mw.logger(f'Removed {scratchRemoved} scratch notes.')

        # Write to new file
        newFileName = f'[7K] {diffName}'
        newFilePath = os.path.join(song, newFileName)
        with open(newFilePath, 'w', encoding='utf-8') as file:
            for line in data:
                file.write(line + "\n")
            for line in timingPoints:
                file.write(line + "\n")
            for line in notes:
                file.write(line + "\n")
        mw.logger(f'Wrote to file: {newFileName}\n')
        

def convertAudio(song):
    mw.logger(f'<b>* Converting audio for {os.path.basename(song)} *</b>')


def zipToOsz(song):
    mw.logger(f'<b>* Zipping {os.path.basename(song)} to .osz *</b><br>')
    mw.logger('<font color="green"><b>Done</b></font><br>-----------------------')


app = qtw.QApplication([])
app.setStyle('Fusion')
mw = MainWindow()
mw.resize(400, 500)
sys.exit(app.exec_())

