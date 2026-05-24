.PHONY: test install-browsers quickstart export dashboard

test:
	pytest

install-browsers:
	python -m playwright install chromium

export:
	python -m homologacao_ponto.cli batch \
		--file servidores.yaml \
		--output-dir data/runs

dashboard:
	cd dashboard && npm run dev

quickstart: test
	python -m json.tool tests/fixtures/crawl_result_completed_sample.json >/dev/null
	python -m json.tool tests/fixtures/crawl_result_empty_sample.json >/dev/null
	python -m json.tool tests/fixtures/crawl_result_partial_sample.json >/dev/null
