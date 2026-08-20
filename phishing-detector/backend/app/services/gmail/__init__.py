def __init__(self) -> None:
    self.token_path: Path = settings.GMAIL_TOKEN_PATH
    self._oauth_flow: Flow | None = None