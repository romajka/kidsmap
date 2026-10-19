$ErrorActionPreference = 'Stop'
$repo = 'C:\kidsmap'
$out = Join-Path $repo 'docs\qa\module11-repair-2026-10-18-pc-r1'
$scratch = Join-Path $repo '.tmp\m11-full-r1'
$stage = Join-Path $out 'stages\images'
if (Test-Path (Join-Path $stage 'applied.json')) { throw 'Stage already applied' }
$snapshot = Get-Content -LiteralPath (Join-Path $scratch 'expected-source.json') -Raw | ConvertFrom-Json
function HashBytes([string]$path) { (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() }
foreach ($property in $snapshot.sources.PSObject.Properties) {
    if ((HashBytes (Join-Path $repo $property.Name)) -ne $property.Value) { throw "Unexpected current source: $($property.Name)" }
}
$paths = @('src/catalog/services/seo.py','src/catalog/controllers/public_details.py','src/catalog/views.py','src/catalog/testcases/test_module11_images.py','src/catalog/templates/catalog/specialist_detail.html','src/catalog/templates/catalog/public_entity_detail.html')
$metadata = [ordered]@{}
foreach ($relative in $paths) {
    $destination = Join-Path $repo $relative
    $candidate = Join-Path (Join-Path $stage 'candidate') $relative
    $entry = Join-Path (Join-Path $stage 'entry-source') $relative
    $before = $null
    if (Test-Path -LiteralPath $entry) {
        $before = HashBytes $entry
        if ((HashBytes $destination) -ne $before) { throw "Entry mismatch: $relative" }
    } elseif (Test-Path -LiteralPath $destination) { throw "New path exists: $relative" }
    $metadata[$relative] = @{before=$before;after=(HashBytes $candidate)}
}
& git -C $repo apply --check (Join-Path $stage 'implemented.diff')
if ($LASTEXITCODE -ne 0) { throw 'Patch check failed' }
foreach ($relative in $paths) {
    $destination = Join-Path $repo $relative
    $bytes = [IO.File]::ReadAllBytes((Join-Path (Join-Path $stage 'candidate') $relative))
    $mode = if (Test-Path -LiteralPath $destination) { [IO.FileMode]::Open } else { [IO.FileMode]::CreateNew }
    $stream = [IO.FileStream]::new($destination,$mode,[IO.FileAccess]::Write,[IO.FileShare]::ReadWrite)
    try { $stream.Position=0; $stream.Write($bytes,0,$bytes.Length); $stream.SetLength($bytes.Length); $stream.Flush($true) } finally { $stream.Dispose() }
    if ((HashBytes $destination) -ne $metadata[$relative].after) { throw "Candidate mismatch: $relative" }
    $snapshot.sources | Add-Member -MemberType NoteProperty -Name $relative -Value $metadata[$relative].after -Force
}
$encoding = [Text.UTF8Encoding]::new($false)
$json = $snapshot | ConvertTo-Json -Depth 8
[IO.File]::WriteAllText((Join-Path $scratch 'expected-source.json'),$json,$encoding)
[IO.File]::WriteAllText((Join-Path $stage 'source-applied.json'),$json,$encoding)
[IO.File]::WriteAllText((Join-Path $stage 'applied.json'),(@{files=$metadata;apply_check_exit=0;native_windows_write=$true} | ConvertTo-Json -Depth 7),$encoding)
[IO.File]::WriteAllText((Join-Path $stage 'native-apply-note.md'),'WSL write_bytes failed EINVAL while opening first source. Before native application, every1057current source and each stage entry hash matched: no partial mutation. Applied exact6candidates using native Windows nontruncating shared-write FileStream, verified final hashes. No foreign process/config/runtime restart or file-attribute change. Git apply --check passed again.',$encoding)
$dep = Get-Content -LiteralPath (Join-Path $out 'evidence\dependency-repair.json') -Raw | ConvertFrom-Json
$dep | Add-Member -MemberType NoteProperty -Name isolated_worker_followup -Value 'Exact verified pypdf6.20.1 wheel installed into OWN app container CoW site-packages; isolated child Python does not inherit parent target. Shared image/foreign containers/host/prod unchanged.' -Force
[IO.File]::WriteAllText((Join-Path $out 'evidence\dependency-repair.json'),($dep | ConvertTo-Json -Depth 5),$encoding)
Write-Output 'Exact6image candidates applied and hash-verified natively; all prior sources preserved.'
