using System.Net.Http.Json;
using System.Text.Json.Serialization;

namespace PortalShell.Services;

/// <summary>
/// What the BFF reported about itself, or why it could not be reached.
/// </summary>
/// <param name="Reachable">True when the BFF answered with a usable payload.</param>
/// <param name="Service">Service name the BFF reports, e.g. <c>novasteel-bff-api</c>.</param>
/// <param name="Environment">Deployment environment the BFF reports.</param>
/// <param name="AuthMode">Authentication mode the BFF is running in.</param>
/// <param name="ApiVersion">API version the BFF is serving.</param>
/// <param name="Detail">Short failure reason, populated only when unreachable.</param>
public sealed record BffProbeResult(
    bool Reachable,
    string? Service = null,
    string? Environment = null,
    string? AuthMode = null,
    string? ApiVersion = null,
    string? Detail = null);

/// <summary>
/// Asks the BFF who it is. Probing the unauthenticated <c>GET /v1/meta</c>
/// bootstrap route lets the shell state exactly which backend it reached, so the
/// connection indicator can report reachability honestly rather than assuming a
/// backend is present. When nothing answers the shell says so plainly and the
/// analytics MFE falls back to its bundled synthetic fixtures.
/// </summary>
public sealed class BffHealthService
{
    private static readonly TimeSpan ProbeTimeout = TimeSpan.FromSeconds(8);

    private readonly HttpClient _http;

    public BffHealthService(HttpClient http)
    {
        _http = http;
    }

    public async Task<BffProbeResult> ProbeAsync(CancellationToken cancellationToken = default)
    {
        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        timeout.CancelAfter(ProbeTimeout);

        try
        {
            using var response = await _http.GetAsync("/v1/meta", timeout.Token);
            if (!response.IsSuccessStatusCode)
            {
                return new BffProbeResult(false, Detail: $"HTTP {(int)response.StatusCode}");
            }

            var envelope = await response.Content.ReadFromJsonAsync<MetaEnvelope>(cancellationToken: timeout.Token);
            var meta = envelope?.Data;
            if (meta is null)
            {
                return new BffProbeResult(false, Detail: "empty response");
            }

            return new BffProbeResult(
                true,
                meta.Service,
                meta.Environment,
                meta.AuthMode,
                meta.ApiVersion);
        }
        catch (OperationCanceledException) when (!cancellationToken.IsCancellationRequested)
        {
            return new BffProbeResult(false, Detail: "timed out");
        }
        catch (Exception exception)
        {
            return new BffProbeResult(false, Detail: exception.Message);
        }
    }

    private sealed record MetaEnvelope([property: JsonPropertyName("data")] MetaData? Data);

    private sealed record MetaData(
        [property: JsonPropertyName("apiVersion")] string? ApiVersion,
        [property: JsonPropertyName("service")] string? Service,
        [property: JsonPropertyName("environment")] string? Environment,
        [property: JsonPropertyName("authMode")] string? AuthMode);
}
