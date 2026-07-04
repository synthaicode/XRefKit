using System;
using System.Collections.Generic;

namespace Brownfield.CustomRuntime;

[AttributeUsage(AttributeTargets.Class)]
public sealed class HandlesMessageAttribute : Attribute
{
    public HandlesMessageAttribute(string messageName)
    {
        MessageName = messageName;
    }

    public string MessageName { get; }
}

[AttributeUsage(AttributeTargets.Method)]
public sealed class RetryableFailureAttribute : Attribute
{
    public RetryableFailureAttribute(string policyName)
    {
        PolicyName = policyName;
    }

    public string PolicyName { get; }
}

public sealed class DomainResult<T>
{
    private DomainResult(T? value, string? rejectionCode)
    {
        Value = value;
        RejectionCode = rejectionCode;
    }

    public T? Value { get; }

    public string? RejectionCode { get; }

    public bool Accepted => RejectionCode is null;

    public static DomainResult<T> Accept(T value) => new(value, null);

    public static DomainResult<T> Reject(string rejectionCode) => new(default, rejectionCode);
}

public sealed class LocalCompositionRoot
{
    private readonly Dictionary<string, Type> _handlers = new();

    public void Register<THandler>() where THandler : class
    {
        var attribute = (HandlesMessageAttribute?)Attribute.GetCustomAttribute(
            typeof(THandler),
            typeof(HandlesMessageAttribute));

        if (attribute is null)
        {
            throw new InvalidOperationException("Handler is missing HandlesMessageAttribute.");
        }

        _handlers[attribute.MessageName] = typeof(THandler);
    }
}

[HandlesMessage("orders.submit")]
public sealed class SubmitOrderHandler
{
    [RetryableFailure("payment-provider-timeout")]
    public DomainResult<string> Handle(SubmitOrder command, IOrderCreditPolicy creditPolicy)
    {
        if (command.CustomerId.Length == 0)
        {
            return DomainResult<string>.Reject("missing-customer");
        }

        if (!creditPolicy.CanAccept(command.CustomerId, command.TotalAmount))
        {
            return DomainResult<string>.Reject("credit-limit");
        }

        return DomainResult<string>.Accept($"accepted:{command.OrderId}");
    }
}

public sealed record SubmitOrder(string OrderId, string CustomerId, decimal TotalAmount);

public interface IOrderCreditPolicy
{
    bool CanAccept(string customerId, decimal amount);
}
