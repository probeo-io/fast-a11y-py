"""Table rules: td-headers-attr, th-has-data-cells, td-has-header,
table-duplicate-name, table-fake-caption, scope-attr-valid
"""

from __future__ import annotations

from ..rule_engine import NodeCheckDetail, RuleRunResult, make_check
from ..tree import FastNode, find_by_tag, get_node_text, is_hidden_or_ancestor_hidden


def _find_ancestor_table(node: FastNode) -> FastNode | None:
    """Find the closest ancestor <table>."""
    current = node.parent
    while current:
        if current.tag == "table":
            return current
        current = current.parent
    return None


def _get_table_grid(table: FastNode) -> tuple[list[list[FastNode]], list[FastNode]]:
    """Get all <td> and <th> cells in a table, organized into a grid."""
    rows: list[list[FastNode]] = []
    all_cells: list[FastNode] = []

    def walk_for_rows(node: FastNode) -> None:
        if node.tag == "tr":
            cells: list[FastNode] = []
            for child in node.children:
                if child.tag in ("td", "th"):
                    cells.append(child)
                    all_cells.append(child)
            rows.append(cells)
        else:
            for child in node.children:
                walk_for_rows(child)

    walk_for_rows(table)
    return rows, all_cells


def _get_table_ids(table: FastNode) -> dict[str, FastNode]:
    """Get all elements with an id inside a table."""
    id_map: dict[str, FastNode] = {}

    def walk(node: FastNode) -> None:
        id_val = node.attrs.get("id")
        if id_val:
            id_map[id_val] = node
        for child in node.children:
            walk(child)

    walk(table)
    return id_map


class _TdHeadersAttr:
    rule_id = "td-headers-attr"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in find_by_tag(nodes, "td"):
            if is_hidden_or_ancestor_hidden(node):
                continue
            headers = node.attrs.get("headers")
            if not headers:
                continue
            table = _find_ancestor_table(node)
            if not table:
                continue
            table_ids = _get_table_ids(table)
            header_ids = headers.strip().split()
            invalid_ids = [hid for hid in header_ids if hid not in table_ids]
            self_ref = node.attrs.get("id") in header_ids if node.attrs.get("id") else False
            if invalid_ids or self_ref:
                reasons = []
                if invalid_ids:
                    reasons.append(f"invalid ID(s): {', '.join(invalid_ids)}")
                if self_ref:
                    reasons.append("references itself")
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("td-headers-attr", "serious",
                        f"headers attribute has {'; '.join(reasons)}")]
                )
            else:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("td-headers-attr", "serious",
                        "All headers IDs are valid references in the same table")]
                )
        return result


class _ThHasDataCells:
    rule_id = "th-has-data-cells"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        tables = find_by_tag(nodes, "table")
        for table in tables:
            if is_hidden_or_ancestor_hidden(table):
                continue
            role = table.attrs.get("role")
            if role in ("presentation", "none"):
                continue
            rows, all_cells = _get_table_grid(table)
            th_cells = [c for c in all_cells if c.tag == "th"]
            td_cells = [c for c in all_cells if c.tag == "td"]
            if not th_cells:
                continue
            if not td_cells:
                for th in th_cells:
                    result.violations.append(th)
                    result.check_details[id(th)] = NodeCheckDetail(
                        all=[make_check("th-has-data-cells", "serious",
                            "Table header has no associated data cells")]
                    )
                continue
            for th in th_cells:
                th_id = th.attrs.get("id")
                has_associated = False
                if th_id:
                    has_associated = any(
                        td.attrs.get("headers") and th_id in td.attrs["headers"].strip().split()
                        for td in td_cells
                    )
                if not has_associated:
                    for ri, row in enumerate(rows):
                        th_index = row.index(th) if th in row else -1
                        if th_index >= 0:
                            has_associated = any(c.tag == "td" for c in row)
                            if not has_associated:
                                for rj in range(len(rows)):
                                    if rj != ri and th_index < len(rows[rj]):
                                        if rows[rj][th_index].tag == "td":
                                            has_associated = True
                                            break
                            break
                if has_associated:
                    result.passes.append(th)
                    result.check_details[id(th)] = NodeCheckDetail(
                        all=[make_check("th-has-data-cells", "serious",
                            "Table header has associated data cells")]
                    )
                else:
                    result.violations.append(th)
                    result.check_details[id(th)] = NodeCheckDetail(
                        all=[make_check("th-has-data-cells", "serious",
                            "Table header has no associated data cells")]
                    )
        return result


