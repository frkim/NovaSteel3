using System.Text.Json;
using PortalShell.Models;

var ctx = new AnalyticsBridgeContext(
    "dark", "en-LU", "PlantManager", "PlantManager", "lu", "tok", "1.0",
    new AnalyticsNavigation("command-center", null, "lu"),
    "http://localhost:5100", new List<string>{"read"}, true);

var json = JsonSerializer.Serialize(ctx);
Console.WriteLine(json.Contains("\"helpBilingual\":true") ? "PASS: helpBilingual present" : "FAIL: helpBilingual missing");
Console.WriteLine(json);
