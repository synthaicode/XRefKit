# Pages release-ref correction

Run 40092704337 (Pages #248) was rejected before steps because tag v0.7.2 is not permitted by the github-pages environment, which allows only main. Core release 40092050532 succeeded and the workflow_run Pages deployment 40092417131 succeeded.

Route release events through an environment-free, least-privilege dispatch job targeting only main. Restrict actual deploy to main; retain the existing workflow_run publisher-trust conditions and environment policy. Existing tags are immutable and are not retagged. New main deployment is the verification target.

Regression tests failed before the fix (3 failures); workflow/site metadata tests pass after it (78 passed). Actual Bash dispatch block was tested with stubbed gh success and error; generated site and release metadata v0.7.2 render successfully.
