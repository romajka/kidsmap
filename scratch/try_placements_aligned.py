import os
from PIL import Image

def generate_options():
    src_path = "/home/ramin/.gemini/antigravity/brain/09119b03-5868-4e04-88ca-d2dee1a28365/events_hero_scene_1779694137662.png"
    src_img = Image.open(src_path).convert("RGBA")
    
    out_dir = "/home/ramin/.gemini/antigravity/brain/09119b03-5868-4e04-88ca-d2dee1a28365/experiments_aligned"
    os.makedirs(out_dir, exist_ok=True)
    
    # Canvas is 1600x500
    # Option D: W=800, X=800, Y=-50
    canvas_d = Image.new("RGBA", (1600, 500), (255, 255, 255, 255))
    ill_d = src_img.resize((800, 800), Image.Resampling.LANCZOS)
    canvas_d.paste(ill_d, (800, -50), ill_d)
    canvas_d.convert("RGB").save(os.path.join(out_dir, "opt_d.webp"), "WEBP", quality=90)
    
    # Option E: W=850, X=750, Y=-80
    canvas_e = Image.new("RGBA", (1600, 500), (255, 255, 255, 255))
    ill_e = src_img.resize((850, 850), Image.Resampling.LANCZOS)
    canvas_e.paste(ill_e, (750, -80), ill_e)
    canvas_e.convert("RGB").save(os.path.join(out_dir, "opt_e.webp"), "WEBP", quality=90)

    # Option F: W=900, X=700, Y=-110
    canvas_f = Image.new("RGBA", (1600, 500), (255, 255, 255, 255))
    ill_f = src_img.resize((900, 900), Image.Resampling.LANCZOS)
    canvas_f.paste(ill_f, (700, -110), ill_f)
    canvas_f.convert("RGB").save(os.path.join(out_dir, "opt_f.webp"), "WEBP", quality=90)

    # Option G: W=950, X=650, Y=-140
    canvas_g = Image.new("RGBA", (1600, 500), (255, 255, 255, 255))
    ill_g = src_img.resize((950, 950), Image.Resampling.LANCZOS)
    canvas_g.paste(ill_g, (650, -140), ill_g)
    canvas_g.convert("RGB").save(os.path.join(out_dir, "opt_g.webp"), "WEBP", quality=90)
    
    print("Options D, E, F, G generated successfully.")

if __name__ == "__main__":
    generate_options()
