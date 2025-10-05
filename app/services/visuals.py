def default_mermaid(project_name: str) -> str:
    return f"""```mermaid\nmindmap\n  root(({project_name}))\n    Planning\n      Gather requirements\n      Align stakeholders\n    Delivery\n      Build solution\n      Validate outcomes\n    Risks\n      Dependencies\n      Compliance\n```"""
