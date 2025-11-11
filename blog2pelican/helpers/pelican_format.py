def pelican_format_datetime(date: str) -> str:
    return ":".join(date.split(":")[0:-1])
