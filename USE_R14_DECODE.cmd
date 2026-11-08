@echo off
setlocal
set "R14_COMPARE_ROOT=%~dp0"
powershell.exe -NoProfile -Command "& ([scriptblock]::Create([IO.File]::ReadAllText((Join-Path $env:R14_COMPARE_ROOT 'tools/select_decode_r14_1.ps1')))) -Variant baseline"
exit /b %errorlevel%
