# BMX2OSU by sxturndev

# Imports
import os
import sys
import math
import zipfile
import shutil
import logging
import time
from datetime import timedelta
import PyQt5.QtWidgets as qtw
from PyQt5.QtCore import QProcess, QRunnable, QThreadPool, pyqtSignal, QObject, Qt
from pydub import AudioSegment

dirname = os.path.dirname(__file__)
# dirname = os.path.dirname(sys.executable)  # Use this line for PyInstaller
inputPath = ''
outputPath = os.path.join(dirname, 'output')

logger = logging.getLogger('bmx2osu')
logger.setLevel(logging.DEBUG)  # Set logging level
fHandler = logging.FileHandler(
    filename='output.log', mode='w', encoding='utf-8')
fFormat = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
fHandler.setFormatter(fFormat)
logger.addHandler(fHandler)


class Settings():
    convertTo7k = 0
    convertSounds = False
    removeFiles = False


class Tracking():
    convertedTo7k = 0
    audioConverted = 0
    audioNotConverted = []
    foldersZipped = 0
    progress = 0
    startTime = ''


class WorkerSignals(QObject):
    textoutput = pyqtSignal(str)
    finished = pyqtSignal()
    updateProgress = pyqtSignal()

    def printError(self, msg):
        logger.error(msg)
        logger.exception('Exception occurred')
        self.textoutput.emit(f'<font color="red">{msg}. Please check the error log file.</font><br>')


