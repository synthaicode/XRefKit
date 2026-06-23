using System;
using System.Collections.Generic;
using System.Data.SqlClient;
using System.Net;
using System.Net.Mail;

namespace ReviewTarget.Mail;

public sealed class BadMailSender
{
    private readonly string connectionString;
    private readonly string smtpHost;
    private readonly int smtpPort;
    private readonly string smtpUser;
    private readonly string smtpPassword;

    public BadMailSender(
        string connectionString,
        string smtpHost,
        int smtpPort,
        string smtpUser,
        string smtpPassword)
    {
        this.connectionString = connectionString;
        this.smtpHost = smtpHost;
        this.smtpPort = smtpPort;
        this.smtpUser = smtpUser;
        this.smtpPassword = smtpPassword;
    }

    public void SendPendingMails()
    {
        var mails = LoadPendingMails();

        foreach (var mail in mails)
        {
            try
            {
                using (var smtp = new SmtpClient(smtpHost, smtpPort))
                {
                    smtp.Credentials = new NetworkCredential(smtpUser, smtpPassword);
                    smtp.EnableSsl = true;
                    smtp.Timeout = 30000;

                    using (var message = new MailMessage(mail.FromAddress, mail.ToAddress, mail.Subject, mail.Body))
                    {
                        smtp.Send(message);
                    }
                }

                MarkAsSent(mail.MailId);
            }
            catch (Exception)
            {
            }
        }
    }

    private List<MailQueueItem> LoadPendingMails()
    {
        var result = new List<MailQueueItem>();

        using (var connection = new SqlConnection(connectionString))
        using (var command = connection.CreateCommand())
        {
            command.CommandText = @"
SELECT TOP (10000)
       MailId,
       FromAddress,
       ToAddress,
       Subject,
       Body
FROM MailQueue
WHERE Status = 'Queued'
ORDER BY CreatedAt";

            connection.Open();

            using (var reader = command.ExecuteReader())
            {
                while (reader.Read())
                {
                    result.Add(new MailQueueItem
                    {
                        MailId = reader.GetInt64(0),
                        FromAddress = reader.GetString(1),
                        ToAddress = reader.GetString(2),
                        Subject = reader.GetString(3),
                        Body = reader.GetString(4)
                    });
                }
            }
        }

        return result;
    }

    private void MarkAsSent(long mailId)
    {
        using (var connection = new SqlConnection(connectionString))
        using (var command = connection.CreateCommand())
        {
            command.CommandText = "UPDATE MailQueue SET Status = 'Sent' WHERE MailId = @MailId";
            command.Parameters.AddWithValue("@MailId", mailId);
            connection.Open();
            command.ExecuteNonQuery();
        }
    }

    private sealed class MailQueueItem
    {
        public long MailId { get; set; }
        public string FromAddress { get; set; } = "";
        public string ToAddress { get; set; } = "";
        public string Subject { get; set; } = "";
        public string Body { get; set; } = "";
    }
}
