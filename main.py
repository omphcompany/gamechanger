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
        "user_manual": "DCS_User_Manual_EN_2020.pdf"
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
        "type": "multi_device",
        "components": ["Flight Stick", "Throttle"],
        "description": "A-10C replica HOTAS with separate stick and throttle units",
        "devices": {
            "Flight Stick": "Thrustmaster Hotas Warthog Joystick (Replica A-10C stick with multiple hats, two-stage trigger)",
            "Throttle": "Thrustmaster Hotas Warthog Throttle (Dual throttles, slew control, multiple switches)"
        }
    },
    "VelocityOne Flightstick": {
        "type": "unified",
        "components": ["Unified HOTAS"],
        "description": "All-in-one HOTAS with integrated throttle levers",
        "devices": {
            "Unified HOTAS": "Turtle Beach VelocityOne Flightstick (Stick + integrated throttles, analog TDC, trim wheel)"
        }
    },
    "Thrustmaster T.16000M FCS": {
        "type": "multi_device",
        "components": ["Joystick", "Throttle", "Rudder Pedals (Optional)"],
        "description": "Complete HOTAS setup with optional pedals",
        "devices": {
            "Joystick": "Thrustmaster T.16000M Joystick (Ambidextrous with 16 buttons)",
            "Throttle": "Thrustmaster TWCS Throttle (Throttle with ministick, slider, 14 buttons)",
            "Rudder Pedals (Optional)": "Thrustmaster TFRP Rudder Pedals"
        }
    },
    "Logitech X56": {
        "type": "multi_device",
        "components": ["Joystick", "Throttle"],
        "description": "Professional HOTAS with RGB and extensive controls",
        "devices": {
            "Joystick": "Logitech X56 Stick (Multiple hats, analog ministick, RGB, 189 commands)",
            "Throttle": "Logitech X56 Throttle (Dual throttles, multiple hats, RGB)"
        }
    },
    "Winwing Orion 2 F/A-18": {
        "type": "multi_device",
        "components": ["Joystick", "Throttle", "Control Panel (Optional)"],
        "description": "F/A-18 replica HOTAS with optional UFC panel",
        "devices": {
            "Joystick": "Winwing Orion 2 F/A-18 Stick (1:1 scale F/A-18 grip)",
            "Throttle": "Winwing Orion 2 F/A-18 Throttle (Dual throttles with TDC)",
            "Control Panel (Optional)": "Winwing Super Taurus UFC"
        }
    },
    "VKB Gladiator NXT + TWCS": {
        "type": "multi_device",
        "components": ["Joystick", "Throttle"],
        "description": "Popular combo: VKB stick + Thrustmaster throttle",
        "devices": {
            "Joystick": "VKB Gladiator NXT (High-precision with multiple hats)",
            "Throttle": "Thrustmaster TWCS Throttle"
        }
    },
    "Virpil Constellation": {
        "type": "multi_device",
        "components": ["Joystick", "Throttle", "Control Panel (Optional)"],
        "description": "Premium modular HOTAS system",
        "devices": {
            "Joystick": "Virpil VPC Constellation ALPHA Grip",
            "Throttle": "Virpil VPC MongoosT-50CM3 Throttle",
            "Control Panel (Optional)": "Virpil VPC Control Panel"
        }
    },
    "Xbox Controller": {
        "type": "gamepad",
        "components": ["Gamepad"],
        "description": "Xbox wireless controller with dual analog sticks",
        "devices": {
            "Gamepad": "Xbox Wireless Controller (Dual analog sticks, triggers, face buttons, D-pad)"
        }
    },
    "Logitech Extreme 3D Pro": {
        "type": "joystick_only",
        "components": ["Joystick"],
        "description": "Single joystick with twist rudder and throttle slider",
        "devices": {
            "Joystick": "Logitech Extreme 3D Pro (Twist rudder, throttle slider, 12 buttons)"
        }
    },
}


