$ErrorActionPreference = 'Stop'
$model = 'bge-m3'
$endpoint = if ($env:OLLAMA_EMBEDDING_URL) { $env:OLLAMA_EMBEDDING_URL } else { 'http://127.0.0.1:11434/api/embed' }
$rows = @()
Get-ChildItem 'outputs/rag/*_chunks.jsonl' | Sort-Object Name | ForEach-Object {
    Get-Content -LiteralPath $_.FullName -Encoding UTF8 | Where-Object { $_.Trim() } | ForEach-Object {
        $item = $_ | ConvertFrom-Json
        $text = [string]$item.text
        $offset = 0
        while ($offset -lt [Math]::Max($text.Length, 1)) {
            $part = if ($text.Length -gt $offset + 1200) { $text.Substring($offset, 1200) } else { $text.Substring($offset) }
            $chunkId = if ($offset -eq 0) { $item.chunk_id } else { "$($item.chunk_id)-$([int]($offset / 1200))" }
            $body = @{ model = $model; prompt = $part } | ConvertTo-Json -Compress
            $response = Invoke-RestMethod -Uri $endpoint -Method Post -ContentType 'application/json' -Body $body -TimeoutSec 120
            if (-not $response.embedding -or $response.embedding.Count -ne 1024) { throw "Unexpected embedding dimension at $chunkId" }
            $rows += [PSCustomObject]@{ chunk_id=$chunkId; content=$part; metadata=$item.metadata; embedding=$response.embedding; model=$model; dimension=1024; source_sha256=$item.metadata.source_sha256 }
            $offset += 1200
        }
    }
}
$rows | ForEach-Object { $_ | ConvertTo-Json -Compress -Depth 20 } | Set-Content 'outputs/rag/embeddings_v2.jsonl' -Encoding UTF8
@{ status='completed'; model=$model; dimension=1024; count=$rows.Count; output='outputs/rag/embeddings_v2.jsonl'; endpoint_type='ollama' } | ConvertTo-Json | Set-Content 'outputs/rag/embedding_metadata.json' -Encoding UTF8
Write-Output "embeddings_generated count=$($rows.Count) dimension=1024"
