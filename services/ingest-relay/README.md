# NovaSteel ingest relay

The relay validates canonical envelopes before publishing them to an Eventstream
publisher port. It keeps invalid/conflicting duplicate records in an explicit
quarantine projection and never exposes a user-facing API or curated-data path.
