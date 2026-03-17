import warnings


def suppress_runtime_warnings() -> None:
    warnings.filterwarnings(
        "ignore",
        message=r"urllib3 v2 only supports OpenSSL 1\.1\.1\+.*",
    )

    try:
        from urllib3.exceptions import NotOpenSSLWarning
    except Exception:
        return

    warnings.filterwarnings("ignore", category=NotOpenSSLWarning)
