# Canonical Rule Registry

V30.1 uses a canonical registry envelope with `rulebook_id`, `version` and `rules[]`.

The beta2 rulebook remains archived and unchanged. Its heterogeneous legacy sections must be migrated section-by-section with explicit mapping and review; do not wrap or relabel the legacy file as a validated V30.1 registry.

See `registry.py` for structural validation, dependency ordering, conservative conflict detection, dependency-aware loading and SHA-256 audit hash.

Structural validity does not establish standard compliance. Evidence status must be independently reviewed.
