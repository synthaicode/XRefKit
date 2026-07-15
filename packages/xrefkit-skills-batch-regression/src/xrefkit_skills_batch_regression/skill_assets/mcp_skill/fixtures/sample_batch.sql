CREATE PROCEDURE dbo.SampleBatch
    @kind nvarchar(10), @amount decimal(10,2)
AS
BEGIN
    IF @kind = 'A' AND @amount > 0
        SELECT 'ok';
    SELECT CASE WHEN @kind IN ('A','B') THEN 1 ELSE 0 END;
END;
