from __future__ import annotations

import getpass
import os
from pathlib import Path
from typing import Callable

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover - dependency is declared for runtime.
    def load_dotenv(path: Path | str) -> bool:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if not line or line.lstrip().startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())
        return True

from homologacao_ponto.models import Credential, CredentialSource


class CredentialProvider:
    def __init__(
        self,
        env_file: Path | str = ".env",
        input_func: Callable[[str], str] = input,
        password_func: Callable[[str], str] = getpass.getpass,
    ) -> None:
        self.env_file = Path(env_file)
        self.input_func = input_func
        self.password_func = password_func

    def load(self) -> Credential:
        if self.env_file.exists():
            load_dotenv(self.env_file)
        username = os.getenv("SIGRH_USERNAME")
        password = os.getenv("SIGRH_PASSWORD")
        if username and password:
            return Credential(username=username, password=password, source=CredentialSource.ENV)
        username = username or self.input_func("SIGRH username: ")
        password = password or self.password_func("SIGRH password: ")
        return Credential(
            username=username,
            password=password,
            source=CredentialSource.INTERACTIVE,
            consent_to_persist=False,
        )
