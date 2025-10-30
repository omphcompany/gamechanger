import streamlit as st
import os
from google import genai
from google.genai import types
import fitz
from PIL import Image
import io
import re
import base64

st.set_page_config(page_title="GAMECHANGER - AI Enabled Controller Configurations", page_icon="✈️", layout="wide")

st.title("✈️ GAMECHANGER - AI Enabled Controller Configurations")
st.markdown("""
**Universal Adaptive HOTAS Profile Generator**

Generate **ready-to-use** controller profiles for any flight simulator. Automatically detects controller type and adapts the configuration accordingly.

 **Combat-Focused** |  **Adaptive Multi-Device Support** |  **Instant Installation**
""")

col_title, col_reset = st.columns([5, 1])
with col_reset:
    if st.button(" Start New", type="secondary", use_container_width=True, help="Clear all and start fresh"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

st.markdown("---")

st.subheader(" Google Gemini API Configuration")

if 'api_key' in st.session_state and st.session_state.api_key:
    api_key = st.session_state.api_key
else:
    api_key = None

col_key1, col_key2 = st.columns([3, 1])

with col_key1:
    user_api_key = st.text_input(
        "Enter your Google Gemini API Key:",
        type="password",
        value=api_key if api_key else "",
        help="Get your free API key from https://aistudio.google.com/",
        placeholder="AIzaSy..."
    )

with col_key2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("✅ Validate Key", use_container_width=True):
        if user_api_key:
            try:
                test_client = genai.Client(api_key=user_api_key)
                st.session_state.api_key = user_api_key
                st.success("✅ API key validated successfully!")
            except Exception as e:
                st.error(f"❌ Invalid API key: {e}")
                st.session_state.api_key = None
        else:
            st.warning("⚠️ Please enter an API key")

if not user_api_key:
    st.info("""
     **How to get a Google Gemini API Key:**
    1. Visit [Google AI Studio](https://aistudio.google.com/)
    2. Sign in with your Google account
    3. Click "Get API Key" 
    4. Create a new API key or use an existing one
    5. Copy and paste it above

    ✨ The free tier includes 15 requests per minute - perfect for this tool!
    """)
    st.stop()

try:
    client = genai.Client(api_key=user_api_key)
except Exception as e:
    st.error(f"Error configuring Gemini API: {e}")
    st.stop()

st.markdown("---")

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
        "description": "Config format with axis and button assignments",
        "multi_device_support": True,
        "template_files": {
            "Thrustmaster HOTAS Warthog": {
                "blk": "War Thunder for Warthog TARGET mapping configuration_blk.txt",
                "fcf": "War Thunder_fcf.txt"
            }
        }
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

HOTAS_COMPONENTS = {
    "Thrustmaster HOTAS Warthog": {
        "type": "multi_device",
        "components": ["Flight Stick", "Throttle"],
        "description": "A-10C replica HOTAS with separate stick and throttle units",
        "software_capable": True,
        "software_name": "TARGET Script Editor",
        "devices": {
            "Flight Stick": "Thrustmaster Hotas Warthog Joystick (Replica A-10C stick with multiple hats, two-stage trigger)",
            "Throttle": "Thrustmaster Hotas Warthog Throttle (Dual throttles, slew control, multiple switches)"
        }
    },
    "VelocityOne Flightstick": {
        "type": "unified",
        "components": ["Unified HOTAS"],
        "description": "All-in-one HOTAS with integrated throttle levers",
        "software_capable": False,
        "devices": {
            "Unified HOTAS": "Turtle Beach VelocityOne Flightstick (Stick + integrated throttles, analog TDC, trim wheel)"
        }
    },
    "Thrustmaster T.16000M FCS": {
        "type": "multi_device",
        "components": ["Joystick", "Throttle", "Rudder Pedals (Optional)"],
        "description": "Complete HOTAS setup with optional pedals",
        "software_capable": True,
        "software_name": "TARGET Script Editor",
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
        "software_capable": True,
        "software_name": "Logitech Gaming Software",
        "devices": {
            "Joystick": "Logitech X56 Stick (Multiple hats, analog ministick, RGB, 189 commands)",
            "Throttle": "Logitech X56 Throttle (Dual throttles, multiple hats, RGB)"
        }
    },
    "Winwing Orion 2 F/A-18": {
        "type": "multi_device",
        "components": ["Joystick", "Throttle", "Control Panel (Optional)"],
        "description": "F/A-18 replica HOTAS with optional UFC panel",
        "software_capable": True,
        "software_name": "SimAppPro",
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
        "software_capable": True,
        "software_name": "VKBDevCfg / TARGET Script Editor",
        "devices": {
            "Joystick": "VKB Gladiator NXT (High-precision with multiple hats)",
            "Throttle": "Thrustmaster TWCS Throttle"
        }
    },
    "Virpil Constellation": {
        "type": "multi_device",
        "components": ["Joystick", "Throttle", "Control Panel (Optional)"],
        "description": "Premium modular HOTAS system",
        "software_capable": True,
        "software_name": "VPC Configuration Tool",
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
        "software_capable": False,
        "devices": {
            "Gamepad": "Xbox Wireless Controller (Dual analog sticks, triggers, face buttons, D-pad)"
        }
    },
    "Logitech Extreme 3D Pro": {
        "type": "joystick_only",
        "components": ["Joystick"],
        "description": "Single joystick with twist rudder and throttle slider",
        "software_capable": False,
        "devices": {
            "Joystick": "Logitech Extreme 3D Pro (Twist rudder, throttle slider, 12 buttons)"
        }
    },
}


def extract_pdf_content(uploaded_file):
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


def load_template_files(simulator, hotas_name):
    """Load template configuration files if available for the simulator and controller combination."""
    sim_config = SIMULATOR_CONFIGS.get(simulator, {})
    template_files = sim_config.get("template_files", {})

    if hotas_name in template_files:
        templates = {}
        for file_type, file_path in template_files[hotas_name].items():
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        templates[file_type] = content
                    st.success(f"✅ Loaded {file_type.upper()} template ({len(content)} chars): {file_path}")
                except Exception as e:
                    st.warning(f"⚠️ Could not load template {file_path}: {e}")
            else:
                st.warning(f"⚠️ Template file not found: {file_path}")
        return templates
    return {}


def generate_adaptive_config(aircraft_text, aircraft_images, controller_manuals, software_manual_text,
                             software_manual_images, hotas_name, hotas_devices, aircraft_name, simulator,
                             controller_type, software_capable, software_name):
    model = "gemini-2.0-flash-exp"
    sim_config = SIMULATOR_CONFIGS.get(simulator, {})
    file_format = sim_config.get("file_format", "txt")
    config_location = sim_config.get("config_location", "")
    simulator_manual_text = load_simulator_manual(simulator)

    template_files = load_template_files(simulator, hotas_name)

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

    software_section = ""
    if software_capable and software_manual_text:
        software_section = f"""
## CONTROLLER SOFTWARE CAPABILITIES:
Software: {software_name}
The controller supports advanced scripting and programming capabilities.

Software Manual Content:
{software_manual_text[:3000]}

**IMPORTANT:** Generate configurations that leverage software capabilities like:
- Multi-stage button presses
- Conditional logic
- Macros and sequences
- Virtual button combinations
- Axis curves and dead zones
- Shift states and layers
"""
    elif software_capable:
        software_section = f"""
## CONTROLLER SOFTWARE CAPABILITIES:
Software: {software_name}
The controller supports advanced scripting (manual not provided, use general knowledge of {software_name}).
"""

    template_section = ""
    if template_files:
        template_section = "\n## 📋 CONFIGURATION TEMPLATES (CRITICAL - FOLLOW EXACTLY):\n\n"
        template_section += f"**CRITICAL IMPORTANCE:** These templates show the EXACT format, syntax, and structure required for {simulator} configurations.\n"
        template_section += f"You MUST replicate this format precisely for {aircraft_name}.\n\n"

        for file_type, content in template_files.items():
            template_section += f"### Template: {file_type.upper()} File Format\n"
            template_section += f"**File Type:** {file_type} format for {simulator}\n"
            template_section += f"**Template Length:** {len(content)} characters\n"
            template_section += f"**EXACT STRUCTURE TO FOLLOW:**\n```\n{content}\n```\n\n"

        template_section += f"""
**🎯 CRITICAL TEMPLATE REQUIREMENTS:**
1. ✅ Copy the EXACT structure, nesting, and hierarchy from the template above
2. ✅ Use the SAME syntax for all entries (keys, values, brackets, semicolons)
3. ✅ Maintain the SAME sectioning (axes{{}}, buttons{{}}, triggers{{}}, etc.)
4. ✅ Follow the SAME naming conventions for controls
5. ✅ Keep the SAME formatting style (indentation, spacing, line breaks)
6. ✅ Generate a COMPLETE file with ALL sections present in the template
7. ✅ Replace control assignments with ones appropriate for {aircraft_name}
8. ✅ Ensure EVERY button/axis from the Thrustmaster HOTAS Warthog is mapped
9. ✅ Match the device naming convention exactly as shown in template
10. ✅ Preserve all structural elements like device IDs, axis ranges, button numbers

**❌ DO NOT:**
- Truncate or abbreviate any part of the configuration
- Change the file structure or format from the template
- Skip any sections that exist in the template
- Invent new syntax not shown in the template
- Alter the indentation or bracketing style
- Modify device identification patterns

**📝 GENERATION INSTRUCTIONS:**
Follow the template structure line-by-line, section-by-section. Generate the COMPLETE configuration matching the template's format exactly while adapting the control assignments for {aircraft_name}'s specific combat needs.
"""

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

    manual_excerpt_section = ""
    if simulator_manual_text:
        manual_excerpt_section = f"\nMANUAL EXCERPT:\n{simulator_manual_text}\n"

    aircraft_manual_section = ""
    if aircraft_text:
        aircraft_manual_section = f"Manual:\n{aircraft_text[:12000]}"
    else:
        aircraft_manual_section = "Use standard combat aircraft controls."

    prompt = f"""## TASK: Generate a COMPLETE COMBAT-FOCUSED controller configuration for {aircraft_name} in {simulator}.

## CONTROLLER TYPE:
{hotas_name} - {controller_type.upper().replace('_', ' ')} ({len(hotas_devices)} device{'s' if len(hotas_devices) > 1 else ''})

{template_section}

{software_section}

## RESPONSE FORMAT (3 parts):

### Part 1: Complete Technical Mapping Table
{table_format}

{mapping_instructions}
- Generate AT LEAST 30-40 comprehensive mappings
- Device ID column: ONLY the identifier (JOY_Y, JOY_BTN1, etc.)
- Cover ALL combat-critical controls
{f"- Leverage {software_name} capabilities where applicable (note in Function & Rationale column)" if software_capable else ""}

### Part 2: Installation Instructions
{"Based on official documentation:" if simulator_manual_text else "Step-by-step installation:"}
{manual_excerpt_section}- File location: {config_location}
- How to load/import profile
- Device detection & calibration
- Testing & verification
{f"- {software_name} setup steps (if applicable)" if software_capable else ""}

### Part 3: COMPLETE Configuration Files
{f"Generate {len(template_files)} COMPLETE configuration files following the template formats EXACTLY:" if template_files else f"Generate a COMPLETE {file_format.upper()} configuration file."}
{f"- File 1: .blk format (controls configuration) - FOLLOW TEMPLATE EXACTLY" if 'blk' in template_files else ""}
{f"- File 2: .fcf format (TARGET configuration) - FOLLOW TEMPLATE EXACTLY" if 'fcf' in template_files else ""}

⚠️ CRITICAL GENERATION REQUIREMENTS:
- Generate the ENTIRE files from start to finish following the template structure
- Do NOT truncate, abbreviate, or skip ANY sections
- Include ALL necessary sections, headers, footers, and structural elements
- Use the EXACT syntax and formatting from the templates
- The files MUST be immediately usable without any modifications
- Match the template length and completeness
{f"- Include {software_name} script code if beneficial for combat effectiveness" if software_capable and software_manual_text else ""}

---
## HARDWARE:
{hotas_name}
{devices_text}

## AIRCRAFT:
{aircraft_name}
{aircraft_manual_section}

---

## FINAL CRITICAL REQUIREMENTS:
1. ✅ COMPLETE table (30-40+ rows minimum)
2. ✅ Device ID column - identifier ONLY
3. ✅ Physical input - exact names from manuals
4. ✅ ACCURATE installation from manual
5. ✅ COMPLETE, UNTRUNCATED configuration files (NO ABBREVIATIONS)
6. ✅ Follow template format EXACTLY if provided
7. ✅ COMBAT-focused prioritization
8. ✅ ALL buttons and axes mapped
{f"9. ✅ Leverage {software_name} for enhanced capabilities" if software_capable else ""}

Generate the COMPLETE response now. Do not truncate, abbreviate, or skip any sections of the configuration files."""

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
    if software_manual_images:
        for img_data in software_manual_images[:3]:
            content_parts.append(
                types.Part.from_bytes(data=base64.b64decode(img_data['data']), mime_type=img_data['mime_type']))

    contents = [types.Content(role="user", parts=content_parts)]
    generate_content_config = types.GenerateContentConfig(
        temperature=0.7,
        top_p=0.95,
        max_output_tokens=30000,
    )
    try:
        controller_type_label = controller_type.replace('_', ' ').title()
        template_info = f" (using {len(template_files)} template{'s' if len(template_files) > 1 else ''})" if template_files else ""
        st.info(f" Generating {simulator} {controller_type_label} configuration for {hotas_name}{template_info}...")
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


st.subheader("⚙️ Configuration Setup")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 1️⃣ Select Flight Simulator")
    selected_simulator = st.selectbox("Choose your simulator:", options=[""] + list(SIMULATOR_CONFIGS.keys()),
                                      format_func=lambda x: "Select simulator..." if x == "" else x,
                                      help="Select your flight simulator")
    if selected_simulator:
        sim_info = SIMULATOR_CONFIGS[selected_simulator]
        manual_status = "✅ Manual Available" if sim_info.get("user_manual") and os.path.exists(
            sim_info.get("user_manual", "")) else "ℹ️ Generic Instructions"
        st.info(
            f"**File Format:** `{sim_info['file_extension']}`\n**Install Location:** `{sim_info['config_location']}`\n**Instructions:** {manual_status}")
    st.markdown("### 2️⃣ Upload Aircraft Manual")
    aircraft_pdf = st.file_uploader(" Upload Aircraft Manual (PDF)", type="pdf", key="aircraft_pdf",
                                    help="Upload aircraft flight manual with cockpit diagrams")

with col2:
    st.markdown("### 3️⃣ Select Controller Setup")
    selected_hotas = st.selectbox("Choose your controller:", options=[""] + list(HOTAS_COMPONENTS.keys()),
                                  format_func=lambda x: "Select controller..." if x == "" else x)
    if selected_hotas:
        hotas_info = HOTAS_COMPONENTS[selected_hotas]
        controller_type = hotas_info.get('type', 'multi_device')
        software_capable = hotas_info.get('software_capable', False)
        software_name = hotas_info.get('software_name', '')
        type_icons = {'unified': '', 'multi_device': '️+️', 'joystick_only': '️', 'gamepad': ''}
        type_labels = {'unified': 'Unified Device', 'multi_device': 'Multi-Device Setup',
                       'joystick_only': 'Single Joystick', 'gamepad': 'Gamepad'}
        software_info = f"\n**Software:** {software_name} (Advanced scripting supported)" if software_capable else ""

        template_info = ""
        if selected_simulator and selected_simulator in SIMULATOR_CONFIGS:
            sim_config = SIMULATOR_CONFIGS[selected_simulator]
            if 'template_files' in sim_config and selected_hotas in sim_config['template_files']:
                template_count = len(sim_config['template_files'][selected_hotas])
                template_info = f"\n**📋 Templates:** {template_count} configuration template{'s' if template_count > 1 else ''} available"

        st.info(
            f"**Type:** {type_icons.get(controller_type, '')} {type_labels.get(controller_type, 'Unknown')}\n**Components:** {', '.join(hotas_info['components'])}\n**Description:** {hotas_info['description']}{software_info}{template_info}")

st.markdown("---")

software_manual_text = None
software_manual_images = []

if selected_hotas:
    hotas_info = HOTAS_COMPONENTS[selected_hotas]
    software_capable = hotas_info.get('software_capable', False)
    software_name = hotas_info.get('software_name', '')

    if software_capable:
        st.markdown(f"### 4️⃣ Upload Software Manual (Optional - {software_name})")
        st.caption(f"Upload {software_name} manual for advanced scripting and programming capabilities")

        software_pdf = st.file_uploader(
            f" Upload {software_name} Manual (PDF)",
            type="pdf",
            key="software_pdf",
            help=f"Upload the {software_name} manual to enable advanced configuration features like macros, conditional logic, and multi-stage buttons"
        )

        if software_pdf:
            with st.spinner(f"Extracting {software_name} manual..."):
                software_manual_text, software_manual_images = extract_pdf_content(software_pdf)
                if software_manual_text:
                    st.success(
                        f"✅ Extracted {software_name} manual: {len(software_manual_text)} characters, {len(software_manual_images)} images")

        st.markdown("---")

    st.markdown(f"### {'5️⃣' if software_capable else '4️⃣'} Upload Controller Manuals (Optional)")
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

if st.button(" GENERATE PROFILE", type="primary", use_container_width=True,
             disabled=not (selected_simulator and selected_hotas and aircraft_pdf)):
    if not selected_simulator or not selected_hotas or not aircraft_pdf:
        st.warning("⚠️ Please select simulator, controller, and upload aircraft manual.")
    else:
        with st.spinner(" Analyzing documents and generating configuration..."):
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
            hotas_info = HOTAS_COMPONENTS[selected_hotas]
            software_capable = hotas_info.get('software_capable', False)
            software_name = hotas_info.get('software_name', '')
            full_response = generate_adaptive_config(aircraft_text, aircraft_images, controller_manuals,
                                                     software_manual_text, software_manual_images, selected_hotas,
                                                     hotas_devices, aircraft_name, selected_simulator, controller_type,
                                                     software_capable, software_name)

            if full_response:
                st.session_state.generated_response = full_response
                st.session_state.sim_info = sim_info
                st.session_state.aircraft_name = aircraft_name
                st.session_state.selected_hotas = selected_hotas
                st.session_state.selected_simulator = selected_simulator
                st.session_state.controller_type = controller_type
                st.session_state.software_capable = software_capable
                st.session_state.software_name = software_name
                st.session_state.software_manual_text = software_manual_text
                st.session_state.hotas_devices = hotas_devices
            else:
                st.error("❌ Failed to generate configuration.")

if 'generated_response' in st.session_state:
    full_response = st.session_state.generated_response
    sim_info = st.session_state.sim_info
    aircraft_name = st.session_state.aircraft_name
    selected_hotas = st.session_state.selected_hotas
    controller_type = st.session_state.controller_type
    software_capable = st.session_state.software_capable
    software_name = st.session_state.software_name
    software_manual_text = st.session_state.software_manual_text
    hotas_devices = st.session_state.hotas_devices

    st.success("✅ Profile generated successfully!")

    # Debug: Show response length
    st.info(f"📊 Generated response: {len(full_response)} characters")

    # Try multiple regex patterns for code blocks
    code_blocks = []

    # Pattern 1: Standard triple backticks with optional language
    pattern1 = re.finditer(r"```(\w+)?\s*\n(.*?)\n```", full_response, re.DOTALL)
    code_blocks.extend(list(pattern1))

    # Pattern 2: Code blocks without language specifier
    if not code_blocks:
        pattern2 = re.finditer(r"```\s*\n(.*?)\n```", full_response, re.DOTALL)
        for match in pattern2:
            code_blocks.append(match)

    sections = full_response.split("###")
    displayed_sections = set()

    type_labels = {'unified': 'Unified Device', 'multi_device': 'Multi-Device Setup',
                   'joystick_only': 'Single Joystick', 'gamepad': 'Gamepad'}

    st.markdown("---")

    # Display mapping table
    for section in sections:
        if "mapping" in section.lower() and "|" in section and "mapping_table" not in displayed_sections:
            st.subheader(f"✈️ {aircraft_name} - {selected_hotas}")
            caption_text = f"{type_labels.get(controller_type, 'Controller')} Configuration for {st.session_state.get('selected_simulator', 'Flight Simulator')}"
            if software_capable and software_manual_text:
                caption_text += f" | Enhanced with {software_name}"
            st.caption(caption_text)
            st.markdown("###" + section)
            displayed_sections.add("mapping_table")
            break

    st.markdown("---")

    # Display installation instructions
    for section in sections:
        if "installation" in section.lower() and "installation_instructions" not in displayed_sections:
            st.subheader("📋 Installation Instructions")
            st.markdown("###" + section)
            displayed_sections.add("installation_instructions")
            break

    st.markdown("---")

    # Display configuration files
    st.subheader(f"⚙️ {st.session_state.get('selected_simulator', 'Flight Simulator')} Configuration File(s)")
    caption_text = "Ready to use - just download and install!"
    if software_capable and software_manual_text:
        caption_text += f" | Includes {software_name} optimizations"
    st.caption(caption_text)

    # Debug: Show what we found
    st.info(f"🔍 Found {len(code_blocks)} code block(s)")

    if code_blocks:
        for idx, match in enumerate(code_blocks):
            # Handle different match patterns
            if match.lastindex == 2:  # Pattern with language
                lang = match.group(1) or sim_info['file_format']
                code = match.group(2).strip()
            else:  # Pattern without language
                lang = sim_info['file_format']
                code = match.group(1).strip()

            file_ext = sim_info['file_extension']
            file_suffix = ""
            file_type_name = file_ext

            if st.session_state.get(
                    'selected_simulator') == "War Thunder" and selected_hotas == "Thrustmaster HOTAS Warthog":
                if idx == 0:
                    file_ext = ".blk"
                    file_suffix = "_controls"
                    file_type_name = "BLK Controls"
                elif idx == 1:
                    file_ext = ".fcf"
                    file_suffix = "_target"
                    file_type_name = "FCF TARGET"

            with st.expander(f"⚙️ Configuration File #{idx + 1}: {file_type_name} ({len(code)} chars)", expanded=True):
                st.code(code, language=lang)
                filename = f"{aircraft_name.replace('/', '-')}_{selected_hotas.replace(' ', '_')}_profile{file_suffix}{file_ext}"
                st.download_button(
                    f"📥 Download {file_type_name} File",
                    data=code,
                    file_name=filename,
                    mime="text/plain",
                    key=f"dl_btn_{idx}",
                    use_container_width=True
                )
    else:
        # No code blocks found - show raw response in expandable section
        st.warning("⚠️ No code blocks detected in response. Showing full output:")
        with st.expander("📄 Full AI Response", expanded=True):
            st.code(full_response, language="text")

        # Allow downloading the raw response
        st.download_button(
            "📥 Download Full Response",
            data=full_response,
            file_name=f"{aircraft_name.replace('/', '-')}_{selected_hotas.replace(' ', '_')}_full_response.txt",
            mime="text/plain",
            key="dl_raw_response"
        )

    st.markdown("---")
    device_list = ', '.join(hotas_devices.keys())
    device_msg = f"Connect your {selected_hotas}" if controller_type == "unified" else f"Connect all devices: {device_list}"
    software_msg = f"\n8. 🔧 Configure {software_name} (if applicable)" if software_capable and software_manual_text else ""
    st.success(f"""
### ✅ Profile Generated Successfully!

**Your {type_labels.get(controller_type, 'controller')} profile is ready!**

**Next Steps:**
1. ✅ Download the configuration file(s) above
2. 📁 Place in: `{sim_info['config_location']}`
3. 🔌 {device_msg}
4. 🚀 Launch {st.session_state.get('selected_simulator', 'your flight simulator')}
5. ⚙️ Follow the installation instructions above
6. 🎮 Verify device detection and calibrate axes
7. ✈️ Take to the skies!{software_msg}

**Important:** Ensure all physical devices are connected BEFORE loading the profile.
    """)