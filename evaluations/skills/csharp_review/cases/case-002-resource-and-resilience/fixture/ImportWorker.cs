namespace ReviewFixture;

public sealed class ImportWorker
{
    private readonly ILogger _logger;
    private readonly IQueue _queue;

    public ImportWorker(ILogger logger, IQueue queue)
    {
        _logger = logger;
        _queue = queue;
    }

    public async Task ImportAsync(IEnumerable<string> paths, CancellationToken ct)
    {
        foreach (var path in paths)
        {
            try
            {
                using var client = new HttpClient();
                var response = await client.GetAsync(path, ct);
                await _queue.SaveAsync(path, await response.Content.ReadAsStringAsync(ct));
                File.Delete(path);
            }
            catch (Exception ex)
            {
                _logger.Error(ex, "Import failed");
                continue;
            }
        }
    }
}

public interface IQueue
{
    Task SaveAsync(string source, string content);
}

public interface ILogger
{
    void Error(Exception error, string message);
}
