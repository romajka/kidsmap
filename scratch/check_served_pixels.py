import urllib.request
from PIL import Image
import io

def check():
    url = "http://127.0.0.1:8000/static/img/banners/events-hero-mobile.webp"
    try:
        response = urllib.request.urlopen(url)
        data = response.read()
        print(f"Successfully downloaded image from server. Size: {len(data)} bytes")
        img = Image.open(io.BytesIO(data)).convert("RGB")
        width, height = img.size
        print(f"Image size: {width}x{height}")
        print("Left-side pixels (X=50, Y=300):", img.getpixel((5, 300)))
        print("Right-side pixels (X=850, Y=300):", img.getpixel((850, 300)))
    except Exception as e:
        print("Error fetching image from server:", e)

if __name__ == "__main__":
    check()
