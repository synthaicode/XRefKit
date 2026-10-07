namespace ReviewFixture;

[AttributeUsage(AttributeTargets.Method)]
public sealed class RetryableAttribute : Attribute
{
    public int Attempts { get; set; }
}
