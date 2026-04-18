.PHONY: setup run inspect

setup:
	python -m venv .venv
	.venv/bin/pip install -r requirements.txt
	.venv/bin/playwright install chromium
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		KEY=$$(.venv/bin/python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"); \
		sed -i'' -e "s/^FERNET_KEY=.*/FERNET_KEY=$$KEY/" .env; \
		echo "Created .env with generated FERNET_KEY"; \
	fi

run:
	.venv/bin/python launch_public.py

inspect:
	npx -y @modelcontextprotocol/inspector
