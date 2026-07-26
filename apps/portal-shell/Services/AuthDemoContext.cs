using PortalShell.Models;

namespace PortalShell.Services;

public interface ITokenReferenceBroker
{
    TokenReference Current { get; }
}

public sealed class DemoTokenReferenceBroker : ITokenReferenceBroker
{
    public TokenReference Current { get; } = new(
        "demo-session-reference",
        DateTimeOffset.UtcNow.AddMinutes(15));
}

public sealed class AuthDemoContext
{
    // Mirrors the BFF role->action map (services/bff-api auth boundary) so the
    // shell can pass a server-consistent permitted-action set to the MFE.
    private static readonly IReadOnlyDictionary<string, string[]> ActionsByRole =
        new Dictionary<string, string[]>
        {
            ["Operator.Read"] = ["dashboard.read", "telemetry.read"],
            ["ProcessEngineer.Contribute"] = ["dashboard.read", "quality.read", "quality.whatIf"],
            ["EnergyPlanner.Approve"] = ["dashboard.read", "energy.read", "energy.simulate", "energy.approve"],
            ["MaintenanceEngineer.Read"] = ["dashboard.read", "furnace.viewForecast", "workorder.createSynthetic"],
            ["Compliance.Auditor"] = ["audit.read", "sustainability.read"],
            ["Platform.Capacity.Manage"] = ["platform.capacity.manage"],
            ["Knowledge.Publisher"] = ["knowledge.read", "knowledge.capture", "knowledge.publish"],
        };

    // Demo plant scope must live in the NS-DEMO-* namespace (BFF fail-closed rule).
    public const string DemoPlant = "NS-DEMO-LUX-01";

    public DemoUser CurrentUser { get; } = new(
        "Synthetic Demo User",
        [
            "Operator.Read",
            "MaintenanceEngineer.Read",
            "EnergyPlanner.Approve",
            "ProcessEngineer.Contribute",
            "Knowledge.Publisher",
            "Compliance.Auditor",
            "Platform.Capacity.Manage"
        ],
        [
            "PlantManager",
            "FurnaceOperator",
            "EnergyManager",
            "QualityEngineer",
            "SustainabilityOfficer",
            "KnowledgeEngineer",
            "Executive",
            "PlatformOps"
        ]);

    public bool IsSignedIn { get; private set; } = true;

    public IReadOnlyList<string> PermittedActions =>
        CurrentUser.Roles
            .SelectMany(role => ActionsByRole.TryGetValue(role, out var actions) ? actions : [])
            .Distinct()
            .OrderBy(action => action, StringComparer.Ordinal)
            .ToArray();

    public bool HasRole(string role) => CurrentUser.Roles.Contains(role);

    /// <summary>Demo-only header set consumed by the BFF's demo authenticator.</summary>
    public IReadOnlyDictionary<string, string> DemoHeaders(string locale) =>
        new Dictionary<string, string>
        {
            ["X-Demo-User"] = "demo-portal-shell",
            ["X-Demo-Roles"] = string.Join(',', CurrentUser.Roles),
            ["X-Demo-Plants"] = DemoPlant,
            ["X-Demo-Display-Name"] = CurrentUser.DisplayName,
            ["X-Demo-Locale"] = locale,
        };

    public void ToggleSignIn() => IsSignedIn = !IsSignedIn;
}
