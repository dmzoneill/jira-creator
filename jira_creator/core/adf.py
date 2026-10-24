"""Convert Atlassian Document Format (ADF) to plain text.

ADF is the structured document format used by Jira Cloud API v3
for rich text fields like description, acceptance criteria, and comments.
"""

from typing import Any

_STATIC_LEAF_NODES = {
    "hardBreak": "\n",
    "mediaGroup": "",
    "mediaSingle": "",
    "rule": "---\n",
}


def _handle_leaf_node(node, node_type):
    """Handle ADF leaf nodes that don't require child processing."""
    if node_type in _STATIC_LEAF_NODES:
        return _STATIC_LEAF_NODES[node_type]
    if node_type == "text":
        return node.get("text", "")
    if node_type == "mention":
        return node.get("attrs", {}).get("text", "")
    if node_type == "emoji":
        return node.get("attrs", {}).get("shortName", "")
    return None


def _handle_block_node(node_type, children_text):
    """Handle ADF block/container nodes."""
    if node_type == "doc":
        return children_text.strip()
    if node_type in ("paragraph", "heading", "codeBlock"):
        return children_text + "\n"
    if node_type == "listItem":
        return "- " + children_text
    if node_type == "blockquote":
        lines = children_text.strip().split("\n")
        return "\n".join("> " + line for line in lines) + "\n"
    return None


def adf_to_text(node) -> str:
    """Convert an ADF document node to plain text.

    Arguments:
        node: ADF node (dict) or plain string

    Returns:
        Plain text representation of the ADF content
    """
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if not isinstance(node, dict):
        return str(node)

    node_type = node.get("type", "")
    content = node.get("content", [])

    leaf_result = _handle_leaf_node(node, node_type)
    if leaf_result is not None:
        return leaf_result

    children_text = "".join(adf_to_text(child) for child in content)

    block_result = _handle_block_node(node_type, children_text)
    if block_result is not None:
        return block_result

    return children_text


