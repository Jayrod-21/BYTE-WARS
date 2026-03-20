"""
engine/sprites.py — Pixel art sprite definitions for BYTE Wars champions.

Each archetype has a unique SVG-based pixel art sprite designed for the
playback renderer. Sprites are defined as inline SVG strings that can be
embedded directly in the HTML playback page.

Sprite animations are handled via CSS transforms in the renderer —
the sprites themselves are static pixel art representations.

Color palettes per archetype:
- Tank: Steel blue/gray (heavy armor)
- Assassin: Dark purple/black (shadows)
- Mage: Deep blue/gold (arcane)
- Ranger: Forest green/brown (nature)
- Support: White/gold (holy/healing)
"""


def _pixel_grid(pixels: list[list[str]], scale: int = 4) -> str:
    """
    Generate an SVG from a pixel grid.

    Each entry in the grid is a hex color string or empty string for transparent.

    Args:
        pixels: 2D list of hex color strings (e.g., "#FF0000" or "" for transparent)
        scale: Size of each pixel in SVG units

    Returns:
        SVG string
    """
    height = len(pixels)
    width = max(len(row) for row in pixels) if pixels else 0
    svg_w = width * scale
    svg_h = height * scale

    rects = []
    for y, row in enumerate(pixels):
        for x, color in enumerate(row):
            if color:
                rects.append(
                    f'<rect x="{x * scale}" y="{y * scale}" '
                    f'width="{scale}" height="{scale}" fill="{color}"/>'
                )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {svg_w} {svg_h}" width="{svg_w}" height="{svg_h}">'
        f'{"".join(rects)}</svg>'
    )


# 16x16 pixel art sprites per archetype
# Each row is 16 pixels wide, using hex colors

_TANK_PIXELS = [
    ["", "", "", "", "", "#6B7B8D", "#6B7B8D", "#6B7B8D", "#6B7B8D", "#6B7B8D", "#6B7B8D", "", "", "", "", ""],
    ["", "", "", "", "#6B7B8D", "#8899AA", "#8899AA", "#8899AA", "#8899AA", "#8899AA", "#8899AA", "#6B7B8D", "", "", "", ""],
    ["", "", "", "", "#6B7B8D", "#FFFFFF", "#4488CC", "#8899AA", "#8899AA", "#4488CC", "#FFFFFF", "#6B7B8D", "", "", "", ""],
    ["", "", "", "", "#6B7B8D", "#8899AA", "#8899AA", "#CC4444", "#CC4444", "#8899AA", "#8899AA", "#6B7B8D", "", "", "", ""],
    ["", "", "", "#556677", "#556677", "#6B7B8D", "#6B7B8D", "#6B7B8D", "#6B7B8D", "#6B7B8D", "#6B7B8D", "#556677", "#556677", "", "", ""],
    ["", "", "#4488CC", "#556677", "#8899AA", "#8899AA", "#8899AA", "#8899AA", "#8899AA", "#8899AA", "#8899AA", "#8899AA", "#556677", "#4488CC", "", ""],
    ["", "", "#4488CC", "#556677", "#8899AA", "#AABBCC", "#8899AA", "#8899AA", "#8899AA", "#8899AA", "#AABBCC", "#8899AA", "#556677", "#4488CC", "", ""],
    ["", "", "", "#556677", "#8899AA", "#8899AA", "#8899AA", "#8899AA", "#8899AA", "#8899AA", "#8899AA", "#8899AA", "#556677", "", "", ""],
    ["", "", "", "#556677", "#8899AA", "#8899AA", "#8899AA", "#8899AA", "#8899AA", "#8899AA", "#8899AA", "#8899AA", "#556677", "", "", ""],
    ["", "", "", "", "#556677", "#8899AA", "#8899AA", "#556677", "#556677", "#8899AA", "#8899AA", "#556677", "", "", "", ""],
    ["", "#4488CC", "#4488CC", "", "#556677", "#8899AA", "#8899AA", "#556677", "#556677", "#8899AA", "#8899AA", "#556677", "", "#4488CC", "#4488CC", ""],
    ["", "#4488CC", "#6699CC", "#4488CC", "", "#556677", "#556677", "", "", "#556677", "#556677", "", "#4488CC", "#6699CC", "#4488CC", ""],
    ["", "", "#4488CC", "#6699CC", "#4488CC", "", "", "", "", "", "", "#4488CC", "#6699CC", "#4488CC", "", ""],
    ["", "", "", "#4488CC", "", "", "", "", "", "", "", "", "", "#4488CC", "", ""],
    ["", "", "", "", "", "", "#556677", "#556677", "#556677", "#556677", "", "", "", "", "", ""],
    ["", "", "", "", "", "#556677", "#556677", "", "", "#556677", "#556677", "", "", "", "", ""],
]

