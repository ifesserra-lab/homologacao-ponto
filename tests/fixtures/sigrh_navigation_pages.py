COMPLETE_MENU_HTML = """
<html>
  <head><title>SIGRH</title></head>
  <body>
    <nav>
      <a>Chefia de Unidade</a>
      <a>Homologação de Ponto Eletrônico</a>
      <a>Relatório</a>
      <a>Espelho do Ponto</a>
    </nav>
    <main><h1>Portal do Servidor</h1></main>
  </body>
</html>
"""

ESPELHO_DESTINATION_HTML = """
<html>
  <head><title>Espelho do Ponto</title></head>
  <body>
    <ol class="breadcrumb"><li>Relatório</li><li>Espelho do Ponto</li></ol>
    <h1>Espelho do Ponto</h1>
  </body>
</html>
"""

MISSING_CHEFIA_HTML = """
<html><body><nav><a>Servidor</a><a>Relatório</a></nav></body></html>
"""

MISSING_HOMOLOGACAO_HTML = """
<html><body><nav><a>Chefia de Unidade</a><a>Relatório</a></nav></body></html>
"""

DESTINATION_MISMATCH_HTML = """
<html><head><title>Relatório</title></head><body><h1>Relatório de Frequência</h1></body></html>
"""

SESSION_EXPIRED_HTML = """
<html><body><h1>Sessão expirada</h1><a href="/sigrh/login.jsf">Login</a></body></html>
"""

BLOCKED_HTML = """
<html><body><h1>CAPTCHA obrigatório</h1><p>bloqueio de automação</p></body></html>
"""
