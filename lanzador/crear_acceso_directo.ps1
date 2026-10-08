# Crea en el escritorio de Windows el acceso directo "SteelPlan" (inicia el servidor y abre el enlace)
# y el enlace web "SteelPlan (enlace)". Uso: powershell -ExecutionPolicy Bypass -File lanzador\crear_acceso_directo.ps1
$raiz = Split-Path -Parent $PSScriptRoot
$escritorio = [Environment]::GetFolderPath('Desktop')
$sh = New-Object -ComObject WScript.Shell

$lnk = $sh.CreateShortcut((Join-Path $escritorio 'SteelPlan.lnk'))
$lnk.TargetPath = Join-Path $raiz 'lanzador\iniciar_plataforma.bat'
$lnk.WorkingDirectory = $raiz
$lnk.IconLocation = (Join-Path $raiz 'plataforma\web\icono.ico') + ',0'
$lnk.Description = 'SteelPlan - gestión de proyectos y cotización de plazos'
$lnk.WindowStyle = 7
$lnk.Save()

$url = Join-Path $escritorio 'SteelPlan (enlace).url'
@"
[InternetShortcut]
URL=http://localhost:8600
IconFile=$(Join-Path $raiz 'plataforma\web\icono.ico')
IconIndex=0
"@ | Set-Content -Path $url -Encoding ASCII

Write-Output "Creados: $($lnk.FullName) y $url"
