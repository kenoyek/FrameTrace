# Reference media rights

Only operators ingest references. Each entry requires a title, publisher assertion and
rights basis. A rights string records an assertion, not legal verification. Verify licenses,
consents, territory, permitted processing and removal obligations before ingesting media.
No user query is automatically used for training or catalog expansion.

scripts/make_fixtures.py creates original deterministic geometric footage with no downloaded
assets. Fixtures have no verified external watch URL. These test assets do not represent
movie/television/social-video catalog coverage. To use real content, secure permission first.

Source links must be HTTPS and manually verified by the operator. No DRM circumvention,
platform scraping, unauthorized download or original-creator claim is implemented.
Revoke an entry using the CLI; old result reads then suppress its candidates. Reindexing
revoked content cannot silently reactivate it. Production takedown auditing is future work.
