import os
from PIL import Image

def apply_left_fade(img, fade_width):
    width, height = img.size
    # Create mask: left side fades to transparent, right side is fully opaque
    mask = Image.new("L", (width, height), 255)
    for x in range(width):
        if x < fade_width:
            alpha = int((x / fade_width) * 255)
        else:
            alpha = 255
        for y in range(height):
            mask.putpixel((x, y), alpha)
            
    # Apply mask
    r, g, b, a = img.split()
    # Multiply the original alpha channel by our fade mask
    new_alpha = Image.merge("L", [a]).point(lambda p: p)
    # Since original has no alpha (it is RGB), we just use the mask directly as alpha
    img.putalpha(mask)
    return img

def create_banners():
    src_path = "/home/ramin/.gemini/antigravity/brain/09119b03-5868-4e04-88ca-d2dee1a28365/events_banner_wide_1779694672046.png"
    if not os.path.exists(src_path):
        print(f"Source file not found: {src_path}")
        return

    # Load source image (1024x1024)
    src_img = Image.open(src_path).convert("RGBA")
    
    out_dir = "/home/ramin/kidsmap/static/img/banners"
    os.makedirs(out_dir, exist_ok=True)

    # 1. Desktop Banner (1600 x 500)
    # We want a white background canvas
    desktop_canvas = Image.new("RGBA", (1600, 500), (255, 255, 255, 255))
    
    # Crop the original image to Y=120 to 900 to remove empty borders
    cropped_desk = src_img.crop((0, 120, 1024, 900))
    
    # Scale it so it is wide and characters are big
    # Width = 950, height = 724
    scaled_desk = cropped_desk.resize((950, 724), Image.Resampling.LANCZOS)
    
    # Apply the left fade gradient to the scaled image
    faded_desk = apply_left_fade(scaled_desk, 280)
    
    # Paste it right-aligned (X = 1600 - 950 = 650)
    desktop_canvas.paste(faded_desk, (650, -110), faded_desk)
    
    # Save as webp
    desktop_canvas.convert("RGB").save(os.path.join(out_dir, "events-hero.webp"), "WEBP", quality=95)
    print("Desktop banner created.")

    # 2. Mobile Banner (900 x 675)
    mobile_canvas = Image.new("RGBA", (900, 675), (255, 255, 255, 255))
    
    # For mobile, we crop a slightly narrower section focusing on center/right
    cropped_mob = src_img.crop((150, 120, 1024, 900))
    scaled_mob = cropped_mob.resize((750, 670), Image.Resampling.LANCZOS)
    
    faded_mob = apply_left_fade(scaled_mob, 200)
    
    # Paste right-aligned (X = 900 - 750 = 150)
    mobile_canvas.paste(faded_mob, (150, 0), faded_mob)
    
    mobile_canvas.convert("RGB").save(os.path.join(out_dir, "events-hero-mobile.webp"), "WEBP", quality=95)
    print("Mobile banner created.")

if __name__ == "__main__":
    create_banners()
