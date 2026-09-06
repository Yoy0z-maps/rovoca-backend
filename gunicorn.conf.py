import os


bind = f"0.0.0.0:{os.environ.get('PORT', '8080')}"
workers = int(os.environ.get("GUNICORN_WORKERS", "1"))
threads = int(os.environ.get("GUNICORN_THREADS", "4"))
worker_class = "gthread"
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "60"))
accesslog = "-"
errorlog = "-"
control_socket_disable = True
