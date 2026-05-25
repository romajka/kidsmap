import os
from PIL import Image, ImageDraw

def create_banners():
    src_path = "/home/ramin/.gemini/antigravity/brain/09119b03-5868-4e04-88ca-d2dee1a28365/events_hero_banner_1779691841254.png"
    if not os.path.exists(src_path):
        print(f"Source file not found: {src_path}")
        return

    # Load source image
    src_img = Image.open(src_path).convert("RGBA")
    src_w, src_h = src_img.size  # Should be 1024x1024

    # Output directory
    out_dir = "/home/ramin/kidsmap/static/img/banners"
    os.makedirs(out_dir, exist_ok=True)

    # Let's generate a few options for the desktop banner:
    options = [
        ("A", 800, 800, -150),
        ("B", 700, 900, -100),
        ("C", 900, 700, -200)
    ]

    for opt_name, size, x_pos, y_pos in options:
        ill_resized = src_img.resize((size, size), Image.Resampling.LANCZOS)

        # Create 1600x500 canvas filled with white
        desktop_canvas = Image.new("RGBA", (1600, 500), (255, 255, 255, 255))
        
        # Paste the illustration
        desktop_canvas.paste(ill_resized, (x_pos, y_pos), ill_resized)

        # Blend the transition:
        mask = Image.new("L", (1600, 500), 255)
        draw = ImageDraw.Draw(mask)
        
        # From x_pos to x_pos + 200, we fade from 0 (white) to 255 (visible)
        fade_start = x_pos
        fade_end = min(1600, x_pos + 200)
        for x in range(fade_start, fade_end):
            alpha = int(255 * (x - fade_start) / (fade_end - fade_start))
            draw.line([(x, 0), (x, 500)], fill=alpha)
        # Left of fade_start is 0 (white canvas)
        draw.rectangle([0, 0, fade_start - 1, 500], fill=0)

        # Apply the mask to a white-background desktop canvas with pasted illustration
        desktop_final = Image.new("RGBA", (1600, 500), (255, 255, 255, 255))
        desktop_final.paste(desktop_canvas, (0, 0), mask)
        
        # Save as WEBP
        desktop_final.convert("RGB").save(os.path.join(out_dir, f"events-hero-opt{opt_name}.webp"), "WEBP", quality=90)
        print(f"Desktop banner Option {opt_name} created.")

    # Save Option A as the default events-hero.webp for now
    Image.open(os.path.join(out_dir, "events-hero-optA.webp")).save(os.path.join(out_dir, "events-hero.webp"))


    # ----------------------------------------------------
    # 2. Mobile Banner (900 x 675)
    # ----------------------------------------------------
    # For mobile, it's 900x675 (4:3 ratio).
    # Since it's more square-ish, we can resize the original 1024x1024 image to 675x675
    # and place it on the right side of a 900x675 canvas, blending the left side.
    mob_ill_size = 675
    mob_ill_resized = src_img.resize((mob_ill_size, mob_ill_size), Image.Resampling.LANCZOS)

    mobile_canvas = Image.new("RGBA", (900, 675), (255, 255, 255, 255))
    mob_past_x = 900 - mob_ill_size + 50  # 275
    mob_past_y = 0
    mobile_canvas.paste(mob_ill_resized, (mob_past_x, mob_past_y), mob_ill_resized)

    mob_mask = Image.new("L", (900, 675), 255)
    mob_draw = ImageDraw.Draw(mob_mask)
    
    mob_fade_start = mob_past_x
    mob_fade_end = mob_past_x + 120
    for x in range(mob_fade_start, mob_fade_end):
        alpha = int(255 * (x - mob_fade_start) / (mob_fade_end - mob_fade_start))
        mob_draw.line([(x, 0), (x, 675)], fill=alpha)
    mob_draw.rectangle([0, 0, mob_fade_start - 1, 675], fill=0)

    mobile_final = Image.new("RGBA", (900, 675), (255, 255, 255, 255))
    mobile_final.paste(mobile_canvas, (0, 0), mob_mask)

    mobile_final.convert("RGB").save(os.path.join(out_dir, "events-hero-mobile.webp"), "WEBP", quality=90)
    print("Mobile banner created.")

if __name__ == "__main__":
    create_banners()
