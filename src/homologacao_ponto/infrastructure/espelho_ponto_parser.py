from __future__ import annotations

import re
from html.parser import HTMLParser
from urllib.parse import urlparse

from homologacao_ponto.infrastructure.attendance_parser import SigrhPageSnapshot
from homologacao_ponto.models import EspelhoPontoExport, RegistroDiaPonto, ServidorSelecionado, normalize_server_name


_SIGRH_ROW_RE = re.compile(r"frequenciaForm:listagemPontos:\d+:")


def _cell_value(cells: list[str], date_idx: int, offset: int) -> str | None:
    idx = date_idx + offset
    if idx >= len(cells):
        return None
    val = cells[idx].split()[0] if cells[idx].split() else ""
    return val if val and val != "---" else None


class EspelhoPontoParseError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class _EspelhoHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.texts: list[str] = []
        self.messages: list[str] = []
        self.rows: list[dict[str, list[str] | str]] = []
        # Legacy class-based row state
        self._capture: str | None = None
        self._buffer: list[str] = []
        self._row: dict[str, list[str] | str] | None = None
        # Real SIGRH row state
        self._sigrh_row: bool = False
        self._sigrh_cells: list[str] = []
        self._sigrh_cell_buf: list[str] = []
        self._sigrh_td_depth: int = 0
        self._in_script: bool = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        classes = set((attrs_dict.get("class") or "").split())
        elem_id = attrs_dict.get("id") or ""

        if tag == "tr":
            if _SIGRH_ROW_RE.match(elem_id):
                self._sigrh_row = True
                self._sigrh_cells = []
                self._sigrh_td_depth = 0
                return
            if {"registro-dia", "registro-ponto"}.intersection(classes):
                self._row = {
                    "data": "", "dia_semana": "", "marcacoes": [],
                    "ocorrencias": [], "observacoes": [], "situacao": "", "textos_visiveis": [],
                }

        if tag == "script":
            self._in_script = True
            return

        if self._sigrh_row:
            if tag == "td":
                self._sigrh_td_depth += 1
                if self._sigrh_td_depth == 1:
                    self._sigrh_cell_buf = []
            return

        if tag in {"td", "span", "div", "p", "h1", "h2", "strong"}:
            self._capture = self._field_from_classes(classes)
            self._buffer = []

    def handle_data(self, data: str) -> None:
        if self._in_script:
            return
        value = " ".join(data.split())
        if value:
            self.texts.append(value)
        if self._sigrh_row:
            if self._sigrh_td_depth > 0:
                self._sigrh_cell_buf.append(data)
        elif self._capture is not None:
            self._buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self._in_script = False
            return
        if self._sigrh_row:
            if tag == "td":
                self._sigrh_td_depth -= 1
                if self._sigrh_td_depth == 0:
                    cell_text = " ".join(p.strip() for p in self._sigrh_cell_buf if p.strip())
                    self._sigrh_cells.append(cell_text)
                    self._sigrh_cell_buf = []
            elif tag == "tr":
                row = self._sigrh_extract_row()
                if row is not None:
                    self.rows.append(row)
                self._sigrh_row = False
                self._sigrh_cells = []
            return

        if self._capture is not None and tag in {"td", "span", "div", "p", "h1", "h2", "strong"}:
            value = " ".join(part.strip() for part in self._buffer if part.strip())
            if value:
                if self._capture == "mensagem":
                    self.messages.append(value)
                elif self._row is not None:
                    if self._capture in {"marcacoes", "ocorrencias", "observacoes", "textos_visiveis"}:
                        self._row[self._capture].append(value)  # type: ignore[index]
                    else:
                        self._row[self._capture] = value
            self._capture = None
            self._buffer = []
        if tag == "tr" and self._row is not None:
            if any(self._row.values()):
                self.rows.append(self._row)
            self._row = None

    def _sigrh_extract_row(self) -> dict[str, list[str] | str] | None:
        date_idx: int | None = None
        for i, cell in enumerate(self._sigrh_cells):
            if re.search(r"\b\d{2}/\d{2}/\d{4}\b", cell):
                date_idx = i
                break
        if date_idx is None:
            return None

        date_cell = self._sigrh_cells[date_idx]
        date_match = re.search(r"\b(\d{2}/\d{2}/\d{4})\b", date_cell)
        if not date_match:
            return None

        day_match = re.search(r"Dia da Semana:\s*(\w+)", date_cell, re.IGNORECASE)
        obs_match = re.search(r"Observa[çc][aã]o:\s*(.+?)(?:\s*//|$)", date_cell, re.IGNORECASE | re.DOTALL)

        time_cell = self._sigrh_cells[date_idx + 1] if date_idx + 1 < len(self._sigrh_cells) else ""

        occ_cell = next(
            (c for c in self._sigrh_cells if re.search(r"Ocorrência:|Ocorrencia:", c, re.IGNORECASE)),
            "",
        )
        occ_match = re.search(
            r"Ocorrên[çc]ia:\s*(.*?)(?=\s*Situa[çc][aã]o:|$)", occ_cell, re.IGNORECASE | re.DOTALL
        )

        return {
            "data": date_match.group(1),
            "dia_semana": day_match.group(1) if day_match else "",
            "marcacoes": [time_cell] if time_cell and time_cell != "---" else [],
            "ocorrencias": [occ_match.group(1).strip()] if occ_match else [],
            "observacoes": [obs_match.group(1).strip()] if obs_match else [],
            "situacao": "",
            "textos_visiveis": [],
            "hr": _cell_value(self._sigrh_cells, date_idx, 2),
            "hc": _cell_value(self._sigrh_cells, date_idx, 3),
            "he": _cell_value(self._sigrh_cells, date_idx, 4),
            "ha": _cell_value(self._sigrh_cells, date_idx, 5),
            "hh": _cell_value(self._sigrh_cells, date_idx, 6),
            "credito": _cell_value(self._sigrh_cells, date_idx, 7),
            "debito": _cell_value(self._sigrh_cells, date_idx, 8),
            "saldo_no_mes": _cell_value(self._sigrh_cells, date_idx, 9),
            "credito_acumulado": _cell_value(self._sigrh_cells, date_idx, 10),
            "dnc": _cell_value(self._sigrh_cells, date_idx, 11),
        }

    @staticmethod
    def _field_from_classes(classes: set[str]) -> str | None:
        if "mensagem" in classes or "alert" in classes:
            return "mensagem"
        if "data" in classes:
            return "data"
        if "dia-semana" in classes:
            return "dia_semana"
        if "marcacoes" in classes or "marcacao" in classes:
            return "marcacoes"
        if "ocorrencias" in classes or "ocorrencia" in classes:
            return "ocorrencias"
        if "observacoes" in classes or "observacao" in classes:
            return "observacoes"
        if "situacao" in classes:
            return "situacao"
        if "texto-visivel" in classes:
            return "textos_visiveis"
        return None


