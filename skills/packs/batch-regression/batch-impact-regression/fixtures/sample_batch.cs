public class SampleBatch
{
    public void Run(string kind, int amount)
    {
        if (kind == "A" && amount > 0) Save();
        if (kind == "B") Save();
    }
}
