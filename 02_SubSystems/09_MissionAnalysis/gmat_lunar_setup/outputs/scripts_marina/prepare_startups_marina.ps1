param(
    [string]$GmatRoot = 'C:\Users\marin\OneDrive\Dokumente\gmat-win-R2022a\GMAT',
    [string]$OutputRoot = 'C:\Users\marin\OneDrive\Desktop\SMD'
)
$ErrorActionPreference = 'Stop'
$nativePath = Join-Path $GmatRoot 'bin\gmat_startup_file.txt'
if (-not (Test-Path -LiteralPath $nativePath)) { throw "GMAT startup file not found: $nativePath" }
$nativeText = [IO.File]::ReadAllText($nativePath)
$portableRoot = $GmatRoot.Replace('\', '/').TrimEnd('/')
$portableOutput = $OutputRoot.Replace('\', '/').TrimEnd('/')
[IO.Directory]::CreateDirectory($OutputRoot) | Out-Null
$utf8 = New-Object System.Text.UTF8Encoding($false)
function Set-StartupValue([string]$Text, [string]$Key, [string]$Value) {
    $pattern = '(?m)^\s*' + [regex]::Escape($Key) + '\s*=.*$'
    if ([regex]::IsMatch($Text, $pattern)) {
        return [regex]::Replace($Text, $pattern, [System.Text.RegularExpressions.MatchEvaluator]{ param($match) "$Key = $Value" })
    }
    return $Text + "`r`n$Key = $Value`r`n"
}
$prepared = @()
foreach ($script in Get-ChildItem -LiteralPath $PSScriptRoot -Filter '*.script' -File) {
    $case = $script.BaseName
    $text = Set-StartupValue $nativeText 'ROOT_PATH' "$portableRoot/"
    $text = Set-StartupValue $text 'OUTPUT_PATH' "$portableOutput/"
    $text = Set-StartupValue $text 'LOG_FILE' "$portableOutput/${case}_GmatLog.txt"
    $text = Set-StartupValue $text 'PERSONALIZATION_FILE' "$portableRoot/data/gui_config/MyGmat.ini"
    $guiPath = Join-Path $PSScriptRoot "$case.startup.txt"
    [IO.File]::WriteAllText($guiPath, $text, $utf8)
    # Console mode uses the same native R2022a settings, with GUI-only plugins disabled.
    $console = [regex]::Replace($text, '(?im)^(\s*PLUGIN\s*=.*(?:OpenFramesInterface|OVtoOFI).*)$', '#$1')
    $consolePath = Join-Path $PSScriptRoot "$case.console.startup.txt"
    [IO.File]::WriteAllText($consolePath, $console, $utf8)
    $prepared += @{ case = $case; gui_sha256 = (Get-FileHash -LiteralPath $guiPath -Algorithm SHA256).Hash; console_sha256 = (Get-FileHash -LiteralPath $consolePath -Algorithm SHA256).Hash }
}
$record = @{ native_startup = $nativePath; native_startup_sha256 = (Get-FileHash -LiteralPath $nativePath -Algorithm SHA256).Hash; gmat_root = $GmatRoot; output_root = $OutputRoot; generated = $prepared; mission_propagated = $false }
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'marina_startups_prepared.json'), ($record | ConvertTo-Json -Depth 6), $utf8)
Write-Host "Prepared GUI and console startup files for $($prepared.Count) cases using $nativePath"
