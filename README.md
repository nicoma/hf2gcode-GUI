
Robot Text Plotter – HF2Gcode GUI
=================================

Robot Text Plotter is a Python GUI application to control a drawing robot (GRBL‑style XY plotter) from text, using the external tool “hf2gcode” by Andreas Weber. It converts text to G‑code with Hershey fonts, previews the toolpath, and sends the resulting G‑code to the robot over Telnet or a serial (COM) port.[1]
It has been tested with midTbot : https://github.com/bdring/midTbot_esp32

Main features
-------------

- Text to G‑code using the external hf2gcode tool (Hershey fonts).
- Live XY preview of the generated toolpath:
  - Full robot workspace outline.
  - Inner text/margin area.
  - Progressive highlighting of segments as they are “drawn”.
- Robot configuration:
  - X / Y min and max (in mm).
  - Safety margin around the working area.
- Text configuration:
  - Hershey font selection.
  - Character height (mm).
  - Automatic interline: char_height + 3 mm.
  - Feed rate, precision, Z up / Z down values.
- G‑code sending:
  - Telnet mode (TCP) to a GRBL board behind a network bridge.
  - Serial mode (COM/tty) using pyserial.
- Settings persistence:
  - All UI parameters (robot area, text, connection mode, host/port or serial/baud) are saved automatically in `RobotPlotter.properties` and reloaded on next startup.
- Modernized Tkinter UI with grouped panels and a clean layout.

Project structure
-----------------

Key files in this repository:

- `app.py`  
  Main entry point. Creates the main Tkinter window, coordinates the UI, preview, and sending logic.

- `controls_panel.py`  
  Builds the top control panels: robot workspace, text settings, connection and control buttons.

- `telnet_sender.py`  
  Threaded sender that streams G‑code lines to a Telnet (TCP) endpoint, waiting for GRBL “ok” replies.

- `serial_sender.py`  
  Threaded sender that streams G‑code lines over a serial port using pyserial, also expecting GRBL “ok” replies.

- `gcode_generator.py`  
  Integration layer that calls the external hf2gcode tool (or library) to generate G‑code from text and UI parameters.

- `gcode_parser.py`  
  Parses G‑code to extract drawable line segments for the XY preview canvas.

- `app_types.py`  
  Shared types and constants, including `HF_FONTS` (list of supported Hershey font names).

- `RobotPlotter.properties`  
  INI‑style configuration file automatically written on exit and read on startup (font, char height, robot area, connection mode, etc.).

- `requirements.txt`  
  Python dependencies for this project (pyserial, plus standard library).

External dependency: hf2gcode
-----------------------------

This GUI does not re‑implement the text‑to‑G‑code conversion logic itself. Instead, it relies on the external open source project **hf2gcode**: “hf2gcode, a Hershey font to G‑code tracer”.[1]

You must install hf2gcode separately for this GUI to work correctly.

hf2gcode repository (original project):  
https://github.com/Andy1978/hf2gcode[1]

hf2gcode in short:
- Command‑line tool written in C.
- Takes text, font name, scaling, offsets, Z up/down, feed, precision, etc.
- Outputs G‑code compatible with GRBL (and similar firmwares).[1]

Typical usage pattern:
- Robot Text Plotter reads your text and UI parameters.
- Robot Text Plotter calls hf2gcode with the right arguments (font, scale, offsets, Z up/down, interline, precision).
- hf2gcode returns G‑code on stdout.
- Robot Text Plotter optionally optimizes pen lifts, parses the G‑code for preview, and then sends it to the robot via Telnet or serial.

You are responsible for:
- Building and installing hf2gcode on your system (for example via `make` in its `src/` directory).[1]
- Making sure the executable is reachable from `gcode_generator.py` (either by PATH or by configuring an absolute path in your code).

Without hf2gcode, this GUI cannot generate G‑code from text.

Requirements
------------

- Python 3.9 or later (tested on 3.10+).
- Operating system:
  - Linux, macOS, or Windows (Tkinter + pyserial must work).
- Python packages:
  - `pyserial`
  - plus standard library modules (`tkinter`, `socket`, `threading`, `configparser`, `pathlib`, etc.).

All Python dependencies are listed in `requirements.txt`. Install them with:

    pip install -r requirements.txt

You also need:
- A working build of hf2gcode available on your system (see above).
- For real hardware:
  - A GRBL‑compatible controller reachable by TCP (for Telnet mode), or
  - A serial/USB connection (COM port or `/dev/tty*`) for serial mode.

Installation
------------

1. Clone this repository:

    git clone https://github.com/<your-user>/<your-repo>.git
    cd <your-repo>

2. (Optional) Create and activate a virtual environment:

    python -m venv .venv
    source .venv/bin/activate       # Windows: .venv\Scripts\activate

3. Install Python dependencies:

    pip install -r requirements.txt

