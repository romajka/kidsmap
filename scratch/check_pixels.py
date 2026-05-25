from PIL import Image

def check():
    path = "/home/ramin/kidsmap/static/img/banners/events-hero-mobile.webp"
    img = Image.open(path).convert("RGB")
    width, height = img.size
    print(f"Image size: {width}x{height}")
    
    # Check some pixels on the far right (e.g. X = 850, Y = 300)
    # Check pixels on the far left (e.g. X = 50, Y = 300)
    print("Left-side pixels (X=50, Y=300):", img.getpixel((50, 300)))
    print("Right-side pixels (X=850, Y=300):", img.getpixel((850, 300)))
    print("Far-right bottom pixels (X=850, Y=600):", img.getpixel((850, 600)))

if __name__ == "__main__":
    check()
