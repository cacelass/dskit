"""
agents.agents.env_agent — Gestión del entorno de desarrollo.

Conoce `pyproject.toml`, `uv.lock` y el Makefile. Verifica que el entorno
esté sincronizado, que la versión de Python sea correcta y que las
dependencias estén instaladas.
"""

from __future__ import annotations

import os
import platform
import re
import sys
from pathlib import Path

from agents.core.base_agent import AgentResult, BaseAgent
from agents.core.registry import register_agent
from agents.exceptions import MissingDependencyError
from agents.tools.process_tool import run_command


@register_agent
class EnvAgent(BaseAgent):
    name = "env"
    description = (
        "Gestiona el entorno de desarrollo: verifica versión de Python, "
        "sincroniza dependencias con uv, configura pre-commit hooks."
    )
    capabilities = [
        "entorno", "environment", "uv", "python version",
        "venv", "pre-commit", "sync", "lock",
    ]

    def actions(self) -> dict:
        return {
            "check_python_version": self.check_python_version,
            "sync": self.sync,
            "check_lock_sync": self.check_lock_sync,
            "add_dependency": self.add_dependency,
            "info": self.info,
        }

    def _pyproject(self) -> dict | None:
        import tomllib
        try:
            with open(self.ctx.pyproject_file, "rb") as f:
                return tomllib.load(f)
        except (FileNotFoundError, tomllib.TOMLDecodeError):
            return None

    def _language(self) -> str:
        """Lenguaje del proyecto segun .copier-answers.yml (default: python)."""
        return str(self.ctx.config.extra.get("language", "python")).lower()

    def check_python_version(self) -> AgentResult:
        if self._language() == "java":
            result = run_command(["java", "-version"], cwd=self.ctx.root)
            raw = f"{result.stderr}\n{result.stdout}"
            match = re.search(r'version "(\d+)(?:\.(\d+))?', raw)
            if not match:
                return AgentResult(False, self.name, "check_python_version", "java no disponible en PATH.")
            major, minor = int(match.group(1)), int(match.group(2) or 0)
            if major == 1:  # Java 8 reporta "1.8"
                major = minor
            required = str(self.ctx.config.extra.get("java_version", "17")).split(".")[0]
            try:
                required_n = int(required)
            except ValueError:
                required_n = 17
            return AgentResult(
                major >= required_n, self.name, "check_python_version",
                f"Java {major} (requiere {required_n}+)",
                data={"current": f"{major}", "required": f"{required_n}+"},
            )
        pyproject = self._pyproject()
        if pyproject is None:
            return AgentResult(False, self.name, "check_python_version", "No se encontró pyproject.toml.")

        requires = pyproject.get("project", {}).get("requires-python", "")
        current = f"{sys.version_info.major}.{sys.version_info.minor}"
        return AgentResult(
            True, self.name, "check_python_version",
            f"Python {current} (requiere {requires})",
            data={"current": current, "required": requires},
            warnings=[] if not requires or current in requires else [f"Python {current} no está en el rango {requires}"],
        )

    def sync(self, *, extras: str | None = None) -> AgentResult:
        """Ejecuta `uv sync` (Python) o `./mvnw dependency:go-offline` (Java)."""
        if self._language() == "java":
            mvnw = "mvnw.cmd" if os.name == "nt" else "./mvnw"
            result = run_command([mvnw, "-q", "dependency:go-offline"], cwd=self.ctx.root)
            if not result.ok:
                return AgentResult(False, self.name, "sync", f"mvnw dependency:go-offline falló: {result.stderr.strip()}")
            return AgentResult(True, self.name, "sync", "Dependencias Maven resueltas correctamente.")
        cmd = ["uv", "sync"]
        if extras:
            for ext in extras.split(","):
                cmd.extend(["--extra", ext.strip()])
        result = run_command(cmd, cwd=self.ctx.root)
        if not result.ok:
            return AgentResult(False, self.name, "sync", f"uv sync falló: {result.stderr.strip()}")
        return AgentResult(True, self.name, "sync", "Entorno sincronizado correctamente.")

    def check_lock_sync(self) -> AgentResult:
        """Verifica pyproject/uv.lock (Python) o el wrapper de Maven (Java)."""
        if self._language() == "java":
            mvnw = self.ctx.root / ("mvnw.cmd" if os.name == "nt" else "mvnw")
            props = self.ctx.root / ".mvn" / "wrapper" / "maven-wrapper.properties"
            missing = [str(p) for p in (mvnw, props) if not p.exists()]
            if missing:
                return AgentResult(
                    False, self.name, "check_lock_sync",
                    f"Falta el wrapper de Maven: {', '.join(missing)}.",
                )
            return AgentResult(
                True, self.name, "check_lock_sync",
                "Wrapper de Maven presente; las dependencias se resuelven con ./mvnw.",
            )
        result = run_command(["uv", "lock", "--check"], cwd=self.ctx.root)
        if result.ok:
            return AgentResult(True, self.name, "check_lock_sync", "pyproject.toml y uv.lock están sincronizados.")
        return AgentResult(
            False, self.name, "check_lock_sync",
            f"uv.lock desincronizado: {result.stderr.strip()}. Ejecuta 'uv lock' para actualizarlo.",
        )

    def add_dependency(self, *, package: str, extra_group: str | None = None) -> AgentResult:
        """Añade una dependencia con `uv add` (Python). En Java se edita pom.xml."""
        if self._language() == "java":
            return AgentResult(
                False, self.name, "add_dependency",
                "En Java la dependencia se añade en pom.xml (Maven resuelve la versión).",
                needs=["groupId:artifactId[:version]"],
            )
        cmd = ["uv", "add", package]
        if extra_group:
            cmd.extend(["--optional", extra_group])
        result = run_command(cmd, cwd=self.ctx.root)
        if not result.ok:
            return AgentResult(False, self.name, "add_dependency", f"uv add falló: {result.stderr.strip()}")
        return AgentResult(True, self.name, "add_dependency", f"Dependencia '{package}' añadida.")

    def info(self) -> AgentResult:
        env_file = self.ctx.root / ".env"
        has_env = env_file.exists()
        warnings = []
        if not has_env:
            warnings.append("No hay .env — copia .env.example a .env y rellena las claves necesarias.")

        if self._language() == "java":
            jdk_result = run_command(["java", "-version"], cwd=self.ctx.root)
            raw = f"{jdk_result.stderr}\n{jdk_result.stdout}"
            match = re.search(r'version "([^"]+)"', raw)
            java_v = match.group(1) if match else "no instalado"
            mvnw = self.ctx.root / ("mvnw.cmd" if os.name == "nt" else "mvnw")
            data = {
                "language": "java",
                "java_version": java_v,
                "framework": self.ctx.config.extra.get("framework"),
                "db": self.ctx.config.extra.get("db"),
                "project_name": self.ctx.config.project_name,
                "mvnw": mvnw.exists(),
                "platform": sys.platform,
                "has_env": has_env,
            }
            return AgentResult(
                True, self.name, "info",
                f"Java {java_v} ({self.ctx.config.extra.get('framework', '?')})",
                data=data, warnings=warnings,
            )

        pyproject = self._pyproject()
        python_v = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        uv_result = run_command(["uv", "--version"], cwd=self.ctx.root)
        uv_v = uv_result.stdout.strip() if uv_result.ok else "no instalado"

        gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not gemini_key:
            warnings.append("GEMINI_API_KEY no está configurada — graphify no podrá hacer extracción semántica (solo AST), obtenla gratis en ai.google.dev.")

        data = {
            "python_version": python_v,
            "uv_version": uv_v,
            "project_name": pyproject.get("project", {}).get("name") if pyproject else None,
            "platform": sys.platform,
            "has_env": has_env,
            "gemini_key_set": bool(gemini_key),
        }
        return AgentResult(True, self.name, "info", f"Python {python_v}, uv {uv_v}", data=data, warnings=warnings)
