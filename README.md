# bmx2osu
Convert BMS to osu!
With options to: 
- convert keysounds to one song file using [BMX2WAV](http://childs.squares.net/program/bmx2wav/v1/index.html)
- include 7k version
- change Overall Difficulty and HP Drain Rate
- and more in the future(?)

<img src="https://raw.githubusercontent.com/sxturndev/bmx2osu/main/preview.png" alt="preview" width="300"/>

## Usage
> #### Disclaimer
> This program is experimental and hasn't been tested thoroughly. So it may not work for all cases.
> It's recommended that you switch your system locale to Japanese or
> enable UTF-8 support for file paths to work. 
> [Short tutorial on where to find that.](https://youtu.be/3PUkcn8QbnE)

1. Install ffmpeg, this is required for audio conversion to work. Press Windows + X and run Powershell as administrator, then paste these commands in:
    ```powershell
    Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    ```
    ```
    choco install ffmpeg
    ```

2. Download the release [here](https://github.com/sxturndev/bmx2osu/releases/download/v1.0/release.zip) and extract it.
    - bmt.exe and bmx2wavc.exe must be in this folder for the program to work.

3. Run bmx2osu.exe and select an input folder, bmx2osu batch converts BMS so your input structure should look something like this:
    ```
    input folder/
    ├─ BMS Song/
    │  ├─ chart.bme
    │  ├─ chart.bml
    ├─ BMS Song/
    ├─ BMS Song/
    ```
4. Select your options and then click Convert

Assuming everything converted properly, you should find the converted .osz files in an output folder inside the main program's folder.

## Contact & Help
Join my [Discord Server](https://discord.gg/9ckmwRTtBh)

## Credit & Thanks
- [vysiondev](https://github.com/vysiondev) - For [bmtranslator](https://github.com/vysiondev/bmtranslator) and showing me how it works.
- [temtan](https://github.com/temtan) - For BMX2WAV and permission to use it. [Website](http://childs.squares.net/)

## License
Distributed under the MIT License. See the `LICENSE` file for more information.
