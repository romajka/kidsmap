import os
from PIL import Image

def create_banners():
    src_path = "/home/ramin/.gemini/antigravity/brain/09119b03-5868-4e04-88ca-d2dee1a28365/events_hero_scene_1779694137662.png"
    if not os.path.exists(src_path):
        print(f"Source file not found: {src_path}")
        return

    # Load source image (1024x1024)
    src_img = Image.open(src_path).convert("RGBA")
    
    out_dir = "/home/ramin/kidsmap/static/img/banners"
    os.makedirs(out_dir, exist_ok=True)

    # 1. Desktop Banner (1600 x 500)
    desktop_canvas = Image.new("RGBA", (1600, 500), (255, 255, 255, 255))
    
    # We want to fit the illustration nicely without aggressive cropping.
    # If we resize to 600x600 and place it at Y=-50, X=1000
    ill_size = 600
    desktop_ill = src_img.resize((ill_size, ill_size), Image.Resampling.LANCZOS)
    desktop_canvas.paste(desktop_ill, (1000, -50), desktop_ill)
    
    desktop_canvas.convert("RGB").save(os.path.join(out_dir, "events-hero.webp"), "WEBP", quality=92)
    print("Desktop banner created.")

    # 2. Mobile Banner (900 x 675)
    mobile_canvas = Image.new("RGBA", (900, 675), (255, 255, 255, 255))
    
    mob_ill_size = 650
    mob_ill = src_img.resize((mob_ill_size, mob_ill_size), Image.Resampling.LANCZOS)
    mobile_canvas.paste(mob_ill, (300, 25), mob_ill)
    
    mobile_canvas.convert("RGB").save(os.path.join(out_dir, "events-hero-mobile.webp"), "WEBP", quality=92)
    print("Mobile banner created.")

if __name__ == "__main__":
    create_banners()
