import argparse

from .ditto_client import DittoClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the traffic junction twins in Eclipse Ditto")
    parser.add_argument("--url", default="http://localhost:8080")
    parser.add_argument("--user", default="ditto")
    parser.add_argument("--password", default="ditto")
    args = parser.parse_args()
    client = DittoClient(args.url, args.user, args.password)
    for junction_id in ("J1", "J2", "J3"):
        client.create_junction(junction_id)
        print(f"created traffic:{junction_id}")


if __name__ == "__main__":
    main()