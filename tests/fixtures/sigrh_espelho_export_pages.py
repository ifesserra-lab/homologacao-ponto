VALID_ESPELHO_PAGE_HTML = """
<html>
  <head><title>Espelho de Ponto</title></head>
  <body>
    <h1>Espelho de Ponto</h1>
    <div class="servidor">Servidor: CELIO PROLICIANO MAIOLI - SIAPE: 1534589</div>
    <div class="periodo">Periodo: Maio/2026</div>
    <div class="mensagem">Espelho gerado com sucesso</div>
    <table id="espelho-ponto">
      <tr class="registro-dia">
        <td class="data">02/05/2026</td>
        <td class="dia-semana">Sabado</td>
        <td class="marcacoes">07:58 12:00 13:00 17:03</td>
        <td class="ocorrencias">Trabalho presencial</td>
        <td class="observacoes">Sem pendencias</td>
        <td class="situacao">Homologado</td>
        <td class="texto-visivel">Credito 00:05</td>
      </tr>
    </table>
  </body>
</html>
"""


EMPTY_ESPELHO_PAGE_HTML = """
<html>
  <head><title>Espelho de Ponto</title></head>
  <body>
    <h1>Espelho de Ponto</h1>
    <div class="servidor">Servidor: CELIO PROLICIANO MAIOLI - SIAPE: 1534589</div>
    <div class="periodo">Periodo: Maio/2026</div>
    <div class="mensagem">Sem registros de ponto para o periodo</div>
  </body>
</html>
"""


WRONG_SERVER_PAGE_HTML = """
<html>
  <body>
    <h1>Espelho de Ponto</h1>
    <div class="servidor">Servidor: OUTRA PESSOA - SIAPE: 9999999</div>
  </body>
</html>
"""


INVALID_PAGE_HTML = "<html><body><h1>Portal SIGRH</h1><p>Pagina inicial</p></body></html>"


SIGRH_FULL_TABLE_ESPELHO_HTML = """
<html>
  <head><title>Espelho de Ponto</title></head>
  <body>
    <h1>Espelho de Ponto</h1>
    <caption>Espelho de Ponto - Dezembro de 2025</caption>
    <div>Servidor: CELIO PROLICIANO MAIOLI - SIAPE: 1534589</div>
    <table>
      <tr id="frequenciaForm:listagemPontos:0:j_id_jsp_123">
        <td>15/12/2025 // Dia da Semana: Segunda // Observação: Servidor com designação remunerada.</td>
        <td>10:56 19:01</td>
        <td>07:00</td>
        <td>01:05</td>
        <td>---</td>
        <td>---</td>
        <td>---</td>
        <td>01:05</td>
        <td>---</td>
        <td>-06:55</td>
        <td>00:00</td>
        <td>---</td>
      </tr>
      <tr id="frequenciaForm:listagemPontos:1:j_id_jsp_456">
        <td>16/12/2025 // Ocorrência: REGISTRO DO PIT - DOCENTE (16/12/2025)</td>
        <td>---</td>
        <td>---</td>
        <td>---</td>
        <td>---</td>
        <td>---</td>
        <td>---</td>
        <td>---</td>
        <td>---</td>
        <td>---</td>
        <td>---</td>
        <td>---</td>
      </tr>
      <tr id="frequenciaForm:listagemPontos:2:j_id_jsp_789">
        <td>20/12/2025 // Dia da Semana: Sábado // Observação: Servidor com designação remunerada.</td>
        <td>---</td>
        <td>00:00</td>
        <td>00:00</td>
        <td>---</td>
        <td>---</td>
        <td>---</td>
        <td>---</td>
        <td>-08:00</td>
        <td>-08:00</td>
        <td>00:00</td>
        <td>---</td>
      </tr>
    </table>
  </body>
</html>
"""

SIGRH_SPARSE_TABLE_ESPELHO_HTML = """
<html>
  <head><title>Espelho de Ponto</title></head>
  <body>
    <h1>Espelho de Ponto</h1>
    <div>Servidor: CELIO PROLICIANO MAIOLI - SIAPE: 1534589</div>
    <div>Periodo: Dezembro/2025</div>
    <table>
      <tr id="frequenciaForm:listagemPontos:0:j_id_jsp_999">
        <td>01/12/2025</td>
        <td>08:00 17:00</td>
      </tr>
    </table>
  </body>
</html>
"""
