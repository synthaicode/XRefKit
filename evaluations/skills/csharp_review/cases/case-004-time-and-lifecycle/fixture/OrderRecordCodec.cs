namespace ReviewFixture;

public sealed class OrderRecordCodec
{
    public string ToRecord(Order order)
    {
        var created = DateTime.Now;
        return $"{order.Id}|{created}|{order.Total.ToString()}";
    }

    public Order ReadRecord(string line)
    {
        var parts = line.Split('|');
        return new Order
        {
            Id = parts[0],
            CreatedAt = DateTime.Parse(parts[1]),
            Total = decimal.Parse(parts[2])
        };
    }
}

public sealed class Order
{
    public string Id { get; set; } = "";
    public DateTime CreatedAt { get; set; }
    public decimal Total { get; set; }
}