class EspelhoPontoParser:
    TIME_RE = re.compile(r"\b\d{1,2}:\d{2}\b")
    DATE_BR_RE = re.compile(r"\b(\d{2})/(\d{2})/(\d{4})\b")

    def parse(
        self,
        snapshot: SigrhPageSnapshot,
        run_id: str,
        expected_server: str,
        expected_identifier: str | None = None,
    ) -> EspelhoPontoExport:
        parsed = _EspelhoHTMLParser()
        parsed.feed(snapshot.html)
        visible_text = " ".join(parsed.texts)
        normalized_text = normalize_server_name(visible_text)
        if "espelho" not in normalized_text or "ponto" not in normalized_text:
            raise EspelhoPontoParseError("invalid_page", "pagina aberta nao e um Espelho de Ponto")
        if normalize_server_name(expected_server) not in normalized_text and not (
            expected_identifier and expected_identifier in visible_text
        ):
            raise EspelhoPontoParseError("wrong_server", "pagina nao identifica o servidor selecionado")

        servidor = ServidorSelecionado(
            nome=self._server_name(visible_text, expected_server),
            identificador=self._identifier(visible_text) or expected_identifier,
            texto_visivel=self._server_label(parsed.texts),
        )
        periodo = self._period(visible_text)
        registros = [self._row_to_record(row) for row in parsed.rows]
        mensagens = self._messages(parsed.messages, visible_text)
        pagina = urlparse(snapshot.url).path or snapshot.url
        if not registros:
            return EspelhoPontoExport.empty(
                run_id=run_id,
                captured_at=snapshot.captured_at,
                servidor=servidor,
                periodo_referencia=periodo,
                mensagens=mensagens or ["Espelho sem registros"],
                pagina=pagina,
            )
        return EspelhoPontoExport(
            run_id=run_id,
            captured_at=snapshot.captured_at,
            servidor=servidor,
            periodo_referencia=periodo,
            mensagens=mensagens,
            registros=registros,
            pagina=pagina,
        )

    def _row_to_record(self, row: dict[str, list[str] | str]) -> RegistroDiaPonto:
        data = self._normalize_date(str(row.get("data") or ""))
        marcacoes = self.TIME_RE.findall(" ".join(row.get("marcacoes", [])))  # type: ignore[arg-type]
        return RegistroDiaPonto(
            data=data,
            dia_semana=str(row.get("dia_semana") or "") or None,
            marcacoes=marcacoes,
            ocorrencias=self._list(row.get("ocorrencias", [])),
            observacoes=self._list(row.get("observacoes", [])),
            situacao=str(row.get("situacao") or "") or None,
            textos_visiveis=self._list(row.get("textos_visiveis", [])),
            hr=row.get("hr"),  # type: ignore[arg-type]
            hc=row.get("hc"),  # type: ignore[arg-type]
            he=row.get("he"),  # type: ignore[arg-type]
            ha=row.get("ha"),  # type: ignore[arg-type]
            hh=row.get("hh"),  # type: ignore[arg-type]
            credito=row.get("credito"),  # type: ignore[arg-type]
            debito=row.get("debito"),  # type: ignore[arg-type]
            saldo_no_mes=row.get("saldo_no_mes"),  # type: ignore[arg-type]
            credito_acumulado=row.get("credito_acumulado"),  # type: ignore[arg-type]
            dnc=row.get("dnc"),  # type: ignore[arg-type]
        )

    @classmethod
    def _normalize_date(cls, value: str) -> str:
        match = cls.DATE_BR_RE.search(value)
        if not match:
            return value
        day, month, year = match.groups()
        return f"{year}-{month}-{day}"

    @staticmethod
    def _list(value: list[str] | str | object) -> list[str]:
        if isinstance(value, list):
            return [item for item in value if item]
        if isinstance(value, str) and value:
            return [value]
        return []

    @staticmethod
    def _period(text: str) -> str | None:
        match = re.search(r"Per[ií]odo\s*:\s*([A-Za-zçÇéÉíÍóÓúÚãÃõÕ]+/\d{4})", text, re.IGNORECASE)
        if match:
            return match.group(1)
        match = re.search(
            r"Espelho de Ponto\s*[-–]\s*([A-Za-zçÇéÉíÍóÓúÚãÃõÕ]+)\s+de\s+(\d{4})",
            text,
            re.IGNORECASE,
        )
        if match:
            return f"{match.group(1).capitalize()}/{match.group(2)}"
        return None

    @staticmethod
    def _identifier(text: str) -> str | None:
        match = re.search(r"(?:SIAPE|Matr[ií]cula)\s*:?\s*(\d{5,})", text, re.IGNORECASE)
        return match.group(1) if match else None

    @staticmethod
    def _server_name(text: str, expected: str) -> str:
        match = re.search(r"Servidor\s*:\s*([A-ZÁÉÍÓÚÃÕÇ ]+?)(?:\s*-\s*SIAPE|\s+SIAPE|$)", text, re.IGNORECASE)
        return " ".join(match.group(1).split()).upper() if match else expected.upper()

    @staticmethod
    def _server_label(texts: list[str]) -> str | None:
        for text in texts:
            if "servidor" in text.lower():
                return text
        return None

    @staticmethod
    def _messages(messages: list[str], visible_text: str) -> list[str]:
        if messages:
            return messages
        if "sem registros" in visible_text.lower():
            return ["Sem registros de ponto para o periodo"]
        return []
