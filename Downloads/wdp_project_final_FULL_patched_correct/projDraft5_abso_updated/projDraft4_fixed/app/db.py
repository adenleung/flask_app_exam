import time
from datetime import datetime, timezone


def normalize_pair(a, b):
    x = int(a)
    y = int(b)
    return (x, y) if x < y else (y, x)


def sg_today():
    return datetime.fromtimestamp(time.time() + 8 * 3600, tz=timezone.utc).strftime("%Y-%m-%d")


def sg_yesterday():
    return datetime.fromtimestamp(time.time() + 8 * 3600 - 86400, tz=timezone.utc).strftime("%Y-%m-%d")


def stage_from_streak(streak):
    s = int(streak or 0)
    if s <= 1:
        return 1
    if s <= 3:
        return 2
    if s <= 6:
        return 3
    if s <= 10:
        return 4
    if s <= 14:
        return 5
    if s <= 21:
        return 6
    return 7


def update_streak_plant(conn, sender_id, receiver_id, message_text, has_image=False):
    text = (message_text or "").strip()
    meaningful = len(text) >= 5 or bool(has_image)
    if not meaningful:
        return None

    a, b = normalize_pair(sender_id, receiver_id)
    now_ts = int(time.time())
    today = sg_today()
    yesterday = sg_yesterday()

    conn.execute(
        """
        INSERT OR IGNORE INTO pair_plants
            (user_a_id, user_b_id, streak_count, longest_streak, last_streak_date, stage, created_at, updated_at)
        VALUES
            (?, ?, 0, 0, NULL, 1, ?, ?)
        """,
        (a, b, now_ts, now_ts),
    )

    row = conn.execute(
        """
        SELECT id, streak_count, last_streak_date, longest_streak
        FROM pair_plants
        WHERE user_a_id = ? AND user_b_id = ?
        LIMIT 1
        """,
        (a, b),
    ).fetchone()
    if not row:
        return None

    last_date = (row["last_streak_date"] or "").strip()
    if last_date == today:
        return None

    if last_date == yesterday:
        streak = int(row["streak_count"] or 0) + 1
    else:
        streak = 1

    longest = max(int(row["longest_streak"] or 0), streak)
    stage = stage_from_streak(streak)

    conn.execute(
        """
        UPDATE pair_plants
           SET streak_count = ?,
               longest_streak = ?,
               last_streak_date = ?,
               stage = ?,
               updated_at = ?
         WHERE id = ?
        """,
        (streak, longest, today, stage, now_ts, int(row["id"])),
    )
    conn.commit()
    return {"streak": streak, "stage": stage, "longest": longest}
