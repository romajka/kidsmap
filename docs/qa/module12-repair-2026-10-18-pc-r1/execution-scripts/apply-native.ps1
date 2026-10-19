param([Parameter(Mandatory=$true)][ValidatePattern('^[a-z0-9]+$')][string]$StageName)
$ErrorActionPreference='Stop'
$m12Repo='C:\kidsmap'
$m12Scratch=Join-Path $m12Repo '.tmp\m12-full-r1'
$m12Stage=Join-Path $m12Repo ('docs\qa\module12-repair-2026-10-18-pc-r1\stages\'+$StageName)
if (Test-Path (Join-Path $m12Stage 'applied.json')) { throw 'Already applied' }
function M12Hash([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
$m12Snapshot=Get-Content -LiteralPath (Join-Path $m12Scratch 'expected-source.json') -Raw | ConvertFrom-Json
$m12Metadata=Get-Content -LiteralPath (Join-Path $m12Stage 'candidate-manifest.json') -Raw | ConvertFrom-Json
foreach ($m12Property in $m12Snapshot.sources.PSObject.Properties) {
 if ((M12Hash (Join-Path $m12Repo $m12Property.Name)) -ne $m12Property.Value) { throw 'Unexpected source change' }
}
foreach ($m12Property in $m12Metadata.PSObject.Properties) {
 $m12Destination=[IO.Path]::GetFullPath((Join-Path $m12Repo $m12Property.Name))
 if (-not $m12Destination.StartsWith($m12Repo+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Outside repository' }
 if ($null -ne $m12Property.Value.before) {
  if ((M12Hash $m12Destination) -ne $m12Property.Value.before) { throw 'Entry mismatch' }
 } elseif (Test-Path -LiteralPath $m12Destination) { throw 'New path exists' }
 if ((M12Hash (Join-Path (Join-Path $m12Stage 'candidate') $m12Property.Name)) -ne $m12Property.Value.after) { throw 'Candidate mismatch' }
}
& git -C $m12Repo apply --check (Join-Path $m12Stage 'implemented.diff')
if ($LASTEXITCODE -ne 0) { throw 'Patch check failed' }
foreach ($m12Property in $m12Metadata.PSObject.Properties) {
 $m12Destination=Join-Path $m12Repo $m12Property.Name
 [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($m12Destination)) | Out-Null
 $m12Bytes=[IO.File]::ReadAllBytes((Join-Path (Join-Path $m12Stage 'candidate') $m12Property.Name))
 $m12Mode=if (Test-Path -LiteralPath $m12Destination) { [IO.FileMode]::Open } else { [IO.FileMode]::CreateNew }
 $m12Stream=[IO.FileStream]::new($m12Destination,$m12Mode,[IO.FileAccess]::Write,[IO.FileShare]::ReadWrite)
 try { $m12Stream.Position=0; $m12Stream.Write($m12Bytes,0,$m12Bytes.Length); if ($m12Stream.Length -ne $m12Bytes.Length) { $m12Stream.SetLength($m12Bytes.Length) }; $m12Stream.Flush($true) } finally { $m12Stream.Dispose() }
 if ((M12Hash $m12Destination) -ne $m12Property.Value.after) { throw 'Written hash mismatch' }
 $m12Snapshot.sources | Add-Member -MemberType NoteProperty -Name $m12Property.Name -Value $m12Property.Value.after -Force
}
$m12Encoding=[Text.UTF8Encoding]::new($false)
$m12Json=$m12Snapshot | ConvertTo-Json -Depth 8
[IO.File]::WriteAllText((Join-Path $m12Scratch 'expected-source.json'),$m12Json,$m12Encoding)
[IO.File]::WriteAllText((Join-Path $m12Stage 'source-applied.json'),$m12Json,$m12Encoding)
[IO.File]::WriteAllText((Join-Path $m12Stage 'applied.json'),(@{files=$m12Metadata;apply_check_exit=0;native_windows_write=$true} | ConvertTo-Json -Depth 8),$m12Encoding)
Write-Output ('Applied and hash-verified module12 stage '+$StageName)
