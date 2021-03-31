def mask_token(token: str) -> str:
    if not token:
        return ""
    return f"*********{token[-4:]}"
