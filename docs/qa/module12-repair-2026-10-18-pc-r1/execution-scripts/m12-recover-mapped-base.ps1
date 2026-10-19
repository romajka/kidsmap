$ErrorActionPreference='Stop'
$m12Root='C:\kidsmap'
$m12Stage=Join-Path $m12Root 'docs\qa\module12-repair-2026-10-18-pc-r1\stages\beacon'
$m12Path=Join-Path $m12Root 'src\catalog\templates\base.html'
$m12Before=[IO.File]::ReadAllBytes((Join-Path $m12Stage 'entry-source\src\catalog\templates\base.html'))
$m12After=[IO.File]::ReadAllBytes((Join-Path $m12Stage 'candidate\src\catalog\templates\base.html'))
$m12Current=[IO.File]::ReadAllBytes($m12Path)
if ($m12Current.Length -ne $m12Before.Length) { throw 'Unexpected current length' }
for ($m12I=0;$m12I -lt $m12Current.Length;$m12I++) {
 $m12Expected=if ($m12I -lt $m12After.Length) { $m12After[$m12I] } else { $m12Before[$m12I] }
 if ($m12Current[$m12I] -ne $m12Expected) { throw 'Unexpected concurrent source bytes' }
}
$m12Stream=[IO.FileStream]::new($m12Path,[IO.FileMode]::Open,[IO.FileAccess]::Write,[IO.FileShare]::ReadWrite)
try { $m12Stream.Write($m12Before,0,$m12Before.Length);$m12Stream.Flush($true) } finally { $m12Stream.Dispose() }
$m12Metadata=Get-Content -LiteralPath (Join-Path $m12Stage 'candidate-manifest.json') -Raw | ConvertFrom-Json
if ((Get-FileHash -LiteralPath $m12Path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $m12Metadata.'src/catalog/templates/base.html'.before) { throw 'Restored hash mismatch' }
Write-Output 'Exact pre-stage base bytes restored after verified partial write; no foreign process touched.'
