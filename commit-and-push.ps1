Write-Host "=== Estado actual ===" -ForegroundColor Cyan
git status

Write-Host "`n=== Agregando cambios ===" -ForegroundColor Cyan
git add .

Write-Host "`n=== Haciendo commit ===" -ForegroundColor Cyan
$message = Read-Host "Mensaje del commit (ej: 'Agregar PropertyCondition y OperationType models')"
git commit -m $message

Write-Host "`n=== Haciendo push a feature/nueva-funcionalidad ===" -ForegroundColor Cyan
git push origin feature/nueva-funcionalidad

Write-Host "`n=== ¡Listo! Puedes crear un Pull Request en GitHub ===" -ForegroundColor Green
