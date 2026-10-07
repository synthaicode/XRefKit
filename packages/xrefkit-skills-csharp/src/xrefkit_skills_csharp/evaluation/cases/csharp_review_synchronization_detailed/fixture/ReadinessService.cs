namespace ReviewFixture;

public sealed class ReadinessService
{
    private readonly FakeClock _clock;
    private readonly State _state = new();

    public ReadinessService(FakeClock clock) => _clock = clock;

    public async Task WaitUntilReadyAsync(CancellationToken ct)
    {
        while (!_state.IsReady)
            await _clock.Delay(TimeSpan.FromSeconds(1), ct);
    }

    public void MarkReady() => _state.IsReady = true;

    private sealed class State
    {
        public bool IsReady { get; set; }
    }
}

public sealed class FakeClock
{
    public Task Delay(TimeSpan duration, CancellationToken ct) =>
        Task.Delay(Timeout.InfiniteTimeSpan, ct);
}
