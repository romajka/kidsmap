param([Parameter(Mandatory=$true)][ValidatePattern('^[a-z0-9]+$')][string]$StageName)
$ErrorActionPreference='Stop'
$m13Repo='C:\kidsmap'
$m13Scratch=Join-Path $m13Repo '.tmp\m13-full-r1'
$m13Stage=Join-Path $m13Repo ('docs\qa\module13-repair-2026-10-19-pc-r1\stages\'+$StageName)
if (Test-Path (Join-Path $m13Stage 'applied.json')) { throw 'Already applied' }
function M13Hash([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
$m13Snapshot=Get-Content -LiteralPath (Join-Path $m13Scratch 'expected-source.json') -Raw | ConvertFrom-Json
$m13Metadata=Get-Content -LiteralPath (Join-Path $m13Stage 'candidate-manifest.json') -Raw | ConvertFrom-Json
foreach ($m13Property in $m13Snapshot.sources.PSObject.Properties) {
 if ((M13Hash (Join-Path $m13Repo $m13Property.Name)) -ne $m13Property.Value) { throw 'Unexpected source change' }
}
foreach ($m13Property in $m13Metadata.PSObject.Properties) {
 $m13Destination=[IO.Path]::GetFullPath((Join-Path $m13Repo $m13Property.Name))
 if (-not $m13Destination.StartsWith($m13Repo+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Outside repository' }
 if ($null -ne $m13Property.Value.before) {
  if ((M13Hash $m13Destination) -ne $m13Property.Value.before) { throw 'Entry mismatch' }
 } elseif (Test-Path -LiteralPath $m13Destination) { throw 'New path exists' }
 if ((M13Hash (Join-Path (Join-Path $m13Stage 'candidate') $m13Property.Name)) -ne $m13Property.Value.after) { throw 'Candidate mismatch' }
}
& git -C $m13Repo apply --check (Join-Path $m13Stage 'implemented.diff')
if ($LASTEXITCODE -ne 0) { throw 'Patch check failed' }
foreach ($m13Property in $m13Metadata.PSObject.Properties) {
 $m13Destination=Join-Path $m13Repo $m13Property.Name
 [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($m13Destination)) | Out-Null
 $m13Bytes=[IO.File]::ReadAllBytes((Join-Path (Join-Path $m13Stage 'candidate') $m13Property.Name))
 $m13Mode=if (Test-Path -LiteralPath $m13Destination) { [IO.FileMode]::Open } else { [IO.FileMode]::CreateNew }
 $m13Stream=[IO.FileStream]::new($m13Destination,$m13Mode,[IO.FileAccess]::Write,[IO.FileShare]::ReadWrite)
 try { $m13Stream.Position=0; $m13Stream.Write($m13Bytes,0,$m13Bytes.Length); if ($m13Stream.Length -ne $m13Bytes.Length) { $m13Stream.SetLength($m13Bytes.Length) }; $m13Stream.Flush($true) } finally { $m13Stream.Dispose() }
 if ((M13Hash $m13Destination) -ne $m13Property.Value.after) { throw 'Written hash mismatch' }
 $m13Snapshot.sources | Add-Member -MemberType NoteProperty -Name $m13Property.Name -Value $m13Property.Value.after -Force
}
$m13Encoding=[Text.UTF8Encoding]::new($false)
$m13Json=$m13Snapshot | ConvertTo-Json -Depth 8
[IO.File]::WriteAllText((Join-Path $m13Scratch 'expected-source.json'),$m13Json,$m13Encoding)
[IO.File]::WriteAllText((Join-Path $m13Stage 'source-applied.json'),$m13Json,$m13Encoding)
[IO.File]::WriteAllText((Join-Path $m13Stage 'applied.json'),(@{files=$m13Metadata;apply_check_exit=0;native_windows_write=$true} | ConvertTo-Json -Depth 8),$m13Encoding)
Write-Output ('Applied and hash-verified module13 stage '+$StageName)
