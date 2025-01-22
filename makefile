
.PHONY: test test-unit test-integration test-all

test-unit:
	pytest tests/unit/

test-integration:
	./tests/integration/api/test_api.sh

test-all: test-unit test-integration

test: test-all
