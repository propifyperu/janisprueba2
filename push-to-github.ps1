# Verificar estado
Write-Host "=== Estado actual del repositorio ===" -ForegroundColor Cyan
git status

Write-Host "`n=== Agregando cambios ===" -ForegroundColor Cyan
git add .

Write-Host "`n=== Haciendo commit ===" -ForegroundColor Cyan
$message = Read-Host "Ingresa el mensaje del commit (ej: 'Agregar PropertyCondition y OperationType')"
git commit -m $message

Write-Host "`n=== Haciendo push a GitHub ===" -ForegroundColor Cyan
git push origin main

Write-Host "`n=== ¡Listo! Verifica en GitHub ===" -ForegroundColor Green
