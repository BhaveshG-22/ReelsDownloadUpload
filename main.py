from dotenv import load_dotenv
from fastapi import FastAPI
import instaloader
import os
import glob
import shutil
import cloudinary
import cloudinary.uploader
import logging


load_dotenv()
app = FastAPI()

# cloudinary config
cloudinary.config(
    cloud_name=os.getenv("CLOUD_NAME"),
    api_key=os.getenv("CLOUD_API_KEY"),
    api_secret=os.getenv("CLOUD_API_SECRET")
)


@app.get("/download-reel/")
def download_reel(shortcode: str, custom_name: str):
    try:
        loader = instaloader.Instaloader()

        target_dir = "reel_downloads"
        loader.download_post(
            instaloader.Post.from_shortcode(loader.context, shortcode),
            target=target_dir
        )

        # Look for the latest .mp4 file inside 'reel_downloads'
        mp4_files = sorted(
            glob.glob(f"{target_dir}/**/*.mp4", recursive=True),
            key=os.path.getmtime,
            reverse=True
        )

        if not mp4_files:
            return {"status": "error", "message": "No .mp4 file found."}

        original_path = mp4_files[0]
        new_path = os.path.join(target_dir, f"{custom_name}.mp4")
        shutil.move(original_path, new_path)
        
        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload_large(
            new_path,
            resource_type="video",
            public_id=f"reels/{custom_name}",
            overwrite=True
        )
        
        clean_reel_downloads(target_dir)


        return {
            "status": "success",
            "message": f"Downloaded and uploaded as {custom_name}.mp4",
            "cloudinary_url": upload_result.get("secure_url")
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}



def clean_reel_downloads(folder: str):
    logging.info(f"Deleting in {folder}")
    for root, dirs, files in os.walk(folder):
        for file in files:
            if not file.endswith(".mp4"):
                try:
                    os.remove(os.path.join(root, file))
                except Exception as e:
                    print(f"Error deleting file {file}: {e}")