4. Install and configure hf2gcode:

   - Clone and build hf2gcode following its README.
   - Ensure the `hf2gcode` binary is in your `PATH` or update `gcode_generator.py` to point at its exact location.

Running the application
-----------------------

From the project directory:

    python app.py

On first run, default parameters are used. On subsequent runs, the application automatically reloads settings from `RobotPlotter.properties`.

Using the GUI
-------------

1. Configure the robot workspace:

   - In the “Robot workspace (mm)” section, set:
     - X min / X max
     - Y min / Y max
     - Margin (safety margin inside the workspace).
   - The preview will show:
     - A gray rectangle for the full robot domain.
     - A blue dashed rectangle for the inner safe area (robot domain minus margin).

2. Configure text settings:

   - In the “Text settings” section:
     - Choose a Hershey font from the dropdown.
     - Set “Height (mm)” for character height.
     - Adjust “Precision” (decimal places in generated G‑code).
     - Set “Feed” (feed rate for cutting / drawing moves).
   - Interline spacing is auto‑computed as: character_height + 3 mm.

3. Choose connection mode:

   - In “Connection & controls”:
     - Mode: `Telnet` or `Serial`.
   - Telnet:
     - Host: IP or hostname of your GRBL controller / bridge.
     - Port: TCP port (e.g. 23, 5000, etc.).
   - Serial:
     - Port: COM port name (Windows) or `/dev/ttyUSB0`, `/dev/ttyACM0`, etc. (Linux/macOS).
     - Baud: typically `115200` for GRBL.

   Switching mode changes only the configuration panel; all other controls stay in place.

4. Generate G‑code:

   - Type your text in the “Input text” area.
   - If “Auto‑generate” is checked, G‑code is regenerated automatically after typing pauses.
   - Otherwise, click “Generate G‑code”.
   - The “Generated G‑code” area updates with new code.
   - The XY preview shows the toolpath in the robot coordinate system.

5. Send G‑code to the robot:

   - Verify the connection parameters.
   - Click “Start”.
   - The sender (Telnet or Serial) streams lines to the robot and waits for “ok” replies.
   - The current line in the G‑code view is highlighted.
   - The corresponding segment in the preview is highlighted in red.
   - Click “Stop” to stop sending from the GUI side.

   The “Home ($H)” button sends a GRBL homing command using the currently selected mode (Telnet or Serial). The “Test pen” button can be wired to a short test sequence on Z to check pen movement.

Configuration persistence
-------------------------

On exit, the application writes `RobotPlotter.properties` next to `app.py`. It includes:

- Font, character height, precision, feed.
- X/Y min/max, margin.
- Z up / Z down values.
- Connection settings:
  - Mode (`Telnet` or `Serial`).
  - Host/port or serial port/baudrate.
- Interline (currently derived from height, but persisted for convenience).

On startup, these values are reloaded so you resume from your last session.

Testing serial mode without hardware (Linux)
--------------------------------------------

If you want to test the serial mode without a physical GRBL board, you can emulate a null‑modem cable using `socat`:

1. Create a pair of virtual serial ports:

    socat -d -d pty,raw,echo=0,link=./ttyV0 pty,raw,echo=0,link=./ttyV1

2. In the GUI, set:
   - Mode: Serial
   - Port: `./ttyV0` or the corresponding `/dev/pts/X` that socat reports
   - Baud: 115200

3. In another terminal, connect to the other side (`./ttyV1`) and act as a fake GRBL:

    socat - /dev/pts/Y,raw,echo=0

   You will see G‑code lines printed, and can answer `ok` followed by Enter to simulate GRBL acknowledgements.

Licensing
---------

This GUI is intended to be released under an open source license (for example MIT, Apache‑2.0, or GPL‑3.0).  
Add a `LICENSE` file at the root of the repository with your chosen license text.

Note that hf2gcode itself is licensed under GPLv3 (see its repository for details). Depending on how you integrate hf2gcode (e.g. as an external binary versus linking as a library), GPL compatibility may affect what license you should choose for this GUI. Please review the hf2gcode license and consider your own licensing accordingly.[3][1]

Contributing
------------

Contributions are welcome:

- Bug reports and feature requests via GitHub issues.
- Pull requests for:
  - UI improvements.
  - Additional configuration options.
  - Better integration with hf2gcode (font discovery, error handling, etc.).
  - Support for other firmwares or connection types.

Before opening a pull request, please:

- Keep coding style reasonably consistent with the existing code.
- Test basic workflows:
  - Text → G‑code → Preview.
  - Telnet send.
  - Serial send (real or virtual).

Acknowledgements
----------------

This project would not exist without:

- hf2gcode by Andreas Weber, which does all the heavy lifting for text‑to‑G‑code conversion. : https://github.com/Andy1978/hf2gcode
- midTbot project, https://github.com/bdring/midTbot_esp32
- The GRBL ecosystem and all the related open source tools.
- The Python and Tkinter communities for the GUI and tooling.
