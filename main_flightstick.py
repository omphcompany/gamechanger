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

# --- Page Setup ---
st.set_page_config(
    page_title="GAMECHANGER - AI Enabled Superior Air Performance",
    page_icon="✈️",
    layout="wide",
)

st.title("✈️ GAMECHANGER - AI Enabled Superior Air Performance")
st.markdown(
    """
    **Universal Flight Simulator Controller Mapper**

    Upload your aircraft manual and controller manual to generate **combat-focused** controller configurations 
    for ANY flight simulator - DCS World, Microsoft Flight Simulator, IL-2 Sturmovik, Falcon BMS, War Thunder, and more!

    Get detailed technical mappings with Device IDs, command strings, and ergonomic rationale.
    """
)
st.markdown("---")


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

            # Extract text
            page_text = page.get_text()
            text_content += f"\n\n--- Page {page_num + 1} ---\n\n{page_text}"

            # Extract images (with limit)
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
                            image_parts.append({
                                'mime_type': 'image/jpeg',
                                'data': img_base64
                            })
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


def generate_universal_config(aircraft_text, aircraft_images, controller_text, controller_images,
                              controller_type, aircraft_name, simulator):
    """Generate universal flight simulator configuration with detailed technical mappings."""

    model = "gemini-2.0-flash-exp"

    # Determine config format based on simulator
    config_formats = {
        "DCS World": "Lua script format with iCommand* functions",
        "Microsoft Flight Simulator 2020": "XML configuration format for MSFS 2020",
        "IL-2 Sturmovik": ".map file format with key bindings",
        "Falcon BMS": ".key file format with command assignments",
        "War Thunder": "Config.blk format with axis and button assignments",
        "X-Plane 11/12": "Joystick configuration format",
        "Elite Dangerous": "Custom bindings XML format",
        "Star Citizen": "ActionMaps XML format",
        "Auto-Detect": "appropriate format based on the aircraft manual content"
    }

    config_format = config_formats.get(simulator, "standard configuration format")

    # Build the prompt
    prompt = f"""## TASK: Generate a COMBAT-FOCUSED controller configuration for {aircraft_name} in {simulator}.

## RESPONSE FORMAT: Your response MUST have two distinct parts:

### Part 1: Enhanced Technical Mapping Table
Create a comprehensive 4-column Markdown table with this EXACT format:

| {controller_type} Input | Device ID & Action | {simulator} Command | Function & Ergonomic Rationale |
|-------------------------|--------------------|--------------------|--------------------------------|

**Table Requirements:**
- Column 1: Physical controller input (e.g., "Stick Y-Axis", "Trigger", "Top POV Hat", "Throttle Lever")
- Column 2: Device identifiers (e.g., "JOY_Y", "JOY_BTN1", "JOY_RZ", "AXIS_1")
- Column 3: Exact command strings for {simulator} (use proper syntax for the simulator)
- Column 4: Detailed explanation including:
  * Primary function in the aircraft
  * Ergonomic reasoning for the mapping
  * Combat effectiveness notes
  * Technical parameters (curves, dead zones, ranges, modifiers)
  * Any special notes for {simulator}

**Priority Mappings (MUST INCLUDE):**
1. **Primary Flight Controls**: Stick axes (pitch/roll/yaw), throttle, rudder
2. **Weapons Systems**: Trigger, gun, weapon release, weapon select, master arm
3. **Sensors & Targeting**: Radar, TDC/cursor control, sensor selection, lock-on
4. **Combat Systems**: Countermeasures (flares/chaff), ECM, defensive systems
5. **Essential Flight Systems**: Landing gear, flaps, speed brake, trim
6. **Tactical Systems**: Autopilot, flight director, tactical displays
7. **Communication**: Radio PTT, IFF, tactical comms

### Part 2: Configuration File
Generate the actual configuration file in {config_format}.
Enclose it in appropriate code block (```lua, ```xml, ```ini, or ```text).

---
## SIMULATOR TARGET:
{simulator}

## CONTROLLER SPECIFICATIONS:
{controller_type}

---
"""

    # Add aircraft manual content
    if aircraft_text:
        prompt += f"""## AIRCRAFT MANUAL CONTENT:
{aircraft_text[:15000]}  

---
"""
    else:
        prompt += f"""## AIRCRAFT INFORMATION:
No manual provided. Use your knowledge of {aircraft_name} to create appropriate mappings.

---
"""

    # Add controller manual content
    if controller_text:
        prompt += f"""## CONTROLLER MANUAL CONTENT:
{controller_text[:10000]}

---
"""

    prompt += f"""
## CRITICAL INSTRUCTIONS:
1. **Focus on COMBAT EFFECTIVENESS** - Prioritize weapon employment and sensor management
2. **Use EXACT command names** for {simulator} - research proper syntax
3. **Map critical functions to accessible controls** - most used = easiest to reach
4. **Include technical specifications** - axis curves, dead zones, sensitivity
5. **Ensure proper table formatting** - use pipe characters and alignment
6. **Add HTML line breaks** (<br>) for multi-line cells if needed
7. **Be specific to {simulator}** - use game-specific terminology and commands
8. **If aircraft manual is provided** - extract EXACT cockpit control names and locations

Generate the complete configuration now.
"""

    # Build content parts
    content_parts = [types.Part.from_text(text=prompt)]

    # Add aircraft images if available
    if aircraft_images:
        for img_data in aircraft_images[:5]:
            content_parts.append(
                types.Part.from_bytes(
                    data=base64.b64decode(img_data['data']),
                    mime_type=img_data['mime_type']
                )
            )

    # Add controller images if available
    if controller_images:
        for img_data in controller_images[:3]:
            content_parts.append(
                types.Part.from_bytes(
                    data=base64.b64decode(img_data['data']),
                    mime_type=img_data['mime_type']
                )
            )

    contents = [types.Content(role="user", parts=content_parts)]

    generate_content_config = types.GenerateContentConfig(
        temperature=0.7,
        top_p=0.95,
        max_output_tokens=8192,
    )

    try:
        st.info(f"🤖 Generating {simulator} configuration for {aircraft_name}... This may take a moment.")

        response_text = ""
        response_placeholder = st.empty()

        for chunk in client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=generate_content_config,
        ):
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
st.subheader("⚙️ Configuration Setup")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 1️⃣ Select Flight Simulator")
    simulator_options = [
        "DCS World",
        "Microsoft Flight Simulator 2020",
        "IL-2 Sturmovik",
        "Falcon BMS",
        "War Thunder",
        "X-Plane 11/12",
        "Elite Dangerous",
        "Star Citizen",
        "Auto-Detect (from manual)"
    ]
    selected_simulator = st.selectbox(
        "Choose your simulator:",
        options=simulator_options,
        index=0,
        help="Select your flight simulator to get the correct configuration format"
    )

    st.markdown("### 2️⃣ Upload Aircraft Manual")
    aircraft_pdf = st.file_uploader(
        "📄 Upload the aircraft flight manual (PDF)",
        type="pdf",
        key="aircraft_pdf",
        help="Upload your jet's manual for accurate cockpit control mapping"
    )

    aircraft_name = st.text_input(
        "Aircraft Name (optional):",
        placeholder="e.g., F/A-18C Hornet, F-16C Viper, Su-27 Flanker",
        help="Leave blank to auto-detect from manual"
    )

