using PortalShell.Models;

namespace PortalShell.Services;

/// <summary>
/// Authoritative shell-side capacity lifecycle surface. Holds the current state,
/// mediates start/pause requests through the BFF, and falls back to a
/// deterministic simulated state machine when the BFF is unavailable so the
/// demo control always works (mirrors the BFF LocalCapacityAdapter).
/// </summary>
public sealed class CapacityState
{
    private static readonly string[] StartSequence = ["ResumeRequested", "Resuming", "ReadinessCheck", "Running"];
    private static readonly string[] PauseSequence = ["DrainRequested", "Draining", "SuspendRequested", "Paused"];

    private readonly CapacityService _service;
    private readonly AuthDemoContext _auth;
    private readonly ShellOptions _options;

    public CapacityState(CapacityService service, AuthDemoContext auth, ShellOptions options)
    {
        _service = service;
        _auth = auth;
        _options = options;
        Status = Simulated("Running");
    }

    public event Action? Changed;

    public CapacityStatusDto Status { get; private set; }

    public string Source { get; private set; } = "simulated";

    public bool Busy { get; private set; }

    public bool PanelOpen { get; private set; }

    public string? LastMessage { get; private set; }

    public List<CapacityTransitionEntry> Transitions { get; } = [];

    public bool CanManage => _auth.HasRole("Platform.Capacity.Manage");

    public bool MutationsLocked => Status.State is
        "ResumeRequested" or "Resuming" or "ReadinessCheck" or
        "DrainRequested" or "Draining" or "SuspendRequested";

    public void TogglePanel()
    {
        PanelOpen = !PanelOpen;
        Notify();
    }

    public void ClosePanel()
    {
        PanelOpen = false;
        Notify();
    }

    public async Task RefreshAsync(string locale)
    {
        var status = await _service.GetStatusAsync(locale);
        if (status is not null)
        {
            Status = status;
            Source = "bff";
            Notify();
        }
    }

    public async Task RequestAsync(string action, string reason, string locale)
    {
        if (!CanManage)
        {
            LastMessage = "Read-only: only Platform.Capacity.Manage may request start or pause.";
            Notify();
            return;
        }

        var normalized = action == "start" ? "start" : "pause";
        if (normalized == "start" && Status.State != "Paused")
        {
            LastMessage = "Capacity must be Paused before a start request.";
            Notify();
            return;
        }

        if (normalized == "pause" && Status.State != "Running")
        {
            LastMessage = "Capacity must be Running before a pause request.";
            Notify();
            return;
        }

        Busy = true;
        LastMessage = null;
        Notify();

        var effectiveReason = string.IsNullOrWhiteSpace(reason) ? "rehearsal readiness" : reason.Trim();
        var result = await _service.RequestAsync(normalized, effectiveReason, locale);
        if (result is not null)
        {
            Source = "bff";
            AppendTransition(Status.State, result.State, effectiveReason, result.OperationId ?? "bff");
            Status = Status with { State = result.State, DemoModeSimulated = true, Stale = false };
            LastMessage = $"{normalized} accepted by the BFF: {result.Status} → {result.State}.";
        }
        else
        {
            Source = "simulated";
            SimulateTransition(normalized, effectiveReason);
            LastMessage = $"{normalized} simulated locally (BFF unavailable); no ARM operation fired.";
        }

        Busy = false;
        Notify();
    }

    private void SimulateTransition(string action, string reason)
    {
        var sequence = action == "start" ? StartSequence : PauseSequence;
        var correlationId = Guid.NewGuid().ToString("N")[..12];
        var current = Status.State;
        foreach (var next in sequence)
        {
            AppendTransition(current, next, reason, correlationId);
            current = next;
        }

        Status = Status with { State = current, DemoModeSimulated = true, Stale = false };
    }

    private void AppendTransition(string from, string to, string reason, string correlationId)
    {
        Transitions.Insert(
            0,
            new CapacityTransitionEntry(
                DateTimeOffset.UtcNow.ToString("HH:mm:ss"),
                _auth.CurrentUser.DisplayName,
                from,
                to,
                reason,
                correlationId));
        if (Transitions.Count > 25)
        {
            Transitions.RemoveAt(Transitions.Count - 1);
        }
    }

    private CapacityStatusDto Simulated(string state) =>
        new(_options.CapacityId, "demo", state, "F2", DemoModeSimulated: true, Stale: false);

    private void Notify() => Changed?.Invoke();
}