# --- Helper Functions ---
def extract_pdf_content(uploaded_file):
    """Extract ALL text and images from PDF using PyMuPDF - no limits."""
    if uploaded_file is None:
        return None, []

    try:
        pdf_bytes = uploaded_file.read()
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")

        text_content = ""
        image_parts = []

        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            page_text = page.get_text()
            text_content += f"\n\n--- Page {page_num + 1} ---\n\n{page_text}"

            # Extract all images from page
            image_list = page.get_images()
            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]
                    base_image = pdf_document.extract_image(xref)
                    image_bytes = base_image["image"]

                    pil_image = Image.open(io.BytesIO(image_bytes))
                    pil_image.thumbnail((800, 800), Image.Resampling.LANCZOS)

                    buffered = io.BytesIO()
                    pil_image.convert('RGB').save(buffered, format="JPEG", quality=85, optimize=True)
                    img_base64 = base64.b64encode(buffered.getvalue()).decode()

                    if len(img_base64) < 4 * 1024 * 1024:
                        image_parts.append({'mime_type': 'image/jpeg', 'data': img_base64})
                except Exception as e:
                    print(f"Could not extract image {img_index} from page {page_num + 1}: {e}")

        pdf_document.close()
        return text_content, image_parts
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None, []


def load_simulator_manual(simulator):
    """Load simulator user manual if available."""
    sim_config = SIMULATOR_CONFIGS.get(simulator, {})
    manual_file = sim_config.get("user_manual")

    if manual_file and os.path.exists(manual_file):
        try:
            with open(manual_file, 'rb') as f:
                pdf_document = fitz.open(stream=f.read(), filetype="pdf")

                text_content = ""
                for page_num in range(min(len(pdf_document), 50)):
                    page = pdf_document[page_num]
                    page_text = page.get_text()
                    if any(keyword in page_text.lower() for keyword in
                           ['control', 'input', 'joystick', 'hotas', 'configuration', 'mapping']):
                        text_content += f"\n\n--- Page {page_num + 1} ---\n\n{page_text}"

                pdf_document.close()
                return text_content[:5000]
        except Exception as e:
            print(f"Could not load simulator manual: {e}")
            return None
    return None


def generate_adaptive_config(aircraft_text, aircraft_images, controller_manuals, hotas_name, hotas_devices,
                             aircraft_name, simulator, controller_type):
    """Generate configuration that adapts to controller type."""
    model = "gemini-2.0-flash-exp"
    sim_config = SIMULATOR_CONFIGS.get(simulator, {})
    file_format = sim_config.get("file_format", "txt")
    config_location = sim_config.get("config_location", "")

    simulator_manual_text = load_simulator_manual(simulator)

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

    if controller_type == "unified":
        table_format = "| Physical Input | Device ID | {simulator} Command | Function & Rationale |\n|----------------|-----------|---------------------|----------------------|"
        mapping_instructions = "**UNIFIED DEVICE** - Single physical unit with all controls integrated."
    elif controller_type == "multi_device":
        table_format = "| HOTAS Component | Physical Input | Device ID | {simulator} Command | Function & Rationale |\n|-----------------|----------------|-----------|---------------------|----------------------|"
        mapping_instructions = "**MULTI-DEVICE** - Separate physical devices requiring unique identification."
    elif controller_type == "joystick_only":
        table_format = "| Physical Input | Device ID | {simulator} Command | Function & Rationale |\n|----------------|-----------|---------------------|----------------------|"
        mapping_instructions = "**JOYSTICK-ONLY** - Single joystick with limited controls."
    elif controller_type == "gamepad":
        table_format = "| Physical Input | Device ID | {simulator} Command | Function & Rationale |\n|----------------|-----------|---------------------|----------------------|"
        mapping_instructions = "**GAMEPAD** - Standard gamepad with dual sticks."
    else:
        table_format = "| HOTAS Component | Physical Input | Device ID | {simulator} Command | Function & Rationale |\n|-----------------|----------------|-----------|---------------------|----------------------|"
        mapping_instructions = ""

    prompt = f"""## TASK: Generate a COMBAT-FOCUSED controller configuration for {aircraft_name} in {simulator}.

## CONTROLLER TYPE:
{hotas_name} - {controller_type.upper().replace('_', ' ')} ({len(hotas_devices)} device{'s' if len(hotas_devices) > 1 else ''})

## RESPONSE FORMAT (3 parts):

### Part 1: Complete Technical Mapping Table
{table_format}

{mapping_instructions}
- Generate AT LEAST 30-40 comprehensive mappings
- Device ID column: ONLY the identifier (JOY_Y, JOY_BTN1, etc.)
- Cover ALL combat-critical controls

### Part 2: Installation Instructions
{"Based on official documentation:" if simulator_manual_text else "Step-by-step installation:"}
{f"\nMANUAL EXCERPT:\n{simulator_manual_text}\n" if simulator_manual_text else ""}
- File location: {config_location}
- How to load/import profile
- Device detection & calibration
- Testing & verification

### Part 3: Configuration File
{file_format.upper()} file - ready to use, properly formatted.

---
## HARDWARE:
{hotas_name}
{devices_text}

## AIRCRAFT:
{aircraft_name}
{f"Manual:\n{aircraft_text[:12000]}" if aircraft_text else "Use standard combat aircraft controls."}

---

## REQUIREMENTS:
1. COMPLETE table (30-40+ rows minimum)
2. Device ID column - identifier ONLY
3. Physical input - exact names from manuals
4. ACCURATE installation from manual
5. READY-TO-USE configuration file
6. COMBAT-focused prioritization

Generate now."""

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
        controller_type_label = controller_type.replace('_', ' ').title()
        st.info(f"🤖 Generating {simulator} {controller_type_label} configuration for {hotas_name}...")
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


