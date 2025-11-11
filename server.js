// server.js
require('dotenv').config();
const express = require('express');
const bodyParser = require('body-parser');
const fetch = require('node-fetch'); // node-fetch v2
const fs = require('fs');
const path = require('path');

const app = express();
app.use(bodyParser.json({ limit: '15mb' }));

const DEEPSEEK_API_KEY = process.env.DEEPSEEK_API_KEY || '';
const DEEPSEEK_ENDPOINT = process.env.DEEPSEEK_ENDPOINT || ''; // e.g. https://api.deepseek.example/parse

// --- Utility: very small "fallback parser" when DeepSeek not configured ---
// This is a naive regex-based parser just for local development/testing.
function fallbackParse({ text, image_base64 }) {
  const txt = (text || '').trim();
  const parsed = {
    question: txt || (image_base64 ? '（从图像得到的题目）' : ''),
    equations: [],
    diagram_desc: null,
    knowledge_tags: []
  };

  if (/\bf\s*\(\s*x\s*\)\s*=/.test(txt) || /x\^2/.test(txt) || /二次函数/.test(txt)) {
    parsed.equations.push(txt.match(/f\s*\(\s*x\s*\)\s*=\s*.+/)? txt.match(/f\s*\(\s*x\s*\)\s*=\s*.+/)[0] : txt);
    parsed.knowledge_tags.push('函数-单调性', '二次函数');
  } else if (/求导|导数|f'/.test(txt)) {
    parsed.knowledge_tags.push('导数-求导法则', '导数-极值讨论');
  } else if (/不等式|≥|≤|<|>/.test(txt)) {
    parsed.knowledge_tags.push('不等式-基本');
  } else if (txt) {
    parsed.knowledge_tags.push('基础-阅读理解');
  }

  // Attach a short summary
  parsed.summary = `自动回退解析：识别到 ${parsed.knowledge_tags.length} 个标签。`;
  return parsed;
}

// --- /parse endpoint ---
app.post('/parse', async (req, res) => {
  try {
    const { text, image_base64 } = req.body || {};

    // If DeepSeek not configured, use fallbackParse
    if (!DEEPSEEK_API_KEY || !DEEPSEEK_ENDPOINT) {
      const parsed = fallbackParse({ text, image_base64 });
      return res.json({ success: true, parsed, used: 'fallback' });
    }

    // If DeepSeek is configured, call it (example shape; adapt to DeepSeek API)
    const deepReq = { text, image_base64 };
    const response = await fetch(DEEPSEEK_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${DEEPSEEK_API_KEY}`
      },
      body: JSON.stringify(deepReq),
      timeout: 15000
    });

    if (!response.ok) {
      // return fallback if remote failed
      const textResp = await response.text();
      console.error('DeepSeek error resp:', response.status, textResp);
      const parsed = fallbackParse({ text, image_base64 });
      return res.json({ success: true, parsed, used: 'fallback_due_to_deepseek_error', deepseek_status: response.status });
    }

    const data = await response.json();
    // Expect DeepSeek to return structure; if not, wrap it safely
    const parsed = data.parsed || data;
    return res.json({ success: true, parsed, used: 'deepseek' });

  } catch (err) {
    console.error('Parse error:', err);
    // fallback parse on any exception
    const parsed = fallbackParse({ text: req.body?.text, image_base64: req.body?.image_base64 });
    return res.status(200).json({ success: true, parsed, used: 'fallback_due_to_exception', error: err.message });
  }
});

// Simple health endpoint
app.get('/', (req, res) => {
  res.send('math-ocr backend OK');
});

// Optional: save wrong endpoint for Day1 convenience (file append)
const WRONG_FILE = path.join(__dirname, 'wrong_book.json');
app.post('/save_wrong', (req, res) => {
  try {
    const record = req.body || {};
    const list = fs.existsSync(WRONG_FILE) ? JSON.parse(fs.readFileSync(WRONG_FILE)) : [];
    record.time = new Date().toISOString();
    list.push(record);
    fs.writeFileSync(WRONG_FILE, JSON.stringify(list, null, 2));
    res.json({ success: true, message: 'saved', recordCount: list.length });
  } catch (err) {
    console.error('save_wrong error', err);
    res.status(500).json({ success: false, error: err.message });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`math-ocr backend listening on port ${PORT}`);
});
