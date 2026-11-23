import os


bind = f"0.0.0.0:{int(os.environ.get('PORT', '8000'))}"
workers = 1
worker_class = 'gthread'
threads = 2
timeout = 120
graceful_timeout = 30
max_requests = 200
max_requests_jitter = 20
accesslog = None
errorlog = '-'
capture_output = True
