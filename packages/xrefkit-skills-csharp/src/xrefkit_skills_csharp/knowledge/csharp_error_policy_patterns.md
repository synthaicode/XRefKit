# C# Error Policy Detection Patterns

Error policy extraction records implemented behavior from source evidence.

Detection patterns include:

- throw sites
- catch blocks
- custom exception types
- global exception handlers
- fire-and-forget tasks
- sync-over-async calls
- DI composition root failures
- options validation
- default, null, empty, bool, or Try-pattern omission behavior

Coverage limits are mandatory because omission policies are often only
partially detectable.
