VALID_BATCH_YAML = """
mes: 5
ano: 2026
servidores:
  - nome: "CELIO PROLICIANO MAIOLI"
    siape: "1534589"
  - nome: "OUTRO SERVIDOR TESTE"
    siape: "9876543"
"""

VALID_BATCH_YAML_SINGLE = """
servidores:
  - nome: "CELIO PROLICIANO MAIOLI"
    siape: "1534589"
"""

VALID_BATCH_YAML_WITH_OVERRIDE = """
mes: 5
ano: 2026
servidores:
  - nome: "CELIO PROLICIANO MAIOLI"
    siape: "1534589"
  - nome: "OUTRO SERVIDOR"
    siape: "9876543"
    mes: 4
    ano: 2025
"""

MALFORMED_YAML = """
servidores:
  - nome: [unclosed bracket
    siape: "123"
"""

EMPTY_SERVERS_YAML = """
mes: 5
ano: 2026
servidores: []
"""

MISSING_SERVERS_YAML = """
mes: 5
ano: 2026
"""