class postProcessing(QRunnable):
    def __init__(self, song: str):
        super(postProcessing, self).__init__()
        self.signals = WorkerSignals()
        self.song = song

    def run(self):
        folderName = os.path.basename(self.song)

        def convert7k():
            logger.info(f'Converting {folderName} to 7k')
            self.signals.textoutput.emit(
                f'<b>* Converting {folderName} to 7 keys. *</b>')
            difficulties = list(filter(lambda x: os.path.splitext(x)[
                                1] == '.osu', os.listdir(self.song)))
            difficulties = list(
                map(lambda x: os.path.join(self.song, x), difficulties))
            total = len(difficulties)

            self.signals.textoutput.emit(f'Found {total} charts to convert.\n')
            for i in range(total):
                try:
                    diff = difficulties[i]
                    diffName = os.path.basename(diff)
                    progress = f'[{i+1}/{total}]'
                    logger.debug(f'{progress} Converting {diffName} to 7k')
                    self.signals.textoutput.emit(
                        f'<b>{progress}</b> Converting {diffName} to 7key...')

                    # Read File
                    with open(diff, 'r', encoding='utf-8', errors='ignore') as file:
                        lines = file.read().splitlines()
                        tpIndex = lines.index('[TimingPoints]')
                        hitObjIndex = lines.index('[HitObjects]')
                        data = lines[:tpIndex]
                        timingPoints = lines[tpIndex:hitObjIndex]
                        notes = lines[hitObjIndex:]
                        lines.clear()

                    # Edit metadata
                    for i in range(len(data)):
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
                            newEvent = 'Sample,{},0,"{}",100'.format(
                                time, hitSample[5])
                        else:
                            newEvent = 'Sample,{},0,"{}",100'.format(
                                time, hitSample[4])

                        data.append(newEvent)

                    # Note conversion
                    # Set i to 1 to skip [HitObjects]
                    i = 1
                    scratchRemoved = 0
                    while i < len(notes):
                        note = notes[i].split(',')
                        columnIndex = math.floor(int(note[0]) * 8 / 512)
                        newColumn = ['36', '109', '182',
                                     '256', '329', '402', '475']

                        if columnIndex == 0:
                            notes.pop(i)
                            i -= 1
                            moveToStoryboard(note)
                            scratchRemoved += 1
                        if (columnIndex >= 1 and columnIndex <= 7):
                            note[0] = newColumn[columnIndex-1]
                            notes[i] = ','.join(note)
                        i += 1
                    self.signals.textoutput.emit(
                        f'Removed {scratchRemoved} scratch notes.')

                    # If 'Only include 7k' option is selected, delete 8k files.
                    if Settings.convertTo7k == 1:
                        logger.debug(f'Removing {diffName}')
                        os.remove(diff)

                    # Write to new file
                    newFileName = diffName if Settings.convertTo7k == 1 else f'[7K] {diffName}'
                    newFilePath = os.path.join(self.song, newFileName)
                    with open(newFilePath, 'w', encoding='utf-8') as file:
                        file.write('\n'.join(data))
                        file.write('\n')
                        file.write('\n'.join(timingPoints))
                        file.write('\n')
                        file.write('\n'.join(notes))
                    Tracking.convertedTo7k += 1
                    logger.debug(f'Wrote to file: {newFileName}')
                    self.signals.textoutput.emit(
                        f'Wrote to file: {newFileName}\n')
                except Exception:
                    self.signals.printError(f'An error occurred while converting {diffName}')

        def convertAudio():
            # Delete .ogg and .wav files
            def deleteAudioFiles():
                try:
                    logger.info(
                        f'Deleting all .ogg and .wav files for {folderName}')
                    self.signals.textoutput.emit(
                        'Deleting all .ogg and .wav files...')
                    for file in audioFiles:
                        os.remove(file)
                    Tracking.audioConverted += 1
                    logger.debug(f'Removed {len(audioFiles)} audio files')
                    logger.info('Finished processing audio')
                    self.signals.textoutput.emit('Done.\n')
                except Exception:
                    self.signals.printError(f'An error occurred while deleting audio files for {folderName}')

            # Convert to mp3 and delete files after finishing with bmx2wav
            def convertToMp3():
                try:
                    logger.info('Converting audio to mp3')
                    self.signals.textoutput.emit(
                        'Trying to convert to .mp3...')
                    input = os.path.join(self.song, 'audio.wav')
                    output = os.path.join(self.song, 'audio.mp3')

                    # Check if audio.wav exists
                    if not os.path.exists(input):
                        logger.error(
                            'Failed to convert audio to mp3, bmx2wav probably failed.')
                        Tracking.audioNotConverted.append(folderName)
                        self.signals.printError('audio.wav not found! bmx2wav probably failed..')
                        return

                    # Append audio.wav to file list to be deleted later.
                    audioFiles.append(input)
                    sound = AudioSegment.from_file(input, format='wav')
                    sound.export(output, format='mp3')
                    self.signals.textoutput.emit(
                        'Finished converting to .mp3.')

                    for file in osuFiles:
                        with open(file, 'r+', encoding='utf-8', errors='ignore') as f:
                            data = f.readlines()
                            data.insert(3, 'AudioFilename: audio.mp3\n')
                            f.seek(0)
                            f.writelines(data)

                    deleteAudioFiles()
                except Exception:
                    self.signals.printError(f'An error occurred while trying to convert to .mp3 for: {folderName}')

            self.signals.textoutput.emit(
                f'<b>* Converting audio for {folderName} *</b>')
            if not (os.path.exists('bmx2wavc.exe')):
                logger.warning('bmx2wavc.exe not found! Can\'t convert audio.')
                self.signals.textoutput.emit(
                    '<font color="red"><b>bmx2wavc.exe not found!</b></font>')
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
            bmsCharts = list(
                map(lambda x: os.path.join(self.song, x), bmsCharts))
            osuFiles = list(
                map(lambda x: os.path.join(self.song, x), osuFiles))
            audioFiles = list(
                map(lambda x: os.path.join(self.song, x), audioFiles))

            diffToConvert = bmsCharts[0]
            output = os.path.join(self.song, 'audio.wav')

            # Run bmx2wav
            try:
                logger.info('Starting bmx2wav.')
                bmx2wav = QProcess()
                self.signals.textoutput.emit('Converting with bmx2wav...')
                bmx2wav.start('bmx2wavc.exe', [diffToConvert, output])
                bmx2wav.finished.connect(convertToMp3)
                bmx2wav.waitForFinished(-1)
            except Exception:
                self.signals.printError('Something went wrong with bmx2wav')
                return

        def removeExtraFiles():
            try:
                logger.info(
                    f'Removing unnecessary files for {folderName}')
                self.signals.textoutput.emit(
                    f'<b>* Removing unnecessary files for {folderName} *</b>')

                filesRemoved = 0
                filesToKeep = ['.wav', '.ogg', '.mp3', '.jpg', '.jpeg', '.osu']
                osuFiles = []
                bgFiles = []

                # Filter .osu files.
                for file in os.listdir(self.song):
                    ext = os.path.splitext(file)[1]
                    if ext == '.osu':
                        osuFiles.append(file)
                osuFiles = list(
                    map(lambda x: os.path.join(self.song, x), osuFiles))

                # Parse background files.
                for file in osuFiles:
                    try:
                        with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                            data = f.read().splitlines()
                            eventsIndex = data.index('[Events]')
                            bgFile = data[eventsIndex +
                                          1].split(',')[2].strip('"').lower()
                            bgFiles.append(bgFile)
                    except Exception:
                        logger.error(
                            f'Error while trying to parse {os.path.basename(file)} for a bg file, skipping.')
                        logger.exception('Exception occurred')

                # Delete all files that don't have an extension in filesToKeep
                for file in os.listdir(self.song):
                    file = os.path.join(self.song, file)
                    # Skip background files
                    if (os.path.basename(file).lower()) in bgFiles:
                        self.signals.textoutput.emit(
                            f'{os.path.basename(file)} is a bg file, skipping!')
                        continue

                    ext = os.path.splitext(file)[1]
                    if ext not in filesToKeep:
                        os.remove(file)
                        filesRemoved += 1
                self.signals.textoutput.emit(f'Removed {filesRemoved} files\n')
                logger.info(
                    f'Removed {filesRemoved} files for {folderName}')
            except Exception:
                self.signals.printError(f'An error occurred while removing extra files for {folderName}')

        # Start processing
        if not Settings.convertTo7k and not Settings.convertSounds and not Settings.removeFiles:
            logger.info('No options were given, skipping processing.')
            self.signals.updateProgress.emit()
            self.signals.finished.emit()
            return

        self.signals.textoutput.emit(
            f'<font color="blue"><b>Processing: {folderName}</b></font><br>')

        if Settings.convertTo7k != 0:
            convert7k()
        if Settings.convertSounds:
            convertAudio()
        if Settings.removeFiles:
            removeExtraFiles()

        logger.info(f'Finished processing {folderName}\n')
        self.signals.textoutput.emit(
            '<font color="green"><b>Done</b></font><br>-----------------------')
        self.signals.updateProgress.emit()
        self.signals.finished.emit()


