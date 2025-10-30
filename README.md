# ✈️ GAMECHANGER - AI Enabled Controller Configurations

![Python Version](https://img.shields.io/badge/Python-3.12%2B-blue.svg)![License](https://img.shields.io/badge/License-Personal%20%26%20Educational%20Use-green.svg)![Framework](https://img.shields.io/badge/Framework-Streamlit-ff4b4b)![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)

GAMECHANGER is an intelligent AI-powered HOTAS profile generator for flight simulators. It automatically creates combat-focused controller configurations by analyzing aircraft manuals and controller hardware specifications using **Google Gemini 2.5 Pro**.

---

## 📚 Table of Contents

- [🎯 Overview](#-overview)
  - [✨ Key Features](#-key-features)
- [🎮 Supported Simulators](#-supported-simulators)
- [🕹️ Compatible Controller Types](#️-compatible-controller-types)
- [🎛️ Pre-configured HOTAS Systems](#️-pre-configured-hotas-systems)
- [📋 Requirements](#-requirements)
- [🚀 Installation](#-installation)
- [💻 Usage](#-usage)
- [📖 How It Works](#-how-it-works)
- [📊 Output Format](#-output-format)
- [🎯 Combat-Focused Priorities](#-combat-focused-priorities)
- [🔧 Advanced Features](#-advanced-features)
- [🛠️ Troubleshooting](#️-troubleshooting)
- [📁 Project Structure](#-project-structure)
- [🤝 Contributing](#-contributing)
- [📝 License & Disclaimer](#-license--disclaimer)
- [🌟 Tips for Best Results](#-tips-for-best-results)
- [🔗 Useful Links](#-useful-links)
- [📞 Support](#-support)
- [🎉 Acknowledgments](#-acknowledgments)

---

## 🎯 Overview

GAMECHANGER prioritizes weapons, sensors, and tactical systems with 30-40+ comprehensive bindings. The AI-powered system uses **Google Gemini 2.5 Pro** to intelligently map controls based on real manuals by extracting text and images from aircraft and controller PDFs using PyMuPDF. It automatically detects unified vs multi-device HOTAS setups and generates installation-ready configuration files in simulator-native formats.

### ✨ Key Features

- **🤖 AI-Powered Mapping**: Uses **Google Gemini 2.5 Pro** to analyze manuals and generate optimal control mappings.
- **📄 PDF Analysis**: Extracts text and images from both aircraft and controller manuals.
- **🎮 Multi-Device Support**: Handles unified HOTAS, multi-device setups, single joysticks, and gamepads.
- **🎯 Combat-Focused**: Prioritizes weapons, sensors, and tactical systems.
- **📦 Ready-to-Use**: Generates installation-ready configuration files.
- **🔧 Multiple Simulators**: Supports 8 major flight simulators.

## 🎮 Supported Simulators

| Simulator                      | File Format      | File Extension |
| :----------------------------- | :--------------- | :------------- |
| DCS World                      | Lua script       | `.lua`         |
| Microsoft Flight Simulator 2020| XML profile      | `.xml`         |
| IL-2 Sturmovik                 | Key-Value format | `.map`         |
| Falcon BMS                     | Binary key file  | `.key`         |
| War Thunder                    | Config format    | `.blk`         |
| X-Plane 11/12                  | Joystick config  | `.txt`         |
| Elite Dangerous                | XML bindings     | `.binds`       |
| Star Citizen                   | ActionMaps XML   | `.xml`         |

## 🕹️ Compatible Controller Types

### Multi-Device HOTAS
Separate stick, throttle, and optional pedals requiring unique device identification.

### Unified HOTAS
All-in-one integrated devices with stick and throttle in a single unit.

### Single Joysticks
Standalone flight sticks with throttle sliders and twist rudder.

### Gamepads
Xbox/PlayStation controllers with dual analog sticks.

## 🎛️ Pre-configured HOTAS Systems

- **Thrustmaster HOTAS Warthog** - Multi-device A-10C replica
- **VelocityOne Flightstick** - Unified all-in-one
- **Thrustmaster T.16000M FCS** - Multi-device with optional pedals
- **Logitech X56** - Multi-device with RGB
- **Winwing Orion 2 F/A-18** - Multi-device F/A-18 replica
- **VKB Gladiator NXT + TWCS** - Multi-device combo
- **Virpil Constellation** - Premium modular system
- **Xbox Controller** - Gamepad
- **Logitech Extreme 3D Pro** - Single joystick

## 📋 Requirements

- **Python**: 3.12 or higher
- **Google Gemini API key**: Free tier available at [Google AI Studio](https://aistudio.google.com/)
- **PDF manuals**: Aircraft and/or controller manuals (optional but recommended)

### Python Dependencies
```text
streamlit>=1.28.0
google-genai>=0.2.0
python-dotenv>=1.0.0
pymupdf>=1.24.0
Pillow>=10.0.0
```

## 🚀 Installation

Follow these steps to get GAMECHANGER running on your local machine.

### 1. Clone the Repository

First, clone the project repository from GitHub and navigate into the project directory.

```bash
git clone https://github.com/yourusername/gamechangerai.git
cd gamechangerai
```

### 2. Set Up a Virtual Environment (Recommended)
It is highly recommended to use a Python virtual environment to avoid conflicts with other projects or your system's Python installation.

Create the environment:

```bash
python -m venv venv
```

Activate the environment:

**On Windows:**
```bash
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
source venv/bin/activate
```

### 3. Install Dependencies
With your virtual environment active, install the required Python packages using pip.

```bash
pip install -r requirements.txt
```

### 4. Configure API Key
Create a new file named `.env` in the root of the project directory. This file will securely store your Google API key.

Add the following line to the `.env` file, replacing `your_api_key_here` with your actual key:

```
GOOGLE_API_KEY=your_api_key_here
```

You can get a free API key from [Google AI Studio](https://aistudio.google.com/).

## 💻 Usage
Launch the desired Streamlit application from your terminal.

**Main Application (All Simulators)**
Run the main Streamlit application for general use:
```bash
streamlit run main.py
```

**DCS World Specific**
For a configuration experience focused on DCS World:
```bash
streamlit run main_dcs.py
```

**Multi-Device Configuration**
For advanced multi-device HOTAS setups (e.g., separate stick, throttle, and pedals):
```bash
streamlit run main_multiconfig.py
```

**Unified HOTAS**
For unified/all-in-one controllers (e.g., VelocityOne Flightstick):
```bash
streamlit run main_flightstick.py
```

**Stick + Throttle**
For traditional separate stick and throttle setups:
```bash
streamlit run main_sticknthrottle.py
```

## 📖 How It Works
**1. Select Your Simulator**
Choose from 8 supported flight simulators. The system automatically adapts to the correct file format and configuration structure.

**2. Upload Aircraft Manual (Optional)**
Upload the aircraft flight manual PDF. The AI will extract:
- Text content for control descriptions
- Cockpit diagrams and images
- Systems information
- Weapon and sensor details

**3. Select Controller Setup**
Choose your HOTAS configuration. The system detects:
- Unified vs multi-device setup
- Available axes and buttons
- Device capabilities

**4. Upload Controller Manuals (Optional)**
Upload manuals for each device component:
- Flight stick manual
- Throttle manual
- Rudder pedals manual
- Additional control panels

**5. Generate Configuration**
Click "Generate Profile" and GAMECHANGER will:
- Analyze all uploaded documents
- Extract text and images using PyMuPDF
- Send to **Google Gemini 2.5 Pro** for intelligent mapping
- Generate complete configuration files
- Create detailed installation instructions

**6. Download & Install**
- Download the generated configuration file(s).
- Place them in the simulator's specified config directory.
- Connect all physical devices.
- Load the profile in the simulator.
- Calibrate and test all controls.

## 📊 Output Format
Each generated profile includes:

**1. Technical Mapping Table**
A detailed table showing:
- **HOTAS Component** (for multi-device)
- **Physical Input** (button/axis names)
- **Device ID** (JOY_BTN1, JOY_X, etc.)
- **Simulator Command**
- **Function & Rationale**

**2. Installation Instructions**
A step-by-step guide including:
- File location
- Profile loading procedure
- Device detection verification
- Calibration steps

**3. Configuration File(s)**
Ready-to-use files in the simulator-native format:
- DCS World: `.lua` files
- MSFS 2020: `.xml` files
- IL-2: `.map` files
- And more...

## 🎯 Combat-Focused Priorities
GAMECHANGER prioritizes controls in the following order to ensure mission readiness:

**1. Primary (Essential)**
- **Flight Controls**: Pitch, roll, yaw, throttle
- **Weapons**: Trigger, gun, weapon release, weapon select
- **Sensors**: TDC (Target Designator Control), radar modes

**2. Secondary (Important)**
- **Combat Systems**: Countermeasures, master arm, cage/uncage
- **Essential Flight**: Gear, flaps, speed brake, trim
- **Tactical**: Autopilot, NWS (Nose Wheel Steering), IFF

**3. Tertiary (Nice to Have)**
- **Radio/Communication**: PTT (Push to Talk), radio select
- **Systems Management**: APU, engine start, lights
- **Advanced**: MFD pages, data link, mission systems

## 🔧 Advanced Features
**Image Extraction**
The system can extract and analyze visual data from PDFs:
- Cockpit layout diagrams
- Control panel schematics
- Button/switch locations
- System flowcharts

**Multi-Device Intelligence**
Automatically handles complex hardware setups:
- Separate stick and throttle identification
- Rudder pedal integration
- Control panel mapping
- Device ID management

**Adaptive Generation**
Creates configurations based on:
- Controller type (unified vs multi-device)
- Available buttons and axes
- Aircraft complexity
- Simulator capabilities

## 🛠️ Troubleshooting
**Device Not Detected**
- Reconnect USB devices and restart the simulator.
- Check Windows Game Controllers by running `joy.cpl` from the Run dialog (Win+R).
- Try different USB ports (USB 3.0 is recommended over 2.0).

**Wrong Button Mappings**
- Use device testing software to verify button IDs.
- Be aware that device IDs may vary by USB port.
- The connection order of devices can affect their numbering in Windows.

**Axis Not Responding**
- Check axis calibration in the simulator's settings.
- Verify that dead zones are configured correctly.
- Some axes may need to be inverted within the simulator's control settings.

**API Errors**
- Verify that `GOOGLE_API_KEY` is correctly set in your `.env` file.
- Check your API quota limits (the free tier is typically 15 requests/minute).
- Ensure you have a stable internet connection.

**PDF Extraction Issues**
- Ensure the PDF is not corrupted or password-protected.
- Try reducing image extraction quality or disabling it if the option is available.
- Very large PDFs (>100MB) may cause timeouts.

## 📁 Project Structure
```
gamechangerai/
├── .env                      # API key configuration (not in git)
├── .gitignore                # Git ignore rules
├── DCS_User_Manual_EN_2020.pdf # Integrated DCS manual
├── main.py                   # Main application (all simulators)
├── main_dcs.py               # DCS World specific
├── main_flightstick.py       # Unified HOTAS
├── main_multiconfig.py       # Multi-device HOTAS
├── main_sticknthrottle.py    # Stick + Throttle
├── main_wo_reset.py          # Version without reset button
├── README.md                 # This file
└── requirements.txt          # Python dependencies
```

## 🤝 Contributing
Contributions are welcome! Please follow these steps:
1. Fork the repository.
2. Create a new feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

## 📝 License & Disclaimer
**License**
This project is provided as-is for personal and educational use.

**⚠️ Disclaimer**
- GAMECHANGER generates suggested control mappings based on AI analysis.
- Always verify generated configurations before use.
- Test all controls in a safe environment (e.g., on the ground, in a training mission) before flight.
- The developers are not responsible for any damage or issues arising from the use of this software.

## 🌟 Tips for Best Results
- **Upload Complete Manuals**: Include aircraft manuals with detailed cockpit diagrams.
- **Include Controller Manuals**: Upload manuals for ALL devices (stick, throttle, pedals) for the most accurate mapping.
- **Provide Context**: Enter the aircraft name even when not uploading a manual to give the AI context.
- **Check Device IDs**: Verify button/axis mappings with a hardware testing utility.
- **Calibrate Axes**: Always calibrate your axes in the simulator after loading a new profile.
- **Test Incrementally**: Test critical controls (flight, weapons) before moving on to complex systems.

## 🔗 Useful Links
- [Google AI Studio](https://aistudio.google.com/) - Get your API key
- [Streamlit Documentation](https://docs.streamlit.io/)
- [PyMuPDF Documentation](https://pymupdf.readthedocs.io/en/latest/)
- [DCS World](https://www.digitalcombatsimulator.com/en/)

## 📞 Support
For issues, questions, or feature requests:
- Open an issue on the GitHub repository.
- Check existing issues for solutions.
- Join relevant flight simulator community forums for general advice.

## 🎉 Acknowledgments
- Google for the **Gemini 2.5 Pro** model.
- The developers of **PyMuPDF** for excellent PDF processing capabilities.
- The **Streamlit** team for making web app creation in Python so accessible.
- The vibrant flight simulator communities for their inspiration and feedback.

---
Made with ❤️ for the flight simulation community# gamechanger
