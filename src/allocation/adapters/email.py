from typing import Any


def send_mail(*args: Any) -> None:
    print("SENDING EMAIL:", *args)