def ensure_text(value) -> str:
    """Ensure a field value is plain text, converting from ADF if needed.

    Arguments:
        value: String, ADF dict, or None

    Returns:
        Plain text string
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict) and value.get("type") == "doc":
        return adf_to_text(value)
    return str(value)


def _parse_inline_markup(text: str) -> list:
    """Parse inline Jira wiki markup into ADF inline nodes.

    Handles *bold*, _italic_, {{monospace}}, and [text|url] links.
    """
    import re

    nodes: list[dict[str, Any]] = []
    # Pattern matches: [text|url], *bold*, _italic_, {{monospace}}, or plain text
    pattern = re.compile(
        r"\[([^|]+)\|([^\]]+)\]"  # [text|url] link
        r"|\{\{(.+?)\}\}"  # {{monospace}}
        r"|\*(.+?)\*"  # *bold*
        r"|_(.+?)_"  # _italic_
        r"|([^[*_{]+(?:[*_{[](?![^[*_{]*(?:\]|\*|_|\}\})))?)"  # plain text (non-greedy fallback)
    )

    pos = 0
    while pos < len(text):
        m = pattern.search(text, pos)
        if not m:
            remaining = text[pos:]
            if remaining:
                nodes.append({"type": "text", "text": remaining})
            break

        # Add any text before the match
        if m.start() > pos:
            nodes.append({"type": "text", "text": text[pos : m.start()]})

        if m.group(1) is not None:
            # [text|url] link
            nodes.append(
                {
                    "type": "text",
                    "text": m.group(1),
                    "marks": [{"type": "link", "attrs": {"href": m.group(2)}}],
                }
            )
        elif m.group(3) is not None:
            # {{monospace}}
            nodes.append(
                {
                    "type": "text",
                    "text": m.group(3),
                    "marks": [{"type": "code"}],
                }
            )
        elif m.group(4) is not None:
            # *bold*
            nodes.append(
                {
                    "type": "text",
                    "text": m.group(4),
                    "marks": [{"type": "strong"}],
                }
            )
        elif m.group(5) is not None:
            # _italic_
            nodes.append(
                {
                    "type": "text",
                    "text": m.group(5),
                    "marks": [{"type": "em"}],
                }
            )
        else:
            # Plain text
            nodes.append({"type": "text", "text": m.group(6)})

        pos = m.end()

    return nodes if nodes else [{"type": "text", "text": text}]


def _parse_table_row(line: str, is_header: bool = False) -> dict:
    """Parse a Jira wiki table row into an ADF tableRow node."""
    # Header rows use ||cell|| syntax, data rows use |cell| syntax
    if is_header:
        cells = [c.strip() for c in line.split("||") if c.strip()]
    else:
        cells = [c.strip() for c in line.split("|") if c.strip()]

    row_content: list[dict[str, Any]] = []
    cell_type = "tableHeader" if is_header else "tableCell"
    for cell in cells:
        row_content.append(
            {
                "type": cell_type,
                "content": [{"type": "paragraph", "content": _parse_inline_markup(cell)}],
            }
        )

    return {"type": "tableRow", "content": row_content}


def text_to_adf(  # pylint: disable=too-many-locals,too-many-branches,too-many-statements,too-many-boolean-expressions
    text: str,
) -> dict:
    """Convert Jira wiki markup text to Atlassian Document Format (ADF).

    Supports headings (h1.-h6.), bullet lists (* ), numbered lists (# ),
    tables (||header|| and |cell|), horizontal rules (----),
    inline markup (*bold*, _italic_, {{monospace}}, [text|url]),
    and plain paragraphs.

    Arguments:
        text: Plain text or Jira wiki markup string

    Returns:
        ADF document dict
    """
    import re

    if not text or not text.strip():
        return {
            "version": 1,
            "type": "doc",
            "content": [{"type": "paragraph", "content": []}],
        }

    lines = text.split("\n")
    content: list[dict[str, Any]] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            i += 1
            continue

        # Headings: h1. through h6.
        heading_match = re.match(r"^h([1-6])\.\s+(.+)$", stripped)
        if heading_match:
            level = int(heading_match.group(1))
            text_content = heading_match.group(2)
            content.append(
                {
                    "type": "heading",
                    "attrs": {"level": level},
                    "content": _parse_inline_markup(text_content),
                }
            )
            i += 1
            continue

        # Horizontal rule
        if stripped.startswith("----"):
            content.append({"type": "rule"})
            i += 1
            continue

        # Table: lines starting with || (header) or | (data)
        if stripped.startswith("||") or (stripped.startswith("|") and not stripped.startswith("|+")):
            table_rows: list[dict[str, Any]] = []
            while i < len(lines):
                row_stripped = lines[i].strip()
                if row_stripped.startswith("||"):
                    table_rows.append(_parse_table_row(row_stripped, is_header=True))
                elif row_stripped.startswith("|"):
                    table_rows.append(_parse_table_row(row_stripped, is_header=False))
                else:
                    break
                i += 1
            if table_rows:
                content.append({"type": "table", "content": table_rows})
            continue

        # Bullet list: lines starting with * or -
        if re.match(r"^[*\-]\s+", stripped):
            list_items: list[dict[str, Any]] = []
            while i < len(lines):
                item_match = re.match(r"^[*\-]\s+(.+)$", lines[i].strip())
                if not item_match:
                    break
                list_items.append(
                    {
                        "type": "listItem",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": _parse_inline_markup(item_match.group(1)),
                            }
                        ],
                    }
                )
                i += 1
            content.append({"type": "bulletList", "content": list_items})
            continue

        # Numbered list: lines starting with #
        if re.match(r"^#\s+", stripped):
            list_items = []
            while i < len(lines):
                item_match = re.match(r"^#\s+(.+)$", lines[i].strip())
                if not item_match:
                    break
                list_items.append(
                    {
                        "type": "listItem",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": _parse_inline_markup(item_match.group(1)),
                            }
                        ],
                    }
                )
                i += 1
            content.append({"type": "orderedList", "content": list_items})
            continue

        # Plain paragraph (collect consecutive non-empty, non-special lines)
        para_lines = []
        while i < len(lines):
            ls = lines[i].strip()
            if (
                not ls
                or re.match(r"^h[1-6]\.\s+", ls)
                or ls.startswith(("||", "|", "----"))
                or re.match(r"^[*\-]\s+", ls)
                or re.match(r"^#\s+", ls)
            ):
                break
            para_lines.append(ls)
            i += 1

        if para_lines:
            inline_content: list[dict[str, Any]] = []
            for j, pl in enumerate(para_lines):
                if j > 0:
                    inline_content.append({"type": "hardBreak"})
                inline_content.extend(_parse_inline_markup(pl))
            content.append({"type": "paragraph", "content": inline_content})

    return {
        "version": 1,
        "type": "doc",
        "content": content if content else [{"type": "paragraph", "content": []}],
    }


def ensure_adf(value) -> dict:
    """Ensure a field value is ADF format, converting from plain text if needed.

    Arguments:
        value: String, ADF dict, or None

    Returns:
        ADF document dict
    """
    if value is None:
        return text_to_adf("")
    if isinstance(value, dict) and value.get("type") == "doc":
        return value
    if isinstance(value, str):
        return text_to_adf(value)
    return text_to_adf(str(value))
