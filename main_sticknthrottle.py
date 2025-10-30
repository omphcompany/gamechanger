import streamlit as st
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import fitz  # PyMuPDF
from PIL import Image
import io
import re
import base64
import json

# --- Configuration ---
load_dotenv()

# Configure the Gemini API
try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("GOOGLE_API_KEY not found. Please set it in your .env file.")
        st.stop()

    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error(f"Error configuring Gemini API: {e}")
    st.stop()

# --- Simulator Configuration Database ---
SIMULATOR_CONFIGS = {
    "DCS World": {
        "file_format": "lua",
        "file_extension": ".lua",
        "config_location": "Saved Games/DCS/Config/Input/",
        "description": "Lua script with device tables and command assignments",
        "multi_device_support": True,
    },
    "Microsoft Flight Simulator 2020": {
        "file_format": "xml",
        "file_extension": ".xml",
        "config_location": "AppData/Local/Packages/Microsoft.FlightSimulator_*/LocalCache/",
        "description": "XML profile with action mappings",
        "multi_device_support": True,
    },
    "IL-2 Sturmovik": {
        "file_format": "map",
        "file_extension": ".map",
        "config_location": "IL-2 Sturmovik Great Battles/data/input/",
        "description": "Key=Value format with device IDs",
        "multi_device_support": True,
    },
    "Falcon BMS": {
        "file_format": "key",
        "file_extension": ".key",
        "config_location": "Falcon BMS 4.37/User/Config/",
        "description": "Binary key file (text representation)",
        "multi_device_support": True,
    },
    "War Thunder": {
        "file_format": "blk",
        "file_extension": ".blk",
        "config_location": "War Thunder/UserPresets/",
        "description": "Config.blk format with axis and button assignments",
        "multi_device_support": True,
    },
    "X-Plane 11/12": {
        "file_format": "txt",
        "file_extension": ".txt",
        "config_location": "X-Plane 12/Output/preferences/",
        "description": "Joystick configuration text file",
        "multi_device_support": True,
    },
    "Elite Dangerous": {
        "file_format": "binds",
        "file_extension": ".binds",
        "config_location": "AppData/Local/Frontier Developments/Elite Dangerous/Options/Bindings/",
        "description": "XML bindings file",
        "multi_device_support": True,
    },
    "Star Citizen": {
        "file_format": "xml",
        "file_extension": ".xml",
        "config_location": "Star Citizen/LIVE/USER/Client/0/Controls/Mappings/",
        "description": "ActionMaps XML format",
        "multi_device_support": True,
    },
}

# --- HOTAS Component Database ---
HOTAS_COMPONENTS = {
    "Thrustmaster HOTAS Warthog": {
        "components": ["Flight Stick", "Throttle"],
        "description": "A-10C replica HOTAS with separate stick and throttle units",
        "devices": {
            "Flight Stick": "Thrustmaster Hotas Warthog Joystick (Replica A-10C stick with multiple hats, two-stage trigger)",
            "Throttle": "Thrustmaster Hotas Warthog Throttle (Dual throttles, slew control, multiple switches)"
        }
    },
    "VelocityOne Flightstick": {
        "components": ["Unified HOTAS"],
        "description": "All-in-one HOTAS with integrated throttle levers",
        "devices": {
            "Unified HOTAS": "Turtle Beach VelocityOne Flightstick (Stick + integrated throttles, analog TDC, trim wheel)"
        }
    },
    "Thrustmaster T.16000M FCS": {
        "components": ["Joystick", "Throttle", "Rudder Pedals (Optional)"],
        "description": "Complete HOTAS setup with optional pedals",
        "devices": {
            "Joystick": "Thrustmaster T.16000M Joystick (Ambidextrous with 16 buttons)",
            "Throttle": "Thrustmaster TWCS Throttle (Throttle with ministick, slider, 14 buttons)",
            "Rudder Pedals (Optional)": "Thrustmaster TFRP Rudder Pedals"
        }
    },
    "Logitech X56": {
        "components": ["Joystick", "Throttle"],
        "description": "Professional HOTAS with RGB and extensive controls",
        "devices": {
            "Joystick": "Logitech X56 Stick (Multiple hats, analog ministick, RGB, 189 commands)",
            "Throttle": "Logitech X56 Throttle (Dual throttles, multiple hats, RGB)"
        }
    },
    "Winwing Orion 2 F/A-18": {
        "components": ["Joystick", "Throttle", "Control Panel (Optional)"],
        "description": "F/A-18 replica HOTAS with optional UFC panel",
        "devices": {
            "Joystick": "Winwing Orion 2 F/A-18 Stick (1:1 scale F/A-18 grip)",
            "Throttle": "Winwing Orion 2 F/A-18 Throttle (Dual throttles with TDC)",
            "Control Panel (Optional)": "Winwing Super Taurus UFC"
        }
    },
    "VKB Gladiator NXT + TWCS": {
        "components": ["Joystick", "Throttle"],
        "description": "Popular combo: VKB stick + Thrustmaster throttle",
        "devices": {
            "Joystick": "VKB Gladiator NXT (High-precision with multiple hats)",
            "Throttle": "Thrustmaster TWCS Throttle"
        }
    },
    "Virpil Constellation": {
        "components": ["Joystick", "Throttle", "Control Panel (Optional)"],
        "description": "Premium modular HOTAS system",
        "devices": {
            "Joystick": "Virpil VPC Constellation ALPHA Grip",
            "Throttle": "Virpil VPC MongoosT-50CM3 Throttle",
            "Control Panel (Optional)": "Virpil VPC Control Panel"
        }
    },
}


