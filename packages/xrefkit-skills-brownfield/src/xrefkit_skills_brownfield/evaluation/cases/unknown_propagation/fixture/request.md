# Change request

Add an optional `customer_code` to order registration. Existing callers must
continue to work. The repository contains an order service and tests, but the
business rule for missing customer codes and the migration treatment of old
rows are not specified.
