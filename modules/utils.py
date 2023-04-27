import subprocess


def execute_command(command: str):
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, shell=True)
        stdout = result.stdout
        stderr = result.stderr
        return {"output": stdout, "error": stderr}
    except Exception as e:
        return {"error": str(e)}
