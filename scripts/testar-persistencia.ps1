<#
  Simula o que o professor vai fazer na prova: desliga e religa o compose
  algumas vezes e confere se a aplicação volta e se os dados continuam lá.

  powershell -ExecutionPolicy Bypass -File scripts\testar-persistencia.ps1
  (use -Build para construir as imagens a partir do código em vez de baixar)
#>
param([int]$Ciclos = 3, [switch]$Build)

$ErrorActionPreference = "Stop"
$raiz = Split-Path $PSScriptRoot -Parent
Set-Location $raiz
$arquivos = if ($Build) { @("-f", "docker-compose.yml", "-f", "docker-compose.build.yml") } else { @("-f", "docker-compose.yml") }
$base = "http://localhost:8080/api"

function Subir {
  if ($Build) { docker compose @arquivos up -d --build --wait } else { docker compose @arquivos up -d --wait }
  if ($LASTEXITCODE -ne 0) { Write-Host "Os containers não ficaram saudáveis. Veja: docker compose logs" -ForegroundColor Red; exit 1 }
}

function Ok($texto) { Write-Host "  [ok] $texto" -ForegroundColor Green }
function Falha($texto) { Write-Host "  [falhou] $texto" -ForegroundColor Red; exit 1 }

Write-Host "`n== 1. Subindo os containers ==" -ForegroundColor Cyan
Subir
Ok "db, api e web saudáveis"

Write-Host "`n== 2. Gravando dados pela aplicação ==" -ForegroundColor Cyan
$email = "teste-$(Get-Random)@pontozero.app"
$senha = "persistencia123"
$sessao = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$corpo = @{ nome = "Teste de Persistência"; email = $email; senha = $senha; empresa = "Empresa Teste"; segmento = "Padaria" } | ConvertTo-Json
Invoke-RestMethod "$base/auth/cadastro" -Method Post -Body $corpo -ContentType "application/json; charset=utf-8" -WebSession $sessao | Out-Null
Ok "conta criada: $email"
$regioes = Invoke-RestMethod "$base/regioes"
$ids = @($regioes | Select-Object -First 2 | ForEach-Object { $_.id_regiao })
$segmentos = Invoke-RestMethod "$base/segmentos"
$padaria = $segmentos | Where-Object { $_.nome -eq "Padaria" } | Select-Object -First 1
if (-not $padaria) { Falha "o segmento Padaria não foi encontrado" }
$analise = @{ nome = "Análise de persistência"; segmento = $padaria.id_categoria; regioes = $ids } | ConvertTo-Json
$criada = Invoke-RestMethod "$base/analises" -Method Post -Body $analise -ContentType "application/json; charset=utf-8" -WebSession $sessao
if (-not $criada.id_analise) { Falha "a API não devolveu o id da análise" }
Ok "análise salva (id $($criada.id_analise))"
$antes = Invoke-RestMethod "$base/status"
Write-Host "  volume criado em $($antes.banco.volume_inicializado_em), $($antes.banco.contagens.usuario) usuário(s), $($antes.banco.contagens.analise) análise(s)"

for ($i = 1; $i -le $Ciclos; $i++) {
  Write-Host "`n== 3.$i Desligando e religando (docker compose down / up) ==" -ForegroundColor Cyan
  docker compose @arquivos down
  Subir
  $depois = Invoke-RestMethod "$base/status"
  if ($depois.banco.volume_inicializado_em -ne $antes.banco.volume_inicializado_em) { Falha "o volume foi recriado" }
  Ok "mesmo volume (criado em $($depois.banco.volume_inicializado_em)); banco religado em $($depois.banco.ligado_em)"

  $nova = New-Object Microsoft.PowerShell.Commands.WebRequestSession
  $login = @{ email = $email; senha = $senha } | ConvertTo-Json
  Invoke-RestMethod "$base/auth/login" -Method Post -Body $login -ContentType "application/json" -WebSession $nova | Out-Null
  Ok "login com a conta criada antes do desligamento"
  $lista = Invoke-RestMethod "$base/analises" -WebSession $nova
  if (-not ($lista | Where-Object { $_.id_analise -eq $criada.id_analise })) { Falha "a análise sumiu" }
  Ok "a análise salva continua lá"
}

Write-Host "`nTudo certo: a aplicação volta sozinha e os dados persistem no volume pgdata." -ForegroundColor Green
Write-Host "Abra http://localhost:8080 para ver."
