<!-- xid: 9E4B7C2A6203 -->
<a id="xid-9E4B7C2A6203"></a>

# External modernization and lifecycle basis

Use this reference as thematic background for pattern learning. Do not import
an external pattern wholesale; compare it with local evidence, current
operation, approved change intent, and decision ownership.

## Adopted themes

### Existing baseline before modernization

Legacy/brownfield modernization guidance emphasizes understanding the existing
system, dependencies, business-critical behavior, and current baseline before
selecting a modernization path. Use this to justify representative-peer
selection, structure findings, and current operational-baseline capture.

### Incremental change

Strangler Fig guidance recommends placing a controlled boundary between legacy
and new behavior and migrating incrementally when a one-shot replacement would
increase risk. Use this as an option for `adapts` or `introduces`, not as a
default architecture. Confirm routing, data ownership, rollback, observability,
and retirement conditions before proposing it.

### Data lifecycle

Data lifecycle guidance treats creation, use, retention, archive, legal hold,
and deletion as managed stages. For brownfield learning, map those stages to
local states, owners, triggers, consumers, audit, recovery, and operational
procedures before changing lifecycle behavior.

### Evolutionary architecture and fitness checks

Evolutionary architecture uses explicit fitness functions or equivalent checks
to keep architecture moving toward desired qualities. For this Skill, convert
that idea into reviewable guard questions: did concepts, states, dependencies,
configuration, support work, monitoring, recovery, or test burden increase, and
can the current operating model sustain the change?

## Sources

- IBM, [Reimagining brownfield application modernization](https://www.ibm.com/think/insights/reimagining-brownfield-application-modernization)
- Microsoft, [Strangler Fig pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig)
- AWS, [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html)
- AWS Well-Architected, [Define data lifecycle management](https://docs.aws.amazon.com/wellarchitected/2023-04-10/framework/sec_data_classification_lifecycle_management.html)
- Microsoft Purview, [Data lifecycle management](https://learn.microsoft.com/en-gb/purview/data-lifecycle-management)
- Thoughtworks, [Building Evolutionary Architectures, free chapter](https://www.thoughtworks.com/content/dam/thoughtworks/documents/books/bk_building_evolutionary_architectures_second_edition_free_chapter.pdf)
