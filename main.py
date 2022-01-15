# BMX2OSU by sxturndev

# Imports
import os, sys, math, zipfile, shutil
import PyQt5.QtWidgets as qtw
from PyQt5.QtCore import QProcess, QRunnable, QThreadPool, pyqtSignal, QObject
from pydub import AudioSegment

convertTo7k = False
convertSounds = False
convertedTo7k = 0
audioConverted = 0
audioNotConverted = []
foldersZipped = 0
progress = 0

dirname = os.path.dirname(sys.executable) # for PyInstaller
inputPath = ''
outputPath = os.path.join(dirname, 'output')


class WorkerSignals(QObject):
    textoutput = pyqtSignal(str)
    finished = pyqtSignal()


class postProcessing(QRunnable):
    def __init__(self, song: str):
        super(postProcessing, self).__init__()
        self.signals = WorkerSignals()
        self.song = song

    def run(self):
        def convert7k():
            global convertedTo7k
            folderName = os.path.basename(self.song)
            self.signals.textoutput.emit(f'<b>* Converting {folderName} to 7 keys. *</b>')
            difficulties = list(filter(lambda x: os.path.splitext(x)[1] == '.osu', os.listdir(self.song)))
            difficulties = list(map(lambda x: os.path.join(self.song, x), difficulties))
            total = len(difficulties)

            self.signals.textoutput.emit(f'Found {total} charts to convert.\n')
            for i in range(total):
                diff = difficulties[i]
                diffName = os.path.basename(diff)
                prog = f'[{i+1}/{total}]'
                self.signals.textoutput.emit(f'<b>{prog}</b> Converting {diffName} to 7key...')

                # Read File
                file = open(diff, 'r', encoding='utf-8', errors='ignore')
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
                        self.signals.textoutput.emit(f'Set version to: [7K] {split[1]}')
                    if data[i].startswith('CircleSize'):
                        data[i] = 'CircleSize: 7'
                        break
                
                # Move scratch note sound to storyboard
                def moveToStoryboard(note):
                    isLongNote = False
                    time = note[2]
                    hitSample = note[-1].split(':')

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
                self.signals.textoutput.emit(f'Removed {scratchRemoved} scratch notes.')

                # Write to new file
                newFileName = f'[7K] {diffName}'
                newFilePath = os.path.join(self.song, newFileName)
                with open(newFilePath, 'w', encoding='utf-8') as file:
                    for line in data:
                        file.write(line + "\n")
                    for line in timingPoints:
                        file.write(line + "\n")
                    for line in notes:
                        file.write(line + "\n")
                convertedTo7k += 1
                self.signals.textoutput.emit(f'Wrote to file: {newFileName}\n')

        def convertAudio():
            # Delete .ogg and .wav files
            def deleteFiles():
                global audioConverted
                self.signals.textoutput.emit('Deleting all .ogg and .wav files...\n')
                for file in audioFiles:
                    os.remove(file)
                audioConverted += 1
                self.signals.finished.emit()

            # Convert to mp3 and delete files after finishing with bmx2wav
            def convertToMp3():
                global audioNotConverted
                self.signals.textoutput.emit('Trying to convert to .mp3...')
                input = os.path.join(self.song, 'audio.wav')
                output = os.path.join(self.song, 'audio.mp3')

                # Check if audio.wav exists
                if not os.path.exists(input):
                    audioNotConverted.append(os.path.basename(self.song))
                    self.signals.textoutput.emit('<font color="red"><b>audio.wav not found! bmx2wav probably failed...</b></font><br>')
                    self.signals.finished.emit()
                    return

                audioFiles.append(input) # Append audio.wav to file list to be deleted later.
                sound = AudioSegment.from_file(input, format='wav')
                sound.export(output, format='mp3')
                self.signals.textoutput.emit('Finished converting to .mp3.')
                
                self.signals.textoutput.emit('Setting song in all .osu files...')
                for file in osuFiles:
                    with open(file, 'r+', encoding='utf-8', errors='ignore') as f:
                        data = f.readlines()
                        data.insert(3, 'AudioFilename: audio.mp3\n')
                        f.seek(0)
                        f.writelines(data)
                
                deleteFiles()

            self.signals.textoutput.emit(f'<b>* Converting audio for {os.path.basename(self.song)} *</b>')
            if not (os.path.exists('bmx2wavc.exe')):
                self.signals.textoutput.emit('<font color="red"><b>bmx2wavc.exe not found!</b></font>')
                self.signals.finished.emit()
                return

            osuFiles = []
            bmsCharts = []
            audioFiles = []

            # Filter files
            for file in os.listdir(self.song):
                ext = os.path.splitext(file)[1]
                if ext == '.osu':
                    osuFiles.append(file)
                if ext == '.bms' or ext == '.bme' or ext == '.bml':
                    bmsCharts.append(file)
                if ext == '.ogg' or ext == '.wav':
                    audioFiles.append(file)
                else:
                    continue

            # Create paths
            bmsCharts = list(map(lambda x: os.path.join(self.song, x), bmsCharts))
            osuFiles = list(map(lambda x: os.path.join(self.song, x), osuFiles))
            audioFiles = list(map(lambda x: os.path.join(self.song, x), audioFiles))

            diffToConvert = bmsCharts[0]
            output = os.path.join(self.song, 'audio.wav')      

            # Run bmx2wav
            bmx2wav = QProcess()
            self.signals.textoutput.emit('Converting with bmx2wav...')
            bmx2wav.start('bmx2wavc.exe', [diffToConvert, output])
            bmx2wav.finished.connect(convertToMp3)
            bmx2wav.waitForFinished(-1)

        # Start processing
        if not convertTo7k and not convertSounds:
            self.signals.finished.emit()
            return
        
        self.signals.textoutput.emit(f'<font color="blue"><b>Processing: {os.path.basename(self.song)}</b></font><br>')

        if convertTo7k:
            convert7k()
        if convertSounds:
            convertAudio()
        self.signals.textoutput.emit('<font color="green"><b>Done</b></font><br>-----------------------')
        self.signals.finished.emit()

