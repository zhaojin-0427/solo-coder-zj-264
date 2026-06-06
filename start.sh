#!/bin/bash
echo "========================================="
echo "  花艺工作室订单管理与花材养护追踪系统"
echo "========================================="

echo ""
echo "正在启动后端服务 (端口 9201)..."
cd backend
pip3 install -q -r requirements.txt
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 9201 --reload &
BACKEND_PID=$!
echo "后端服务已启动 PID: $BACKEND_PID"

sleep 3

echo ""
echo "正在启动前端服务 (端口 9101)..."
cd ../frontend
npm install --silent
npm run dev &
FRONTEND_PID=$!
echo "前端服务已启动 PID: $FRONTEND_PID"

echo ""
echo "========================================="
echo "  系统已启动完成!"
echo "  客户端选购页面: http://localhost:9101"
echo "  管理后台:       http://localhost:9101/admin/flowers"
echo "  后端 API:       http://localhost:9201"
echo "  API 文档:       http://localhost:9201/docs"
echo "========================================="
echo ""
echo "按 Ctrl+C 停止所有服务"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo '服务已停止'; exit" INT TERM

wait
