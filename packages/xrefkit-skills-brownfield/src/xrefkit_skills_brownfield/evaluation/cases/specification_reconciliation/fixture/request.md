# Design request

The current approved specification says that the order status code is shown
unchanged in the customer UI. Current UI evidence shows that code `1` is
displayed as `受付中`. The new requirement says that status code `1` must be
displayed as `処理中`, while existing downstream API consumers must remain
compatible. Reconcile the current specification, current behavior, and new
requirement before approving the design.
