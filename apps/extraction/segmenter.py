# apps/extraction/segmenter.py
import re
from apps.extraction.geometry import get_visual_rect, get_visual_width_height, PROFILES

DATE_PATTERN = re.compile(r'^\d{1,2}/\d{1,2}/\d{2,4}$')

def segment_page_into_blocks(words, rotation, page_width, page_height):
    """
    Segments a Schedule A page into individual visual contributor blocks.
    Returns a list of dictionaries, each representing a block with its visual y-bounds and words.
    """
    profile = PROFILES["modern_netfile_schedule_a"]
    v_width, v_height = get_visual_width_height(rotation, page_width, page_height)
    
    # 1. Transform all words to visual coordinate space and filter out header/footer words
    visual_words = []
    subtotal_vy = v_height # Default end of contributor area
    
    for w in words:
        rect = (w[0], w[1], w[2], w[3])
        vx0, vy0, vx1, vy1 = get_visual_rect(rect, rotation, page_width, page_height)
        
        # Check if it is a subtotal or summary marker to anchor the end of the table
        text = w[4].strip()
        if (text.upper() in ("SUBTOTAL", "SUBTOTALS") or (text.upper() == "SCHEDULE" and vx0 > 400)) and vy0 > 120:
            if vy0 < subtotal_vy:
                subtotal_vy = vy0
                
        visual_words.append({
            "vx0": vx0, "vy0": vy0, "vx1": vx1, "vy1": vy1,
            "text": text,
            "original_tuple": w
        })

    # 2. Find row start dates (anchor points) in the date column
    # Date column vx range in visual space: 30 to 100 (in 792 scale)
    date_anchors = []
    for vw in visual_words:
        # Check if the word is in the date column area
        if 20 <= vw["vx0"] <= 110:
            if DATE_PATTERN.match(vw["text"]):
                # Filter out header/footer dates (e.g. statement period dates)
                # Header region is usually vy < 120, footer region is vy > 460
                if 120 <= vw["vy0"] <= subtotal_vy:
                    date_anchors.append(vw)
                    
    # Sort date anchors by vertical position
    date_anchors.sort(key=lambda x: x["vy0"])
    
    # Dedup anchors that are on the exact same vertical line (within 3px)
    unique_anchors = []
    for anchor in date_anchors:
        if not unique_anchors or abs(anchor["vy0"] - unique_anchors[-1]["vy0"]) > 5:
            unique_anchors.append(anchor)
            
    # 3. Create block slices
    blocks = []
    for i, anchor in enumerate(unique_anchors):
        vy_start = anchor["vy0"] - 2 # Add slight padding above the date
        if i + 1 < len(unique_anchors):
            vy_end = unique_anchors[i+1]["vy0"] - 2
        else:
            vy_end = subtotal_vy - 2
            
        # Collect all words belonging to this block slice
        block_words = [
            vw for vw in visual_words 
            if vy_start <= vw["vy0"] < vy_end and vw["vy0"] < subtotal_vy
        ]
        
        blocks.append({
            "block_number": i + 1,
            "vy_start": vy_start,
            "vy_end": vy_end,
            "words": block_words,
            "date_text": anchor["text"]
        })
        
    return blocks
