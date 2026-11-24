
import streamlit as st
from openai import OpenAI
from PIL import Image, ImageOps
from io import BytesIO
from pathlib import Path
import base64
import zipfile
import os
import hmac

# ==========================================
# SETTINGS
# ==========================================

MODEL = "gpt-image-2.6-sunburst"
QUALITY = "high"
MAX_IMAGES = 30
MAX_WIDTH = 1600
JPEG_QUALITY = 93

st.set_page_config(
    page_title="Car Photo Enhancer",
    page_icon="🚘",
    layout="wide"
)

# ==========================================
# WEBSITE STYLING
# ==========================================

st.markdown("""
<style>
    .stApp {
        background-color: #111318;
        color: white;
    }

    h1, h2, h3 {
        color: #e5bd80 !important;
    }

    .stButton > button {
        background-color: #e5bd80;
        color: #111318;
        border: none;
        border-radius: 8px;
        font-weight: bold;
        min-height: 48px;
        width: 100%;
    }

    .stDownloadButton > button {
        border: 1px solid #e5bd80;
        border-radius: 8px;
        width: 100%;
    }

    [data-testid="stFileUploaderDropzone"] {
        border: 2px dashed #b99a68;
        border-radius: 12px;
        padding: 30px;
    }

    .block-container {
        max-width: 1100px;
        padding-top: 3rem;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# SECURE SETTINGS
# ==========================================

def get_setting(name, default=None):
    try:
        return st.secrets[name]
    except (KeyError, FileNotFoundError):
        return os.getenv(name, default)


API_KEY = get_setting("OPENAI_API_KEY")
APP_PASSWORD = get_setting("APP_PASSWORD")

# ==========================================
# PASSWORD PROTECTION
# ==========================================

if not APP_PASSWORD:
    st.error("Application password is not configured.")
    st.stop()

if not st.session_state.get("authenticated", False):

    st.title("🚘 Car Photo Enhancer")
    st.caption("Professional automotive photography")

    password = st.text_input(
        "Enter access password",
        type="password"
    )

    if st.button("Login"):

        if hmac.compare_digest(password, APP_PASSWORD):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password.")

    st.stop()


if not API_KEY:
    st.error("OpenAI API key is not configured.")
    st.stop()

client = OpenAI(
    api_key=API_KEY,
    timeout=300.0
)

# ==========================================
# AI ENHANCEMENT PROMPT
# ==========================================



PROMPT = """
Act as an expert automotive photographer and
professional commercial photo retoucher specialising
in premium car dealership website photography.

Transform this original photograph into a clean,
attractive, professionally presented vehicle listing.

The result must look like a real car photographed
after professional detailing in a premium showroom.

WINDSCREEN AND WINDOWS - HIGH PRIORITY:
Reduce distracting glare, cloudy reflections,
fingerprints, temporary dust, water spots and
cleaning streaks on all glass surfaces.

Make the windscreen and side windows appear
naturally clean, clear and professionally presented.

Preserve the original window tint, glass colour,
stickers, interior visibility and realistic reflections.

Do not remove actual cracks, chips or permanent
glass damage. Do not make the windows artificially
black or completely transparent.

VEHICLE BODYWORK:
Enhance the original paint colour and metallic finish.
Maintain rich, vibrant and natural colours.

Reduce distracting roller-door reflections and
harsh concentrated light spots.

Retain soft, attractive reflections that highlight
the natural curves and contours of the vehicle.

Do not make the paint excessively shiny, dull,
matte, plastic or artificially smooth.

WHEELS AND TYRES:
Improve the clarity and presentation of the
original alloy wheels and tyres.

Maintain a natural clean tyre finish without
excessive wet-looking tyre shine.

Preserve the original wheel design and condition.

HEADLIGHTS AND CHROME:
Improve clarity and photographic definition.
Enhance natural highlights on chrome and trim.
Preserve the original design and physical condition.
Do not artificially switch on the headlights.

PROFESSIONAL LIGHTING:
Use bright, soft, balanced showroom lighting.

Illuminate the front, sides and roof of the vehicle
evenly, avoiding harsh highlights and dark areas.

Add a very subtle warm golden accent along the
bottom edges of the roller-door background.

Keep the overall lighting predominantly neutral.
Avoid excessive yellow, orange or golden tones.

BACKGROUND:
Retain the original industrial roller-door background.
Improve its cleanliness, contrast and visual balance.

Make the background slightly less distracting
without making it excessively dark.

Do not replace the background or add decorations,
visible LED strips or unnecessary objects.

FLOOR AND SHADOWS:
Retain realistic concrete floor texture.

Create subtle, elegant reflections underneath
the tyres, wheels and lower vehicle body.

Maintain soft directional shadows that naturally
ground the vehicle and provide realistic depth.

Avoid a mirror-like or excessively wet-looking floor.

IMAGE QUALITY:
Improve exposure, white balance, dynamic range,
sharpness, clarity and natural colour vibrancy.

Ensure the entire vehicle is clearly visible,
well illuminated and visually attractive.

Avoid excessive saturation, HDR effects,
oversharpening and artificial textures.

VEHICLE ACCURACY:
Preserve the exact original vehicle, model,
body shape, dimensions, paint colour, wheels,
number plate, badges, accessories and camera angle.

Do not conceal scratches, dents, cracks,
paint damage or other permanent defects.

Do not invent, replace or modify vehicle features.

INTERIOR AND CLOSE-UP PHOTOS:
Apply professional photographic corrections,
natural lighting, improved clarity and balanced
colours without changing the actual condition.

FINAL QUALITY CHECK:
Before completing the image, ensure:

1. The windscreen looks naturally clean and clear.
2. The paint looks vibrant and naturally polished.
3. The wheels and tyres are clearly defined.
4. The vehicle is bright and evenly illuminated.
5. Floor reflections and shadows look realistic.
6. Warm lighting is subtle and not overpowering.
7. The original vehicle remains accurate.
8. The photograph does not look AI-generated.

FINAL AESTHETIC:
Premium commercial automotive photography.
Bright, clean, sophisticated, realistic and inviting.

The photograph should attract potential buyers
while accurately representing the actual vehicle.

Do not add text, watermarks or logos.
Maintain the original composition and aspect ratio.
"""

# ==========================================
# IMAGE ENHANCEMENT FUNCTION
# ==========================================

def enhance_image(image_bytes):

    with Image.open(BytesIO(image_bytes)) as original:

        image = ImageOps.exif_transpose(
            original
        ).convert("RGB")

        image.thumbnail((2048, 2048))

        width, height = image.size

        scale = 1536 / max(width, height)

        new_width = max(
            16, round(width * scale / 16) * 16
        )

        new_height = max(
            16, round(height * scale / 16) * 16
        )

        ratio = max(new_width, new_height) / min(
            new_width, new_height
        )

        size = (
            f"{new_width}x{new_height}"
            if ratio <= 3
            and new_width * new_height >= 655360
            else "auto"
        )

        buffer = BytesIO()

        image.save(
            buffer,
            format="JPEG",
            quality=95
        )

        buffer.seek(0)

    result = client.images.edit(
        model=MODEL,
        image=(
            "original.jpg",
            buffer,
            "image/jpeg"
        ),
        prompt=PROMPT,
        quality=QUALITY,
        size=size,
        n=1,
        output_format="jpeg",
        output_compression=95
    )

    enhanced_bytes = base64.b64decode(
        result.data[0].b64_json
    )

    enhanced = Image.open(
        BytesIO(enhanced_bytes)
    ).convert("RGB")

    if enhanced.width > MAX_WIDTH:

        scale = MAX_WIDTH / enhanced.width

        enhanced = enhanced.resize(
            (
                MAX_WIDTH,
                int(enhanced.height * scale)
            ),
            Image.Resampling.LANCZOS
        )

    output = BytesIO()

    enhanced.save(
        output,
        format="JPEG",
        quality=JPEG_QUALITY,
        optimize=True
    )

    return output.getvalue()


# ==========================================
# MAIN WEBSITE
# ==========================================

st.title("🚘 Car Photo Enhancer")

st.caption(
    "Transform everyday vehicle photos into "
    "premium dealership images."
)

st.divider()

uploaded_files = st.file_uploader(
    "Upload your vehicle photos",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=True
)

if "results" not in st.session_state:
    st.session_state.results = []

if uploaded_files:

    st.success(
        f"{len(uploaded_files)} photos uploaded"
    )

    if len(uploaded_files) > MAX_IMAGES:
        st.error(
            f"Maximum {MAX_IMAGES} photos per batch."
        )
        st.stop()

    # Preview uploaded images
    with st.expander("Preview uploaded photos"):

        columns = st.columns(4)

        for i, file in enumerate(uploaded_files):

            with columns[i % 4]:
                st.image(
                    file,
                    caption=file.name,
                    use_container_width=True
                )

    st.caption(
        "Enhancing photos uses OpenAI API credits."
    )

    if st.button(
        "✨ Enhance All Photos",
        type="primary"
    ):

        st.session_state.results = []

        progress = st.progress(0)
        status = st.empty()

        for i, file in enumerate(uploaded_files):

            status.info(
                f"Enhancing {i + 1} of "
                f"{len(uploaded_files)}: "
                f"{file.name}"
            )

            try:

                original_bytes = file.getvalue()

                enhanced_bytes = enhance_image(
                    original_bytes
                )

                filename = (
                    f"{i + 1:03d}_"
                    f"{Path(file.name).stem}"
                    "_enhanced.jpg"
                )

                st.session_state.results.append({
                    "filename": filename,
                    "original": original_bytes,
                    "enhanced": enhanced_bytes
                })

            except Exception as e:

                st.error(
                    f"Failed to enhance {file.name}: "
                    f"{type(e).__name__}"
                )

                # Stop if credentials or billing fail
                if getattr(e, "status_code", None) in (
                    401, 403, 429
                ):
                    st.warning(
                        "Processing stopped. "
                        "Check API access or credits."
                    )
                    break

            progress.progress(
                (i + 1) / len(uploaded_files)
            )

        status.success(
            f"{len(st.session_state.results)} "
            "photos successfully enhanced!"
        )


# ==========================================
# RESULTS AND DOWNLOADS
# ==========================================

if st.session_state.results:

    st.divider()

    st.header("Your Enhanced Photos")

    st.caption(
        "Review enhanced images against the originals "
        "before publishing vehicle listings."
    )

    # Create ZIP file
    zip_buffer = BytesIO()

    with zipfile.ZipFile(
        zip_buffer,
        "w",
        zipfile.ZIP_DEFLATED
    ) as zip_file:

        for result in st.session_state.results:

            zip_file.writestr(
                result["filename"],
                result["enhanced"]
            )

    st.download_button(
        label="📦 Download All Photos (ZIP)",
        data=zip_buffer.getvalue(),
        file_name="Enhanced_Car_Photos.zip",
        mime="application/zip"
    )

    # Individual before and after comparisons
    for i, result in enumerate(
        st.session_state.results
    ):

        st.divider()

        st.subheader(result["filename"])

        col1, col2 = st.columns(2)

        with col1:

            st.image(
                result["original"],
                caption="Original",
                use_container_width=True
            )

        with col2:

            st.image(
                result["enhanced"],
                caption="Enhanced",
                use_container_width=True
            )

        st.download_button(
            label="⬇ Download Enhanced Photo",
            data=result["enhanced"],
            file_name=result["filename"],
            mime="image/jpeg",
            key=f"download_{i}"
        )

    if st.button("Clear Results"):
        st.session_state.results = []
        st.rerun()

st.divider()

st.caption(
    "Car Photo Enhancer | "
    "Professional Automotive Photography"
)
