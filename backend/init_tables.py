"""List checked-in SQL migrations in execution order."""
from pathlib import Path


def migration_files() -> list[Path]:
    return sorted(
        path
        for path in (Path(__file__).parent / "migrations").glob("*.sql")
        if "hosted_legacy" not in path.name
    )


if __name__ == "__main__":
    files = migration_files()
    if not files:
        raise SystemExit("No migrations found under backend/migrations")
    print("Apply these migrations to Supabase in order:")
    for path in files:
        print(f"- {path.name}")
    print("Hosted legacy projects use 003_hosted_legacy_compatibility.sql instead; do not mix the two paths.")
