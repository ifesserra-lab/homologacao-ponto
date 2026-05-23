SERVER_SEARCH_FORM_HTML = """
<html>
  <head><title>Espelho de Ponto</title></head>
  <body>
    <form id="form">
      <input type="checkbox" id="form:checkServidor" name="form:checkServidor" />
      <input type="text" id="form:nomeServidor" name="form:nomeServidor" />
      <input type="hidden" id="form:suggestionServidor_selection" />
      <input type="submit" id="form:buscarServidores" value="Buscar" />
    </form>
  </body>
</html>
"""

UNIQUE_SERVER_RESULT_HTML = """
<html>
  <head><title>Espelho de Ponto</title></head>
  <body>
    <table class="listagem">
      <tr><th>SIAPE</th><th>Nome</th><th>Cargo</th><th></th></tr>
      <tr>
        <td>1534589</td>
        <td>CELIO PROLICIANO MAIOLI</td>
        <td>PROFESSOR</td>
        <td><a id="form:selecionar" title="Selecionar Servidor" href="#">Selecionar</a></td>
      </tr>
    </table>
  </body>
</html>
"""

AMBIGUOUS_SERVER_RESULT_HTML = """
<html>
  <body>
    <table class="listagem">
      <tr><td>1534589</td><td>CELIO PROLICIANO MAIOLI</td><td><a title="Selecionar Servidor">Selecionar</a></td></tr>
      <tr><td>9999999</td><td>CELIO PROLICIANO SILVA</td><td><a title="Selecionar Servidor">Selecionar</a></td></tr>
    </table>
  </body>
</html>
"""

MISSING_SERVER_RESULT_HTML = """
<html><body><div class="info">Nenhum servidor encontrado.</div></body></html>
"""

MISSING_SELECTION_CONTROL_HTML = """
<html>
  <body>
    <table class="listagem">
      <tr><td>1534589</td><td>CELIO PROLICIANO MAIOLI</td><td></td></tr>
    </table>
  </body>
</html>
"""

SELECTED_SERVER_PAGE_HTML = """
<html>
  <head><title>Espelho de Ponto - Maio de 2026</title></head>
  <body>
    <h1>PONTO DIÁRIO DO SERVIDOR: CELIO PROLICIANO MAIOLI (1534589)</h1>
  </body>
</html>
"""

SELECTION_DESTINATION_MISMATCH_HTML = """
<html><body><h1>Espelho de Ponto</h1><p>Servidor diferente</p></body></html>
"""

SELECTION_SESSION_EXPIRED_HTML = """
<html><body><h1>Sessão expirada</h1><a href="/sigrh/login.jsf">Login</a></body></html>
"""

SELECTION_BLOCKED_HTML = """
<html><body><h1>CAPTCHA obrigatório</h1><p>bloqueio de automação</p></body></html>
"""
