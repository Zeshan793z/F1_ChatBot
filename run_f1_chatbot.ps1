# run_f1_chatbot.ps1
Write-Host "🏎️  Starting F1 Chatbot..." -ForegroundColor Cyan
Write-Host ""

# Start Backend
Write-Host "Starting Backend Server..." -ForegroundColor Yellow
$backend = Start-Process -NoNewWindow -PassThru powershell -ArgumentList @"
    cd 'D:\Python_Project\f1_chatbot'
    Write-Host 'Backend: http://localhost:8000' -ForegroundColor Green
    uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
"@

Start-Sleep -Seconds 3

# Start Frontend
Write-Host "Starting Frontend..." -ForegroundColor Yellow
$frontend = Start-Process -NoNewWindow -PassThru powershell -ArgumentList @"
    cd 'D:\Python_Project\f1_chatbot\frontend'
    Write-Host 'Frontend: http://localhost:3000' -ForegroundColor Green
    npm start
"@

Write-Host ""
Write-Host "✅ Both servers are running!" -ForegroundColor Green
Write-Host "📍 Backend: http://localhost:8000"
Write-Host "📍 Frontend: http://localhost:3000"
Write-Host ""
Write-Host "Press any key to stop both servers..."
Read-Host

# Kill processes on exit
Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
Stop-Process -Id $frontend.Id -Force -ErrorAction SilentlyContinue