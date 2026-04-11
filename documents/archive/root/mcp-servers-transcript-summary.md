# MCP 서버 요약

**원칙**: CLI·로컬 파일·공식 문서로 충분하면 MCP를 켜지 않아도 된다. 반복·정확도 이득이 클 때만 연결한다.

**세부 호출·보안·실패 시 대안**은 `.cursor/rules/anivault-mcp.mdc` 와 [AGENTS.md](../AGENTS.md)의 MCP 표를 따른다. API 키는 `mcp.json`에 직접 넣지 말고 환경 변수로 넘긴다.

| 성격 | 고려할 MCP | 없을 때 |
|------|------------|---------|
| 라이브러리 문서 | Context7 등 | 공식 문서 URL + 이 폴더에 요약 한 줄 |
| Git / PR | GitHub MCP, `gh` | `git log`, 웹 UI |
| Qt GUI | 로컬 `python -m anivault` | MCP는 문서 보조만 |
