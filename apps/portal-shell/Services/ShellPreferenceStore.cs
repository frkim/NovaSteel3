using Microsoft.JSInterop;
using PortalShell.Models;

namespace PortalShell.Services;

/// <summary>
/// Restores and persists the shell preferences a visitor is expected to set
/// once — theme, display language, and the Help Assistant's bilingual mode —
/// in first-party cookies.
/// </summary>
/// <remarks>
/// The store is deliberately the only component that knows preferences are
/// persisted at all: <see cref="ShellState"/> stays a synchronous, in-memory
/// state machine, and this class listens to its change notification and writes
/// through whenever one of the three tracked values actually changes. That
/// keeps a JavaScript round-trip out of every state mutation and means a
/// failure to reach the cookie jar can never break the UI.
/// </remarks>
public sealed class ShellPreferenceStore : IAsyncDisposable
{
    private const string ThemeKey = "theme";
    private const string LocaleKey = "locale";
    private const string BilingualKey = "helpBilingual";

    private readonly IJSRuntime _js;
    private readonly ShellState _shell;

    private IJSObjectReference? _module;
    private bool _initialized;
    private string? _lastTheme;
    private string? _lastLocale;
    private string? _lastBilingual;

    public ShellPreferenceStore(IJSRuntime js, ShellState shell)
    {
        _js = js;
        _shell = shell;
    }

    /// <summary>
    /// Applies any stored preference to the shell, then starts writing through.
    /// Safe to call more than once; only the first call does the work.
    /// </summary>
    public async Task InitializeAsync()
    {
        if (_initialized)
        {
            return;
        }

        _initialized = true;

        try
        {
            _module = await _js.InvokeAsync<IJSObjectReference>("import", "./js/shellPreferences.js");
            var stored = await _module.InvokeAsync<Dictionary<string, string>>("read");
            Apply(stored);
        }
        catch (JSException)
        {
            // A browser that refuses cookies is a supported configuration: the
            // shell simply falls back to its in-memory defaults.
        }
        catch (InvalidOperationException)
        {
            // Interop unavailable (prerender or a test host) — same fallback.
        }

        Snapshot();
        _shell.Changed += OnShellChanged;
    }

    private void Apply(IReadOnlyDictionary<string, string> stored)
    {
        if (stored.TryGetValue(ThemeKey, out var theme)
            && Enum.TryParse<ThemeMode>(theme, ignoreCase: true, out var mode))
        {
            _shell.SetThemeMode(mode);
        }

        if (stored.TryGetValue(LocaleKey, out var locale))
        {
            _shell.SetLocale(locale);
        }

        if (stored.TryGetValue(BilingualKey, out var bilingual) && bool.TryParse(bilingual, out var enabled))
        {
            _shell.SetHelpBilingual(enabled);
        }
    }

    private void Snapshot()
    {
        _lastTheme = _shell.ThemeMode.ToString();
        _lastLocale = _shell.Locale;
        _lastBilingual = _shell.HelpBilingual.ToString();
    }

    private void OnShellChanged() => _ = PersistAsync();

    private async Task PersistAsync()
    {
        if (_module is null)
        {
            return;
        }

        try
        {
            if (_shell.ThemeMode.ToString() is var theme && theme != _lastTheme)
            {
                _lastTheme = theme;
                await _module.InvokeVoidAsync("write", ThemeKey, theme);
            }

            if (_shell.Locale != _lastLocale)
            {
                _lastLocale = _shell.Locale;
                await _module.InvokeVoidAsync("write", LocaleKey, _shell.Locale);
            }

            if (_shell.HelpBilingual.ToString() is var bilingual && bilingual != _lastBilingual)
            {
                _lastBilingual = bilingual;
                await _module.InvokeVoidAsync("write", BilingualKey, bilingual);
            }
        }
        catch (JSException)
        {
            // Losing a preference write is not worth failing a render over.
        }
    }

    public async ValueTask DisposeAsync()
    {
        _shell.Changed -= OnShellChanged;

        if (_module is not null)
        {
            try
            {
                await _module.DisposeAsync();
            }
            catch (JSDisconnectedException)
            {
                // The page is going away; nothing to release.
            }

            _module = null;
        }
    }
}