with col2:
    st.markdown("### 3️⃣ Select Controller")
    controller_options = {
        "VelocityOne Flightstick": "Turtle Beach VelocityOne Flightstick (HOTAS with analog TDC, trim wheel)",
        "Thrustmaster T.16000M": "Thrustmaster T.16000M FCS HOTAS (Full HOTAS setup)",
        "Logitech X56": "Logitech X56 HOTAS (Professional-grade with multiple hats)",
        "VKB Gladiator": "VKB Gladiator NXT (High-precision joystick)",
        "Thrustmaster Warthog": "Thrustmaster HOTAS Warthog (A-10C replica HOTAS)",
        "Winwing Orion": "Winwing Orion 2 HOTAS (F/A-18 replica)",
        "Xbox Controller": "Xbox Wireless Controller (Gamepad)",
        "PS5 DualSense": "PlayStation 5 DualSense Controller",
        "Custom HOTAS": "Custom HOTAS setup",
    }
    selected_controller = st.selectbox(
        "Choose your controller:",
        options=list(controller_options.keys()),
        index=0
    )
    controller_description = controller_options[selected_controller]

    st.markdown("### 4️⃣ Upload Controller Manual")
    controller_pdf = st.file_uploader(
        "📄 Upload controller manual (PDF)",
        type="pdf",
        key="controller_pdf",
        help="Upload for exact button/axis identification"
    )

st.markdown("---")

# Advanced Options
with st.expander("⚙️ Advanced Options"):
    extract_images = st.checkbox(
        "Extract images from PDFs",
        value=True,
        help="Disable if PDFs are very large or causing errors"
    )

    max_images = st.slider(
        "Maximum images to extract per manual",
        min_value=0,
        max_value=20,
        value=10,
        help="More images = better accuracy but slower processing"
    )

