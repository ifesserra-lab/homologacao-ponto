.PHONY: test install-browsers quickstart

test:
	pytest

install-browsers:
	python -m playwright install chromium

quickstart: test
	python -m json.tool tests/fixtures/crawl_result_completed_sample.json >/dev/null
	python -m json.tool tests/fixtures/crawl_result_empty_sample.json >/dev/null
	python -m json.tool tests/fixtures/crawl_result_partial_sample.json >/dev/null

