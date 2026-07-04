<!-- xid: D8F2A6C91B74 -->
<a id="xid-D8F2A6C91B74"></a>

# Modular Monolith with DDD API Structure Findings

## Status

- Target identity: `kgrzybek/modular-monolith-with-ddd`
- Source scope: `src/API`, `src/Modules`, `src/BuildingBlocks`, `src/Database`, and `src/CompanyName.MyMeetings.sln`
- Source snapshot: `91c8ef24b4cb6ef558c95d8267fa07d68c7059f8`
- Last verified on: 2026-07-04
- Analysis kind: `dotnet_structure`, `brownfield_api_naming`, `business_logic_api`
- Producer Skill: `source_structure_overview`
- Current status: current for the named source snapshot and source scope.

This finding is a brownfield source-structure basis for testing whether
`design_flow` can extract naming rules from an API whose public operations are
business actions rather than simple CRUD names.

## Structure Pivots

- The solution is a .NET 8 modular monolith with one ASP.NET Core API host and
  module assemblies for `Administration`, `Meetings`, `Payments`,
  `Registrations`, and `UserAccess`.
- The API host depends on each module's application/domain/infrastructure and
  integration-event assemblies. Module entry points are exposed through module
  contracts such as `IMeetingsModule`, `IPaymentsModule`,
  `IAdministrationModule`, and `IUserAccessModule`.
- API controllers are grouped by module and business area under
  `src/API/CompanyName.MyMeetings.API/Modules`.
- Application behavior is mediated through command/query objects and handlers.
  Public API methods usually instantiate `*Command` or `*Query` and dispatch it
  through the module contract.
- Domain behavior is concentrated in aggregate/domain methods and rules, not in
  controllers. Graph fan-in highlights `MemberId`, `Entity.AddDomainEvent`,
  `Entity.CheckRule`, `Meeting.AddAttendee`, `Meeting.AddComment`, and
  `MeetingGroup.JoinToGroupMember` as important structural pivots.

## Business API Surface

The API surface contains business actions and business state transitions:

- Meetings: create/edit/cancel meetings, add/remove attendees, add not-attendee
  decisions, sign up/sign off waitlist members, set host/attendee roles, add or
  edit comments, add comment likes, and configure meeting commenting.
- Meeting groups and proposals: propose meeting groups, create/edit groups,
  join/leave groups, request verification, and accept proposals.
- Payments and subscriptions: buy subscriptions, renew subscriptions, register
  subscription payments, create meeting fee payments, mark meeting fee payments
  as paid, create/change/activate/deactivate price list items, and get payer
  state.
- User access and registrations: register new users, confirm registration,
  authenticate, get authenticated users, get permissions, and manage email
  confirmation flow.

This means naming extraction should look at verb + business object + lifecycle
suffix combinations, not only noun entity names.

## Brownfield API Naming Extractor

Deterministic naming profile over `src` excluding tests reported:

- C# type, interface, method, property, and parameter names are consistently
  PascalCase or camelCase in the expected declaration positions.
- Interfaces use `I` prefix at 100 percent in the extracted interface set.
- Private fields predominantly use `_camelCase`.
- Top type suffixes include `Handler`, `Command`, `Event`, `Module`, `Rule`,
  and `Dto`.

### Naming Evidence Surfaces

- API route segments and controller actions provide external operation names.
- Request DTOs provide input contract names.
- Permission constants and `HasPermission` attributes provide authorization
  names tied to endpoint behavior.
- Commands, queries, handlers, validators, jobs, integration events, inbox,
  outbox, tables, schemas, and configuration bindings provide data-flow and
  runtime-binding names.

### Local Naming Vocabularies

Useful API and application naming patterns:

- API request DTOs use business-action names ending in `Request`, for example
  `BuySubscriptionRequest`, `RenewSubscriptionRequest`,
  `RegisterSubscriptionPaymentRequest`, `CreateMeetingRequest`,
  `ChangeMeetingMainAttributesRequest`, `ProposeMeetingGroupRequest`, and
  `RegisterMeetingFeePaymentRequest`.
- Application commands use verb/action + business object + `Command`, for
  example `AcceptMeetingGroupProposalCommand`, `SignUpMemberToWaitlistCommand`,
  `ChangeNotAttendeeDecisionCommand`, `SetMeetingHostRoleCommand`,
  `BuySubscriptionRenewalCommand`, `MarkSubscriptionPaymentAsPaidCommand`, and
  `MarkMeetingFeePaymentAsPaidCommand`.
- Queries use `Get` or `GetAll` + business object + `Query`, with result DTO
  suffixes such as `MeetingDetailsDto`, `MeetingGroupProposalDto`,
  `SubscriptionDetailsDto`, and `PayerDto`.
- Long names are accepted when they preserve the business distinction, for
  example `MeetingCommentingConfiguration`,
  `RequestMeetingGroupProposalVerification`, and
  `ChangeSubscriptionExpirationDateForMember`.
- Permission constants mirror business actions and are attached to endpoints by
  `HasPermission`, so API naming must stay aligned with authorization naming.

