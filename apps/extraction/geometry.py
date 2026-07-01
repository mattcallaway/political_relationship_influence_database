# apps/extraction/geometry.py

class FormGeometryProfile:
    """
    Defines coordinate layout profiles for various Form 460 Schedule A designs.
    All bounds are defined as proportions (0.0 to 1.0) of visual page width and height.
    This ensures size independence.
    """
    def __init__(self, name, date_col, name_addr_col, code_col, occ_emp_col, amount_col, cumulative_col, per_election_col):
        self.name = name
        self.date_col = date_col                # (vx_min, vx_max)
        self.name_addr_col = name_addr_col      # (vx_min, vx_max)
        self.code_col = code_col                # (vx_min, vx_max)
        self.occ_emp_col = occ_emp_col          # (vx_min, vx_max)
        self.amount_col = amount_col            # (vx_min, vx_max)
        self.cumulative_col = cumulative_col    # (vx_min, vx_max)
        self.per_election_col = per_election_col# (vx_min, vx_max)

# Profile definitions: proportion-based (0.0 to 1.0)
PROFILES = {
    "modern_netfile_schedule_a": FormGeometryProfile(
        name="modern_netfile_schedule_a",
        date_col=(0.02, 0.12),
        name_addr_col=(0.12, 0.48),
        code_col=(0.48, 0.57),
        occ_emp_col=(0.57, 0.74),
        amount_col=(0.74, 0.86),
        cumulative_col=(0.86, 1.00),
        per_election_col=(0.86, 1.00) # often shares the cumulative space in continuation
    ),
    "scanned_historical_schedule_a": FormGeometryProfile(
        name="scanned_historical_schedule_a",
        date_col=(0.02, 0.11),
        name_addr_col=(0.11, 0.46),
        code_col=(0.46, 0.55),
        occ_emp_col=(0.55, 0.73),
        amount_col=(0.73, 0.86),
        cumulative_col=(0.86, 1.00),
        per_election_col=(0.86, 1.00)
    )
}

def get_visual_rect(rect, rotation, page_width, page_height):
    """
    Transforms coordinates from PDF space to visual screen space (0, 0 is top-left).
    - rect: (x0, y0, x1, y1) in PDF space
    - rotation: page rotation (0, 90, 180, 270)
    - page_width: unrotated page width
    - page_height: unrotated page height
    """
    x0, y0, x1, y1 = rect
    if rotation == 90:
        # Visual width is page_height, visual height is page_width
        # vx = page_height - y, vy = x
        return (page_height - y1, x0, page_height - y0, x1)
    elif rotation == 180:
        return (page_width - x1, page_height - y1, page_width - x0, page_height - y0)
    elif rotation == 270:
        # vx = y, vy = page_width - x
        return (y0, page_width - x1, y1, page_width - x0)
    else:
        return (x0, y0, x1, y1)

def get_visual_width_height(rotation, page_width, page_height):
    """
    Returns visual page width and height after rotation.
    """
    if rotation in (90, 270):
        return page_height, page_width
    return page_width, page_height
