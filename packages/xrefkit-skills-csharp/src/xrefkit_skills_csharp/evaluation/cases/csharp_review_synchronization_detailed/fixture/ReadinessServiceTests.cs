namespace ReviewFixture;

public sealed class ReadinessServiceTests
{
    public async Task CompletesWhenClockAdvances()
    {
        using var cts = new CancellationTokenSource();
        var service = new ReadinessService(new FakeClock());
        var wait = service.WaitUntilReadyAsync(cts.Token);
        await Task.Yield();
        service.MarkReady();
        await wait;
    }
}
