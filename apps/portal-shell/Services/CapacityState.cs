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

    /// <summary>
    /// SKUs the portal may request. Kept in step with the BFF allow-list
    /// (<c>BFF_CAPACITY_SKU_ALLOWLIST</c>) and the Azure Policy guardrail
    /// <c>restrict-fabric-capacity-sku.json</c>; the server is authoritative and
    /// overrides this fallback through <c>skuOptions</c> on the status payload.
    /// </summary>
    private static readonly string[] DefaultSkuOptions = ["F2", "F4", "F8"];

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

    /// <summary>SKUs offered by the capacity dialog, server-authoritative when available.</summary>
    public IReadOnlyList<string> SkuOptions =>
        Status.SkuOptions is { Count: > 0 } options ? options : DefaultSkuOptions;

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

    /// <summary>
    /// Opens the panel without toggling, so an analytics tile can request the
    /// control surface without ever closing an already-open dialog.
    /// </summary>
    public void OpenPanel()
    {
        if (PanelOpen)
        {
            return;
        }

        PanelOpen = true;
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
        var result = await _service.RequestAsync(normalized, effectiveReason, locale, Status.CapacityId);
        if (result is not null)
        {
            Source = "bff";
            AppendTransition(Status.State, result.State, effectiveReason, result.OperationId ?? "bff");
            Status = Status with { State = result.State, Stale = false };
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

    /// <summary>
    /// Requests a Fabric capacity SKU change. Scaling does not change the
    /// lifecycle state: a Running capacity stays Running and a Paused capacity
    /// stays Paused, so the demo can resize without a resume/pause round trip.
    /// </summary>
    public async Task RequestSkuAsync(string sku, string reason, string locale)
    {
        if (!CanManage)
        {
            LastMessage = "Read-only: only Platform.Capacity.Manage may change the SKU.";
            Notify();
            return;
        }

        var requested = (sku ?? string.Empty).Trim().ToUpperInvariant();
        if (!SkuOptions.Contains(requested))
        {
            LastMessage = $"SKU must be one of {string.Join(", ", SkuOptions)}.";
            Notify();
            return;
        }

        if (MutationsLocked)
        {
            LastMessage = $"A lifecycle operation is in progress ({Status.State}); the SKU cannot change until it settles.";
            Notify();
            return;
        }

        if (string.Equals(requested, Status.Sku, StringComparison.OrdinalIgnoreCase))
        {
            LastMessage = $"Capacity is already running SKU {Status.Sku}.";
            Notify();
            return;
        }

        Busy = true;
        LastMessage = null;
        Notify();

        var effectiveReason = string.IsNullOrWhiteSpace(reason) ? "rehearsal readiness" : reason.Trim();
        var previousSku = Status.Sku;
        var result = await _service.RequestSkuAsync(requested, effectiveReason, locale, Status.CapacityId);
        if (result.Data is not null)
        {
            Source = "bff";
            var applied = result.Data.Sku ?? requested;
            AppendTransition(Status.State, result.Data.State, $"{effectiveReason} (SKU {previousSku} → {applied})", result.Data.OperationId ?? "bff");
            Status = Status with { State = result.Data.State, Sku = applied, Stale = false };
            LastMessage = $"SKU change accepted by the BFF: {previousSku} → {applied} ({result.Data.Status}).";
        }
        else if (result.ErrorMessage is not null)
        {
            LastMessage = $"SKU change refused. {result.ErrorMessage}";
        }
        else
        {
            Source = "simulated";
            AppendTransition(
                Status.State,
                Status.State,
                $"{effectiveReason} (SKU {previousSku} → {requested})",
                Guid.NewGuid().ToString("N")[..12]);
            Status = Status with { Sku = requested, DemoModeSimulated = true, Stale = false };
            LastMessage = $"SKU change simulated locally (BFF unavailable): {previousSku} → {requested}; no ARM operation fired.";
        }

        Busy = false;
        Notify();
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
        new(_options.CapacityId, "demo", state, "F2", DemoModeSimulated: true, Stale: false, SkuOptions: DefaultSkuOptions);

    private void Notify() => Changed?.Invoke();
}
