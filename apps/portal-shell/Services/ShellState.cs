using PortalShell.Models;

namespace PortalShell.Services;

public sealed class ShellState
{
    private readonly ITokenReferenceBroker _tokenReferenceBroker;
    private readonly ShellOptions _options;

    public ShellState(AuthDemoContext auth, ITokenReferenceBroker tokenReferenceBroker, ShellOptions options)
    {
        Auth = auth;
        _tokenReferenceBroker = tokenReferenceBroker;
        _options = options;
    }

    public static IReadOnlyList<string> Sites { get; } = ["lu", "de", "be", "es", "all"];

    public static IReadOnlyList<string> Locales { get; } =
        ["en-LU", "fr-LU", "de-DE", "nl-BE", "es-ES"];

    public IReadOnlyList<ShellNavItem> NavigationItems { get; } =
    [
        // Daily operations
        new("Command Center", "command-center", null, "PlantManager", "⌂", "Daily operations"),
        new("Operations", "operations", null, "PlantManager", "◫", "Daily operations"),
        new("Furnace Health", "furnace-health", "lining-forecast", "FurnaceOperator", "◉", "Daily operations"),
        new("Energy Optimization", "energy-optimization", "spot-price-schedule", "EnergyManager", "ϟ", "Daily operations"),
        new("Quality", "quality", "batches", "QualityEngineer", "✓", "Daily operations"),
        // Insight & governance
        new("Executive Overview", "executive-overview", null, "Executive", "▤", "Insight & governance"),
        new("Sustainability", "sustainability-compliance", "emissions-ledger", "SustainabilityOfficer", "♧", "Insight & governance"),
        new("Knowledge Hub", "knowledge-hub", "procedures", "KnowledgeEngineer", "⌕", "Insight & governance"),
        new("Dashboards", "dashboards", "collections", "PlantManager", "▦", "Insight & governance"),
        // Platform & reference
        new("Device Operations", "device-operations", "fleet", "PlatformOps", "◈", "Platform & reference"),
        new("Platform Ops", "platform-ops", "capacity", "PlatformOps", "⚙", "Platform & reference"),
        new("AxelorMetal", "company-website", "home", "PlantManager", "◇", "Platform & reference")
    ];

    public event Action? Changed;

    public AuthDemoContext Auth { get; }

    public ThemeMode ThemeMode { get; private set; } = ThemeMode.System;

    public string Locale { get; private set; } = "en-LU";

    public string Site { get; private set; } = "lu";

    public string Section { get; private set; } = "command-center";

    public string? SubView { get; private set; }

    public string ActivePersona { get; private set; } = "PlantManager";

    public string PrimaryPersona { get; private set; } = "PlantManager";

    public string BffBaseUrl => _options.BffBaseUrl;

    public bool DemoMode { get; private set; } = true;

    public bool HelpBilingual { get; private set; }

    public ToastNotification? LastToast { get; private set; }

    public void ApplyRoute(string? site, string? section, string? subView)
    {
        Site = NormalizeSite(site);
        var target = NavigationItems.FirstOrDefault(item =>
            string.Equals(item.Section, section, StringComparison.OrdinalIgnoreCase))
            ?? NavigationItems[0];

        Section = target.Section;
        SubView = string.IsNullOrWhiteSpace(subView) ? target.DefaultSubView : subView;
        ActivePersona = target.Persona;
        Notify();
    }

    public void SetSite(string site)
    {
        Site = NormalizeSite(site);
        Notify();
    }

    public void SetLocale(string locale)
    {
        if (Locales.Contains(locale, StringComparer.OrdinalIgnoreCase))
        {
            Locale = locale;
            Notify();
        }
    }

    public void ToggleDemoMode()
    {
        DemoMode = !DemoMode;
        PublishToast(
            DemoMode ? "info" : "warning",
            DemoMode
                ? "Demo mode is active; all data is synthetic."
                : "Live mode remains a shell state until authenticated BFF integration is configured.");
    }

    public void CycleTheme()
    {
        ThemeMode = ThemeMode switch
        {
            ThemeMode.System => ThemeMode.Light,
            ThemeMode.Light => ThemeMode.Dark,
            _ => ThemeMode.System
        };
        Notify();
    }

    public void PublishToast(string severity, string message)
    {
        LastToast = new ToastNotification(severity, message);
        Notify();
    }

    public void SetHelpBilingual(bool value)
    {
        HelpBilingual = value;
        Notify();
    }

    public string RouteFor(string section, string? subView)
    {
        var route = $"/{Site}/{section}";
        return string.IsNullOrWhiteSpace(subView) ? route : $"{route}/{subView}";
    }

    public string RouteForPersona(string persona)
    {
        var item = NavigationItems.FirstOrDefault(candidate =>
            string.Equals(candidate.Persona, persona, StringComparison.OrdinalIgnoreCase))
            ?? NavigationItems[0];
        return RouteFor(item.Section, item.DefaultSubView);
    }

    public void SetPrimaryPersona(string persona)
    {
        PrimaryPersona = persona;
        Notify();
    }

    public AnalyticsBridgeContext ToAnalyticsBridgeContext() =>
        new(
            ThemeMode.ToString().ToLowerInvariant(),
            Locale,
            ActivePersona,
            Site,
            DemoMode,
            _tokenReferenceBroker.Current.Value,
            "1.0",
            new AnalyticsNavigation(Section, SubView, Site),
            _options.BffBaseUrl,
            Auth.PermittedActions,
            HelpBilingual);

    private static string NormalizeSite(string? site) =>
        Sites.Contains(site ?? string.Empty, StringComparer.OrdinalIgnoreCase)
            ? site!.ToLowerInvariant()
            : "lu";

    private void Notify() => Changed?.Invoke();
}
