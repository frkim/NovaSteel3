# Lakehouse data contracts

The zone manifests define v1 tables, grains, primary keys, and idempotency
keys. Bronze is immutable source preservation; quarantine retains failures;
silver canonicalizes data; gold supplies stable Direct Lake and BFF projections.

The Fabric workstream owns physical Delta DDL generated from these manifests.
