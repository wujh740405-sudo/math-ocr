@echo off
chcp 65001 >nul
echo 🚀 正在测试本地 API...
curl -X POST "http://127.0.0.1:8000/api/solve" ^
-H "Content-Type: application/json" ^
-d "{\"problem\":\"已知 f(x)=x^2-3x+2，求单调区间\",\"level\":\"高一\"}"
echo.
echo ✅ 测试完成，请查看上方返回结果。
pause
