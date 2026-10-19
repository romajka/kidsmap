$ErrorActionPreference = 'Stop'
Set-Location 'C:\kidsmap'
$out = 'docs/qa/site-qa01-resume-2026-10-18-pc-r1'
$plan = 'docs/qa/site-qa01-recheck-2026-10-18-pc-r1'
function HashFile($path) {
    if (Test-Path -LiteralPath $path -PathType Leaf) { return (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLower() }
    return $null
}
$baseline = Get-Content "$plan/source-entry.json" -Raw | ConvertFrom-Json
$manifest = Get-Content "$plan/candidate-manifest.json" -Raw | ConvertFrom-Json
$sourceMismatch = @($baseline.sources.PSObject.Properties | Where-Object { (HashFile $_.Name) -ne $_.Value } | ForEach-Object Name)
$priorMissing = @()
$priorChanged = @()
$priorMatched = 0
foreach ($package in $baseline.prior_packages.PSObject.Properties) {
    foreach ($entry in $package.Value.PSObject.Properties) {
        $path = "docs/qa/$($package.Name)/$($entry.Name)"
        $hash = HashFile $path
        if ($null -eq $hash) { $priorMissing += $path }
        elseif ($hash -ne $entry.Value) { $priorChanged += $path }
        else { $priorMatched++ }
    }
}
$candidates = @($manifest.files.PSObject.Properties | ForEach-Object {
    [ordered]@{path=$_.Name; before_match=((HashFile $_.Name) -eq $_.Value.before_sha256); candidate_match=((HashFile "$plan/candidate/$($_.Name)") -eq $_.Value.candidate_sha256)}
})
$indexBefore = HashFile '.git/index'
$statusBefore = @(git status --porcelain=v2 --branch)
$applyOutput = @(git apply --check "$plan/proposed.diff" 2>&1)
$applyExit = $LASTEXITCODE
$staged = @(git diff --cached --name-only)
$remote = @(git ls-remote origin refs/heads/codex/module09-transfer-2026-10-16-r1 refs/heads/main)
$remoteExit = $LASTEXITCODE
$activeLines = @(Select-String -Path docs/task33/implementation-status.md -Pattern '^active_run\s*:' | ForEach-Object { $_.Line })
$result = [ordered]@{
    utc=[DateTime]::UtcNow.ToString('o'); mode='RESUME / PLAN VALIDATION ONLY'; approval='PENDING'; candidate_applied=$false
    head=(git rev-parse HEAD); branch=(git branch --show-current); task33_ref=(git rev-parse refs/heads/task33-progress)
    head_tree=(git rev-parse 'HEAD^{tree}'); staged_count=$staged.Count; index_sha256_before=$indexBefore; index_sha256_after=(HashFile '.git/index')
    remote=$remote; remote_exit=$remoteExit; origin_main_divergence=(git rev-list --left-right --count HEAD...origin/main)
    active_run_lines=$activeLines; status=$statusBefore
    source_count=@($baseline.sources.PSObject.Properties).Count; source_mismatches=$sourceMismatch
    prior_package_count=@($baseline.prior_packages.PSObject.Properties).Count; prior_files_matched=$priorMatched; prior_missing=$priorMissing; prior_changed=$priorChanged
    candidate_checks=$candidates; diff_hash_match=((HashFile "$plan/proposed.diff") -eq $manifest.diff_sha256)
    apply_check_exit=$applyExit; apply_check_output=$applyOutput
    graph='C-kidsmap ready; generation 2026-10-16T18:56:53Z; exact paths coverage_unavailable/metadata_changed. Direct source and hashes authoritative.'
    historical_modules='01-08 LOCAL PASS per guide; 09 CLOSED LOCAL composite; 10 ACCEPT FAIL / OPEN16; 11-13 not started in current continuation'
    tests='NOT RUN (historical RED retained; fresh RED/GREEN and browser follow approval)'; production='UNKNOWN / NOT RUN'
    command='powershell -NoProfile -File docs/qa/site-qa01-resume-2026-10-18-pc-r1/verify.ps1'
    earlier_command_errors='Unquoted HEAD^{tree} was parsed by PowerShell; corrected quoted read returned 881e0c48c7d557c46221beb3b2410a157982f861. Guessed STATE.md absent; actual implementation-status.md used. No mutation from either probe.'
}
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath "$out/verification.json" -Encoding utf8
[ordered]@{source_count=$result.source_count; source_mismatches=$sourceMismatch; prior_packages=$result.prior_package_count; prior_matched=$priorMatched; prior_missing_count=$priorMissing.Count; prior_changed=$priorChanged; candidate_checks=$candidates; apply_exit=$applyExit; staged_count=$staged.Count; index_preserved=($indexBefore -eq $result.index_sha256_after); active=$activeLines} | ConvertTo-Json -Depth 5
if ($sourceMismatch.Count -or $priorChanged.Count -or $applyExit -or $remoteExit -or $staged.Count -or ($candidates | Where-Object { -not $_.before_match -or -not $_.candidate_match })) { exit 1 }
