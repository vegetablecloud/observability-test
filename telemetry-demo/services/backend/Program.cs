// backend – C# ASP.NET Core API med affärslogiken.
// En fråga: kvotkontroll (Postgres) -> ai-chat (LangGraph-agenten) -> spara konversationen (Postgres).
// Agenten anropar i sin tur rag-api och algorithm som verktyg.
//
// Det här är ALLT som krävs för att en .NET-tjänst ska bli observerbar:
//   1. AddOpenTelemetry() med tracing + metrics + logs
//   2. UseOtlpExporter() – skickar allt (push) till OTEL_EXPORTER_OTLP_ENDPOINT
//   3. Resource: service.name/version + deployment.environment.name (via env)
// Trace context (W3C traceparent) propageras automatiskt i HttpClient-anrop.

using System.Diagnostics;
using System.Diagnostics.Metrics;
using System.Text.Json;
using Npgsql;
using OpenTelemetry;
using OpenTelemetry.Logs;
using OpenTelemetry.Metrics;
using OpenTelemetry.Resources;
using OpenTelemetry.Trace;

var builder = WebApplication.CreateBuilder(args);
var serviceName = builder.Configuration["OTEL_SERVICE_NAME"] ?? "backend";

// ---- OpenTelemetry --------------------------------------------------------
builder.Services.AddOpenTelemetry()
    .ConfigureResource(r => r.AddService(serviceName, serviceVersion: "1.4.0"))
    .WithTracing(t => t
        .AddSource(Telemetry.Source.Name)       // våra egna spans
        .AddAspNetCoreInstrumentation()         // inkommande HTTP
        .AddHttpClientInstrumentation()         // utgående HTTP (+ traceparent)
        .AddNpgsql())                           // SQL-spans mot Postgres
    .WithMetrics(m => m
        .AddMeter(Telemetry.Meter.Name)         // våra egna metrics
        .AddAspNetCoreInstrumentation()         // http.server.request.duration m.fl.
        .AddHttpClientInstrumentation()         // http.client.request.duration
        .AddRuntimeInstrumentation()            // GC, threadpool, heap
        .AddMeter("Npgsql")                     // connection pool m.m.
        .SetExemplarFilter(ExemplarFilterType.TraceBased)) // exemplars -> klick från metric till trace
    .WithLogging(l => { }, o => o.IncludeFormattedMessage = true)
    .UseOtlpExporter();                         // PUSH till Collectorn (OTLP/gRPC 4317)

// ---- Beroenden ------------------------------------------------------------
builder.Services.AddHttpClient("ai-chat", c =>
{
    c.BaseAddress = new Uri(builder.Configuration["AI_CHAT_URL"] ?? "http://ai-chat:8080");
    c.Timeout = TimeSpan.FromSeconds(20);
});
builder.Services.AddSingleton(NpgsqlDataSource.Create(
    builder.Configuration["POSTGRES_CONNECTION"] ?? "Host=postgres;Username=demo;Password=demo;Database=demo"));

var app = builder.Build();
const int QuotaPerHour = 500;
var badCardinality = string.Equals(app.Configuration["BAD_CARDINALITY"], "true", StringComparison.OrdinalIgnoreCase);

_ = Task.Run(() => Db.EnsureSchemaAsync(app.Services.GetRequiredService<NpgsqlDataSource>(), app.Logger));

app.MapGet("/health", () => Results.Ok(new { ok = true }));