# --- Main Application UI ---
st.set_page_config(page_title="GAMECHANGER - AI Enabled Controller Configurations", page_icon="✈️", layout="wide")

st.title("✈️ GAMECHANGER - AI Enabled Controller Configurations")
st.markdown("""
**Universal Adaptive HOTAS Profile Generator**

Generate **ready-to-use** controller profiles for any flight simulator. Automatically detects controller type 
and adapts the configuration accordingly.

🎯 **Combat-Focused** | 🎮 **Adaptive Multi-Device Support** | 📦 **Instant Installation**
""")

# Reset button
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
    selected_simulator = st.selectbox(
        "Choose your simulator:",
        options=[""] + list(SIMULATOR_CONFIGS.keys()),
        format_func=lambda x: "Select simulator..." if x == "" else x,
        help="Select your flight simulator"
    )

    if selected_simulator:
        sim_info = SIMULATOR_CONFIGS[selected_simulator]
        manual_status = "✅ Manual Available" if sim_info.get("user_manual") and os.path.exists(
            sim_info.get("user_manual", "")) else "ℹ️ Generic Instructions"
        st.info(
            f"**File Format:** `{sim_info['file_extension']}`\n**Install Location:** `{sim_info['config_location']}`\n**Instructions:** {manual_status}")

    st.markdown("### 2️⃣ Upload Aircraft Manual")
    aircraft_pdf = st.file_uploader("📄 Upload Aircraft Manual (PDF)", type="pdf", key="aircraft_pdf",
                                    help="Upload aircraft flight manual with cockpit diagrams")

with col2:
    st.markdown("### 3️⃣ Select Controller Setup")
    selected_hotas = st.selectbox(
        "Choose your controller:",
        options=[""] + list(HOTAS_COMPONENTS.keys()),
        format_func=lambda x: "Select controller..." if x == "" else x
    )

    if selected_hotas:
        hotas_info = HOTAS_COMPONENTS[selected_hotas]
        controller_type = hotas_info.get('type', 'multi_device')

        type_icons = {'unified': '🎮', 'multi_device': '🕹️+🎚️', 'joystick_only': '🕹️', 'gamepad': '🎮'}
        type_labels = {'unified': 'Unified Device', 'multi_device': 'Multi-Device Setup',
                       'joystick_only': 'Single Joystick', 'gamepad': 'Gamepad'}

        st.info(
            f"**Type:** {type_icons.get(controller_type, '🎮')} {type_labels.get(controller_type, 'Unknown')}\n**Components:** {', '.join(hotas_info['components'])}\n**Description:** {hotas_info['description']}")

st.markdown("---")

