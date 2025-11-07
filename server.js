import express from "express";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

// 让服务器识别 static 文件夹
app.use(express.static(path.join(__dirname, "static")));

// 让 /ocr.html 能被访问到
app.get("/ocr.html", (req, res) => {
  res.sendFile(path.join(__dirname, "static", "ocr.html"));
});

// 测试首页
app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "static", "index.html"));
});

// 启动服务
app.listen(PORT, () => {
  console.log(`✅ Server running on port ${PORT}`);
});
