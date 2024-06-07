build-LangChainLayer:
	mkdir -p "$(ARTIFACTS_DIR)/python"
	python -m pip install -r requirements.txt --platform manylinux2014_x86_64 -t "$(ARTIFACTS_DIR)/python" --only-binary=:all:
	