# --- Helper Functions ---
def extract_pdf_content(uploaded_file, max_images=10, max_image_size=(800, 800)):
    """Extract text and images from PDF using PyMuPDF with size limits."""
    if uploaded_file is None:
        return None, []

    try:
        pdf_bytes = uploaded_file.read()
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")

        text_content = ""
        image_parts = []
        image_count = 0

        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            page_text = page.get_text()
            text_content += f"\n\n--- Page {page_num + 1} ---\n\n{page_text}"

            if image_count < max_images:
                image_list = page.get_images()
                for img_index, img in enumerate(image_list):
                    if image_count >= max_images:
                        break

                    try:
                        xref = img[0]
                        base_image = pdf_document.extract_image(xref)
                        image_bytes = base_image["image"]

                        pil_image = Image.open(io.BytesIO(image_bytes))
                        pil_image.thumbnail(max_image_size, Image.Resampling.LANCZOS)

                        buffered = io.BytesIO()
                        pil_image.convert('RGB').save(buffered, format="JPEG", quality=85, optimize=True)
                        img_base64 = base64.b64encode(buffered.getvalue()).decode()

                        if len(img_base64) < 4 * 1024 * 1024:
                            image_parts.append({'mime_type': 'image/jpeg', 'data': img_base64})
                            image_count += 1
                    except Exception as e:
                        print(f"Could not extract image {img_index} from page {page_num + 1}: {e}")

        pdf_document.close()

        if image_count >= max_images:
            st.info(f"ℹ️ Extracted first {max_images} images to stay within size limits.")

        return text_content, image_parts
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None, []


