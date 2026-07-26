namespace PortalShell.Services;

/// <summary>Resolved shell configuration shared with services and the MFE bridge.</summary>
public sealed class ShellOptions
{
    public string BffBaseUrl { get; init; } = "http://localhost:8080";

    public string CapacityId { get; init; } = "cap-novasteel-demo-sc";
}
