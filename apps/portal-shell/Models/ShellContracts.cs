using System.Text.Json;
using System.Text.Json.Serialization;

namespace PortalShell.Models;

public enum ThemeMode
{
    System,
    Light,
    Dark
}

public sealed record DemoUser(
    string DisplayName,
    IReadOnlyList<string> Roles,
    IReadOnlyList<string> Personas);

public sealed record TokenReference(string Value, DateTimeOffset ExpiresAt);

public sealed record ShellNavItem(
    string Label,
    string Section,
    string? DefaultSubView,
    string Persona,
    string Symbol,
    string Group = "");

public sealed record AnalyticsNavigation(
    [property: JsonPropertyName("section")] string Section,
    [property: JsonPropertyName("subView")] string? SubView,
    [property: JsonPropertyName("site")] string Site);

public sealed record AnalyticsBridgeContext(
    [property: JsonPropertyName("themeMode")] string ThemeMode,
    [property: JsonPropertyName("locale")] string Locale,
    [property: JsonPropertyName("activePersona")] string ActivePersona,
    [property: JsonPropertyName("site")] string Site,
    [property: JsonPropertyName("demoMode")] bool DemoMode,
    [property: JsonPropertyName("tokenRef")] string TokenRef,
    [property: JsonPropertyName("bridgeVersion")] string BridgeVersion,
    [property: JsonPropertyName("navigation")] AnalyticsNavigation Navigation,
    [property: JsonPropertyName("bffBaseUrl")] string? BffBaseUrl,
    [property: JsonPropertyName("permittedActions")] IReadOnlyList<string> PermittedActions,
    [property: JsonPropertyName("helpBilingual")] bool HelpBilingual = false);

public sealed record AnalyticsEvent(string Type, JsonElement Payload);

public sealed record NavigationIntent(
    [property: JsonPropertyName("route")] string Route);

public sealed record CapacityRequest(
    [property: JsonPropertyName("action")] string Action,
    [property: JsonPropertyName("reason")] string? Reason);

public sealed record ToastNotification(
    [property: JsonPropertyName("severity")] string Severity,
    [property: JsonPropertyName("message")] string Message);

public sealed record CapacityStatusDto(
    [property: JsonPropertyName("capacityId")] string CapacityId,
    [property: JsonPropertyName("environment")] string Environment,
    [property: JsonPropertyName("state")] string State,
    [property: JsonPropertyName("sku")] string Sku,
    [property: JsonPropertyName("demoModeSimulated")] bool DemoModeSimulated,
    [property: JsonPropertyName("stale")] bool Stale,
    [property: JsonPropertyName("skuOptions")] IReadOnlyList<string>? SkuOptions = null);

public sealed record CapacityStatusEnvelope(
    [property: JsonPropertyName("data")] CapacityStatusDto Data,
    [property: JsonPropertyName("asOf")] string AsOf,
    [property: JsonPropertyName("correlationId")] string CorrelationId);

public sealed record CapacityMutationDto(
    [property: JsonPropertyName("status")] string Status,
    [property: JsonPropertyName("state")] string State,
    [property: JsonPropertyName("operationId")] string? OperationId,
    [property: JsonPropertyName("capacityId")] string CapacityId,
    [property: JsonPropertyName("sku")] string? Sku = null,
    [property: JsonPropertyName("previousSku")] string? PreviousSku = null);

public sealed record CapacityMutationEnvelope(
    [property: JsonPropertyName("data")] CapacityMutationDto Data,
    [property: JsonPropertyName("asOf")] string AsOf,
    [property: JsonPropertyName("correlationId")] string CorrelationId);

public sealed record CapacityMutationRequest(
    [property: JsonPropertyName("capacityId")] string CapacityId,
    [property: JsonPropertyName("reason")] string Reason);

public sealed record CapacitySkuRequest(
    [property: JsonPropertyName("capacityId")] string CapacityId,
    [property: JsonPropertyName("sku")] string Sku,
    [property: JsonPropertyName("reason")] string Reason);

/// <summary>Flat BFF error envelope, used to surface a refused SKU change verbatim.</summary>
public sealed record BffErrorEnvelope(
    [property: JsonPropertyName("code")] string Code,
    [property: JsonPropertyName("message")] string Message,
    [property: JsonPropertyName("correlationId")] string? CorrelationId,
    [property: JsonPropertyName("retryable")] bool Retryable);

/// <summary>Outcome of a BFF-mediated capacity call: either data or a server-supplied refusal.</summary>
public sealed record CapacityCallResult(CapacityMutationDto? Data, string? ErrorMessage);

public sealed record CapacityTransitionEntry(
    string Time,
    string Actor,
    string FromState,
    string ToState,
    string Reason,
    string CorrelationId);
