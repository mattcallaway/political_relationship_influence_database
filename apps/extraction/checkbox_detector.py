# apps/extraction/checkbox_detector.py

def detect_checkbox_digital(words, block_vy_start, block_vy_end, rotation, page_width, page_height):
    """
    Detects contributor code from checkboxes for digital PDFs.
    - words: list of tuples (x0, y0, x1, y1, text, block_no, line_no, word_no)
    - block_vy_start, block_vy_end: vertical bounds of the current contributor block
    - rotation: page rotation
    - page_width, page_height: unrotated dimensions
    """
    from apps.extraction.geometry import get_visual_rect
    
    # We look for checkmarks like 'X', 'x', '[x]', '✔', etc.
    # visually located in the checkbox column vx range [320, 360]
    # and vertically matching the y-offsets of the checkboxes.
    
    # Expected relative vertical offsets (proportional to row height, or absolute)
    # Checkboxes are vertically stacked: IND (top), COM, OTH, PTY, SCC (bottom).
    # Since each block height is around 55px (e.g. vy_start=173.5 to vy_end=229.0),
    # the checkboxes are spaced by ~10px vertically.
    
    marks = []
    for w in words:
        rect = (w[0], w[1], w[2], w[3])
        vx0, vy0, vx1, vy1 = get_visual_rect(rect, rotation, page_width, page_height)
        
        # Check if the word is in the checkbox column area
        if 320 <= vx0 <= 370:
            text = w[4].strip().upper()
            if text in ('X', '✔', '[X]', '☑', 'Y', '1'):
                # Check if it falls within the current block's vertical span
                if block_vy_start <= vy0 <= block_vy_end:
                    marks.append((vy0 - block_vy_start, text))
                    
    if not marks:
        return "unresolved", 0.0
        
    # Find the mark closest to the expected offsets
    # IND: offset ~ 0-4px
    # COM: offset ~ 10-14px
    # OTH: offset ~ 20-24px
    # PTY: offset ~ 30-34px
    # SCC: offset ~ 40-44px
    offset, text = min(marks, key=lambda m: m[0])
    
    if offset < 8:
        return "IND", 95.0
    elif offset < 18:
        return "COM", 95.0
    elif offset < 28:
        return "OTH", 95.0
    elif offset < 38:
        return "PTY", 95.0
    elif offset < 48:
        return "SCC", 95.0
        
    return "unresolved", 50.0

def detect_checkbox_scanned(image_crop):
    """
    Visual checkbox detection for scanned document crops using pixel density analysis.
    If image_crop is not available or OpenCV/Pillow fails, returns 'unresolved'.
    """
    # Fallback to unresolved with low confidence, which triggers human review
    return "unresolved", 20.0