class _TdHasHeader:
    rule_id = "td-has-header"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        tables = find_by_tag(nodes, "table")
        for table in tables:
            if is_hidden_or_ancestor_hidden(table):
                continue
            role = table.attrs.get("role")
            if role in ("presentation", "none"):
                continue
            rows, all_cells = _get_table_grid(table)
            num_rows = len(rows)
            num_cols = max((len(r) for r in rows), default=0)
            if num_rows < 3 or num_cols < 3:
                continue
            th_cells = [c for c in all_cells if c.tag == "th"]
            if not th_cells:
                for row in rows:
                    for cell in row:
                        if cell.tag == "td" and get_node_text(cell):
                            result.violations.append(cell)
                            result.check_details[id(cell)] = NodeCheckDetail(
                                all=[make_check("td-has-header", "serious",
                                    "Data cell in a large table has no associated header")]
                            )
                continue
            th_ids = {th.attrs["id"] for th in th_cells if th.attrs.get("id")}
            for ri, row in enumerate(rows):
                for ci, cell in enumerate(row):
                    if cell.tag != "td":
                        continue
                    if not get_node_text(cell):
                        continue
                    has_header = False
                    headers_attr = cell.attrs.get("headers")
                    if headers_attr:
                        has_header = any(hid in th_ids for hid in headers_attr.strip().split())
                    if not has_header:
                        has_header = any(c.tag == "th" for c in row)
                    if not has_header:
                        for rj in range(len(rows)):
                            if ci < len(rows[rj]) and rows[rj][ci].tag == "th":
                                has_header = True
                                break
                    if has_header:
                        result.passes.append(cell)
                        result.check_details[id(cell)] = NodeCheckDetail(
                            all=[make_check("td-has-header", "serious",
                                "Data cell has an associated table header")]
                        )
                    else:
                        result.violations.append(cell)
                        result.check_details[id(cell)] = NodeCheckDetail(
                            all=[make_check("td-has-header", "serious",
                                "Data cell in a large table has no associated header")]
                        )
        return result


class _TableDuplicateName:
    rule_id = "table-duplicate-name"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for table in find_by_tag(nodes, "table"):
            if is_hidden_or_ancestor_hidden(table):
                continue
            summary = (table.attrs.get("summary") or "").strip().lower()
            caption_node = next((c for c in table.children if c.tag == "caption"), None)
            caption = get_node_text(caption_node).strip().lower() if caption_node else ""
            if not summary or not caption:
                continue
            if summary == caption:
                result.violations.append(table)
                result.check_details[id(table)] = NodeCheckDetail(
                    all=[make_check("table-duplicate-name", "minor",
                        "Table caption and summary have identical text")]
                )
            else:
                result.passes.append(table)
                result.check_details[id(table)] = NodeCheckDetail(
                    all=[make_check("table-duplicate-name", "minor",
                        "Table caption and summary are different")]
                )
        return result


class _TableFakeCaption:
    rule_id = "table-fake-caption"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for table in find_by_tag(nodes, "table"):
            if is_hidden_or_ancestor_hidden(table):
                continue
            role = table.attrs.get("role")
            if role in ("presentation", "none"):
                continue
            rows, _ = _get_table_grid(table)
            if len(rows) < 2:
                continue
            first_row = rows[0]
            if len(first_row) == 1:
                cell = first_row[0]
                try:
                    colspan = int(cell.attrs.get("colspan", "1"))
                except ValueError:
                    colspan = 1
                max_cols = max((len(r) for r in rows[1:]), default=0)
                if colspan >= max_cols and max_cols > 1 and get_node_text(cell):
                    result.violations.append(table)
                    result.check_details[id(table)] = NodeCheckDetail(
                        all=[make_check("table-fake-caption", "serious",
                            "First row contains a single cell spanning all columns -- use <caption> instead")]
                    )
                    continue
            result.passes.append(table)
            result.check_details[id(table)] = NodeCheckDetail(
                all=[make_check("table-fake-caption", "serious",
                    "Table does not use a fake caption")]
            )
        return result


VALID_SCOPES = frozenset({"col", "row", "colgroup", "rowgroup"})


class _ScopeAttrValid:
    rule_id = "scope-attr-valid"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in nodes:
            if is_hidden_or_ancestor_hidden(node):
                continue
            if "scope" not in node.attrs:
                continue
            scope = node.attrs["scope"].lower()
            if node.tag != "th":
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("scope-attr-valid", "moderate",
                        "scope attribute is only valid on <th> elements")]
                )
                continue
            if scope in VALID_SCOPES:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("scope-attr-valid", "moderate",
                        f'scope attribute has a valid value: "{scope}"')]
                )
            else:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("scope-attr-valid", "moderate",
                        f'scope attribute has an invalid value: "{scope}"')]
                )
        return result


table_rules = [
    _TdHeadersAttr(),
    _ThHasDataCells(),
    _TdHasHeader(),
    _TableDuplicateName(),
    _TableFakeCaption(),
    _ScopeAttrValid(),
]