# Thread for zipping folders to .osz
class zipToOsz(QRunnable):
    def __init__(self, songs: list):
        super(zipToOsz, self).__init__()
        self.signals = WorkerSignals()
        self.songs = songs

    def run(self):
        global foldersZipped

        self.signals.textoutput.emit('<br><font size="4"><b>* Zipping folders to .osz *</b></font>')
        for folder in self.songs:
            output = f'{folder}.osz'
            oszFile = zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_STORED)
            for root, dirs, files in os.walk(folder):
                for file in files:
                    oszFile.write(os.path.join(root, file), arcname=file)
            oszFile.close()
            foldersZipped += 1
            self.signals.textoutput.emit(f'Zipped {os.path.basename(output)}')
            shutil.rmtree(folder) # Delete temp folder.
            self.signals.textoutput.emit(f'Removed folder: {os.path.basename(folder)}\n')
        
        self.signals.finished.emit()


class MainWindow(qtw.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("BMX2OSU (by sxturndev)")
        layout = qtw.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.converter()
        self.output()
        self.pool = QThreadPool()
        self.pool.setMaxThreadCount(1) # To queue worker threads.
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

        self.openFolder.clicked.connect(self.get_input)
        
        # Options layout
        options = qtw.QVBoxLayout()
        self.include7kBox = qtw.QCheckBox(text='Include 7k Version')
        self.convertAudioBox = qtw.QCheckBox(text='Convert Audio to .mp3 (Removes keysounds)')

        diffOptions = qtw.QFormLayout()
        self.od = qtw.QLineEdit()
        self.od.setPlaceholderText('(Default 8.0)')
        self.od.setFixedWidth(75)
        self.hp = qtw.QLineEdit()
        self.hp.setPlaceholderText('(Default 8.5)')
        self.hp.setFixedWidth(75)
        diffOptions.addRow('OD:', self.od)
        diffOptions.addRow('HP:', self.hp)

        options.addWidget(self.include7kBox)
        options.addWidget(self.convertAudioBox)
        options.addLayout(diffOptions)

        # Github link and Convert button layout
        bottom = qtw.QHBoxLayout()
        github = qtw.QLabel('<a href=\"https://github.com/sxturndev/bmx2osu\">Github</a>')
        github.setOpenExternalLinks(True)
        spacer = qtw.QSpacerItem(0, 0, qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Minimum)
        self.convertbtn = qtw.QPushButton('Convert')
        self.convertbtn.clicked.connect(self.convert)

        bottom.addWidget(github)
        bottom.addItem(spacer)
        bottom.addWidget(self.convertbtn)

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

    # Update output box when called
    def logger(self, text):
        self.outputBox.append(text)

    # UI state toggle
    def ui_state(self, enabled: bool):
        self.openFolder.setEnabled(enabled)
        self.folderInput.setEnabled(enabled)
        self.convertAudioBox.setEnabled(enabled)
        self.include7kBox.setEnabled(enabled)
        self.convertbtn.setEnabled(enabled)
        self.od.setEnabled(enabled)
        self.hp.setEnabled(enabled)


    # Pipe stdout and stderr for bmtranslator
    def handle_stdout(self, process):
        line = process.readAllStandardOutput().data().decode(encoding='utf-8', errors='ignore').strip()
        self.logger(line)


    def handle_stderr(self, process):
        line = process.readAllStandardError().data().decode(encoding='utf-8', errors='ignore').strip()
        self.logger(line)

    # Open file dialog
    def get_input(self):
        global inputPath
        dir = qtw.QFileDialog.getExistingDirectory(
            parent=self,
            caption='Open Song Directory',
        )
        inputPath = dir
        self.folderInput.setText(inputPath)


    # Start conversion
    def convert(self):
        global convertedTo7k, audioConverted, audioNotConverted, foldersZipped, progress
        if (inputPath == ''):
            self.logger('<font color="red"><b>No input path selected!</b></font>')
            return
        if (len(os.listdir(inputPath)) == 0):
            self.logger('<font color="red"><b>Nothing found in input folder!</b></font>')
            return
        if not (os.access(outputPath, os.F_OK)):
            self.logger('<font color="red"><b>Output folder doesn\'t exist... Creating.</b></font>')
            os.mkdir(outputPath)
        if (len(os.listdir(outputPath)) != 0):
            self.logger('<font color="red"><b>Files exist in output folder!</b></font>')
            return
        if not (os.path.exists('bmt.exe')):
            self.logger('<font color="red"><b>bmt.exe not found!</b></font>')
            return

        self.logger(f'Input path: {inputPath}')
        self.logger(f'Output path: {outputPath}\n')
        self.logger('<font size="4"><b>Starting conversion</b></font><br>-----------------------')

        # Disable UI and reset values
        self.ui_state(False)
        convertedTo7k = 0
        audioConverted = 0
        audioNotConverted = []
        foldersZipped = 0
        progress = 0

        # Add args for bmtranslator
        def args():
            overallDifficulty = self.od.text()
            hpDrainRate = self.hp.text()

            args = ['-i', inputPath, '-o', outputPath, '-type', 'osu']
            if overallDifficulty != '':
                args.append('-od')
                args.append(overallDifficulty)
            if hpDrainRate != '':
                args.append('-hp')
                args.append(hpDrainRate)
            self.logger(f'bmt.exe {" ".join(args)}\n')
            return args

        # Run bmtranslator
        bmt = QProcess()
        bmt.readyReadStandardOutput.connect(lambda: self.handle_stdout(bmt))
        bmt.readyReadStandardError.connect(lambda: self.handle_stderr(bmt))
        bmt.finished.connect(self.finish_processing)
        bmt.start('bmt.exe', args())

    # Start post-processing after bmtranslator finishes
    def finish_processing(self):
        global convertTo7k, convertSounds
        self.logger('<br><font color="green"><b>Finished processing with bmtranslator</b></font><br>-----------------------')
                
        convertTo7k = self.include7kBox.isChecked()
        convertSounds = self.convertAudioBox.isChecked()

        folders = os.listdir(outputPath)
        if (len(folders) == 0):
            self.logger('<br><font color="red"><b>No folders found in output! Stopping. Please check your settings and input folder.</b></font>')
            self.ui_state(True)
            return

        # Create paths
        songs = list(map(lambda folder: os.path.join(outputPath, folder), folders))

        def finish():
            self.logger('<br><br><font size="5"><b>FINISHED</b></font><br>')
            if convertTo7k:
                self.logger(f'{convertedTo7k} charts converted to 7k.')
            if convertSounds:
                self.logger(f'Converted audio: <font color="green">{audioConverted} Successful</font>, <font color="red">{len(audioNotConverted)} Failed</font>')
            if len(audioNotConverted) > 0:
                for file in audioNotConverted:
                    self.logger(f'Failed for: {file}')
            self.logger(f'{foldersZipped} folders zipped.')
            self.ui_state(True)

        # Check progress after each thread finishes
        # Zip everything to .osz if processing is done.
        def checkProgress():
            global progress
            progress += 1
            if (progress == len(songs)):
                worker = zipToOsz(songs)
                worker.signals.textoutput.connect(self.logger)
                worker.signals.finished.connect(finish)
                self.pool.start(worker)
        
        # Queue worker thread for each song in output folder
        for i in range(len(songs)):
            song = songs[i]         
            worker = postProcessing(song)
            worker.signals.textoutput.connect(self.logger)
            worker.signals.finished.connect(checkProgress)
            self.pool.start(worker)


if __name__ == '__main__':
    app = qtw.QApplication([])
    app.setStyle('Fusion')
    mw = MainWindow()
    mw.resize(400, 500)
    sys.exit(app.exec_())

