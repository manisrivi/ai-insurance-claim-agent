# reset_demo_data.py: deletes ALL claims and saved agent progress (for a clean launch).
# Run:  python -m app.reset_demo_data --yes
# This cannot be undone, so it refuses to run without --yes.
import sys

from app import db

# LangGraph's checkpoint tables (created by PostgresSaver.setup())
CHECKPOINT_TABLES = ["checkpoint_writes", "checkpoint_blobs", "checkpoints"]


def main() -> None:
    if "--yes" not in sys.argv:
        print("This deletes ALL claims and agent history. Run again with --yes to confirm.")
        sys.exit(1)

    db.open_pool()
    try:
        with db.pool.connection() as conn:
            count = conn.execute("select count(*) as total from claims").fetchone()["total"]
            conn.execute("delete from claims")
            for table in CHECKPOINT_TABLES:
                exists = conn.execute("select to_regclass(%s) as t", (table,)).fetchone()["t"]
                if exists:
                    conn.execute(f"delete from {table}")
        print(f"Deleted {count} claims and all saved agent progress.")
    finally:
        db.close_pool()


if __name__ == "__main__":
    main()
