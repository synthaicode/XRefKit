CREATE PROCEDURE dbo.ApplyOrderBatch @Region nvarchar(10), @Mode nvarchar(10) AS
BEGIN
    UPDATE dbo.OrderSummary SET ProcessedCount = ProcessedCount + 1 WHERE Region = @Region;
END;
