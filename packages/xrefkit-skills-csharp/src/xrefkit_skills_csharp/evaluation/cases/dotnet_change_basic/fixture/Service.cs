namespace Fixture;
public sealed class Service
{
    public Task ExecuteAsync(Request request) => new Worker().RunAsync(request);
}
public sealed class Worker
{
    public Task RunAsync(Request request) => Task.CompletedTask;
}
public sealed class Request { public string Id { get; set; } = ""; }
