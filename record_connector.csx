// run with:
// dotnet script record_connector.csx

using System;
using System.Diagnostics;
using System.IO;

string exePath = "Connector_v3.0.0-beta.9.exe";
string logPath = "connector_recording.log";

// Clear or create the log file
File.WriteAllText(logPath, string.Empty);

// Set up the process
var startInfo = new ProcessStartInfo
{
    FileName = exePath,
    RedirectStandardOutput = true,
    UseShellExecute = false,
    CreateNoWindow = true
};

using (var process = new Process { StartInfo = startInfo })
{
    process.Start();

    void LogOutput(StreamReader reader)
    {
        while (!reader.EndOfStream)
        {
            string line = reader.ReadLine();
            string timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff");
            File.AppendAllText(logPath, $"{timestamp} {line}{Environment.NewLine}");
        }
    }

    // Read stdout asynchronously
    var stdoutTask = Task.Run(() => LogOutput(process.StandardOutput));

    // Wait for everything to finish
    process.WaitForExit();
    stdoutTask.Wait();
}