### Candidate-Name Construction Rules

For brownfield design, candidate names should be proposed by matching the
existing action vocabulary (`Create`, `Change`, `Edit`, `Accept`, `Reject`,
`Buy`, `Renew`, `Register`, `Mark`, `Expire`, `SignUp`, `SignOff`, `Set`,
`Enable`, `Disable`) with the existing domain object vocabulary
(`Meeting`, `MeetingGroup`, `MeetingGroupProposal`, `MeetingComment`,
`MeetingFee`, `Subscription`, `SubscriptionPayment`, `Payer`,
`PriceListItem`, `UserRegistration`) and the local suffix role
(`Request`, `Command`, `Query`, `Handler`, `Dto`, `Rule`, `Event`).

### Naming Clusters

- Route segment, controller action, request DTO, command/query, handler, and
  permission constant should be treated as one operation naming cluster.
- Integration events, inbox/outbox stored type names, and handlers should be
  treated as one message naming cluster.
- Quartz job names, scheduler registrations, recurring commands, and process
  commands should be treated as one background-processing naming cluster.
- EF table/schema names and DbContext/DbSet/entity configuration names should
  be treated as one persistence naming cluster.

## External Dependency And Implicit Binding Points

The following structure elements can depend on external configuration,
framework conventions, or runtime wiring:

- ASP.NET Core route attributes, HTTP method attributes, model binding
  attributes, and `ProducesResponseType` metadata on API controllers.
- `HasPermission` attributes and permission constants, because route access is
  coupled to authorization naming.
- Connection strings read in API startup.
- ASP.NET Core pipeline order: CORS, correlation middleware, HSTS/HTTPS,
  routing, authorization, endpoints, Swagger, and IdentityServer.
- DI and module startup through ASP.NET Core services plus Autofac modules.
- EF Core entity type configurations, schema/table names, strongly typed ID
  converters, and DbContext boundaries.
- Quartz jobs for internal processing, inbox, outbox, subscription expiration,
  and subscription-payment expiration.
- Outbox/inbox processing that resolves message and command types by reflection
  and stored type names.
- IdentityServer configuration and resource-owner password validation.
- Email configuration and event bus integration passed into module startup.
- SQL project/database scripts; `structure_graph` could not open the `.sqlproj`
  as a language project, so database DDL remains a file-level source basis.

## Prohibited Change Rules For Later Design

- Do not rename API route segments, request DTOs, commands, queries,
  permissions, or integration events independently. They form a public
  operation, authorization, dispatch, and message-processing naming cluster.
- Do not treat a controller action name as the sole source of behavior. Follow
  the module dispatch to the corresponding command/query handler and domain
  aggregate/rule.
- Do not infer external dependency safety from direct call graph edges only.
  Reflection dispatch, outbox/inbox stored type names, Quartz jobs, EF mapping,
  IdentityServer, and configuration keys are call-invisible dependencies.
- Do not reduce naming candidates to entity nouns. Business action verbs and
  lifecycle state words are part of the local naming rule.
- Do not use tests as the primary source scope for current structure, although
  tests can validate intended lifecycle and naming semantics.

## Deterministic Evidence

- `dotnet restore C:\dev\oss\modular-monolith-with-ddd\src\CompanyName.MyMeetings.sln` initially failed because NuGet audit warning `NU1902` for `IdentityServer4` was treated as an error.
- Restore succeeded for analysis with warning-as-error disabled for the audit
  gate: `/p:TreatWarningsAsErrors=false /p:WarningsNotAsErrors=NU1902 /p:NuGetAudit=false`.
- `tools/structure_graph` produced `nodes=5737` and `edges=12816` over the
  solution; `.sqlproj` was reported as not associated with a language.
- Attribute inventory found `HasPermissionAttribute`, route and HTTP method
  attributes, and controller metadata as high-count API attributes.
- Invocation facts found connection-string access, ASP.NET Core pipeline order,
  IdentityServer setup, and reflection/discovery sites in inbox/outbox/internal
  command processing.
- Naming profile was generated over `src` and excluded 142 test files from the
  convention summary.

## Source Basis

- source_type: external_repository_snapshot
- source_locator: `https://github.com/kgrzybek/modular-monolith-with-ddd`
- source_commit: `91c8ef24b4cb6ef558c95d8267fa07d68c7059f8`
- local_clone: `C:\dev\oss\modular-monolith-with-ddd`
- archived_source: `sources/web/github.com/kgrzybek/modular-monolith-with-ddd/modular-monolith-with-ddd-91c8ef2.zip`
- work_report: `work/reports/2026-07-04_modular_monolith_ddd_api_source_structure_overview.md`
- evidence_dir: `work/source_structure_overview/modular_monolith_ddd_api`

## Unresolved Verification

- Runtime execution, database migration execution, browser/API behavior, and
  security review are outside this finding.
- SQL project contents were not parsed by Roslyn structure tooling; database
  DDL must be inspected directly if a later design touches schema/table
  contracts.
- NuGet audit findings are recorded only as restore-gate evidence, not assessed
  for remediation here.
