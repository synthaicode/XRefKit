namespace Fixture;
public sealed class Policy
{
    public void Send(string value)
    {
        try { Transport.Send(value); }
        catch (TimeoutException) { return; }
        catch (Exception error) { Console.Error.WriteLine(error); }
    }
    private static class Transport { public static void Send(string value) { } }
}
