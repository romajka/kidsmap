import os
from PIL import Image

def generate_options():
    src_path = "/home/ramin/.gemini/antigravity/brain/09119b03-5868-4e04-88ca-d2dee1a28365/events_hero_scene_1779694137662.png"
    src_img = Image.open(src_path).convert("RGBA")
    
    out_dir = "/home/ramin/.gemini/antigravity/brain/09119b03-5868-4e04-88ca-d2dee1a28365/experiments"
    os.makedirs(out_dir, exist_ok=True)
    
    # Option A: 900x900 scaled, pasted at X=750, Y=-120
    canvas_a = Image.new("RGBA", (1600, 500), (255, 255, 255, 255))
    ill_a = src_img.resize((900, 900), Image.Resampling.LANCZOS)
    canvas_a.paste(ill_a, (750, -120), ill_a)
    canvas_a.convert("RGB").save(os.path.join(out_dir, "opt_a.webp"), "WEBP", quality=90)
    
    # Option B: 1000x1000 scaled, pasted at X=650, Y=-160
    canvas_b = Image.new("RGBA", (1600, 500), (255, 255, 255, 255))
    ill_b = src_img.resize((1000, 1000), Image.Resampling.LANCZOS)
    canvas_b.paste(ill_b, (650, -160), ill_b)
    canvas_b.convert("RGB").save(os.path.join(out_dir, "opt_b.webp"), "WEBP", quality=90)

    # Option C: 800x800 scaled, pasted at X=850, Y=-100
    canvas_c = Image.new("RGBA", (1600, 500), (255, 255, 255, 255))
    ill_c = src_img.resize((800, 800), Image.Resampling.LANCZOS)
    canvas_c.paste(ill_c, (850, -100), ill_c)
    canvas_c.convert("RGB").save(os.path.join(out_dir, "opt_c.webp"), "WEBP", quality=90)
    
    print("Options generated successfully.")

if __name__ == "__main__":
    generate_options()
