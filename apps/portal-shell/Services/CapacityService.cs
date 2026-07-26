using System.Net.Http.Json;
using PortalShell.Models;

namespace PortalShell.Services;

/// <summary>
/// Shell-owned, BFF-mediated Fabric capacity client. The browser only calls the
/// FastAPI BFF (<c>GET /v1/platform/capacity</c> plus the start, pause and
/// SKU-change request routes); it never reaches ARM directly. Every SKU change
/// is allow-list checked, role-gated and audited server-side.
/// </summary>
public sealed class CapacityService
{
    private readonly HttpClient _http;
    private readonly AuthDemoContext _auth;
    private readonly ShellOptions _options;

    public CapacityService(HttpClient http, AuthDemoContext auth, ShellOptions options)
    {
        _http = http;
        _auth = auth;
        _options = options;
    }

    public async Task<CapacityStatusDto?> GetStatusAsync(string locale, CancellationToken cancellationToken = default)
    {
        try
        {
            using var request = new HttpRequestMessage(HttpMethod.Get, "/v1/platform/capacity");
            ApplyHeaders(request, locale);
            using var response = await _http.SendAsync(request, cancellationToken);
            if (!response.IsSuccessStatusCode)
            {
                return null;
            }

            var envelope = await response.Content.ReadFromJsonAsync<CapacityStatusEnvelope>(cancellationToken: cancellationToken);
            return envelope?.Data;
        }
        catch (Exception)
        {
            // Fail soft: the caller falls back to a simulated local state.
            return null;
        }
    }

    /// <summary>
    /// The capacity the BFF reports is authoritative: the shell's configured id is
    /// only a fallback for the very first render, before the status call returns.
    /// Posting a stale build-time id gets the mutation refused by the BFF
    /// allow-list, which is silent for start/pause.
    /// </summary>
    private string ResolveCapacityId(string? capacityId) =>
        string.IsNullOrWhiteSpace(capacityId) ? _options.CapacityId : capacityId.Trim();

    public async Task<CapacityMutationDto?> RequestAsync(
        string action,
        string reason,
        string locale,
        string? capacityId = null,
        CancellationToken cancellationToken = default)
    {
        var path = action == "start"
            ? "/v1/platform/capacity/start-requests"
            : "/v1/platform/capacity/pause-requests";
        try
        {
            using var request = new HttpRequestMessage(HttpMethod.Post, path)
            {
                Content = JsonContent.Create(new CapacityMutationRequest(ResolveCapacityId(capacityId), reason)),
            };
            ApplyHeaders(request, locale);
            request.Headers.TryAddWithoutValidation("Idempotency-Key", Guid.NewGuid().ToString("N"));
            using var response = await _http.SendAsync(request, cancellationToken);
            if (!response.IsSuccessStatusCode)
            {
                return null;
            }

            var envelope = await response.Content.ReadFromJsonAsync<CapacityMutationEnvelope>(cancellationToken: cancellationToken);
            return envelope?.Data;
        }
        catch (Exception)
        {
            return null;
        }
    }

    /// <summary>
    /// Requests a Fabric capacity SKU change through the BFF. Unlike start/pause,
    /// a refusal carries a reason the operator must see (an unsupported SKU, a
    /// lifecycle operation in flight, or a capacity outside the allow-list), so
    /// the server's message is returned rather than collapsed into null.
    /// </summary>
    public async Task<CapacityCallResult> RequestSkuAsync(
        string sku,
        string reason,
        string locale,
        string? capacityId = null,
        CancellationToken cancellationToken = default)
    {
        try
        {
            using var request = new HttpRequestMessage(HttpMethod.Post, "/v1/platform/capacity/sku-requests")
            {
                Content = JsonContent.Create(new CapacitySkuRequest(ResolveCapacityId(capacityId), sku, reason)),
            };
            ApplyHeaders(request, locale);
            request.Headers.TryAddWithoutValidation("Idempotency-Key", Guid.NewGuid().ToString("N"));
            using var response = await _http.SendAsync(request, cancellationToken);
            if (!response.IsSuccessStatusCode)
            {
                var error = await ReadErrorAsync(response, cancellationToken);
                return new CapacityCallResult(null, error);
            }

            var envelope = await response.Content.ReadFromJsonAsync<CapacityMutationEnvelope>(cancellationToken: cancellationToken);
            return new CapacityCallResult(envelope?.Data, null);
        }
        catch (Exception)
        {
            // Unreachable BFF: the caller falls back to a simulated local change.
            return new CapacityCallResult(null, null);
        }
    }

    private static async Task<string?> ReadErrorAsync(
        HttpResponseMessage response,
        CancellationToken cancellationToken)
    {
        try
        {
            var error = await response.Content.ReadFromJsonAsync<BffErrorEnvelope>(cancellationToken: cancellationToken);
            return string.IsNullOrWhiteSpace(error?.Message) ? null : $"{error!.Code}: {error.Message}";
        }
        catch (Exception)
        {
            return $"The BFF refused the request ({(int)response.StatusCode}).";
        }
    }

    private void ApplyHeaders(HttpRequestMessage request, string locale)
    {
        foreach (var (key, value) in _auth.DemoHeaders(locale))
        {
            request.Headers.TryAddWithoutValidation(key, value);
        }
    }
}