app.MapPost("/api/ask", async (AskRequest req, IHttpClientFactory http, NpgsqlDataSource db, ILogger<Program> log) =>
{
    var sw = Stopwatch.StartNew();
    var span = Activity.Current;
    // Höga cardinality-värden (user.id) hör hemma i TRACES och LOGS – inte som metric-labels.
    span?.SetTag("user.id", req.UserId);
    // user.email är PII – Collectorn redigerar bort den innan lagring (se otel-collector/config.yaml)
    span?.SetTag("user.email", req.UserEmail);
    log.LogInformation("ask_received user={UserEmail} chars={Chars}", req.UserEmail, req.Question.Length);

    string outcome = "ok", intent = "unknown";
    var conversationId = Guid.NewGuid().ToString("N")[..16];
    span?.SetTag("gen_ai.conversation.id", conversationId);
    try
    {
        // 1) Affärsregel: max antal frågor per användare och timme – egen span runt ett affärssteg
        using (var quota = Telemetry.Source.StartActivity("check quota"))
        {
            await using var cmd = db.CreateCommand(
                "SELECT count(*) FROM conversations WHERE user_id = $1 AND created_at > now() - interval '1 hour'");
            cmd.Parameters.AddWithValue(req.UserId ?? "anonymous");
            var used = (long)(await cmd.ExecuteScalarAsync() ?? 0L);
            quota?.SetTag("app.quota.used", used);
            quota?.SetTag("app.quota.limit", QuotaPerHour);
            if (used >= QuotaPerHour)
            {
                outcome = "quota_exceeded";
                quota?.SetStatus(ActivityStatusCode.Error, "quota exceeded");
                log.LogWarning("quota_exceeded used={Used} limit={Limit}", used, QuotaPerHour);
                return Results.Problem("quota exceeded", statusCode: 429);
            }
        }

        // 2) AI-chatten: LangGraph-agenten väljer själv verktyg (rag-api, algorithm)
        using var chatRes = await http.CreateClient("ai-chat").PostAsJsonAsync("/chat",
            new { question = req.Question, conversation_id = conversationId });
        if (!chatRes.IsSuccessStatusCode)
        {
            outcome = "ai_error";
            log.LogError("ai_chat_failed status={Status}", (int)chatRes.StatusCode);
            return Results.Problem("ai-chat failed", statusCode: 502);
        }
        var chat = (await chatRes.Content.ReadFromJsonAsync<ChatResponse>())!;
        intent = chat.Intent;
        span?.SetTag("app.intent", intent);
        span?.SetTag("agent.steps", chat.Steps.GetArrayLength());

        // 3) Spara konversationen
        using (var persist = Telemetry.Source.StartActivity("persist conversation"))
        {
            await using var cmd = db.CreateCommand(
                "INSERT INTO conversations (user_id, question, intent, answer, trace_id) VALUES ($1, $2, $3, $4, $5)");
            cmd.Parameters.AddWithValue(req.UserId ?? "anonymous");
            cmd.Parameters.AddWithValue(req.Question);
            cmd.Parameters.AddWithValue(intent);
            cmd.Parameters.AddWithValue(chat.Answer);
            cmd.Parameters.AddWithValue(span?.TraceId.ToString() ?? "");
            await cmd.ExecuteNonQueryAsync();
        }

        log.LogInformation("ask_completed intent={Intent} steps={Steps} ms={Ms}", intent, chat.Steps.GetArrayLength(), sw.ElapsedMilliseconds);
        return Results.Ok(new { answer = chat.Answer, intent, conversationId, sources = chat.Sources, steps = chat.Steps, tools = chat.Tools, usage = chat.Usage });
    }
    catch (Exception ex)
    {
        outcome = "exception";
        log.LogError(ex, "ask_failed");
        return Results.Problem("unexpected error", statusCode: 500);
    }
    finally
    {
        // Labels: få och stabila. BAD_CARDINALITY=true visar vad som händer annars.
        var tags = new TagList { { "app.intent", intent }, { "outcome", outcome } };
        if (badCardinality)
        {
            tags.Add("user_id", req.UserId);
            tags.Add("request_id", Guid.NewGuid().ToString("N")[..12]);
        }
        Telemetry.AskRequests.Add(1, tags);
        Telemetry.AskDuration.Record(sw.Elapsed.TotalSeconds, new TagList { { "app.intent", intent }, { "outcome", outcome } });
    }
});

app.MapGet("/api/history", async (NpgsqlDataSource db) =>
{
    await using var cmd = db.CreateCommand(
        "SELECT created_at, user_id, question, intent, trace_id FROM conversations ORDER BY id DESC LIMIT 20");
    await using var r = await cmd.ExecuteReaderAsync();
    var rows = new List<object>();
    while (await r.ReadAsync())
        rows.Add(new { createdAt = r.GetDateTime(0), userId = r.GetString(1), question = r.GetString(2), intent = r.GetString(3), traceId = r.GetString(4) });
    return Results.Ok(rows);
});

app.Run();

static class Telemetry
{
    public static readonly ActivitySource Source = new("Backend");
    public static readonly Meter Meter = new("Backend", "1.4.0");
    public static readonly Counter<long> AskRequests = Meter.CreateCounter<long>("app.ask.requests", "{request}", "Antal frågor per intent och utfall");
    public static readonly Histogram<double> AskDuration = Meter.CreateHistogram<double>("app.ask.duration", "s", "Total tid för en fråga",
        advice: new InstrumentAdvice<double> { HistogramBucketBoundaries = [0.1, 0.25, 0.5, 0.75, 1, 1.5, 2, 3, 4, 6, 10] });
}

static class Db
{
    public static async Task EnsureSchemaAsync(NpgsqlDataSource db, ILogger log)
    {
        for (var attempt = 1; attempt <= 30; attempt++)
        {
            try
            {
                await using var cmd = db.CreateCommand("""
                    CREATE TABLE IF NOT EXISTS conversations (
                      id BIGSERIAL PRIMARY KEY,
                      created_at TIMESTAMP NOT NULL DEFAULT now(),
                      user_id TEXT NOT NULL, question TEXT NOT NULL, intent TEXT NOT NULL,
                      answer TEXT NOT NULL, trace_id TEXT NOT NULL)
                    """);
                await cmd.ExecuteNonQueryAsync();
                log.LogInformation("db_schema_ready");
                return;
            }
            catch (Exception ex)
            {
                log.LogWarning("db_not_ready attempt={Attempt} error={Error}", attempt, ex.GetType().Name);
                await Task.Delay(2000);
            }
        }
    }
}

record AskRequest(string Question, string? UserId, string? UserEmail);
record ChatResponse(string Answer, string Intent, JsonElement Sources, JsonElement Steps, JsonElement Tools, JsonElement Usage);
