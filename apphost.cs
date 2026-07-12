#:sdk Aspire.AppHost.Sdk@13.4.6
#:package Aspire.Hosting.Python@13.4.6

#pragma warning disable ASPIRECERTIFICATES001

var builder = DistributedApplication.CreateBuilder(args);

var qdrant = builder.AddContainer("qdrant", "qdrant/qdrant")
    .WithContainerName("qdrant")
    .WithHttpEndpoint(port: 6333, targetPort: 6333, name: "http");

var n8n = builder.AddContainer("n8n", "docker.n8n.io/n8nio/n8n")
    .WithHttpEndpoint(port: 5678, targetPort: 5678, name: "http", isProxied: false)
    .WithEnvironment("NODE_TLS_REJECT_UNAUTHORIZED", "0")
    .WithEnvironment("N8N_PORT", "5678")
    .WithEnvironment("N8N_PROTOCOL", "http")
    .WithContainerName("n8n");

// apphost.cs runs in the devcontainer, which CAN reach the Mac via Docker Desktop's
// fixed host gateway (e.g. 192.168.65.254 — stable, NOT your changing LAN IP).
// Resolve it here and hand it to the container so host.docker.internal works through
// the docker-in-docker layer without hardcoding anything.
string hostGatewayMapping = "host.docker.internal:host-gateway"; // fallback
try
{
    var addrs = System.Net.Dns.GetHostAddresses("host.docker.internal");
    var hostIp = System.Array.Find(addrs, a => a.AddressFamily == System.Net.Sockets.AddressFamily.InterNetwork);
    if (hostIp != null)
        hostGatewayMapping = $"host.docker.internal:{hostIp}";
}
catch { /* devcontainer couldn't resolve it either; keep the host-gateway fallback */ }

var openwebui = builder.AddContainer("openwebui", "ghcr.io/open-webui/open-webui", "main")
    .WithContainerName("openwebui")
    .WithHttpEndpoint(port: 8080, targetPort: 8080, name: "http", isProxied: false)
    .WithEnvironment("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
    .WithEnvironment("WEBUI_AUTH", "false")  // optional: skip login for local dev
    // Point host.docker.internal at the devcontainer's route to the Mac (resolved above):
    .WithContainerRuntimeArgs("--add-host=" + hostGatewayMapping)
    .WithBindMount("openwebui_data", "/app/backend/data", isReadOnly: false);

// Python URL-shortener demo (FastAPI on Uvicorn), served from ./src.
// Aspire provisions src/.venv from src/requirements.txt, which installs the
// project plus its dev/test tooling from pyproject.toml.
builder.AddUvicornApp("shortener", "src", "app.main:app")
    .WithExternalHttpEndpoints()
    .WithHttpHealthCheck("/health");

// On-demand pytest runner for the shortener suite. It does not auto-start:
// click "Start" on the "shortener-tests" resource in the Aspire dashboard to
// run `python -m pytest` (coverage gate included) against ./src.
builder.AddPythonModule("shortener-tests", "src", "pytest")
    .WithExplicitStart();

builder.Build().Run();
