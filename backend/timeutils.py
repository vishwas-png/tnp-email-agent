from datetime import timezone, timedelta

# Rule: store UTC in the DB, show IST to the user.
IST = timezone(timedelta(hours=5, minutes=30))


def as_utc(dt):
    # Naive datetimes are treated as UTC. SQLite drops tzinfo, so everything
    # read back from the DB is naive UTC.
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def to_ist(dt):
    if dt is None:
        return None
    return as_utc(dt).astimezone(IST)
