"""Video time/string helpers."""


def format_timestamp(seconds: float) -> str:
    """Format seconds as HH:MM:SS.mmm."""
    if seconds is None or seconds < 0:
        seconds = 0
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def parse_time_to_seconds(value: str | int | float) -> float:
    """Parse HH:MM:SS, MM:SS, or seconds into a float number of seconds."""
    if isinstance(value, (int, float)):
        return float(value)
    value = value.strip()
    if not value:
        return 0.0
    parts = value.split(":")
    try:
        parts_f = [float(p) for p in parts]
    except ValueError:
        return 0.0
    if len(parts_f) == 3:
        return parts_f[0] * 3600 + parts_f[1] * 60 + parts_f[2]
    if len(parts_f) == 2:
        return parts_f[0] * 60 + parts_f[1]
    return parts_f[0]
