def parse_lat_long(point_str: str) -> tuple[float, float]:
    lat, long = point_str.split(',')
    return float(lat.replace('°', '')), float(long.replace('°', ''))
