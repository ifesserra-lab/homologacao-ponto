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


VALID_ESPELHO_WITH_RESUMO_HTML = """
<html>
  <head><title>Espelho de Ponto</title></head>
  <body>
    <h1>Espelho de Ponto</h1>
    <div>Servidor: CELIO PROLICIANO MAIOLI - SIAPE: 1534589</div>
    <div>Periodo: Maio/2026</div>
    <table>
      <tr id="frequenciaForm:listagemPontos:0:j_id_jsp_001">
        <td>02/05/2026 // Dia da Semana: Sabado</td>
        <td>07:58 12:00 13:00 17:03</td>
        <td>08:05</td>
        <td>00:00</td>
        <td>---</td>
        <td>---</td>
        <td>---</td>
        <td>00:00</td>
        <td>---</td>
        <td>---</td>
        <td>00:00</td>
        <td>---</td>
      </tr>
    </table>
    <table class="visualizacao" style="width: 70%;">
      <caption>Resumo das Horas Apuradas no Mês</caption>
      <tbody>
      <tr>
        <th nowrap="nowrap">Carga Horária Contratada:</th>
        <td>160:00</td>
      </tr>
      <tr>
        <th nowrap="nowrap">Carga Horária Esperada no Mês:</th>
        <td>160:00</td>
      </tr>
      <tr>
        <th nowrap="nowrap">Total de Horas Registradas:</th>
        <td>50:31</td>
      </tr>
      <tr>
        <th nowrap="nowrap">Total de Horas Justificadas:</th>
        <td>00:00</td>
      </tr>
      <tr>
        <th nowrap="nowrap">Total de Horas Homologadas:</th>
        <td>49:25</td>
      </tr>
      <tr>
        <th nowrap="nowrap">Saldo de Abril/2026 Para Compensação:</th>
        <td>00:00</td>
      </tr>
      <tr>
        <th nowrap="nowrap">Total de Horas de Abril/2026 Compensadas:</th>
        <td>00:00</td>
      </tr>
      <tr>
        <th nowrap="nowrap">Débito de Abril/2026 Não Compensado em Maio/2026:</th>
        <td>00:00</td>
      </tr>
      <tr>
        <th nowrap="nowrap">Débito de Maio/2026 Não Autorizado à Compensação:</th>
        <td>-61:25</td>
      </tr>
      <tr>
        <th nowrap="nowrap">Outros Débitos Não Compensados Vencidos em Maio/2026:</th>
        <td>00:00</td>
      </tr>
      <tr>
        <th nowrap="nowrap">Totalização do Débito Não Compensável:</th>
        <td>-61:25</td>
      </tr>
      <tr>
        <th nowrap="nowrap">Total de Horas Pendentes de Compensação:</th>
        <td>-09:10</td>
      </tr>
      <tr>
        <th nowrap="nowrap">Saldo de Horas de Maio/2026:</th>
        <td>-09:10</td>
      </tr>
      <tr>
        <th nowrap="nowrap">Saldo de Horas de Maio/2026 a compensar até Junho/2026:</th>
        <td>-09:10</td>
      </tr>
      <tr>
        <th nowrap="nowrap">Crédito de Horas Disponível em Maio/2026:</th>
        <td>00:00</td>
      </tr>
      <tr>
        <th nowrap="nowrap">Crédito em Horas:</th>
        <td>00:00</td>
      </tr>
      </tbody>
    </table>
  </body>
</html>
"""
