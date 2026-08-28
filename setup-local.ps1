# 本地环境一键准备：建库 + 装依赖
# 用法：在项目目录 PowerShell 里运行  .\setup-local.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path "connect.py")) {
    Copy-Item "connect.example.py" "connect.py"
    Write-Host "已创建 connect.py — 请先打开并填入 MySQL 密码，再重新运行本脚本。" -ForegroundColor Yellow
    exit 1
}

$connect = Get-Content "connect.py" -Raw
if ($connect -match "你的MySQL密码|YOUR_MYSQL_PASSWORD") {
    Write-Host "请先在 connect.py 里填入 MySQL 密码，再重新运行本脚本。" -ForegroundColor Yellow
    exit 1
}

Write-Host "安装 Python 依赖..."
pip install -r requirements.txt

Write-Host "导入数据库 fms-local.sql（会提示输入 MySQL 密码）..."
$mysql = "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
if (-not (Test-Path $mysql)) {
    $mysql = (Get-Command mysql -ErrorAction SilentlyContinue).Source
}
if (-not $mysql) {
    Write-Host "找不到 mysql 命令，请手动在 MySQL Workbench 里运行 fms-local.sql" -ForegroundColor Red
    exit 1
}

Get-Content (Join-Path $PSScriptRoot "fms-local.sql") -Raw | & $mysql -u root -p --default-character-set=utf8mb4
if ($LASTEXITCODE -ne 0) {
    Write-Host "数据库导入失败，请检查密码和 MySQL 服务是否已启动。" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "准备完成。启动网站：" -ForegroundColor Green
Write-Host "  python app.py"
Write-Host "  浏览器打开 http://127.0.0.1:5000/"
