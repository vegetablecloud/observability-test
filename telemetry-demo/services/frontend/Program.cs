// frontend – C# ASP.NET Core som serverar chatt-UI:t och fungerar som BFF
// (backend-for-frontend). Här STARTAR varje trace: första spanen skapas när
// webbläsaren/loadgen anropar /ask, och trace_id följer sedan med hela vägen ner.

using System.Diagnostics;
using OpenTelemetry;
using OpenTelemetry.Metrics;
using OpenTelemetry.Resources;
using OpenTelemetry.Trace;

var builder = WebApplication.CreateBuilder(args);
var serviceName = builder.Configuration["OTEL_SERVICE_NAME"] ?? "frontend";

builder.Services.AddOpenTelemetry()
    .ConfigureResource(r => r.AddService(serviceName, serviceVersion: "2.1.0"))
    .WithTracing(t => t
        .AddAspNetCoreInstrumentation(o => o.Filter = ctx => ctx.Request.Path.StartsWithSegments("/ask")
                                                         || ctx.Request.Path.StartsWithSegments("/api"))
        .AddHttpClientInstrumentation())
    .WithMetrics(m => m
        .AddAspNetCoreInstrumentation()
        .AddHttpClientInstrumentation()
        .AddRuntimeInstrumentation()
        .SetExemplarFilter(ExemplarFilterType.TraceBased))
    .WithLogging(l => { }, o => o.IncludeFormattedMessage = true)
    .UseOtlpExporter();

builder.Services.AddHttpClient("backend", c =>
{
    c.BaseAddress = new Uri(builder.Configuration["BACKEND_URL"] ?? "http://backend:8080");
    c.Timeout = TimeSpan.FromSeconds(20);
});

var app = builder.Build();
var grafanaUrl = app.Configuration["GRAFANA_PUBLIC_URL"] ?? "http://localhost:3000";

app.UseDefaultFiles();
app.UseStaticFiles();

// Returnera trace_id till klienten så att UI:t kan länka direkt till tracen i Grafana.
app.Use(async (ctx, next) =>
{
    ctx.Response.OnStarting(() =>
    {
        if (Activity.Current is { } a) ctx.Response.Headers["x-trace-id"] = a.TraceId.ToString();
        return Task.CompletedTask;
    });
    await next();
});

app.MapGet("/config", () => Results.Ok(new { grafanaUrl }));

app.MapPost("/ask", async (HttpRequest request, IHttpClientFactory http, ILogger<Program> log) =>
{
    // Testare (och loadgen) märker sina anrop med x-test-run-id. Det blir ett attribut på
    // root-spanen, så dashboarden "Testflöde A→Ö" kan lista exakt en testkörnings traces.
    var testRun = request.Headers["x-test-run-id"].FirstOrDefault() ?? "manual";
    Activity.Current?.SetTag("test.run.id", testRun);
    using var body = new StreamContent(request.Body);
    body.Headers.ContentType = new("application/json");
    log.LogInformation("request_started route=/ask test_run={TestRun}", testRun);
    var sw = Stopwatch.StartNew();
    using var res = await http.CreateClient("backend").PostAsync("/api/ask", body);
    var content = await res.Content.ReadAsStringAsync();
    if (!res.IsSuccessStatusCode) log.LogWarning("backend_error status={Status} test_run={TestRun}", (int)res.StatusCode, testRun);
    log.LogInformation("response_sent status={Status} duration_ms={Ms}", (int)res.StatusCode, sw.ElapsedMilliseconds);
    return Results.Content(content, "application/json", statusCode: (int)res.StatusCode);
});

app.MapGet("/api/history", async (IHttpClientFactory http) =>
    Results.Content(await http.CreateClient("backend").GetStringAsync("/api/history"), "application/json"));

// Endast för demo: sätt ett chaos-läge i hela stacken. Varje tjänst reagerar på "sina" lägen
// och går till normal för alla andra, så att bara ett fel är aktivt åt gången.
string[] chaosTargets = (app.Configuration["CHAOS_TARGETS"]
    ?? "http://vllm-gemma:8000,http://vllm-embed:8000,http://rag-api:8080,http://algorithm:8080").Split(',');
app.MapPost("/demo/chaos/{mode}", async (string mode, IHttpClientFactory http, ILogger<Program> log) =>
{
    var client = http.CreateClient();
    var results = await Task.WhenAll(chaosTargets.Select(async t =>
    {
        try { using var r = await client.PostAsync($"{t}/chaos/{mode}", null); return $"{t}={(int)r.StatusCode}"; }
        catch (Exception e) { return $"{t}={e.GetType().Name}"; }
    }));
    log.LogWarning("chaos_mode_set mode={Mode} targets={Targets}", mode, string.Join(" ", results));
    return Results.Ok(new { mode, targets = results });
});

app.MapGet("/health", () => Results.Ok(new { ok = true }));

app.Run();
