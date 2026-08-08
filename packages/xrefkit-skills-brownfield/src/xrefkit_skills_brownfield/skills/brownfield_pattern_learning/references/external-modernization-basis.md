<!-- xid: 9E4B7C2A6204 -->
<a id="xid-9E4B7C2A6204"></a>

# External modernization and lifecycle basis

Use this as thematic background, not as a replacement for local evidence.

- Establish the existing system and operational baseline before selecting a
  modernization path.
- Treat incremental migration, such as Strangler Fig, as an option whose
  routing, data ownership, rollback, observability, and retirement conditions
  must be evidenced.
- Learn data creation, use, retention, archive, legal hold, deletion, audit,
  recovery, and ownership as one lifecycle.
- Use explicit complexity and operability checks as evolutionary-architecture
  guardrails: states, dependencies, configuration, monitoring, recovery,
  support, and test burden must remain within the operating model.

Sources:

- https://www.ibm.com/think/insights/reimagining-brownfield-application-modernization
- https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig
- https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html
- https://docs.aws.amazon.com/wellarchitected/2023-04-10/framework/sec_data_classification_lifecycle_management.html
- https://learn.microsoft.com/en-gb/purview/data-lifecycle-management
- https://www.thoughtworks.com/content/dam/thoughtworks/documents/books/bk_building_evolutionary_architectures_second_edition_free_chapter.pdf
