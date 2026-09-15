import os
import json
import urllib.request
import urllib.error
from http.server import SimpleHTTPRequestHandler, HTTPServer
import ssl

class MyHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        # Serve static files
        if self.path == '/':
            self.path = '/static/index.html'
        return super().do_GET()

    def do_POST(self):
        if self.path == '/api/generate':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data)
                text = data.get('text', '')
            except json.JSONDecodeError:
                self.send_response(400)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"detail": "Invalid JSON"}).encode('utf-8'))
                return

            if not text or not text.strip():
                self.send_response(400)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"detail": "Текст лекции не может быть пустым."}).encode('utf-8'))
                return

            # Read .env (naive parser)
            env = {}
            if os.path.exists('.env'):
                with open('.env', 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            key, val = line.split('=', 1)
                            env[key.strip()] = val.strip()

            api_key = env.get("OPENAI_API_KEY", "")
            mock_llm = env.get("MOCK_LLM", "False") == "True"

            if not api_key:
                if mock_llm:
                    mock_response = {
                        "summary": "Это сгенерированный мок-конспект для тестирования.",
                        "key_points": ["Мок-тезис 1", "Мок-тезис 2"],
                        "quiz": [{"question": "Вопрос 1?", "options": ["А", "Б"], "correct_answer": "А", "source": "Исходник"}],
                        "flashcards": [{"question": "Термин 1", "answer": "Определение 1"}]
                    }
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps(mock_response, ensure_ascii=False).encode('utf-8'))
                    return
                else:
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps({"detail": "API ключ не настроен. Проверьте файл .env."}).encode('utf-8'))
                    return

            # Call OpenAI API using urllib
            prompt = f"""Ты — образовательный AI-помощник. Твоя задача — обработать текст лекции и создать учебные материалы.
            ВАЖНЫЕ ПРАВИЛА:
            1. Используй ТОЛЬКО информацию из предоставленного текста.
            2. Не добавляй внешние знания.
            3. Если необходимой информации нет, верни пустые массивы.

            Текст лекции:
            {text}

            Верни ответ СТРОГО в формате JSON со следующей структурой:
            {{
                "summary": "Краткий конспект",
                "key_points": ["Тезис 1"],
                "quiz": [
                    {{
                        "question": "Вопрос",
                        "options": ["Вар 1", "Вар 2"],
                        "correct_answer": "Вар 1",
                        "source": "Фрагмент лекции"
                    }}
                ],
                "flashcards": [
                    {{
                        "question": "Термин",
                        "answer": "Определение"
                    }}
                ]
            }}"""

            url = env.get("OPENAI_BASE_URL", "https://api.openai.com/v1") + "/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            payload = {
                "model": env.get("MODEL_NAME", "gpt-3.5-turbo"),
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that strictly outputs JSON."},
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.3
            }

            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
            try:
                # Disabling SSL verification just in case environment has certificate issues
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                
                with urllib.request.urlopen(req, context=ctx) as response:
                    res_body = response.read().decode('utf-8')
                    res_json = json.loads(res_body)
                    content = res_json['choices'][0]['message']['content']
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(content.encode('utf-8'))
                    
            except Exception as e:
                print(f"Error calling AI API: {e}")
                self.send_response(500)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"detail": "Ошибка при генерации материалов. Проверьте API-ключ или попробуйте позже."}).encode('utf-8'))
        else:
            self.send_error(404, "Not Found")

def run(server_class=HTTPServer, handler_class=MyHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting server on port {port}...")
    httpd.serve_forever()

if __name__ == '__main__':
    run()
