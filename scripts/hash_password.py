"""Generate the shared password setting without putting plaintext in shell history."""
from getpass import getpass

from src.misptool.application.auth_service import PASSWORD_HASHER


def main() -> None:
    password = getpass("Shared password (15–128 characters): ")
    if not 15 <= len(password) <= 128:
        raise SystemExit("Password must contain 15–128 characters.")
    if password != getpass("Confirm password: "):
        raise SystemExit("Passwords do not match.")
    print(f"APP_PASSWORD_HASH='{PASSWORD_HASHER.hash(password)}'")


if __name__ == "__main__":
    main()