def generate_multi_device_config(aircraft_text, aircraft_images, controller_manuals, hotas_name, hotas_devices,
                                 aircraft_name, simulator):
    """Generate configuration supporting multiple HOTAS components."""
    model = "gemini-2.0-flash-exp"
    sim_config = SIMULATOR_CONFIGS.get(simulator, {})
    file_format = sim_config.get("file_format", "txt")
    config_location = sim_config.get("config_location", "")

    device_descriptions = []
    for component, device_desc in hotas_devices.items():
        manual_info = controller_manuals.get(component, {})
        manual_text = manual_info.get('text', 'No manual provided')
        if manual_text and manual_text != 'No manual provided':
            device_descriptions.append(
                f"\n### {component}\n- Hardware: {device_desc}\n- Manual Content: {manual_text[:2000]}")
        else:
            device_descriptions.append(
                f"\n### {component}\n- Hardware: {device_desc}\n- Manual Content: No manual provided")

    devices_text = "\n".join(device_descriptions)

    prompt = f"""## TASK: Generate a COMBAT-FOCUSED multi-device HOTAS configuration for {aircraft_name} in {simulator}.

## CRITICAL REQUIREMENTS:
This is a **MULTI-DEVICE HOTAS SETUP**: {hotas_name}
Configuration MUST handle MULTIPLE physical devices: {', '.join(hotas_devices.keys())}

## RESPONSE FORMAT: Your response MUST have THREE distinct parts:

### Part 1: Multi-Device Enhanced Technical Mapping Table
Create a comprehensive 5-column Markdown table with this EXACT format:

| HOTAS Component | Physical Input | Device ID | {simulator} Command | Function & Rationale |
|-----------------|----------------|-----------|---------------------|----------------------|

**CRITICAL TABLE FORMAT:**
- Column 1: HOTAS Component (e.g., "**Flight Stick**", "**Throttle**", "**Rudder Pedals**")
- Column 2: Physical Input - The actual button/axis name from controller manual (e.g., "Stick Y-Axis", "Trigger", "TDC Slew Up")
- Column 3: Device ID - ONLY the device identifier (e.g., "JOY_Y", "JOY_BTN1", "JOY_SLIDER1") - NO action descriptions
- Column 4: {simulator} Command - Exact command for the simulator
- Column 5: Function & Rationale - Detailed explanation including aircraft function, ergonomic reasoning, technical notes

**CRITICAL MAPPING PRIORITIES:**
1. **Flight Stick Device:** Primary flight axes, weapon trigger, NWS button, trim hat, weapon release
2. **Throttle Device:** Throttle axes, TDC slew, sensor switches, countermeasures, speed brake, master arm, radio PTT
3. **Additional Devices:** Rudder pedals (yaw, brakes), control panels

### Part 2: Installation Instructions
Step-by-step instructions for installing in {simulator}:
- File location: {config_location}
- How to activate/load the profile
- Device detection verification steps

### Part 3: Complete Configuration File(s)
Generate {file_format.upper()} configuration file ready for immediate use.

---
## HOTAS HARDWARE CONFIGURATION:
{hotas_name}
{devices_text}

---
## AIRCRAFT SPECIFICATIONS:
Aircraft: {aircraft_name}
{f"Aircraft Manual Content:\n{aircraft_text[:12000]}" if aircraft_text else "No aircraft manual provided."}

---

## FINAL INSTRUCTIONS:
1. **Device ID Column** - MUST contain ONLY the device identifier - NO action descriptions
2. **Physical Input Column** - Extract exact button/axis names from controller manual if provided
3. **Ensure DEVICE SEPARATION** - Each physical device must have unique identifiers
4. **Generate READY-TO-USE files** - User copies directly into {simulator}
5. **Focus on COMBAT effectiveness** - Weapons, sensors, countermeasures are priority

Generate the complete multi-device configuration now."""

    content_parts = [types.Part.from_text(text=prompt)]

    if aircraft_images:
        for img_data in aircraft_images[:5]:
            content_parts.append(
                types.Part.from_bytes(data=base64.b64decode(img_data['data']), mime_type=img_data['mime_type']))

    for component, manual_data in controller_manuals.items():
        if manual_data.get('images'):
            for img_data in manual_data['images'][:2]:
                content_parts.append(
                    types.Part.from_bytes(data=base64.b64decode(img_data['data']), mime_type=img_data['mime_type']))

    contents = [types.Content(role="user", parts=content_parts)]
    generate_content_config = types.GenerateContentConfig(temperature=0.7, top_p=0.95, max_output_tokens=8192)

    try:
        st.info(f"🤖 Generating {simulator} multi-device configuration for {hotas_name}...")
        response_text = ""
        response_placeholder = st.empty()

        for chunk in client.models.generate_content_stream(model=model, contents=contents,
                                                           config=generate_content_config):
            if chunk.text:
                response_text += chunk.text
                response_placeholder.markdown(f"*Generating... {len(response_text)} characters*")

        response_placeholder.empty()
        return response_text
    except Exception as e:
        st.error(f"An error occurred during API call: {e}")
        return None


def parse_markdown_table_to_text(table_text):
    """Convert a markdown table to plain text format."""
    lines = table_text.strip().split('\n')
    text_format_lines = []

    for i, line in enumerate(lines):
        if '---' in line or not line.strip():
            continue
        cells = [cell.strip() for cell in line.split('|') if cell.strip()]
        if cells:
            text_format_lines.extend(cells)
            if i > 0:
                text_format_lines.append('')

    return '\n'.join(text_format_lines)


# --- Main Application UI ---
st.set_page_config(page_title="GAMECHANGER - AI Enabled Controller Configurations", page_icon="✈️", layout="wide")

