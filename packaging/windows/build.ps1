$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $ProjectRoot

$Version = (Get-Content (Join-Path $ProjectRoot "VERSION") -Raw).Trim()
if (-not $Version) {
    throw "VERSION est vide."
}

python packaging/build_icons.py
python -m PyInstaller --noconfirm --clean packaging/abisses.spec

$SelfTest = Start-Process -FilePath (Join-Path $ProjectRoot "dist\Abisses\Abisses.exe") -ArgumentList "--self-test" -Wait -PassThru
if ($SelfTest.ExitCode -ne 0) {
    throw "L'auto-test de l'application Windows a échoué avec le code $($SelfTest.ExitCode)."
}

$Iscc = Get-Command ISCC.exe -ErrorAction SilentlyContinue
if (-not $Iscc) {
    $Candidates = @(
        "$env:ProgramFiles(x86)\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
    )
    $IsccPath = $Candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
} else {
    $IsccPath = $Iscc.Source
}

if (-not $IsccPath) {
    throw "Inno Setup 6 est introuvable."
}

New-Item -ItemType Directory -Force -Path release | Out-Null
& $IsccPath "/DAppVersion=$Version" packaging/windows/Abisses.iss

Write-Host "Installateur Windows créé dans release/."
