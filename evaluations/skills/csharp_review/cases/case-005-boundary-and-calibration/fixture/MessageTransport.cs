namespace ReviewFixture;

public sealed class MessageTransport
{
    [Retryable(Attempts = 3)]
    public Task SendAsync(Message message) => _transport.SendAsync(message);

    public Task ForwardAsync(string tenantId, Message message)
        => _queue.PublishAsync($"tenant/{tenantId}", message);

    public Task SaveAsync(Message message)
        => _repository.InsertAsync(message);

    public string Label(Order order)
        => order.Customer.Name.ToUpper();

    private readonly ITransport _transport = null!;
    private readonly IQueue _queue = null!;
    private readonly IRepository _repository = null!;
}

public sealed class Message { }
public sealed class Order { public Customer Customer { get; set; } = null!; }
public sealed class Customer { public string Name { get; set; } = ""; }
public interface ITransport { Task SendAsync(Message message); }
public interface IQueue { Task PublishAsync(string topic, Message message); }
public interface IRepository { Task InsertAsync(Message message); }