st.title("✈️ GAMECHANGER - AI Enabled Controller Configurations")
st.markdown("""
**Universal Multi-Device HOTAS Profile Generator**

Generate **ready-to-use** controller profiles for any flight simulator. Supports multi-device HOTAS setups 
(Stick + Throttle + Pedals) with proper device separation and installation instructions.

🎯 **Combat-Focused** | 🎮 **Multi-Device Support** | 📦 **Instant Installation**
""")

# Add reset button at the top right
col_title, col_reset = st.columns([5, 1])
with col_reset:
    if st.button("🔄 Start New", type="secondary", use_container_width=True, help="Clear all and start fresh"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

st.markdown("---")

st.subheader("⚙️ Configuration Setup")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 1️⃣ Select Flight Simulator")
    selected_simulator = st.selectbox("Choose your simulator:", options=list(SIMULATOR_CONFIGS.keys()), index=0,
                                      help="Select your flight simulator")

    sim_info = SIMULATOR_CONFIGS[selected_simulator]
    st.info(
        f"**File Format:** `{sim_info['file_extension']}`\n**Install Location:** `{sim_info['config_location']}`\n**Multi-Device Support:** {'✅ Yes' if sim_info.get('multi_device_support') else '❌ No'}")

    st.markdown("### 2️⃣ Aircraft Configuration")
    aircraft_name = st.text_input("Aircraft Name:", placeholder="e.g., F/A-18C Hornet, F-16C Viper",
                                  help="Enter aircraft name or leave blank")
    aircraft_pdf = st.file_uploader("📄 Upload Aircraft Manual (PDF) - Optional", type="pdf", key="aircraft_pdf",
                                    help="Upload aircraft manual")

with col2:
    st.markdown("### 3️⃣ Select HOTAS Setup")
    selected_hotas = st.selectbox("Choose your HOTAS configuration:", options=list(HOTAS_COMPONENTS.keys()), index=0)

    hotas_info = HOTAS_COMPONENTS[selected_hotas]
    st.info(f"**Components:** {', '.join(hotas_info['components'])}\n**Description:** {hotas_info['description']}")

st.markdown("---")
st.markdown("### 4️⃣ Upload Controller Manuals (Optional)")
st.caption("Upload a manual for each device component for best accuracy")

hotas_devices = HOTAS_COMPONENTS[selected_hotas]['devices']
controller_manuals = {}
cols = st.columns(len(hotas_devices))

for idx, (component, description) in enumerate(hotas_devices.items()):
    with cols[idx]:
        st.markdown(f"**{component}**")
        st.caption(description[:100] + ("..." if len(description) > 100 else ""))
        uploaded = st.file_uploader(f"Upload {component} manual", type="pdf", key=f"manual_{component}",
                                    label_visibility="collapsed")
        controller_manuals[component] = {'file': uploaded}

st.markdown("---")

with st.expander("⚙️ Advanced Options"):
    col_a, col_b = st.columns(2)
    with col_a:
        extract_images = st.checkbox("Extract images from PDFs", value=True)
        max_images = st.slider("Max images per manual", 0, 20, 10)
    with col_b:
        generate_backup = st.checkbox("Generate backup instructions", value=True)
        include_troubleshooting = st.checkbox("Include troubleshooting guide", value=True)

st.markdown("---")

if st.button("🚀 GENERATE MULTI-DEVICE PROFILE", type="primary", use_container_width=True):
    if not aircraft_name and not aircraft_pdf:
        st.warning("⚠️ Please upload an aircraft manual OR enter an aircraft name.")
    else:
        with st.spinner("🔍 Analyzing manuals and generating configuration..."):
            aircraft_text = None
            aircraft_images = []

            if aircraft_pdf:
                aircraft_text, aircraft_images = extract_pdf_content(aircraft_pdf,
                                                                     max_images=max_images if extract_images else 0)
                if aircraft_text:
                    st.success(
                        f"✅ Extracted aircraft manual: {len(aircraft_text)} characters, {len(aircraft_images)} images")

            for component, data in controller_manuals.items():
                if data['file']:
                    text, images = extract_pdf_content(data['file'],
                                                       max_images=max_images // 2 if extract_images else 0)
                    data['text'] = text
                    data['images'] = images
                    if text:
                        st.success(f"✅ Extracted {component} manual")
                else:
                    data['text'] = None
                    data['images'] = []

            if not aircraft_name:
                aircraft_name = "Aircraft from Manual" if aircraft_text else "Generic Combat Aircraft"

            full_response = generate_multi_device_config(aircraft_text, aircraft_images, controller_manuals,
                                                         selected_hotas, hotas_devices, aircraft_name,
                                                         selected_simulator)

            if full_response:
                st.success("✅ Multi-device profile generated successfully!")

                code_blocks = list(re.finditer(r"```(\w+)?\n(.*?)\n```", full_response, re.DOTALL))
                sections = full_response.split("###")

                st.markdown("---")
                for section in sections:
                    if "mapping" in section.lower() and "|" in section:
                        st.subheader(f"✈️ {aircraft_name} - {selected_hotas}")
                        st.caption(f"Multi-Device Configuration for {selected_simulator}")
                        st.markdown("###" + section)

                        table_match = re.search(r'\|.*?\|.*?\|.*?\|.*?\|.*?\|(?:\n\|.*?\|.*?\|.*?\|.*?\|.*?\|)+',
                                                section, re.DOTALL)
                        if table_match:
                            clean_table = table_match.group(0)
                            text_format = parse_markdown_table_to_text(clean_table)

                            tab1, tab2 = st.tabs(["📊 Markdown Table", "📝 Plain Text"])
                            with tab1:
                                st.text_area("Markdown Format:", value=clean_table, height=200, key="md_table")
                                st.download_button("📥 Download Markdown", data=clean_table,
                                                   file_name=f"{aircraft_name.replace('/', '-')}_mapping.md",
                                                   mime="text/markdown")
                            with tab2:
                                st.text_area("Plain Text Format:", value=text_format, height=200, key="txt_table")
                                st.download_button("📥 Download Text", data=text_format,
                                                   file_name=f"{aircraft_name.replace('/', '-')}_mapping.txt",
                                                   mime="text/plain")
                        break

                st.markdown("---")

                for section in sections:
                    if "installation" in section.lower():
                        st.subheader("📦 Installation Instructions")
                        st.markdown("###" + section)
                        break

                st.markdown("---")

                st.subheader(f"📝 {selected_simulator} Configuration File(s)")
                st.caption("Ready to use - just download and install!")

                if code_blocks:
                    for idx, match in enumerate(code_blocks):
                        lang = match.group(1) or sim_info['file_format']
                        code = match.group(2).strip()

                        with st.expander(f"📄 Configuration File #{idx + 1}", expanded=(idx == 0)):
                            st.code(code, language=lang)

                            file_ext = sim_info['file_extension']
                            filename = f"{aircraft_name.replace('/', '-')}_{selected_hotas.replace(' ', '_')}_profile{file_ext}"

                            st.download_button(label=f"📥 Download Configuration File #{idx + 1}", data=code,
                                               file_name=filename, mime="text/plain", key=f"download_{idx}",
                                               use_container_width=True)
                else:
                    st.code(full_response, language="text")

                st.markdown("---")

                st.success(f"""
### 🎉 Profile Generated Successfully!

**Your multi-device HOTAS profile is ready!**

**Next Steps:**
1. ✅ Download the configuration file(s) above
2. 📁 Place in: `{sim_info['config_location']}`
3. 🔌 Connect all devices: {', '.join(hotas_devices.keys())}
4. 🚀 Launch {selected_simulator}
5. ⚙️ Load the profile from the controls menu
6. 🎯 Verify device detection and calibrate axes
7. ✈️ Take to the skies!

**Important:** Ensure all physical devices are connected BEFORE loading the profile.
                """)

                if include_troubleshooting:
                    with st.expander("🔧 Troubleshooting Guide"):
                        st.markdown("""
### Common Issues and Solutions

**Problem: Device not detected**
- Reconnect USB devices and restart the simulator
- Check Windows Game Controllers (joy.cpl)
- Try different USB ports (USB 3.0 recommended)

**Problem: Wrong button mappings**
- Use device testing software to verify button IDs
- Device IDs may vary by USB port or connection order

**Problem: Axis inverted or not responding**
- Check axis calibration in simulator settings
- Verify dead zones are configured
- Some axes may need inversion in controls menu

**Need More Help?**
- Check simulator's official forums
- Join community Discord servers
- Consult device manufacturer support
                        """)
            else:
                st.error("❌ Failed to generate configuration.")

st.markdown("---")
st.caption(
    "💡 **Pro Tip:** Upload manuals for ALL devices (stick, throttle, pedals) and include aircraft manual with cockpit diagrams!")
st.caption("🌟 **GAMECHANGER AI** - Making flight simulation setup effortless")