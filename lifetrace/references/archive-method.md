# Portable archive method

## Format and provenance

The canonical archive is UTF-8 JSON matching `schema/lifetrace-profile.schema.json`. `archive_id` is a UUID for one person's archive; `revision` is the file-level revision. Each confirmed entry has a stable UUID, a positive `version`, timestamps, and at least one source. A source records whether the account came from the subject, another person, a document, or an imported archive. Avoid claiming independent verification merely because a source exists.

Dates can be exact (`YYYY-MM-DD`) or approximate free text in `when_text`; use neither if unknown. Keep the person's own words in `content`; do not insert inferred detail. When an existing entry changes, increment `version`, retain the earlier version in `history`, and update the timestamp. The CLI currently adds new entries but does not offer an edit command; edits can be made with a JSON editor and checked with `validate`.

## Merge and deletion

Import means reading and validating an archive file. Export means providing a copy of the JSON file to the person. Validate before and after a merge. The merge tool accepts only the same `archive_id`; it combines independent entries and accepts identical shared entries. Divergent shared entries cause a conflict, even if their version numbers differ, so a person can review them explicitly. A tombstone suppresses an entry with the same ID, including one in an older export.

Deletion uses a tombstone with time, reason, and version. Delete by exact entry ID after confirming the target with the person. `delete` removes the entry's content from the new archive file, but prior exports, backup files, model context, and host logs may still contain it. Handle those copies according to the person's request and the host's real capabilities. To remove the whole archive, identify all known copies and delete them using the host's authorized file operations; do not claim that a single tombstone erases every copy.

## Privacy

Store only what the person confirms. Avoid including third-party private details when a less identifying description works. `visibility` is an advisory value (`private` or `shareable`) for drafting and export decisions, not an access-control mechanism. JSON files are plain text; the user controls where they are stored and shared. Do not upload or send them without separate authorization.
