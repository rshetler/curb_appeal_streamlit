# Simple streamlit starter page
import streamlit as st
from PIL import Image, ExifTags
from octoai.client import Client
from octoai.clients.image_gen import Engine, ImageGenerator
#import os
from pydantic import BaseModel
from typing import Dict
from io import BytesIO
from base64 import b64decode, b64encode
import random

# Initialize the client
#OCTOAI_TOKEN = os.getenv("OCTOAI_TOKEN")
OCTOAI_TOKEN = st.secrets["octoai_token"]
client = Client(token=OCTOAI_TOKEN)

# Base model schema for SDXL requests
class SDXLRequest(BaseModel):
    prompt: str
    seed: int
    negative_prompt: str
    checkpoint: str
    loras: Dict[str, float]
    width: int
    height: int
    num_images: int
    sampler: str
    steps: int
    cfg_scale: int
    use_refiner: bool
    high_noise_frac: float
    style_preset: str
    
def random_seed():
    return random.randint(0, 10000000000)
    
base_payload = SDXLRequest(
    prompt="house with updated landscaping",
    seed=random_seed(),
    negative_prompt="Blurry photo, distortion, low-res, poor quality",
    checkpoint="octoai:crystal-clear",
    loras={"octoai:add-detail":0.5},
    width=1024,
    height=1024,
    num_images=3,
    sampler="DDIM",
    steps=30,
    cfg_scale=12,
    use_refiner=True,
    high_noise_frac=0.8,
    style_preset="base",
    init_image="<BASE64 IMAGE>",
    strength=0.45,
)

# Helper funcs for the cli
from pathlib import Path
image_path = Path("sd_images")
image_path.mkdir(exist_ok=True)

def imagen_request(image_path: str, upload,rand_seed,strength):
    
    input_img = Image.open(upload)

    try:
        # Rotate based on Exif Data
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation]=='Orientation':
                break
        exif = input_img._getexif()
        if exif[orientation] == 3:
            input_img=input_img.rotate(180, expand=True)
        elif exif[orientation] == 6:
            input_img=input_img.rotate(270, expand=True)
        elif exif[orientation] == 8:
            input_img=input_img.rotate(90, expand=True)
    except:
        # Do nothing
        print("No rotation to perform based on Exif data")
    #Display uploaded image with correct rotation
    col1.image(input_img)

    buffer = BytesIO()
    input_img.save(buffer, format="png")
    image_out_bytes = buffer.getvalue()
    image_out_b64 = b64encode(image_out_bytes)


    image_gen = ImageGenerator(token=st.secrets["octoai_token"])
    image_gen_response = image_gen.generate(
        engine = Engine.SDXL,
        prompt = base_payload.prompt,
        seed = rand_seed,
        negative_prompt = base_payload.negative_prompt,
        checkpoint = base_payload.checkpoint,
        loras = base_payload.loras,
        width = base_payload.width,
        height = base_payload.height,
        num_images = base_payload.num_images,
        sampler = base_payload.sampler,
        steps = base_payload.steps,
        cfg_scale = base_payload.cfg_scale,
        use_refiner = base_payload.use_refiner,
        high_noise_frac = base_payload.high_noise_frac,
        style_preset = base_payload.style_preset,
        init_image=image_out_b64.decode("utf8"),
        strength=strength,
    )
    images = image_gen_response.images
    #output images to list
    _images = []
    for i, image in enumerate(images):
        img_path = f"{image_path}/result{i}.jpg"
        image.to_file(img_path)
        _images.append(image.to_bytes())
    return _images

# Page Layout
st.set_page_config(layout="wide", page_title="Curb Appeal")
    
# Sidebar
st.sidebar.image('images/curb_appeal_logo.png')


# increase number images returned
num_images = st.sidebar.slider("Number of images", 1, 10, 2)
base_payload.num_images = num_images

#Set image display grid output
n = st.sidebar.number_input("Select image grid Width", 1, 5, 2)


strength = st.sidebar.slider("Creativity Slider",0.3, 0.7, 0.45,0.05)

st.markdown("""
<style>
.big-font {
    font-size:12px;
}
</style>
""", unsafe_allow_html=True)

st.sidebar.markdown('<p class="big-font">(lower: closer to original, higher: more creative the result)</p>', unsafe_allow_html=True)

# change up the prompt
#prompt = st.sidebar.text_input("Prompt", value=base_payload.prompt)
#base_payload.prompt = prompt


container1 = st.container()
col1, col2 = container1.columns(2)

container2 = st.container()
col1, col2 = container2.columns(2)

container3 = st.container()

def main():
     with container1:  
        st.write('### Curb Appeal - Powered by OctoAI')
        st.markdown('Curb Appeal, is an AI home and landscape design idea generator powered by OctoAI. Simply upload an image of your home, adjust the level of creativity in the output, and the app will generate various options for you.')
    
        my_upload = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"]) 

        st.markdown("###### :arrow_left: Adjust additional settings on the sidebar panel.") 

        generate_button = st.button("Beautify Home")

        with container2:
            if my_upload is not None:
                col1.write("### Original Image:")
                #col1.image(my_upload)
        with container3:
                if generate_button:
                        try:
                            st.spinner("Generating Image")  
                            #Randomize seed each time button is pressed
                            rand_seed = random.randint(0, 1024)
                            images = imagen_request(image_path,my_upload,rand_seed,strength)
                            col1.write("### Generated Images:")
                            #create a group based on input grid size
                            groups = []
                            for i in range(0, len(images), n):
                                groups.append(images[i:i+n])
                            
                            #Display images in grid
                            for group in groups:
                                cols = st.columns(n)
                                for i, images in enumerate(group):
                                    cols[i].image(images)
                        except:
                            st.error("Please upload a source image of your home.")
if __name__ == "__main__":
    main()