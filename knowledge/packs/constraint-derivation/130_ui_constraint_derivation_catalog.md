<!-- xid: 31C5A06B7E22 -->
<a id="xid-31C5A06B7E22"></a>

# UI Constraint Derivation Catalog

## Derivation Areas

| Design element | Confirm as requirement | Decision class |
|---|---|---|
| text input | empty, max length, forbidden-char behavior | requirement |
| numeric input | out-of-range, decimal, minus, zero behavior | requirement |
| date input | past, future, invalid-date behavior | requirement |
| select or radio | unselected state and default selection | requirement |
| checkbox | behavior when all remain unchecked | requirement |
| file upload | empty, oversize, invalid format, malware result | requirement |
| correlated inputs | cross-field validation behavior | requirement |
| async submit button | repeated click, loading, back-navigation behavior | requirement |
| delete action | confirmation and post-delete navigation | requirement |
| bulk action | zero-selected and partial-failure behavior | requirement |
| download | zero-result and large-data behavior | requirement |
| return navigation | unsaved-input behavior | requirement |
| search list | zero-result content and default sort | requirement |
| paging | last-page and data-changed-during-view behavior | requirement |
| sort tie | secondary sort key definition | design |
| direct URL or transition | unauthenticated, unauthorized, deleted-target behavior | requirement |
| modal close | background-click and ESC behavior | requirement |
| real-time update | reconnect, autosave failure, multi-toast behavior | requirement or design depending on the case |

## Output Shape

- derivation basis table with `UCD-` ids
- grouped confirmation items by screen or UI element
- explicit UI design-time decisions

## Knowledge Relations

- part_of: [Constraint Derivation Framework](110_constraint_derivation_framework.md#xid-81A6C4E2B190)
