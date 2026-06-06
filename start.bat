@echo off
echo =========================================
echo   花艺工作室订单管理与花材养护追踪系统
echo =========================================

echo.
echo 正在启动后端服务 (端口 9201)...
cd backend
start "Backend" cmd /c "pip install -r requirements.txt && python -m uvicorn app.main:app --host 0.0.0.0 --port 9201 --reload"

timeout /t 5 /nobreak >nul

echo.
echo 正在启动前端服务 (端口 9101)...
cd ..\frontend
start "Frontend" cmd /c "npm install && npm run dev"

echo.
echo =========================================
echo   系统已启动完成!
echo   客户端选购页面: http://localhost:9101
echo   管理后台:       http://localhost:9101/admin/flowers
echo   后端 API:       http://localhost:9201
echo   API 文档:       http://localhost:9201/docs
echo =========================================
pause
