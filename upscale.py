from PIL import Image
import sys
import os

def upscale_pixelart(input_path, output_path, scale_factor=4):
    """
    Upscale a pixel art image by an integer scale factor using nearest-neighbor scaling.
    
    :param input_path: Path to input PNG file
    :param output_path: Path to save upscaled PNG file
    :param scale_factor: How much to scale (e.g. 2, 3, 4)
    """
    # Open image
    img = Image.open(input_path)
    
    # Calculate new size
    new_size = (img.width * scale_factor, img.height * scale_factor)
    
    # Resize with NEAREST to preserve pixel edges
    upscaled = img.resize(new_size, Image.NEAREST)
    
    # Save result
    upscaled.save(output_path)
    print(f"Upscaled image saved to {output_path} (x{scale_factor})")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python upscale.py <input_file> <output_file> [scale_factor]")
        print("Example: python upscale.py assets/images/wtc.png assets/images/wtc_upscaled.png 3")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    scale = int(sys.argv[3]) if len(sys.argv) > 3 else 4

    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found")
        sys.exit(1)

    upscale_pixelart(input_file, output_file, scale)




