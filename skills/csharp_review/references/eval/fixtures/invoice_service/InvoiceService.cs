using System.Collections.Generic;
using System.Linq;

namespace ReviewTarget.Billing;

public sealed class InvoiceService
{
    public Dictionary<string, decimal> RateCache = new();

    public decimal CalculateTotal(Invoice invoice)
    {
        decimal subtotal = invoice.Lines.Sum(line => line.UnitPrice * line.Quantity);
        decimal taxRate = GetTaxRate(invoice.Region);
        decimal tax = subtotal * taxRate;

        decimal rate = RateCache[invoice.Currency];
        return (subtotal + tax) * rate;
    }

    public decimal GetTaxRate(string region)
    {
        var config = LoadTaxConfig();
        if (config.ContainsKey(region))
        {
            return config[region];
        }

        return 0;
    }

    private static Dictionary<string, decimal> LoadTaxConfig()
    {
        return new Dictionary<string, decimal>
        {
            ["JP"] = 0.10m
        };
    }
}

public sealed class Invoice
{
    public string Region = "";
    public string Currency = "";
    public List<InvoiceLine> Lines = new();
}

public sealed class InvoiceLine
{
    public decimal UnitPrice;
    public int Quantity;
}