# Thread for zipping folders to .osz


class zipToOsz(QRunnable):
    def __init__(self, songs: list):
        super(zipToOsz, self).__init__()
        self.signals = WorkerSignals()
        self.songs = songs

    def run(self):
        self.signals.textoutput.emit(
            '<br><font size="4"><b>* Zipping folders to .osz *</b></font>')
        for folder in self.songs:
            try:
                output = f'{folder}.osz'
                with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_STORED) as oszFile:
                    for root, dirs, files in os.walk(folder):
                        for file in files:
                            oszFile.write(os.path.join(
                                root, file), arcname=file)
                Tracking.foldersZipped += 1
                self.signals.textoutput.emit(
                    f'Zipped {os.path.basename(output)}')
                shutil.rmtree(folder)  # Delete temp folder.
                self.signals.textoutput.emit(
                    f'Removed folder: {os.path.basename(folder)}\n')
                logger.info(
                    f'Zipped {os.path.basename(output)} and deleted temp folder.')
                self.signals.updateProgress.emit()
            except Exception:
                self.signals.printError(f'An error occurred while trying to zip {os.path.basename(folder)}')
                self.signals.updateProgress.emit()

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
        self.pool.setMaxThreadCount(1)  # To queue worker threads.
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

        def change7kText():
            state = self.include7kBox.checkState()
            if state == 0:
                self.include7kBox.setText('7k Version (Two Options)')
            if state == 1:
                self.include7kBox.setText('Only include 7k')
            if state == 2:
                self.include7kBox.setText('Include 7k and 8k')

        # Options layout
        options = qtw.QVBoxLayout()
        self.include7kBox = qtw.QCheckBox(text='7k Version')
        self.include7kBox.setTristate(True)
        self.include7kBox.stateChanged.connect(change7kText)
        self.convertAudioBox = qtw.QCheckBox(
            text='Convert Audio to .mp3 (Removes keysounds)')
        self.removeFilesBox = qtw.QCheckBox(
            text='Remove extra files (.bmp, .bms, etc.)')

        diffOptions = qtw.QFormLayout()
        self.od = qtw.QDoubleSpinBox()
        self.od.setMaximum(10.0)
        self.od.setMinimum(0)
        self.od.setValue(8.0)
        self.od.setSingleStep(0.1)
        self.od.setFixedWidth(55)

        self.hp = qtw.QDoubleSpinBox()
        self.hp.setMaximum(10.0)
        self.hp.setMinimum(0)
        self.hp.setValue(7.0)
        self.hp.setSingleStep(0.1)
        self.hp.setFixedWidth(55)

        self.vol = qtw.QSpinBox()
        self.vol.setMaximum(100)
        self.vol.setMinimum(0)
        self.vol.setSingleStep(5)
        self.vol.setValue(60)
        self.vol.setSuffix('%')
        self.vol.setFixedWidth(55)

        diffOptions.addRow('OD:', self.od)
        diffOptions.addRow('HP:', self.hp)
        diffOptions.addRow('Vol:', self.vol)

        options.addWidget(self.include7kBox)
        options.addWidget(self.convertAudioBox)
        options.addWidget(self.removeFilesBox)
        options.addLayout(diffOptions)

        # Github link and Convert button layout
        bottom = qtw.QHBoxLayout()
        github = qtw.QLabel(
            '<a href=\"https://github.com/sxturndev/bmx2osu\">Github</a>')
        github.setOpenExternalLinks(True)
        spacer = qtw.QSpacerItem(
            0, 0, qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Minimum)
        self.convert_btn = qtw.QPushButton('Convert')
        self.convert_btn.clicked.connect(self.convert)

        bottom.addWidget(github)
        bottom.addItem(spacer)
        bottom.addWidget(self.convert_btn)

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

        self.progressBar = qtw.QProgressBar()
        self.progressBar.setFormat('Progress: %p% (%v/%m)')
        self.progressBar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        output.layout().addWidget(groupBox)
        output.layout().addWidget(self.progressBar)
        self.layout().addLayout(output)

    # Update output box when called
    def updateOutput(self, text):
        self.outputBox.append(text)

    def updateProgressBar(self):
        self.progressBar.setValue(self.progressBar.value() + 1)

    # UI state toggle
    def ui_state(self, enabled: bool):
        self.openFolder.setEnabled(enabled)
        self.folderInput.setEnabled(enabled)
        self.convertAudioBox.setEnabled(enabled)
        self.include7kBox.setEnabled(enabled)
        self.removeFilesBox.setEnabled(enabled)
        self.convert_btn.setEnabled(enabled)
        self.od.setEnabled(enabled)
        self.hp.setEnabled(enabled)
        self.vol.setEnabled(enabled)
        self.progressBar.setValue(0)
        self.progressBar.setMaximum(0)
        self.progressBar.setTextVisible(not enabled)

    # Pipe stdout and stderr for bmtranslator

    def handle_stdout(self, process):
        line = process.readAllStandardOutput().data().decode(
            encoding='utf-8', errors='ignore').strip()
        self.updateOutput(line)

    def handle_stderr(self, process):
        line = process.readAllStandardError().data().decode(
            encoding='utf-8', errors='ignore').strip()
        self.updateOutput(line)

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
        if (inputPath == ''):
            self.updateOutput(
                '<font color="red"><b>No input path selected!</b></font>')
            return
        if (len(os.listdir(inputPath)) == 0):
            self.updateOutput(
                '<font color="red"><b>Nothing found in input folder!</b></font>')
            return
        if not (os.access(outputPath, os.F_OK)):
            self.updateOutput(
                '<font color="red"><b>Output folder doesn\'t exist... Creating.</b></font>')
            os.mkdir(outputPath)
        if (len(os.listdir(outputPath)) != 0):
            self.updateOutput(
                '<font color="red"><b>Files exist in output folder!</b></font>')
            return
        if not (os.path.exists('bmt.exe')):
            self.updateOutput(
                '<font color="red"><b>bmt.exe not found!</b></font>')
            return

        self.updateOutput(f'\nInput path: {inputPath}')
        self.updateOutput(f'Output path: {outputPath}\n')
        self.updateOutput(
            '<font size="4"><b>Starting conversion</b></font><br>-----------------------')
        logger.info(
            f'Starting conversion.\nInput: {inputPath}\nOutput: {outputPath}')

        # Disable UI, reset values, check options.
        self.ui_state(False)
        Settings.convertTo7k = self.include7kBox.checkState()
        Settings.convertSounds = self.convertAudioBox.isChecked()
        Settings.removeFiles = self.removeFilesBox.isChecked()

        Tracking.convertedTo7k = 0
        Tracking.audioConverted = 0
        Tracking.audioNotConverted = []
        Tracking.foldersZipped = 0
        Tracking.progress = 0

        # Add args for bmtranslator
        def args():
            overallDifficulty = str(round(self.od.value(), 2))
            hpDrainRate = str(round(self.hp.value(), 2))
            volume = str(self.vol.value())

            args = ['-i', inputPath, '-o', outputPath, '-type', 'osu',
                    '-vol', volume, '-od', overallDifficulty, '-hp', hpDrainRate]

            if Settings.removeFiles:
                args.append('-no-storyboard')
            self.updateOutput(f'bmt.exe {" ".join(args)}\n')
            logger.info(f'Starting bmtranslator: bmt.exe {" ".join(args)}')
            return args

        # Run bmtranslator
        Tracking.startTime = time.time()
        bmt = QProcess()
        bmt.readyReadStandardOutput.connect(lambda: self.handle_stdout(bmt))
        bmt.readyReadStandardError.connect(lambda: self.handle_stderr(bmt))
        bmt.finished.connect(self.finish_processing)
        bmt.start('bmt.exe', args())

    # Start post-processing after bmtranslator finishes
    def finish_processing(self):
        logger.info('Finished processing with bmtranslator')
        self.updateOutput(
            '<br><font color="green"><b>Finished processing with bmtranslator</b></font><br>-----------------------')
        logger.info('Starting post processing')

        folders = os.listdir(outputPath)
        if (len(folders) == 0):
            logger.error(
                'STOPPING. No folders found in output. Check settings and make sure input folder is selected properly.')
            self.updateOutput(
                '<font color="red"><b>No folders found in output! Please check your input folder.</b></font>')
            self.ui_state(True)
            return

        # Create paths
        songs = list(map(lambda folder: os.path.join(
            outputPath, folder), folders))
        self.progressBar.setValue(0)
        self.progressBar.setMaximum(len(songs))
        self.progressBar.setTextVisible(True)

        def finish():
            elapsed = timedelta(seconds=round(time.time() - Tracking.startTime))

            logger.info(f'FINISHED in {elapsed}')
            self.updateOutput(
                f'<br><br><font size="5"><b>FINISHED in {elapsed}</b></font><br>')
            if Settings.convertTo7k != 0:
                self.updateOutput(f'{Tracking.convertedTo7k} charts converted to 7k.')
            if Settings.convertSounds:
                successful = f'<font color="green">{Tracking.audioConverted} Successful</font>'
                failed = f'<font color="red">{len(Tracking.audioNotConverted)} Failed</font>'
                self.updateOutput(
                    f'Converted audio: {successful}, {failed}')
            if len(Tracking.audioNotConverted) > 0:
                for file in Tracking.audioNotConverted:
                    self.updateOutput(f'Failed for: {file}')
            self.updateOutput(f'{Tracking.foldersZipped} folders zipped.')
            self.ui_state(True)

        # Check progress after each thread finishes
        # Zip everything to .osz if processing is done.
        def checkProgress():
            Tracking.progress += 1
            if (Tracking.progress == len(songs)):
                self.progressBar.setFormat('Zipping to .osz: %p% (%v/%m)')
                self.progressBar.setValue(0)
                self.progressBar.setMaximum(len(songs))  # Reset Progress Bar
                worker = zipToOsz(songs)
                worker.signals.textoutput.connect(self.updateOutput)
                worker.signals.finished.connect(finish)
                worker.signals.updateProgress.connect(self.updateProgressBar)
                self.pool.start(worker)

        # Queue worker thread for each song in output folder
        for i in range(len(songs)):
            song = songs[i]
            worker = postProcessing(song)
            worker.signals.textoutput.connect(self.updateOutput)
            worker.signals.finished.connect(checkProgress)
            worker.signals.updateProgress.connect(self.updateProgressBar)
            self.pool.start(worker)


if __name__ == '__main__':
    app = qtw.QApplication([])
    app.setStyle('Fusion')
    mw = MainWindow()
    mw.resize(400, 500)
    sys.exit(app.exec_())
