public sealed class Policy
{
    public void Run()
    {
        try { Execute(); }
        catch (TimeoutException) { throw; }
        catch (Exception) { }
    }

    private static void Execute() { }
}
