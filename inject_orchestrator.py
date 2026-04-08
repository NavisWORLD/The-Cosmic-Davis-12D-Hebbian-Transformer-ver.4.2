import os

target_file = r"d:\Cosmos\Cosmos\web\server.py"
content = open(target_file, "r", encoding="utf-8").read()

if "orchestrator import router as _orch_router" not in content:
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == "if __name__ == '__main__':" or line.strip() == "if __name__ == \"__main__\":":
            lines.insert(i, "try:")
            lines.insert(i+1, "    from routes.orchestrator import router as _orch_router")
            lines.insert(i+2, "    app.include_router(_orch_router)")
            lines.insert(i+3, "except Exception as e:")
            lines.insert(i+4, "    print(f'Could not load Orchestrator routes: {e}')")
            lines.insert(i+5, "")
            break
    open(target_file, "w", encoding="utf-8").write("\n".join(lines))
    print("Injected!")
else:
    print("Already there!")
