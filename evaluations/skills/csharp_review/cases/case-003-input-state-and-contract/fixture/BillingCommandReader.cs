using System.Text.Json;

namespace ReviewFixture;

public sealed class BillingCommandReader
{
    private static readonly Dictionary<string, decimal> Rates = new();

    public BillingCommand Read(string json)
    {
        var options = new JsonSerializerOptions { IgnoreUnknownProperties = true };
        var command = JsonSerializer.Deserialize<BillingCommand>(json, options)
                      ?? new BillingCommand();

        if (!decimal.TryParse(command.AmountText, out var amount))
            amount = 0m;

        if (string.IsNullOrWhiteSpace(command.Currency))
            command.Currency = "USD";

        Rates[command.CustomerId ?? ""] = amount;
        return command;
    }
}

public sealed class BillingCommand
{
    public string? CustomerId { get; set; }
    public string? Currency { get; set; }
    public string? AmountText { get; set; }
}
