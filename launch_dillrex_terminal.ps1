$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

$commands = @("pyw", "pythonw", "py", "python")

foreach ($command in $commands) {
    if (Get-Command $command -ErrorAction SilentlyContinue) {
        Start-Process -FilePath $command -ArgumentList @("-m", "dillrex.terminal_app") -WorkingDirectory $PSScriptRoot -WindowStyle Hidden
        exit 0
    }
}

Add-Type -AssemblyName PresentationFramework
[System.Windows.MessageBox]::Show("Python was not found. Install Python, then run Dillrex Terminal again.", "Dillrex Terminal") | Out-Null