if selected_hotas:
    st.markdown("### 4️⃣ Upload Controller Manuals (Optional)")
    st.caption("Upload manuals for accurate button/axis identification")

    hotas_devices = HOTAS_COMPONENTS[selected_hotas]['devices']
    controller_manuals = {}

    num_devices = len(hotas_devices)
    cols = [st.container()] if num_devices == 1 else st.columns(num_devices)

    for idx, (component, description) in enumerate(hotas_devices.items()):
        with cols[idx] if num_devices > 1 else cols[0]:
            st.markdown(f"**{component}**")
            st.caption(description[:100] + ("..." if len(description) > 100 else ""))
            uploaded = st.file_uploader(f"Upload {component} manual", type="pdf", key=f"manual_{component}",
                                        label_visibility="collapsed")
            controller_manuals[component] = {'file': uploaded}

    st.markdown("---")

if st.button("🚀 GENERATE PROFILE", type="primary", use_container_width=True,
             disabled=not (selected_simulator and selected_hotas and aircraft_pdf)):
    if not selected_simulator or not selected_hotas or not aircraft_pdf:
        st.warning("⚠️ Please select simulator, controller, and upload aircraft manual.")
    else:
        with st.spinner("🔍 Analyzing documents and generating configuration..."):
            aircraft_text, aircraft_images = extract_pdf_content(aircraft_pdf)

            if aircraft_text:
                st.success(
                    f"✅ Extracted aircraft manual: {len(aircraft_text)} characters, {len(aircraft_images)} images")

            for component, data in controller_manuals.items():
                if data['file']:
                    text, images = extract_pdf_content(data['file'])
                    data['text'] = text
                    data['images'] = images
                    if text:
                        st.success(f"✅ Extracted {component} manual")
                else:
                    data['text'] = None
                    data['images'] = []

            aircraft_name = "Aircraft from Manual"

            full_response = generate_adaptive_config(aircraft_text, aircraft_images, controller_manuals,
                                                     selected_hotas, hotas_devices, aircraft_name,
                                                     selected_simulator, controller_type)

            if full_response:
                st.success("✅ Profile generated successfully!")

                code_blocks = list(re.finditer(r"```(\w+)?\n(.*?)\n```", full_response, re.DOTALL))
                sections = full_response.split("###")

                displayed_sections = set()

                st.markdown("---")

                # Mapping table - just display it, no export section
                for section in sections:
                    if "mapping" in section.lower() and "|" in section and "mapping_table" not in displayed_sections:
                        st.subheader(f"✈️ {aircraft_name} - {selected_hotas}")
                        st.caption(
                            f"{type_labels.get(controller_type, 'Controller')} Configuration for {selected_simulator}")
                        st.markdown("###" + section)
                        displayed_sections.add("mapping_table")
                        break

                st.markdown("---")

                # Installation instructions
                for section in sections:
                    if "installation" in section.lower() and "installation_instructions" not in displayed_sections:
                        st.subheader("📦 Installation Instructions")
                        st.markdown("###" + section)
                        displayed_sections.add("installation_instructions")
                        break

                st.markdown("---")

                # Configuration files
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
                            st.download_button(f"📥 Download Configuration #{idx + 1}", data=code, file_name=filename,
                                               mime="text/plain", key=f"download_{idx}", use_container_width=True)
                else:
                    st.code(full_response, language="text")

                st.markdown("---")

                device_list = ', '.join(hotas_devices.keys())
                device_msg = f"Connect your {selected_hotas}" if controller_type == "unified" else f"Connect all devices: {device_list}"

                st.success(f"""
### 🎉 Profile Generated Successfully!

**Your {type_labels.get(controller_type, 'controller')} profile is ready!**

**Next Steps:**
1. ✅ Download the configuration file(s) above
2. 📁 Place in: `{sim_info['config_location']}`
3. 🔌 {device_msg}
4. 🚀 Launch {selected_simulator}
5. ⚙️ Follow the installation instructions above
6. 🎯 Verify device detection and calibrate axes
7. ✈️ Take to the skies!

**Important:** Ensure all physical devices are connected BEFORE loading the profile.
                """)
            else:
                st.error("❌ Failed to generate configuration.")

st.markdown("---")
st.caption(
    "💡 **Pro Tip:** Upload manuals for ALL devices and include aircraft manual with cockpit diagrams for best results!")
st.caption("🌟 **GAMECHANGER AI** - Making flight simulation setup effortless with intelligent controller detection")