using System;
using System.Data.SqlClient;
using System.IO;

namespace ReviewTarget.Operational;

public sealed class BadFileImportWorker
{
    private readonly string connectionString;
    private readonly string importDirectory;

    public BadFileImportWorker(string connectionString, string importDirectory)
    {
        this.connectionString = connectionString;
        this.importDirectory = importDirectory;
    }

    public void ImportAll()
    {
        foreach (var file in Directory.GetFiles(importDirectory, "*.dat", SearchOption.AllDirectories))
        {
            try
            {
                var bytes = File.ReadAllBytes(file);

                using (var connection = new SqlConnection(connectionString))
                using (var command = connection.CreateCommand())
                {
                    command.CommandText = @"
INSERT INTO ImportedFiles(FileName, Content, ImportedAt)
VALUES(@FileName, @Content, GETDATE())";

                    command.Parameters.AddWithValue("@FileName", Path.GetFileName(file));
                    command.Parameters.AddWithValue("@Content", bytes);

                    connection.Open();
                    command.ExecuteNonQuery();
                }

                File.Delete(file);
            }
            catch (Exception)
            {
            }
        }
    }
}
