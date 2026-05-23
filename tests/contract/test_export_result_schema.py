from jsonschema import validate

from fixtures.espelho_export_samples import load_contract_schema, sample_result_dict


def test_export_result_schema_accepts_valid_sample() -> None:
    validate(sample_result_dict(), load_contract_schema("export-result.schema.json"))


def test_export_result_schema_accepts_failure_without_export_path() -> None:
    sample = sample_result_dict()
    sample.update(
        {
            "success": False,
            "status": "failed",
            "export_path": None,
            "message": "pagina invalida",
            "error_code": "invalid_page",
        }
    )

    validate(sample, load_contract_schema("export-result.schema.json"))
