
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
Professionally retouch this original car photograph
for a premium automotive dealership website.

The goal is to make the vehicle look attractive,
bright, clean and desirable to potential buyers,
while maintaining a completely realistic appearance.

VEHICLE PRESERVATION:
Keep the exact original vehicle, paint colour,
body shape, wheels, tyres, number plate,
accessories and camera angle.
Preserve all existing vehicle defects.

LIGHTING:
Use bright, balanced, professional showroom lighting.
Improve illumination across the entire vehicle.
Add a very subtle warm ambient glow along the
bottom edges of the background.
Avoid dark, moody or overly cinematic lighting.

PAINT AND REFLECTIONS:
Preserve the original metallic paint finish,
colour vibrancy and natural gloss.
Reduce distracting roller-door reflections
and harsh glare on the body panels only.
Do not remove all reflections.
Do not make the vehicle look matte, dull,
plastic or artificially polished.

BACKGROUND:
Retain the original industrial roller-door background.
Make it clean, neutral and visually balanced.
Do not excessively darken the background.
Avoid strong orange or yellow lighting.

FLOOR:
Retain realistic concrete texture.
Add subtle, natural reflections underneath
the tyres and wheels.
Maintain soft, realistic shadows.
Avoid an excessively glossy or wet-looking floor.

IMAGE QUALITY:
Improve brightness, exposure, sharpness,
colour vibrancy, clarity and dynamic range.
Keep the vehicle brighter and more visually
prominent than the background.

HEADLIGHTS AND WHEELS:
Enhance the clarity of existing headlights,
chrome details, alloy wheels and tyres.
Preserve their original appearance.

For interior and close-up photographs,
apply natural photographic corrections only.

FINAL RESULT:
Bright, inviting, premium automotive dealership
photography with realistic colours, natural
paint gloss and professional lighting.

The image should look like a professionally
retouched real photograph, not an AI-generated
render.

Prioritise commercial attractiveness and realism
over dramatic cinematic effects.

Do not add text, logos or watermarks.
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
