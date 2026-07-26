using System.Net.Http.Json;
using PortalShell.Models;

namespace PortalShell.Services;

/// <summary>
/// Shell-owned, BFF-mediated Fabric capacity client. The browser only calls the
/// FastAPI BFF (<c>GET /v1/platform/capacity</c> and the start/pause request
/// routes); it never reaches ARM and never scales a SKU.
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

    public async Task<CapacityMutationDto?> RequestAsync(
        string action,
        string reason,
        string locale,
        CancellationToken cancellationToken = default)
    {
        var path = action == "start"
            ? "/v1/platform/capacity/start-requests"
            : "/v1/platform/capacity/pause-requests";
        try
        {
            using var request = new HttpRequestMessage(HttpMethod.Post, path)
            {
                Content = JsonContent.Create(new CapacityMutationRequest(_options.CapacityId, reason)),
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

    private void ApplyHeaders(HttpRequestMessage request, string locale)
    {
        foreach (var (key, value) in _auth.DemoHeaders(locale))
        {
            request.Headers.TryAddWithoutValidation(key, value);
        }
    }
}
