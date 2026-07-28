# Per-repo fleet start config for ring-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'ring-mcp'
    BackendPort  = 10729
    FrontendPort = 10728
    HealthPath   = '/health'
    WebRoot      = 'D:\Dev\repos\ring-mcp\web_sota'
    Backend = @{
        Kind          = 'uvicorn'
        UvicornTarget = 'ring_mcp.http_server:app'
        SyncExtras    = @('dev')
        Env           = @{ WEB_PORT = '10729' }
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
