param(
    [int]$Port = 8000,
    [string]$Root = "."
)

$ErrorActionPreference = "Stop"

$resolvedRoot = (Resolve-Path $Root).Path
$prefix = "http://localhost:$Port/"

$mimeTypes = @{
    ".html" = "text/html; charset=utf-8"
    ".htm"  = "text/html; charset=utf-8"
    ".js"   = "application/javascript; charset=utf-8"
    ".mjs"  = "application/javascript; charset=utf-8"
    ".css"  = "text/css; charset=utf-8"
    ".json" = "application/json; charset=utf-8"
    ".txt"  = "text/plain; charset=utf-8"
    ".svg"  = "image/svg+xml"
    ".png"  = "image/png"
    ".jpg"  = "image/jpeg"
    ".jpeg" = "image/jpeg"
    ".gif"  = "image/gif"
    ".ico"  = "image/x-icon"
    ".webp" = "image/webp"
    ".map"  = "application/json; charset=utf-8"
}

$listener = [System.Net.HttpListener]::new()
$listener.Prefixes.Add($prefix)

try {
    $listener.Start()
    Write-Host "Serving $resolvedRoot at $prefix"
    Write-Host "Press Ctrl+C to stop."

    while ($listener.IsListening) {
        $context = $listener.GetContext()
        $request = $context.Request
        $response = $context.Response

        try {
            $urlPath = [System.Uri]::UnescapeDataString($request.Url.AbsolutePath)
            if ([string]::IsNullOrWhiteSpace($urlPath) -or $urlPath -eq "/") {
                $urlPath = "/index.html"
            }

            $relativePath = $urlPath.TrimStart('/').Replace('/', [IO.Path]::DirectorySeparatorChar)
            $candidatePath = Join-Path $resolvedRoot $relativePath
            $fullPath = [IO.Path]::GetFullPath($candidatePath)

            # Prevent path traversal outside the root folder.
            if (-not $fullPath.StartsWith($resolvedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
                $response.StatusCode = 403
                $bytes = [Text.Encoding]::UTF8.GetBytes("403 Forbidden")
                $response.ContentType = "text/plain; charset=utf-8"
                $response.OutputStream.Write($bytes, 0, $bytes.Length)
                continue
            }

            if ((Test-Path $fullPath) -and -not (Get-Item $fullPath).PSIsContainer) {
                $ext = [IO.Path]::GetExtension($fullPath).ToLowerInvariant()
                $contentType = if ($mimeTypes.ContainsKey($ext)) { $mimeTypes[$ext] } else { "application/octet-stream" }

                $bytes = [IO.File]::ReadAllBytes($fullPath)
                $response.StatusCode = 200
                $response.ContentType = $contentType
                $response.ContentLength64 = $bytes.Length
                $response.OutputStream.Write($bytes, 0, $bytes.Length)
            }
            else {
                $response.StatusCode = 404
                $bytes = [Text.Encoding]::UTF8.GetBytes("404 Not Found")
                $response.ContentType = "text/plain; charset=utf-8"
                $response.OutputStream.Write($bytes, 0, $bytes.Length)
            }
        }
        catch {
            $response.StatusCode = 500
            $bytes = [Text.Encoding]::UTF8.GetBytes("500 Internal Server Error")
            $response.ContentType = "text/plain; charset=utf-8"
            $response.OutputStream.Write($bytes, 0, $bytes.Length)
        }
        finally {
            $response.OutputStream.Close()
        }
    }
}
finally {
    if ($listener.IsListening) {
        $listener.Stop()
    }
    $listener.Close()
}