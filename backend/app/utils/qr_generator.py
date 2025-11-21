import io
import qrcode
import logging
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


def generate_qr_code_image(qr_reference: str, booking_info: dict) -> io.BytesIO:
    """
    Generate QR code image with booking information.
    
    Args:
        qr_reference: Unique QR code reference string
        booking_info: Dictionary containing booking details
        
    Returns:
        BytesIO object containing PNG image
    """
    # Create QR code with high error correction
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    
    # QR data payload - just the reference for scanning
    qr_data = qr_reference
    
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    # Create QR code image
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to RGB for adding text
    qr_img = qr_img.convert('RGB')
    
    # Create a larger image to add text below QR code
    width, height = qr_img.size
    new_height = height + 120  # Space for text
    
    final_img = Image.new('RGB', (width, new_height), 'white')
    final_img.paste(qr_img, (0, 0))
    
    # Add text information below QR code
    draw = ImageDraw.Draw(final_img)
    
    # Try to use a better font, fallback to default
    font_title = None
    font_text = None
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        font_text = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        logger.info("Successfully loaded TrueType fonts for QR code")
    except Exception as e:
        logger.warning(f"Could not load TrueType fonts, using default: {str(e)}")
        # Use default font with size parameter for Pillow 10+
        try:
            font_title = ImageFont.load_default(size=16)  # CHANGE THIS
            font_text = ImageFont.load_default(size=12)   # CHANGE THIS
        except TypeError:
            # Fallback for older Pillow versions
            font_title = ImageFont.load_default()
            font_text = ImageFont.load_default()
    
    # Add text
    y_offset = height + 10
    
    # Title
    title = "ULENDO TIKETI"
    title_bbox = draw.textbbox((0, 0), title, font=font_title)
    title_width = title_bbox[2] - title_bbox[0]
    draw.text(((width - title_width) // 2, y_offset), title, fill='black', font=font_title)
    y_offset += 25
    
    # Booking details
    details = [
        f"Booking: {booking_info.get('booking_id')}",
        f"Route: {booking_info.get('route')}",
        f"Date: {booking_info.get('departure_date')}"
    ]
    
    for detail in details:
        detail_bbox = draw.textbbox((0, 0), detail, font=font_text)
        detail_width = detail_bbox[2] - detail_bbox[0]
        draw.text(((width - detail_width) // 2, y_offset), detail, fill='black', font=font_text)
        y_offset += 18
    
    # Save to BytesIO
    img_io = io.BytesIO()
    final_img.save(img_io, 'PNG', quality=95)
    img_io.seek(0)
    
    return img_io


def parse_qr_reference(qr_data: str) -> dict:
    """
    Parse QR code reference string.
    
    Args:
        qr_data: Scanned QR code string (the reference)
        
    Returns:
        Dictionary with parsed information or error
    """
    try:
        # QR reference format: UTK-{booking_id}-{timestamp}-{random}
        if not qr_data.startswith('UTK-'):
            return {
                'valid': False,
                'error': 'Invalid QR code format'
            }
        
        parts = qr_data.split('-')
        if len(parts) < 3:
            return {
                'valid': False,
                'error': 'Invalid QR code structure'
            }
        
        return {
            'valid': True,
            'qr_reference': qr_data,
            'booking_id': int(parts[1])
        }
        
    except Exception as e:
        logger.error(f"Failed to parse QR code: {str(e)}")
        return {
            'valid': False,
            'error': f'Failed to parse QR code: {str(e)}'
        }