st.markdown("---")

# --- Generate Button ---
if st.button("🚀 GENERATE CONFIGURATION", type="primary", use_container_width=True):
    if not aircraft_pdf and not aircraft_name:
        st.warning("⚠️ Please upload an aircraft manual OR enter an aircraft name to continue.")
    else:
        with st.spinner("🔍 Analyzing manuals and generating configuration..."):
            # Extract PDF content
            aircraft_text = None
            aircraft_images = []
            controller_text = None
            controller_images = []

            if aircraft_pdf:
                aircraft_text, aircraft_images = extract_pdf_content(
                    aircraft_pdf,
                    max_images=max_images if extract_images else 0
                )
                if aircraft_text:
                    st.success(
                        f"✅ Extracted {len(aircraft_text)} characters and {len(aircraft_images)} images from aircraft manual")

            if controller_pdf:
                controller_text, controller_images = extract_pdf_content(
                    controller_pdf,
                    max_images=max_images // 2 if extract_images else 0
                )
                if controller_text:
                    st.success(f"✅ Extracted controller manual content")

            # Auto-detect aircraft name if not provided
            if not aircraft_name and aircraft_text:
                aircraft_name = "Aircraft from Manual"
            elif not aircraft_name:
                aircraft_name = "Generic Combat Aircraft"

            # Generate configuration
            full_response = generate_universal_config(
                aircraft_text,
                aircraft_images,
                controller_text,
                controller_images,
                controller_description,
                aircraft_name,
                selected_simulator
            )

            if full_response:
                st.success("✅ Configuration generated successfully!")

                # Parse response - look for any code block
                code_block_match = re.search(r"```(\w+)?\n(.*?)\n```", full_response, re.DOTALL)

                if code_block_match:
                    table_markdown = full_response[:code_block_match.start()].strip()
                    config_language = code_block_match.group(1) or "text"
                    config_code = code_block_match.group(2).strip()

                    # Display Enhanced Technical Mapping
                    st.markdown("---")
                    st.subheader(f"✈️ {aircraft_name} - {selected_controller}")
                    st.caption(f"Configuration for {selected_simulator}")
                    st.markdown(table_markdown)

                    # Extract table for copying
                    table_match = re.search(r'\|.*?\|.*?\|.*?\|.*?\|(?:\n\|.*?\|.*?\|.*?\|.*?\|)+', table_markdown,
                                            re.DOTALL)

                    if table_match:
                        clean_table = table_match.group(0)
                        text_format = parse_markdown_table_to_text(clean_table)

                        st.markdown("#### 📋 Export Mapping Table")

                        tab1, tab2 = st.tabs(["📊 Markdown", "📝 Plain Text"])

                        with tab1:
                            st.text_area(
                                "Markdown Format:",
                                value=clean_table,
                                height=250,
                                key="markdown_table"
                            )
                            st.download_button(
                                label="📥 Download Markdown Table",
                                data=clean_table,
                                file_name=f"{aircraft_name.replace('/', '-')}_{selected_simulator.replace(' ', '_')}_mapping.md",
                                mime="text/markdown"
                            )

                        with tab2:
                            st.text_area(
                                "Plain Text Format:",
                                value=text_format,
                                height=250,
                                key="text_table"
                            )
                            st.download_button(
                                label="📥 Download Text Table",
                                data=text_format,
                                file_name=f"{aircraft_name.replace('/', '-')}_{selected_simulator.replace(' ', '_')}_mapping.txt",
                                mime="text/plain"
                            )

                    st.markdown("---")

                    # Display Configuration File
                    st.subheader(f"📝 {selected_simulator} Configuration File")
                    st.code(config_code, language=config_language)

                    st.download_button(
                        label=f"📥 Download Configuration File",
                        data=config_code,
                        file_name=f"{aircraft_name.replace('/', '-')}_{selected_simulator.replace(' ', '_')}_config.{config_language}",
                        mime="text/plain"
                    )

                    # Success message with instructions
                    st.success(
                        "🎉 Configuration complete! Download the files above and import them into your simulator.")

                else:
                    st.warning("⚠️ Could not parse response format. Displaying raw output.")
                    st.markdown(full_response)
            else:
                st.error("❌ Failed to generate configuration. Please try again.")

st.markdown("---")
st.caption("💡 **Pro Tip:** Upload both aircraft AND controller manuals for the most accurate mappings!")