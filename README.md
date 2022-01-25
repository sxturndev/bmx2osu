[bmx2wav]: http://childs.squares.net/program/bmx2wav/v1/index.html
[bmt]: https://github.com/vysiondev/bmtranslator
[bmtfork]: https://github.com/sxturndev/bmtranslator
[ffmpeg]: https://www.gyan.dev/ffmpeg/builds/

# bmx2osu

Convert BMS to osu!
- convert keysounds to one song file using [BMX2WAV][bmx2wav]
- include 7k version (two options; only 7k or both)
- change Overall Difficulty and HP Drain Rate
- adjust hitsound volume
- remove extra files such as .bmp and converted bmx files
- and more in the future(?)

<img src="https://raw.githubusercontent.com/sxturndev/bmx2osu/main/preview.png" alt="preview" width="300"/>

---

## Usage

> #### Disclaimer
> This program is experimental and hasn't been tested thoroughly. So it may not work for all cases. It's recommended that you switch your system locale to Japanese or enable UTF-8 support for file paths to work. [Short tutorial on where to find that.](https://youtu.be/3PUkcn8QbnE)

#### Install FFmpeg

- This is required for audio conversion to work. Press Windows + X and run Powershell as administrator, then paste this command in:
    ```powershell
    Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    ```
    Once Chocolatey is installed, run: `choco install ffmpeg`

#### Downloading and Running

- Download the release [here](https://github.com/sxturndev/bmx2osu/releases/latest) and extract it.
    - `bmt.exe` and `bmx2wavc.exe` must be in this folder for the program to work.

- Run `bmx2osu.exe` and select an input folder, bmx2osu batch converts BMS so your input structure should look something like this:
    ```
    input folder/
    ├─ BMS Song/
    │  ├─ chart.bme
    │  ├─ chart.bml
    ├─ BMS Song/
    ├─ BMS Song/
    ```
- Select your options and then click Convert
  - Assuming everything converted properly, you should find the converted .osz files in an output folder inside the main program's folder.

---

## Development

#### Dependencies
- [Python 3.10+](https://www.python.org/downloads/)
- [FFmpeg][ffmpeg]
- [bmtranslator][bmtfork]
- [BMX2WAV v1][bmx2wav]

#### Setting up & Running

Assuming you already have git, python, and pip installed:
  - Install [FFmpeg][ffmpeg] and add it to the Windows PATH environment variable, or [install with Chocolatey.](#install-ffmpeg)
  - Build my fork of [bmtranslator][bmtfork]:
    - Install [Golang](https://go.dev/doc/install)
    - Clone the repo: `git clone https://github.com/sxturndev/bmtranslator`
    - Run `go build`
    - Rename `bmtranslator.exe` to `bmt.exe`
  - Download [BMX2WAV v1][bmx2wav] for the CLI version of BMX2WAV, you need `bmx2wavc.exe`

  - Clone this repo `git clone https://github.com/sxturndev/bmx2osu`
    - Move bmt.exe and bmx2wavc.exe into the project's main directory.
  - Install package dependencies using: `pip install -r requirements.txt`
  - Run `py main.py`

Documentation coming soon.

---

### Contact & Help

Join my [Discord Server](https://discord.gg/9ckmwRTtBh)

### Credit & Thanks

- [vysiondev](https://github.com/vysiondev) - For [bmtranslator][bmt] and showing me how it works.
- [temtan](https://github.com/temtan) - For BMX2WAV and permission to use it. [Website](http://childs.squares.net/)
- [IceDynamix](https://github.com/IceDynamix) - Advice on formatting and managing a python project. Thank you!
- And others for testing and giving me feedback.

---

### License

Distributed under the MIT License. See the `LICENSE` file for more information.
