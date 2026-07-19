namespace Fixture;
public sealed class Service
{
    private readonly FakeClock _clock;
    private bool _ready;
    public Service(FakeClock clock) => _clock = clock;
    public async Task WaitAsync(CancellationToken ct)
    {
        while (!_ready) await _clock.Delay(TimeSpan.FromSeconds(1), ct);
    }
    public void Ready() => _ready = true;
}
public sealed class FakeClock
{
    public Task Delay(TimeSpan value, CancellationToken ct) => Task.Delay(Timeout.Infinite, ct);
}
