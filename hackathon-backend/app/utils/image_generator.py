"""
Image generator utility for creating seed-based placeholder images.
Generates images with solid color backgrounds based on item titles.
"""
import hashlib
import io
from typing import Tuple
from PIL import Image, ImageDraw, ImageFont


def generate_color_from_title(title: str) -> Tuple[int, int, int]:
    """
    Generate a deterministic color from a title string.
    Uses hash of the title to create consistent colors.
    
    Args:
        title: The item title
        
    Returns:
        RGB tuple (r, g, b)
    """
    # Create hash from title
    hash_obj = hashlib.md5(title.encode('utf-8'))
    hash_hex = hash_obj.hexdigest()
    
    # Extract RGB values from hash (using first 6 hex digits)
    r = int(hash_hex[0:2], 16)
    g = int(hash_hex[2:4], 16)
    b = int(hash_hex[4:6], 16)
    
    # Adjust brightness to ensure good contrast with white text
    # Make colors more vibrant by increasing saturation
    brightness = (r + g + b) / 3
    if brightness < 128:
        # Darken if too bright
        r = min(255, int(r * 0.7))
        g = min(255, int(g * 0.7))
        b = min(255, int(b * 0.7))
    else:
        # Lighten if too dark, but keep it readable
        r = min(200, int(r * 1.2))
        g = min(200, int(g * 1.2))
        b = min(200, int(b * 1.2))
    
    return (r, g, b)


def generate_item_image(
    title: str,
    width: int = 800,
    height: int = 800
) -> bytes:
    """
    Generate an image with a solid color background and centered title text.
    
    Args:
        title: The item title to display
        width: Image width in pixels
        height: Image height in pixels
        
    Returns:
        Image bytes in PNG format
    """
    # Generate color from title
    bg_color = generate_color_from_title(title)
    
    # Create image with solid color background
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Try to use a nice font, fallback to default if not available
    try:
        # Try to use a system font (works on most systems)
        font_size = min(width // len(title) if title else 60, 80)
        font_size = max(40, font_size)  # Minimum 40px
        
        # Try different font paths
        font_paths = [
            '/System/Library/Fonts/Helvetica.ttc',  # macOS
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',  # Linux
            'C:/Windows/Fonts/arial.ttf',  # Windows
        ]
        
        font = None
        for font_path in font_paths:
            try:
                font = ImageFont.truetype(font_path, font_size)
                break
            except (OSError, IOError):
                continue
        
        if font is None:
            # Fallback to default font
            font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()
    
    # Calculate text position (centered)
    # Get text bounding box
    bbox = draw.textbbox((0, 0), title, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Center the text
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # Draw text with white color and slight shadow for better visibility
    # Draw shadow first (offset by 2 pixels)
    draw.text((x + 2, y + 2), title, fill=(0, 0, 0, 128), font=font)
    # Draw main text
    draw.text((x, y), title, fill=(255, 255, 255), font=font)
    
    # Convert to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes.getvalue()


def generate_image_data_url(title: str, width: int = 800, height: int = 800) -> str:
    """
    Generate an image and return it as a data URL.
    
    Args:
        title: The item title
        width: Image width
        height: Image height
        
    Returns:
        Data URL string (data:image/png;base64,...)
    """
    import base64
    
    image_bytes = generate_item_image(title, width, height)
    base64_str = base64.b64encode(image_bytes).decode('utf-8')
    return f"data:image/png;base64,{base64_str}"


