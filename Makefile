PREFIX ?= $(HOME)/.local

install:
	install -d $(PREFIX)/lib/claude-workspace
	install -d $(PREFIX)/bin
	cp -r claude_workspace $(PREFIX)/lib/claude-workspace/
	sed 's|LIBDIR|$(PREFIX)/lib/claude-workspace|' bin/claude-workspace.sh > $(PREFIX)/bin/claude-workspace
	chmod +x $(PREFIX)/bin/claude-workspace

uninstall:
	rm -rf $(PREFIX)/lib/claude-workspace
	rm -f $(PREFIX)/bin/claude-workspace

lint:
	python3 -m pycodestyle --max-line-length=100 claude_workspace/

.PHONY: install uninstall lint
