#:sdk Aspire.AppHost.Sdk@13.4.6

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

builder.Build().Run();
