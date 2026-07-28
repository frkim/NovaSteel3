using PortalShell.Models;

namespace PortalShell.Services;

public sealed class ShellState
{
    private readonly ITokenReferenceBroker _tokenReferenceBroker;
    private readonly ShellOptions _options;
    private readonly BffHealthService _bffHealth;

    public ShellState(
        AuthDemoContext auth,
        ITokenReferenceBroker tokenReferenceBroker,
        ShellOptions options,
        BffHealthService bffHealth)
    {
        Auth = auth;
        _tokenReferenceBroker = tokenReferenceBroker;
        _options = options;
        _bffHealth = bffHealth;
    }

    public static IReadOnlyList<string> Sites { get; } = ["lu", "de", "be", "es", "all"];

    public static IReadOnlyDictionary<string, string> SiteNames { get; } = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase)
    {
        ["lu"] = "LU - Moselle Integrated Works",
        ["de"] = "DE - Saarbrücken Steelworks",
        ["be"] = "BE - Liège Melt & Rolling Works",
        ["es"] = "ES - Asturias Long Products",
        ["all"] = "ALL - All sites",
    };

    public static string SiteLabel(string site) =>
        SiteNames.TryGetValue(site, out var label) ? label : site.ToUpperInvariant();

    public static IReadOnlyList<string> Locales { get; } =
        ["en-LU", "fr-LU", "de-DE", "nl-BE", "es-ES"];

    /// <summary>
    /// Human names for the demo personas, mirroring the persona registry the
    /// analytics MFE ships (<c>apps/analytics-mfe/src/personas.ts</c>). A jury
    /// remembers "Sofia Lindqvist" far better than "EnergyManager", and the
    /// Copilot question catalog already prefixes its questions with the same
    /// names, so the two surfaces must agree byte-for-byte.
    /// </summary>
    public static IReadOnlyDictionary<string, string> PersonaNames { get; } = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase)
    {
        ["PlantManager"] = "Marc Weber - Plant Manager",
        ["FurnaceOperator"] = "Elena Duarte - Furnace Operator",
        ["EnergyManager"] = "Sofia Lindqvist - Energy Manager",
        ["QualityEngineer"] = "Jens Bakker - Quality Engineer",
        ["SustainabilityOfficer"] = "Amina Haddad - Sustainability Officer",
        ["KnowledgeEngineer"] = "Pieter Claes - Knowledge Engineer",
        ["Executive"] = "Isabelle Moreau - Executive",
        ["PlatformOps"] = "Nils Andersen - Platform Ops",
    };

    public static string PersonaLabel(string persona) =>
        PersonaNames.TryGetValue(persona, out var label)
            ? label
            : System.Text.RegularExpressions.Regex.Replace(persona, "([a-z])([A-Z])", "$1 $2");

    /// <summary>
    /// The sections each persona actually works in.
    /// </summary>
    /// <remarks>
    /// Every role but the plant manager gets a narrowed workspace: showing an
    /// energy manager the device fleet or the quality engineer the capacity
    /// controls is noise that a demo jury reads as an undifferentiated menu.
    /// The plant manager is deliberately the cross-domain triage role, so the
    /// full menu stays available there — that is also the safe default for any
    /// persona this map does not cover.
    /// </remarks>
    private static readonly IReadOnlyDictionary<string, string[]> SectionsByPersona =
        new Dictionary<string, string[]>(StringComparer.OrdinalIgnoreCase)
        {
            ["FurnaceOperator"] = ["command-center", "operations", "furnace-health", "knowledge-hub"],
            ["EnergyManager"] = ["command-center", "energy-optimization", "sustainability-compliance", "dashboards"],
            ["QualityEngineer"] = ["command-center", "quality", "knowledge-hub", "dashboards"],
            ["SustainabilityOfficer"] =
                ["sustainability-compliance", "executive-overview", "dashboards", "proof-of-execution"],
            ["KnowledgeEngineer"] = ["operations", "quality", "knowledge-hub", "dashboards"],
            ["Executive"] =
            [
                "executive-overview",
                "sustainability-compliance",
                "dashboards",
                "proof-of-execution",
                "technical-requirements",
                "company-website",
            ],
            ["PlatformOps"] = ["command-center", "device-operations", "platform-ops", "dashboards"],
        };

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
        new("Proof of Execution", "proof-of-execution", "requirements", "PlantManager", "⎋", "Insight & governance"),
        new("Technical Requirements", "technical-requirements", "criteria", "PlantManager", "⌘", "Insight & governance"),
        // Platform & reference
        new("Device Operations", "device-operations", "fleet", "PlatformOps", "◈", "Platform & reference"),
        new("Platform Ops", "platform-ops", "capacity", "PlatformOps", "⚙", "Platform & reference"),
        new("AxelorMetal", "company-website", "home", "PlantManager", "◇", "Platform & reference")
    ];

    public event Action? Changed;

    /// <summary>
    /// The navigation the selected persona should see: their own sections plus
    /// whatever section is currently open, so a deep link (a proof badge, for
    /// example) can never strand the user on a page with no menu entry.
    /// Group headings are not modelled here — the layout emits a heading only
    /// when an item of that group survives the filter, so a group that empties
    /// out disappears with its items.
    /// </summary>
    public IReadOnlyList<ShellNavItem> VisibleNavigationItems
    {
        get
        {
            if (!SectionsByPersona.TryGetValue(PrimaryPersona, out var sections))
            {
                return NavigationItems;
            }

            return NavigationItems
                .Where(item =>
                    sections.Contains(item.Section, StringComparer.OrdinalIgnoreCase)
                    || string.Equals(item.Section, Section, StringComparison.OrdinalIgnoreCase))
                .ToArray();
        }
    }

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

    /// <summary>
    /// True while a cloud-mode switch is waiting for the BFF to identify itself.
    /// </summary>
    public bool BffProbeInFlight { get; private set; }

    /// <summary>
    /// What the BFF last told us about itself, or <c>null</c> before the first probe.
    /// </summary>
    public BffProbeResult? BffProbe { get; private set; }

    /// <summary>
    /// Flips between the demo data set and cloud mode. Existing callers are
    /// synchronous event handlers, so the probe is started here and completed in
    /// the background; the UI updates again when it lands.
    /// </summary>
    public void ToggleDemoMode() => _ = ToggleDemoModeAsync();

    /// <summary>
    /// Switching back to demo is instant. Switching to cloud mode asks the BFF
    /// who it is first: if nothing answers, the shell stays in demo mode rather
    /// than showing a CLOUD badge with no backend behind it.
    /// </summary>
    public async Task ToggleDemoModeAsync(CancellationToken cancellationToken = default)
    {
        if (!DemoMode)
        {
            DemoMode = true;
            BffProbeInFlight = false;
            PublishToast("info", "Demo mode is active: synthetic data set, demo controls visible.");
            return;
        }

        DemoMode = false;
        BffProbeInFlight = true;
        PublishToast("info", $"Cloud mode: contacting the NovaSteel BFF at {BffBaseUrl}\u2026");

        var probe = await _bffHealth.ProbeAsync(cancellationToken);
        BffProbe = probe;
        BffProbeInFlight = false;

        if (!probe.Reachable)
        {
            DemoMode = true;
            PublishToast(
                "warning",
                $"Cloud mode unavailable: {BffBaseUrl} did not answer ({probe.Detail}). Staying in demo mode.");
            return;
        }

        var descriptor = string.Join(
            " \u00b7 ",
            new[]
            {
                probe.Service,
                probe.ApiVersion is null ? null : $"API {probe.ApiVersion}",
                probe.Environment is null ? null : $"env {probe.Environment}",
                probe.AuthMode is null ? null : $"auth {probe.AuthMode}",
            }.Where(part => !string.IsNullOrWhiteSpace(part)));

        // The data set is synthetic in both modes by design; cloud mode is about
        // where the data comes from, not whether it describes a real plant.
        var dataNote = probe.DemoData
            ? "Every screen is now served by that backend. The data set stays synthetic by design."
            : "Every screen is now served by that backend.";

        PublishToast("success", $"Cloud mode: connected to {descriptor}. {dataNote}");
    }

    public void SetThemeMode(ThemeMode mode)
    {
        if (ThemeMode == mode)
        {
            return;
        }

        ThemeMode = mode;
        Notify();
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
