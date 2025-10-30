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
    page_title="GAMECHANGER AI - Superior Air Combat",
    page_icon="✈️",
    layout="wide",
)

st.title("✈️ GAMECHANGER AI - An Experience For Superior Air Combat")
st.markdown(
    """
    Upload your aircraft's flight manual and select your controller to generate a **combat-focused** 
    DCS World configuration with detailed technical mappings including Device IDs and Lua commands.
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


def generate_dcs_config(aircraft_text, aircraft_images, controller_manual_text, controller_type, aircraft_name):
    """Generate DCS World configuration with detailed technical mappings."""

    model = "gemini-2.0-flash-exp"

    # Build the prompt with DCS-specific requirements
    prompt = f"""## TASK: Generate a COMBAT-FOCUSED DCS World controller configuration for {aircraft_name}.

## RESPONSE FORMAT: Your response MUST have two distinct parts:

### Part 1: Enhanced Technical Mapping Table
Create a comprehensive 4-column Markdown table with this EXACT format:

| {controller_type} Input | Joystick Device ID & Action | DCS {aircraft_name} Lua Command | Function & Ergonomic Rationale |
|-------------------------|----------------------------|----------------------------------|--------------------------------|

**Table Requirements:**
- Column 1: Physical controller input (e.g., "Stick Y-Axis", "Trigger (B1)", "Top POV Hat")
- Column 2: DCS device identifiers (e.g., "JOY_Y", "JOY_BTN1", "JOY_RZ")
- Column 3: Exact DCS Lua command strings (e.g., "iCommandPlanePitch", "iCommandPlaneWeaponRelease")
- Column 4: Detailed explanation including ergonomic reasoning and any DCS-specific notes (curves, ranges, etc.)

**Priority Mappings (MUST INCLUDE):**
1. **Primary Flight Controls**: Stick axes (pitch/roll/yaw), throttle
2. **Weapons Systems**: Trigger, gun, pickle button, weapon select
3. **Sensors & Targeting**: TDC (Throttle Designator Control), sensor select hat, radar controls
4. **Combat Systems**: Countermeasures, cage/uncage, master arm
5. **Essential Flight Systems**: Gear, flaps, speed brake, trim
6. **Tactical Systems**: Autopilot disconnect, NWS (Nose Wheel Steering), IFF

### Part 2: DCS Lua Configuration Script
A complete Lua script enclosed in ```lua ... ``` that implements the mappings for DCS World.

---
## CONTROLLER SPECIFICATIONS:
{controller_type}

---
## AIRCRAFT MANUAL CONTENT:
{aircraft_text or "No text extracted from aircraft manual."}

---
"""

    if controller_manual_text:
        prompt += f"""## CONTROLLER MANUAL CONTENT:
{controller_manual_text}

---
"""

    prompt += """
## CRITICAL INSTRUCTIONS:
1. Focus on COMBAT EFFECTIVENESS - prioritize weapon employment and sensor management
2. Use EXACT DCS command names from the DCS World API (iCommand*, device.*, etc.)
3. Map the most critical functions to the most accessible controls
4. Include technical notes (axis curves, dead zones, modifiers)
5. Ensure the table is properly formatted with pipe characters and alignment
6. Add HTML line breaks (<br>) for multi-line cells if needed

Generate the response now.
"""

    # Build content parts
    content_parts = [types.Part.from_text(text=prompt)]

    # Add images if available
    if aircraft_images:
        for img_data in aircraft_images[:5]:  # Limit to 5 images for API
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
        st.info("🤖 Generating DCS World configuration... This may take a moment.")

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
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Select DCS World Aircraft")
    aircraft_options = [
        "F/A-18C Hornet",
        "F-16C Viper",
        "A-10C Warthog",
        "F-15E Strike Eagle",
        "AV-8B Harrier",
        "F-14 Tomcat",
        "AH-64D Apache",
        "Mi-24P Hind",
        "Custom Aircraft"
    ]
    selected_aircraft = st.selectbox(
        "Choose your aircraft:",
        options=aircraft_options,
        index=0
    )

    if selected_aircraft == "Custom Aircraft":
        selected_aircraft = st.text_input("Enter aircraft name:", "")

    st.subheader("2. Upload Aircraft Manual (Optional)")
    aircraft_pdf = st.file_uploader(
        "Upload flight manual for enhanced mappings (cockpit diagrams help!).",
        type="pdf",
        key="aircraft_pdf"
    )

with col2:
    st.subheader("3. Select Your Controller")
    controller_options = {
        "VelocityOne Flightstick": "Turtle Beach VelocityOne Flightstick (HOTAS-style with analog TDC, trim wheel, multiple hats)",
        "Thrustmaster T.16000M": "Thrustmaster T.16000M FCS HOTAS (Joystick + throttle with multiple axes and buttons)",
        "Logitech X56": "Logitech X56 HOTAS (Professional-grade with multiple hats, analog ministick, and RGB lighting)",
        "VKB Gladiator": "VKB Gladiator NXT (High-precision joystick with multiple hats and buttons)",
        "Xbox Controller": "Xbox Wireless Controller (Limited buttons, dual analog sticks)",
        "Generic HOTAS": "Generic HOTAS setup (Joystick + throttle with standard controls)",
    }
    selected_controller = st.selectbox(
        "Choose your game controller:",
        options=list(controller_options.keys()),
        index=0
    )
    controller_description = controller_options[selected_controller]

    st.subheader("4. Upload Controller Manual (Optional)")
    controller_pdf = st.file_uploader(
        "Upload controller manual for exact button/axis mappings.",
        type="pdf",
        key="controller_pdf"
    )

st.markdown("---")

# Options
extract_images = st.checkbox("Extract images from PDFs", value=True,
                             help="Disable if PDF is very large or causing errors")

st.markdown("---")

# --- Submit Button and Results ---
if st.button("🚀 Generate DCS Configuration", type="primary", use_container_width=True):
    if selected_aircraft:
        with st.spinner("Processing documents..."):
            # Extract PDF content
            aircraft_text = None
            aircraft_images = []
            controller_text = None

            if aircraft_pdf:
                aircraft_text, aircraft_images = extract_pdf_content(
                    aircraft_pdf,
                    max_images=10 if extract_images else 0
                )
                if aircraft_text:
                    st.success(f"✅ Extracted {len(aircraft_images)} images from aircraft manual")

            if controller_pdf:
                controller_text, _ = extract_pdf_content(
                    controller_pdf,
                    max_images=5 if extract_images else 0
                )

            # Generate configuration
            full_response = generate_dcs_config(
                aircraft_text,
                aircraft_images,
                controller_text,
                controller_description,
                selected_aircraft
            )

            if full_response:
                st.success("✅ Configuration generated!")

                # Parse response
                lua_code_match = re.search(r"```lua(.*?)```", full_response, re.DOTALL)

                if lua_code_match:
                    table_markdown = full_response[:lua_code_match.start()].strip()
                    lua_code = lua_code_match.group(1).strip()

                    # Display Enhanced Technical Mapping
                    st.subheader(f"✈️ Enhanced Technical Mapping: {selected_controller} to {selected_aircraft}")
                    st.markdown(table_markdown)

                    # Extract table for copying
                    table_match = re.search(r'\|.*?\|.*?\|.*?\|.*?\|(?:\n\|.*?\|.*?\|.*?\|.*?\|)+', table_markdown,
                                            re.DOTALL)

                    if table_match:
                        clean_table = table_match.group(0)
                        text_format = parse_markdown_table_to_text(clean_table)

                        st.markdown("#### 📋 Export Options")

                        col_a, col_b = st.columns(2)

                        with col_a:
                            st.markdown("**Markdown Table**")
                            st.text_area(
                                "Copy markdown:",
                                value=clean_table,
                                height=250,
                                key="markdown_table",
                                label_visibility="collapsed"
                            )

                        with col_b:
                            st.markdown("**Plain Text**")
                            st.text_area(
                                "Copy plain text:",
                                value=text_format,
                                height=250,
                                key="text_table",
                                label_visibility="collapsed"
                            )

                        col_c, col_d, col_e = st.columns(3)
                        with col_c:
                            st.download_button(
                                label="📥 Download Markdown",
                                data=clean_table,
                                file_name=f"{selected_controller.replace(' ', '_')}_{selected_aircraft.replace('/', '-')}_mapping.md",
                                mime="text/markdown"
                            )
                        with col_d:
                            st.download_button(
                                label="📥 Download Text",
                                data=text_format,
                                file_name=f"{selected_controller.replace(' ', '_')}_{selected_aircraft.replace('/', '-')}_mapping.txt",
                                mime="text/plain"
                            )

                    st.markdown("---")

                    # Display Lua Code
                    st.subheader("📝 DCS World Lua Configuration")
                    st.code(lua_code, language='lua')

                    st.download_button(
                        label="📥 Download Lua Config",
                        data=lua_code,
                        file_name=f"{selected_controller.replace(' ', '_')}_{selected_aircraft.replace('/', '-')}_config.lua",
                        mime="text/plain"
                    )
                else:
                    st.warning("Could not parse response format. Displaying raw output.")
                    st.markdown(full_response)
            else:
                st.error("Failed to generate configuration.")
    else:
        st.warning("Please select an aircraft to continue.")