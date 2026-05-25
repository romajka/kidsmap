from PIL import Image

def check():
    path = "/home/ramin/kidsmap/static/img/banners/events-hero.webp"
    img = Image.open(path).convert("RGB")
    width, height = img.size
    print(f"Desktop banner size: {width}x{height}")
    
    # Check pixels at Y=250 (middle) for different X coordinates
    for x in [0, 50, 100, 200, 300, 400, 500, 600, 700]:
        print(f"Pixel at X={x}, Y=250:", img.getpixel((x, 250)))

if __name__ == "__main__":
    check()
