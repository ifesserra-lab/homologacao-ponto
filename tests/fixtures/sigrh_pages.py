LOGIN_SUCCESS_HTML = """
<html><title>SIGRH - Portal do Servidor</title><body>Bem-vindo</body></html>
"""

LOGIN_FAILURE_HTML = """
<html><body>Usuario ou senha invalidos</body></html>
"""

ANTI_AUTOMATION_HTML = """
<html><body>captcha obrigatorio para continuar</body></html>
"""

SESSION_EXPIRED_HTML = """
<html><body>Sessao expirada. Faca login novamente.</body></html>
"""

ATTENDANCE_HTML = """
<html><body>
<table id="registros-ponto">
  <tr class="registro-ponto" data-date="2026-05-20">
    <td class="entrada">08:00</td>
    <td class="saida">12:00</td>
    <td class="entrada">13:00</td>
    <td class="saida">17:00</td>
  </tr>
</table>
</body></html>
"""

EMPTY_ATTENDANCE_HTML = """
<html><body><table id="registros-ponto"></table></body></html>
"""