_ASSASSIN_PIXELS = [
    ["", "", "", "", "", "", "#2D1B4E", "#2D1B4E", "#2D1B4E", "#2D1B4E", "", "", "", "", "", ""],
    ["", "", "", "", "", "#2D1B4E", "#4A2D6E", "#4A2D6E", "#4A2D6E", "#4A2D6E", "#2D1B4E", "", "", "", "", ""],
    ["", "", "", "", "", "#2D1B4E", "#FF4444", "#4A2D6E", "#4A2D6E", "#FF4444", "#2D1B4E", "", "", "", "", ""],
    ["", "", "", "", "", "#2D1B4E", "#4A2D6E", "#4A2D6E", "#4A2D6E", "#4A2D6E", "#2D1B4E", "", "", "", "", ""],
    ["", "", "", "", "", "", "#2D1B4E", "#2D1B4E", "#2D1B4E", "#2D1B4E", "", "", "", "", "", ""],
    ["", "", "", "", "#1A1A2E", "#2D1B4E", "#3D2B5E", "#3D2B5E", "#3D2B5E", "#3D2B5E", "#2D1B4E", "#1A1A2E", "", "", "", ""],
    ["", "", "", "#1A1A2E", "#2D1B4E", "#3D2B5E", "#4A2D6E", "#3D2B5E", "#3D2B5E", "#4A2D6E", "#3D2B5E", "#2D1B4E", "#1A1A2E", "", "", ""],
    ["", "", "", "", "#2D1B4E", "#3D2B5E", "#3D2B5E", "#3D2B5E", "#3D2B5E", "#3D2B5E", "#3D2B5E", "#2D1B4E", "", "", "", ""],
    ["", "", "", "", "", "#2D1B4E", "#3D2B5E", "#3D2B5E", "#3D2B5E", "#3D2B5E", "#2D1B4E", "", "", "", "", ""],
    ["", "", "", "", "", "#2D1B4E", "#3D2B5E", "#2D1B4E", "#2D1B4E", "#3D2B5E", "#2D1B4E", "", "", "", "", ""],
    ["#CCCCCC", "#CCCCCC", "", "", "", "#2D1B4E", "#2D1B4E", "", "", "#2D1B4E", "#2D1B4E", "", "", "", "", ""],
    ["", "#CCCCCC", "#CCCCCC", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["", "", "#CCCCCC", "#CCCCCC", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["", "", "", "#AAAAAA", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "#2D1B4E", "#1A1A2E", "#1A1A2E", "#2D1B4E", "", "", "", "", "", ""],
    ["", "", "", "", "", "#2D1B4E", "#1A1A2E", "", "", "#1A1A2E", "#2D1B4E", "", "", "", "", ""],
]

_MAGE_PIXELS = [
    ["", "", "", "", "", "#1A237E", "#1A237E", "#1A237E", "#1A237E", "#1A237E", "#1A237E", "", "", "", "", ""],
    ["", "", "", "", "#1A237E", "#283593", "#FFD700", "#283593", "#283593", "#FFD700", "#283593", "#1A237E", "", "", "", ""],
    ["", "", "", "", "#1A237E", "#3949AB", "#FFFFFF", "#3949AB", "#3949AB", "#FFFFFF", "#3949AB", "#1A237E", "", "", "", ""],
    ["", "", "", "", "#1A237E", "#3949AB", "#3949AB", "#3949AB", "#3949AB", "#3949AB", "#3949AB", "#1A237E", "", "", "", ""],
    ["", "", "", "", "", "#1A237E", "#1A237E", "#1A237E", "#1A237E", "#1A237E", "#1A237E", "", "", "", "", ""],
    ["", "", "", "#1A237E", "#283593", "#3949AB", "#5C6BC0", "#3949AB", "#3949AB", "#5C6BC0", "#3949AB", "#283593", "#1A237E", "", "", ""],
    ["", "", "#1A237E", "#283593", "#3949AB", "#FFD700", "#5C6BC0", "#5C6BC0", "#5C6BC0", "#5C6BC0", "#FFD700", "#3949AB", "#283593", "#1A237E", "", ""],
    ["", "", "", "#1A237E", "#3949AB", "#3949AB", "#5C6BC0", "#5C6BC0", "#5C6BC0", "#5C6BC0", "#3949AB", "#3949AB", "#1A237E", "", "", ""],
    ["", "", "", "", "#1A237E", "#3949AB", "#3949AB", "#3949AB", "#3949AB", "#3949AB", "#3949AB", "#1A237E", "", "", "", ""],
    ["", "", "", "", "#1A237E", "#283593", "#283593", "#1A237E", "#1A237E", "#283593", "#283593", "#1A237E", "", "", "", ""],
    ["", "", "", "", "", "#1A237E", "#1A237E", "", "", "#1A237E", "#1A237E", "", "", "", "", ""],
    ["", "", "", "", "", "", "", "", "", "", "", "", "", "#8B4513", "", ""],
    ["", "", "", "", "", "", "", "", "", "", "", "", "#8B4513", "#FFD700", "", ""],
    ["", "", "", "", "", "", "", "", "", "", "", "#8B4513", "", "", "#FFD700", ""],
    ["", "", "", "", "", "#1A237E", "#283593", "#1A237E", "#1A237E", "#283593", "#1A237E", "", "", "", "", ""],
    ["", "", "", "", "#1A237E", "#283593", "", "", "", "", "#283593", "#1A237E", "", "", "", ""],
]

_RANGER_PIXELS = [
    ["", "", "", "", "", "#2E7D32", "#2E7D32", "#2E7D32", "#2E7D32", "#2E7D32", "#2E7D32", "", "", "", "", ""],
    ["", "", "", "", "#2E7D32", "#4CAF50", "#4CAF50", "#4CAF50", "#4CAF50", "#4CAF50", "#4CAF50", "#2E7D32", "", "", "", ""],
    ["", "", "", "", "#2E7D32", "#FFFFFF", "#388E3C", "#4CAF50", "#4CAF50", "#388E3C", "#FFFFFF", "#2E7D32", "", "", "", ""],
    ["", "", "", "", "#2E7D32", "#4CAF50", "#4CAF50", "#795548", "#795548", "#4CAF50", "#4CAF50", "#2E7D32", "", "", "", ""],
    ["", "", "", "", "", "#2E7D32", "#2E7D32", "#2E7D32", "#2E7D32", "#2E7D32", "#2E7D32", "", "", "", "", ""],
    ["", "", "", "#5D4037", "#4CAF50", "#66BB6A", "#66BB6A", "#4CAF50", "#4CAF50", "#66BB6A", "#66BB6A", "#4CAF50", "#5D4037", "", "", ""],
    ["", "", "", "#5D4037", "#4CAF50", "#66BB6A", "#81C784", "#66BB6A", "#66BB6A", "#81C784", "#66BB6A", "#4CAF50", "#5D4037", "", "", ""],
    ["", "", "", "", "#2E7D32", "#4CAF50", "#66BB6A", "#66BB6A", "#66BB6A", "#66BB6A", "#4CAF50", "#2E7D32", "", "", "", ""],
    ["", "", "", "", "#2E7D32", "#4CAF50", "#4CAF50", "#4CAF50", "#4CAF50", "#4CAF50", "#4CAF50", "#2E7D32", "", "", "", ""],
    ["", "", "", "", "#2E7D32", "#4CAF50", "#4CAF50", "#2E7D32", "#2E7D32", "#4CAF50", "#4CAF50", "#2E7D32", "", "", "", ""],
    ["", "", "", "", "", "#2E7D32", "#2E7D32", "", "", "#2E7D32", "#2E7D32", "", "", "#8B4513", "", ""],
    ["", "", "", "", "", "", "", "", "", "", "", "", "#8B4513", "#CCCCCC", "#8B4513", ""],
    ["", "", "", "", "", "", "", "", "", "", "", "#8B4513", "", "", "", "#8B4513"],
    ["", "", "", "", "", "", "", "", "", "", "#8B4513", "", "", "", "", ""],
    ["", "", "", "", "", "#2E7D32", "#5D4037", "#2E7D32", "#2E7D32", "#5D4037", "#2E7D32", "", "", "", "", ""],
    ["", "", "", "", "#2E7D32", "#5D4037", "", "", "", "", "#5D4037", "#2E7D32", "", "", "", ""],
]

_SUPPORT_PIXELS = [
    ["", "", "", "", "", "#F5F5F5", "#F5F5F5", "#FFD700", "#FFD700", "#F5F5F5", "#F5F5F5", "", "", "", "", ""],
    ["", "", "", "", "#F5F5F5", "#FFFFFF", "#FFFFFF", "#FFFFFF", "#FFFFFF", "#FFFFFF", "#FFFFFF", "#F5F5F5", "", "", "", ""],
    ["", "", "", "", "#F5F5F5", "#FFFFFF", "#4FC3F7", "#FFFFFF", "#FFFFFF", "#4FC3F7", "#FFFFFF", "#F5F5F5", "", "", "", ""],
    ["", "", "", "", "#F5F5F5", "#FFFFFF", "#FFFFFF", "#FFB6C1", "#FFB6C1", "#FFFFFF", "#FFFFFF", "#F5F5F5", "", "", "", ""],
    ["", "", "", "", "", "#F5F5F5", "#F5F5F5", "#F5F5F5", "#F5F5F5", "#F5F5F5", "#F5F5F5", "", "", "", "", ""],
    ["", "", "", "#FFD700", "#F5F5F5", "#FFFFFF", "#FFFFFF", "#F5F5F5", "#F5F5F5", "#FFFFFF", "#FFFFFF", "#F5F5F5", "#FFD700", "", "", ""],
    ["", "", "#FFD700", "#F5F5F5", "#FFFFFF", "#FFD700", "#FFFFFF", "#FFFFFF", "#FFFFFF", "#FFFFFF", "#FFD700", "#FFFFFF", "#F5F5F5", "#FFD700", "", ""],
    ["", "", "", "#F5F5F5", "#FFFFFF", "#FFFFFF", "#FFFFFF", "#FFFFFF", "#FFFFFF", "#FFFFFF", "#FFFFFF", "#FFFFFF", "#F5F5F5", "", "", ""],
    ["", "", "", "", "#F5F5F5", "#FFFFFF", "#FFFFFF", "#FFFFFF", "#FFFFFF", "#FFFFFF", "#FFFFFF", "#F5F5F5", "", "", "", ""],
    ["", "", "", "", "#F5F5F5", "#FFFFFF", "#FFFFFF", "#F5F5F5", "#F5F5F5", "#FFFFFF", "#FFFFFF", "#F5F5F5", "", "", "", ""],
    ["", "", "", "", "", "#F5F5F5", "#F5F5F5", "", "", "#F5F5F5", "#F5F5F5", "", "", "", "", ""],
    ["", "", "", "", "", "", "", "", "", "", "", "", "#FFD700", "", "", ""],
    ["", "", "", "", "", "", "", "", "", "", "", "#FFD700", "#FF4444", "#FFD700", "", ""],
    ["", "", "", "", "", "", "", "", "", "", "#FFD700", "#FF4444", "#FFD700", "", "", ""],
    ["", "", "", "", "", "#F5F5F5", "#E0E0E0", "#F5F5F5", "#F5F5F5", "#E0E0E0", "#F5F5F5", "", "", "", "", ""],
    ["", "", "", "", "#F5F5F5", "#E0E0E0", "", "", "", "", "#E0E0E0", "#F5F5F5", "", "", "", ""],
]

# Archetype → pixel grid mapping
SPRITE_GRIDS = {
    "tank": _TANK_PIXELS,
    "assassin": _ASSASSIN_PIXELS,
    "mage": _MAGE_PIXELS,
    "ranger": _RANGER_PIXELS,
    "support": _SUPPORT_PIXELS,
}


def get_sprite_svg(archetype: str, scale: int = 4) -> str:
    """
    Get the SVG sprite for an archetype.

    Args:
        archetype: One of tank, assassin, mage, ranger, support.
        scale: Pixel scale factor (default 4 = 64x64 SVG).

    Returns:
        SVG string for the archetype's pixel art sprite.
    """
    grid = SPRITE_GRIDS.get(archetype, SPRITE_GRIDS["ranger"])
    return _pixel_grid(grid, scale)


def get_all_sprites(scale: int = 4) -> dict[str, str]:
    """Get SVG sprites for all archetypes."""
    return {arch: get_sprite_svg(arch, scale) for arch in SPRITE_GRIDS}
