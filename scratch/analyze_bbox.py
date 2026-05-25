import os
from PIL import Image

def analyze():
    img_path = "/home/ramin/.gemini/antigravity/brain/09119b03-5868-4e04-88ca-d2dee1a28365/events_hero_scene_1779694137662.png"
    img = Image.open(img_path).convert("RGB")
    width, height = img.size
    
    # Calculate average color for each column
    cols = []
    for x in range(width):
        col_r, col_g, col_b = 0, 0, 0
        for y in range(height):
            r, g, b = img.getpixel((x, y))
            col_r += r
            col_g += g
            col_b += b
        avg_r = col_r / height
        avg_g = col_g / height
        avg_b = col_b / height
        cols.append((avg_r, avg_g, avg_b))
        
    # Find where it starts to deviate from pure white (R,G,B > 254.5)
    start_x = -1
    for x in range(width):
        r, g, b = cols[x]
        if r < 254 or g < 254 or b < 254:
            start_x = x
            break
            
    print(f"Illustration starts deviating from white at X = {start_x}")
    # Print average color of some columns
    for x in range(0, width, 50):
        print(f"Col {x:04d}: R={cols[x][0]:.1f}, G={cols[x][1]:.1f}, B={cols[x][2]:.1f}")

if __name__ == "__main__":
    analyze()
