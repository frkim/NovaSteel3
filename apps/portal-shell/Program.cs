using Microsoft.AspNetCore.Components.Web;
using Microsoft.AspNetCore.Components.WebAssembly.Hosting;
using PortalShell;
using PortalShell.Services;

var builder = WebAssemblyHostBuilder.CreateDefault(args);
builder.RootComponents.Add<App>("#app");
builder.RootComponents.Add<HeadOutlet>("head::after");

var bffBaseUrl = builder.Configuration["Bff:BaseUrl"] ?? builder.HostEnvironment.BaseAddress;
var capacityId = builder.Configuration["Bff:CapacityId"] ?? "cap-novasteel-demo-sc";
builder.Services.AddSingleton(new ShellOptions { BffBaseUrl = bffBaseUrl, CapacityId = capacityId });
builder.Services.AddScoped(_ => new HttpClient { BaseAddress = new Uri(bffBaseUrl) });
builder.Services.AddScoped<AuthDemoContext>();
builder.Services.AddScoped<ITokenReferenceBroker, DemoTokenReferenceBroker>();
builder.Services.AddScoped<CapacityService>();
builder.Services.AddScoped<CapacityState>();
builder.Services.AddScoped<ShellState>();

var clientId = builder.Configuration["AzureAd:ClientId"];
if (string.IsNullOrWhiteSpace(clientId))
{
    builder.Services.AddAuthorizationCore();
}
else
{
    builder.Services.AddMsalAuthentication(options =>
    {
        options.ProviderOptions.Authentication.ClientId = clientId;
        options.ProviderOptions.Authentication.Authority =
            builder.Configuration["AzureAd:Authority"] ?? "https://login.microsoftonline.com/common";
    });
}

await builder.Build().RunAsync();
