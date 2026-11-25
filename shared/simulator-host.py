"""Print the model endpoint host used by Compose for the Harbor allowlists."""

import os
from urllib.parse import urlsplit


def main():
    endpoint = os.environ.get("FDEGYM_LLM_URL") or "https://openrouter.ai/api/v1/chat/completions"
    try:
        url = urlsplit(endpoint)
        if url.scheme not in ("http", "https") or not url.hostname or url.username is not None:
            raise ValueError
        host = url.hostname
    except ValueError:
        raise SystemExit("FDEGYM_LLM_URL must be an HTTP(S) URL without credentials") from None
    print(host)


if __name__ == "__main__":
    main()
