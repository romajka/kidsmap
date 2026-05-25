import os
from PIL import Image

def process():
    user_img_path = "/home/ramin/.gemini/antigravity/brain/09119b03-5868-4e04-88ca-d2dee1a28365/media__1779697141930.png"
    if not os.path.exists(user_img_path):
        print(f"Uploaded file not found: {user_img_path}")
        return

    src_img = Image.open(user_img_path).convert("RGBA")
    
    out_dir = "/home/ramin/kidsmap/static/img/banners"
    os.makedirs(out_dir, exist_ok=True)
    
    # Mobile Banner: 900x300 (3:1 aspect ratio, matching desktop structure but optimized for mobile viewports)
    # Scale to 900x300 using high-quality Lanczos resampling
    scaled_mobile = src_img.resize((900, 300), Image.Resampling.LANCZOS)
    
    # Blend onto solid #f6faf6 background canvas to remove transparency and match the website's background
    mobile_canvas = Image.new("RGB", (900, 300), (246, 250, 246)) # #f6faf6 matching color
    mobile_canvas.paste(scaled_mobile, (0, 0), scaled_mobile)
    
    # Save with LOSSLESS WebP mode to preserve maximum quality
    mobile_canvas.save(os.path.join(out_dir, "events-hero-mobile.webp"), "WEBP", lossless=True)
    print("Mobile banner processed successfully as 900x300 seamless asset.")

if __name__ == "__main__":
    process()
