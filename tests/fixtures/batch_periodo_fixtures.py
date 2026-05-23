from homologacao_ponto.models.batch_config import BatchConfig, BatchEntry

VALID_ANOS_LIST_YAML = """
anos: [2025]
servidores:
  - nome: "CELIO PROLICIANO MAIOLI"
    siape: "1534589"
"""

VALID_ANOS_TWO_YEARS_YAML = """
anos: [2025, 2026]
servidores:
  - nome: "CELIO PROLICIANO MAIOLI"
    siape: "1534589"
"""

VALID_ANOS_ALL_YAML = """
anos: All
servidores:
  - nome: "CELIO PROLICIANO MAIOLI"
    siape: "1534589"
"""

VALID_ANOS_ALL_LOWERCASE_YAML = """
anos: all
servidores:
  - nome: "CELIO PROLICIANO MAIOLI"
    siape: "1534589"
"""

VALID_ANOS_WITH_LEGACY_FIELDS_YAML = """
anos: [2025]
mes: 5
ano: 2026
servidores:
  - nome: "CELIO PROLICIANO MAIOLI"
    siape: "1534589"
"""

INVALID_ANOS_EMPTY_LIST_YAML = """
anos: []
servidores:
  - nome: "CELIO PROLICIANO MAIOLI"
    siape: "1534589"
"""

INVALID_ANOS_BAD_STRING_YAML = """
anos: "Invalido"
servidores:
  - nome: "CELIO PROLICIANO MAIOLI"
    siape: "1534589"
"""

INVALID_ANOS_OUT_OF_RANGE_YAML = """
anos: [1900]
servidores:
  - nome: "CELIO PROLICIANO MAIOLI"
    siape: "1534589"
"""

INVALID_ANOS_STRING_IN_LIST_YAML = """
anos: ["x", 2025]
servidores:
  - nome: "CELIO PROLICIANO MAIOLI"
    siape: "1534589"
"""

LEGACY_NO_ANOS_YAML = """
mes: 5
ano: 2026
servidores:
  - nome: "CELIO PROLICIANO MAIOLI"
    siape: "1534589"
"""

ENTRY_CELIO = BatchEntry(nome="CELIO PROLICIANO MAIOLI", siape="1534589")

BATCH_CONFIG_LEGACY = BatchConfig(
    servidores=[ENTRY_CELIO],
    mes=5,
    ano=2026,
)

BATCH_CONFIG_ANOS_2025 = BatchConfig(
    servidores=[ENTRY_CELIO],
    anos=[2025],
)

BATCH_CONFIG_ANOS_TWO_YEARS = BatchConfig(
    servidores=[ENTRY_CELIO],
    anos=[2025, 2026],
)

BATCH_CONFIG_ANOS_ALL = BatchConfig(
    servidores=[ENTRY_CELIO],
    anos="All",
)
