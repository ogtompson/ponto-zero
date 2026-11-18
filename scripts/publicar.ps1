<#
  Constrói as 3 imagens do PontoZero e envia para o Docker Hub (Windows / PowerShell).

  Antes, uma vez só:   docker login
  Para rodar:          powershell -ExecutionPolicy Bypass -File scripts\publicar.ps1
  Outro usuário/tag:   powershell -ExecutionPolicy Bypass -File scripts\publicar.ps1 -Usuario seuusuario -Tag 1.1

  Por padrão gera imagens para Intel/AMD (amd64) e para Mac M1/M2/M3 (arm64),
  assim o professor consegue rodar em qualquer computador.
  Use -SoAmd64 se quiser um build mais rápido só para Intel/AMD.
#>
param(
  [string]$Usuario = "ogabrieltenorio",
  [string]$Tag = "1.0",
  [switch]$SoAmd64
)

$raiz = Split-Path $PSScriptRoot -Parent
Set-Location $raiz
$Usuario = $Usuario.ToLower()   # nomes de imagem precisam ser minúsculos
$plataformas = if ($SoAmd64) { "linux/amd64" } else { "linux/amd64,linux/arm64" }

Write-Host "`n== PontoZero: publicando imagens em $Usuario (tag $Tag) ==" -ForegroundColor Cyan

docker version --format "{{.Server.Version}}" *> $null
if ($LASTEXITCODE -ne 0) { Write-Host "O Docker Desktop não está aberto. Abra e tente de novo." -ForegroundColor Red; exit 1 }

# builder que sabe gerar várias arquiteturas
docker buildx inspect pontozero *> $null
if ($LASTEXITCODE -ne 0) { docker buildx create --name pontozero --driver docker-container *> $null }
docker buildx use pontozero

foreach ($img in @("db", "api", "web")) {
  Write-Host "`n-> pontozero-$img ($plataformas)" -ForegroundColor Yellow
  docker buildx build --platform $plataformas `
    -t "$Usuario/pontozero-${img}:$Tag" -t "$Usuario/pontozero-${img}:latest" `
    --push "./$img"
  if ($LASTEXITCODE -ne 0) {
    Write-Host "Falhou ao publicar pontozero-$img. Você rodou 'docker login'?" -ForegroundColor Red
    exit 1
  }
}

Write-Host "`nPronto! Imagens no Docker Hub:" -ForegroundColor Green
foreach ($img in @("db", "api", "web")) { Write-Host "  https://hub.docker.com/r/$Usuario/pontozero-$img" }
Write-Host "`nAgora qualquer pessoa sobe o projeto só com o docker-compose.yml:  docker compose up -d"
