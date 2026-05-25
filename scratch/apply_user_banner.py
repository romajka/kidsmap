import os
from PIL import Image

def fade_to_white(img, fade_width):
    width, height = img.size
    white_img = Image.new("RGB", (width, height), (255, 255, 255))
    mask = Image.new("L", (width, height), 255)
    for x in range(width):
        if x < fade_width:
            factor = int((x / fade_width) * 255)
        else:
            factor = 255
        for y in range(height):
            mask.putpixel((x, y), factor)
            
    return Image.composite(img, white_img, mask)

def process():
    user_img_path = "/home/ramin/.gemini/antigravity/brain/09119b03-5868-4e04-88ca-d2dee1a28365/media__1779697141930.png"
    if not os.path.exists(user_img_path):
        print(f"Uploaded file not found: {user_img_path}")
        return

    src_img = Image.open(user_img_path).convert("RGBA")
    
    out_dir = "/home/ramin/kidsmap/static/img/banners"
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. Desktop Banner: Scale to 1600x533 using high-quality Lanczos resampling
    scaled_desktop = src_img.resize((1600, 533), Image.Resampling.LANCZOS)
    
    # Blend onto solid #f6faf6 background canvas to remove transparency
    desktop_canvas = Image.new("RGB", (1600, 533), (246, 250, 246)) # #f6faf6 matching color
    desktop_canvas.paste(scaled_desktop, (0, 0), scaled_desktop)
    
    # Save with LOSSLESS WebP mode to preserve 100% quality (no compression artifacts)
    desktop_canvas.save(os.path.join(out_dir, "events-hero.webp"), "WEBP", lossless=True)
    print("Desktop banner processed losslessly.")
    
    # 2. Mobile Banner: 900x675 canvas for Retina/High-DPI sharp display
    mobile_canvas = Image.new("RGB", (900, 675), (255, 255, 255))
    
    # Crop from X=350 to 1024, Y=0 to 341 (focus on character group)
    cropped = src_img.crop((350, 0, 1024, 341))
    
    # Scale to height = 450. Width is 450 * (674/341) = 890.
    scaled = cropped.resize((890, 450), Image.Resampling.LANCZOS)
    
    # Blend scaled RGBA onto a white 890x450 RGB background
    white_bg = Image.new("RGB", (890, 450), (255, 255, 255))
    white_bg.paste(scaled, (0, 0), scaled)
    
    # Fade to white on the left edge (250px fade width)
    faded = fade_to_white(white_bg, 250)
    
    # Paste right-bottom aligned (X=10, Y=225)
    mobile_canvas.paste(faded, (10, 225))
    
    # Save with LOSSLESS WebP mode
    mobile_canvas.save(os.path.join(out_dir, "events-hero-mobile.webp"), "WEBP", lossless=True)
    print("Mobile banner processed losslessly.")

if __name__ == "__main__":
    process()
