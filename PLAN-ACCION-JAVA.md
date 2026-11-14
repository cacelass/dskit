# PLAN-ACCION-JAVA — v2 (revisada) · Qué hacer tras el informe E2E

Basado en `TEST-PLAN-JAVA.md` (resultados Nov 2026) y `PLAN-JAVA.md` (§9).
Estado: propuesta revisada para ejecutar.

### Qué se ha corregido o matizado respecto a v1

1. **No romper el modo Python.** Los fixes de agentes (A0.2) y las reescrituras
   (A1.3) deben ser *language-aware* (`config.extra["language"]`), no
   sustituciones: el árbol Python sigue existiendo y sus 663 tests siguen
   siendo la red de seguridad.
2. **JaCoCo ≥80% no puede aplicarse al proyecto recién generado** (solo hay
   `contextLoads`, que ya no ejecuta el job tras F2): hace falta un test semilla
   del job, exclusiones estándar y umbral configurable.
3. **OWASP dependency-check exige API key de NVD** (rate-limit): el análisis de
   vulnerabilidades va por Trivy + OSV, y OWASP queda como opcional.
4. **`refactor` Java se descarta por ahora** (el agente actual es AST-Python;
   no se reimplementa un mutador casero para Java — si acaso OpenRewrite en el
   futuro). `graph` (figuras) se elimina para Java, no se reescribe.
5. **Orden de dominios:** `migrations` antes que `batch` (JAVA-007 se queda con
   el esquema `BATCH_*`, como ya dice el SPEC). Multi-módulo sale del alcance
   de `architecture` (regla del proyecto: nada de abstracción anticipada).
6. **El fork no tiene versión alineada** (README 1.15.1, pyproject 1.16.0,
   `dskit_version` 1.16.0): se fija un esquema de versionado propio + tag.
7. **Los checks Java de la rúbrica viven en `init.sh`** (el gate solo lee su
   informe), y el reviewer-as-PR-check depende del CI Java (A1.2).
8. **Eliminar el árbol Python es L, no M**, y se hace tras el H1 completo (CI
   Java verde + agentes podados), para no perder la red de seguridad antes de
   tiempo.
9. **A0.1:** el JSON condicional del backlog debe mantener `depends_on`
   coherente por rama, y `plan scope` (entrevista DS) se adapta en JAVA-005;
   hasta entonces SCOPE-001 Java no lo referencia.
10. **La fórmula de conteo de agentes** (`{{ 19 + ... }}`) debe incluir
    `language` cuando se poden/reescriban agentes (A1.3), o `prompts-check`
    fallará.

---

## 1. Análisis del informe

### Qué demuestra la prueba

- El **núcleo del arnés funciona en Java**: render, puerta
  (`./mvnw verify` + `contextLoads`), backlog, `finish` con GATE-1..4 y
  evals (`harness` 14/14, `contracts` PASS).
- El **template genera proyectos Spring Boot/Batch reales**: 5 combos y un
  procesador de pedidos con chunk processing, tests end-to-end y `java -jar`.
- **La puerta muerde**: con un test roto, `harness finish` rechaza el cierre.
- **8 bugs corregidos** (F1, F2, F3, F4, F5, F8, F11, F14), casi todos solo
  visibles en Windows o con jobs reales — el CI Linux no los habría visto.

### Qué queda abierto

| Tipo | Hallazgo | Destino |
|---|---|---|
| Feature | Backlog semilla de DS en proyectos Java (F6) | JAVA-003 |
| Feature | `commit_feature` sin bump de `pom.xml` (F7) | JAVA-005 |
| Feature | `doctor`/`env` con checks Python (F9) | JAVA-005 |
| Feature | `suggest_commit_message` ignora untracked (F10) | JAVA-005 |
| Entorno | `make` no instalado en Windows (F12) | — (CI Linux) |
| Entorno | `prompts_sync` en render con `--skip-tasks` (F13) | — |

### Límites de la prueba

1. **Pipeline de calidad JVM inexistente** (JaCoCo, Spotless, PIT, Trivy).
2. **CI del fork**: matriz Python-only y Actions desactivados (JAVA-013).
3. **Agentes Python/DS**: `test` (pytest), `dependency` (PyPI), `doctor`
   (`pyproject.toml`)…
4. **Dominios sin dueño**: batch/migrations/security/api/architecture/obs.
5. **Ejecución real no cubierta**: Postgres vivo, JDK 21 ejecutado, Docker,
   `copier update`, render interactivo.

**Diagnóstico:** esqueleto y gobierno probados; falta la capa que convierte el
arnés en *garantía* para un equipo Java: calidad, agentes y CI.

---

## 2. Priorización (revisada)

| Prioridad | Acción | Impacto | Esfuerzo | Depende de |
|---|---|---|---|---|
| **P0** | A0.1 JAVA-003 — semilla de backlog Java | Alto | S | — |
| **P0** | A0.2 JAVA-005a — fixes language-aware (commit/doctor/env) | Alto | S-M | — |
| **P0** | A0.3 — versionado del fork + primer tag | Medio | S | — |
| **P1** | A1.1 JAVA-012 — pipeline de calidad (fase A: JaCoCo+Spotless) | Muy alto | M | P0 |
| **P1** | A1.1b JAVA-012b — fase B: PIT, análisis estático y seguridad | Muy alto | M | A1.1 |
| **P1** | A1.2 JAVA-013 — CI Java + Actions del fork | Muy alto | M | A1.1 |
| **P1** | A1.3 JAVA-005b — reescritura/poda de agentes | Muy alto | L | P0 |
| **P2** | A2.1 JAVA-007 — agente `migrations` | Alto | M | A1.3 |
| **P2** | A2.2 JAVA-006 — agente `batch` | Muy alto | L | A2.1 |
| **P2** | A2.3 JAVA-008 — agente `security` | Alto | M | A1.3 |
| **P2** | A2.4 JAVA-011 — observabilidad (`ops`) | Alto | M | A1.3 |
| **P2** | A2.5 JAVA-009 — agente `api` Spring | Medio | M | A1.3 |
| **P2** | A2.6 JAVA-010 — agente `architecture` (ArchUnit) | Medio | S-M | A1.3 |
| **P3** | A3.1 JAVA-014 — rúbrica Java (checks en `init.sh` + R-criterios) | Alto | M | A2.1–A2.4 |
| **P3** | A3.2 JAVA-004 — agentes que razonan (prompts) | Alto | S-M | A3.1 |
| **P3** | A3.3 JAVA-015 — DX (PR check, IntelliJ, fricción) | Medio | M | A1.2 + A3.1 |
| **P4** | A4.1 — eliminar el árbol Python/DS | Estratégico | L | H1 completo |
| **P4** | A4.2 JAVA-001b — Gradle | Bajo | M | — |
| **P4** | A4.3 — segunda ronda E2E (Postgres real, JDK 21, update) | Alto | S | A1.2 |

---

## 3. Detalle de acciones

### P0 — Cerrar lo abierto del E2E

**A0.1 — JAVA-003: semilla de backlog Java**
`harness/featureslist.json` con `{% if language == 'java' %}`: `SCOPE-001`
(objetivo y métrica del servicio/batch, **sin** referencia a `plan scope`
hasta que la entrevista tenga variante Java en JAVA-005), `ARCH-001`
(arquitectura y paquetes), `DB-001` (modelo + migraciones), `JOB-001` (job con
restartability, si batch), `API-001` (si web), `SEC-001` (si security),
`OBS-001` (si observability), `CI-001`. `depends_on` coherente por rama.
**Done:** `harness next` en render Java propone la semilla Java; `init.sh`
valida el JSON en ambos idiomas; `validate_template.py` 0 bugs.
**Esfuerzo:** S · **Riesgo:** bajo (JSON condicional, vigilar `depends_on`).

**A0.2 — JAVA-005a: fixes pequeños de agentes (language-aware)**
Todos leen `language` de `.copier-answers.yml` (`config.extra`) y **conservan
la rama Python**:
- `git commit_feature`/`tag_release`: si `language == java`, bump de
  `<version>` en `pom.xml` y del badge `Version-…` del README generado;
  Python queda como está. Coordinar con `documentation` (CHANGELOG/README).
- `git suggest_commit_message`: incluir untracked (`git status --porcelain`),
  respetando `.gitignore` (sin ruido de `target/`).
- `doctor`/`env`: rama Java (`pom.xml`, JDK, `mvnw`, `application.yml`,
  `target/`) junto a la rama Python actual.
**Done:** tests portados/ampliados (los 15 de `test_doctor_agent.py` pasan en
ambas ramas) + E2E sobre el render Java.
**Esfuerzo:** S-M · **Riesgo:** romper la rama Python (los tests lo acotan).

**A0.3 — Versionado del fork**
Alinear versión en los tres sitios (README badge, `pyproject.toml`,
`copier.yml` `dskit_version`) a un esquema propio, p. ej. `2.0.0-java` o
`1.16.0-java.1`, y crear el primer tag. Los proyectos generados registran
`dskit_version` en `.copier-answers.yml` para `copier update`.
**Done:** una sola fuente (copier.yml) y tag `v…` pusheado.
**Esfuerzo:** S · **Riesgo:** ninguno relevante.

### P1 — Fiabilidad para un equipo Java

**A1.1 — JAVA-012 (fase A): cobertura y formato**
- JaCoCo: plugin `jacoco-maven-plugin` (`prepare-agent` + `report` + `check`)
  con umbral **configurable** `${COVERAGE_MIN:0.80}`; exclusiones estándar
  (`*Config`, `Application`, records); **test semilla** del `demoJob`
  (equivalente a `PedidoJobTest`) para que el proyecto recién generado
  **cumpla el umbral sin tocar nada** — sin este test, la puerta nacería roja.
- Spotless (google-java-format) con `check` en `verify` y `apply` en
  `make format`. Checkstyle/PMD quedan para la fase B (no sobre-configurar).
**Done:** `./mvnw verify` verde en render limpio con cobertura ≥ umbral;
`make format` aplica y `verify` detecta formato roto.
**Esfuerzo:** M · **Riesgo:** umbral vs semilla (el test semilla lo resuelve).

**A1.1b — JAVA-012 (fase B): mutación, estática y seguridad**
- PIT: plugin `pitest-maven` + `pitest-junit5-plugin`, `mutationThreshold`
  configurable, `targetClasses` excluyendo config; perfil `mutation` fuera del
  `verify` (lento). `make mutation`.
- Estática: Error Prone (plugin del compilador) con `-Werror` **sin NullAway
  por ahora** (exige anotaciones; opt-in posterior). Checkstyle/PMD y CRAP
  calculado con JaCoCo + complejidad de PMD (descartado `crap4j`, sin
  mantenimiento).
- Seguridad: **Trivy** (+ OSV-Scanner) como principal y SBOM con cyclonedx;
  OWASP dependency-check solo opcional (NVD exige API key y rate-limita).
**Done:** `make mutation` mata un mutante sembrado; `make security` corre
Trivy/SBOM; documentado.
**Esfuerzo:** M · **Riesgo:** tiempo de PIT (perfil aparte, incremental),
falsos positivos (suppressions versionadas).

**A1.2 — JAVA-013: CI Java**
- Workflow del template **condicional por lenguaje**: hoy los renders Java
  excluyen `/.github/` entero; se sustituye por
  `template/.github/workflows/ci.yml` con rama Java (`setup-java` 17 y 21,
  caché `.m2`, `./mvnw verify`, JaCoCo, PIT opcional, SBOM + Trivy) y rama
  Python actual.
- dskit CI: job **`smoke-java` separado** (no mezclar en el job Python del
  `smoke` actual) + `ci-generado` con render Java.
- Activar Actions en el fork (paso manual) y verificar el badge del README.
**Done:** CI del fork verde; el workflow entregado pasa en un proyecto
generado (job `ci-generado`).
**Esfuerzo:** M · **Riesgo:** tiempo de Maven en Actions (caché), forks con
Actions desactivados.

**A1.3 — JAVA-005b: reescritura y poda de agentes**
- Reescribir (language-aware): `test` (JUnit/JaCoCo), `dependency`
  (Maven/OWASP/versions), `cicd` (workflow Java), `make` (targets Java),
  `doc` (Javadoc), `env`, `plan` (entrevista `plan scope` Java).
- **Eliminar para Java**: `graph` (era para figuras) y `refactor`
  (AST-Python; Java queda fuera de alcance, opcional OpenRewrite futuro).
- Podar: `data`, `ml`, `mlflow`, `notebook` (+ prompts/tests; contratos
  tolerados).
- `contracts.py`: recursos Java (`pom.xml`, `application.yml`,
  `db/migration/`, configs de batch).
- **Actualizar la fórmula de conteo de agentes** en AGENTS.md/prompts con
  `language` + `make prompts-check` en CI.
**Done:** `agents.evals.runner` verde en render Java; agentes podados
ausentes; `prompts-check` verde.
**Esfuerzo:** L · **Riesgo:** regresiones (portar las 663 pruebas de
referencia agente a agente).

### P2 — Dominios Java (orden: migrations → batch → security/ops → api/arch)

| Acción | Qué añade | Caso canónico |
|---|---|---|
| A2.1 JAVA-007 `migrations` | Flyway/Liquibase, checksum, undo, out-of-order; **dueño del esquema `BATCH_*`** | editar migración aplicada → rechazo |
| A2.2 JAVA-006 `batch` | Job/Step, chunk, retry/skip, restartability, idempotencia | writer sin transacción → rechazo; job relanzado que duplica → rechazo |
| A2.3 JAVA-008 `security` | Spring Security/JWT/CORS + gate de actuator expuesto | management endpoint público en prod → rechazo |
| A2.4 JAVA-011 `ops` | Actuator/Micrometer/OTel/MDC, métricas por step, logging JSON | servicio sin health real → no `done` |
| A2.5 JAVA-009 `api` | REST, DTOs + Bean Validation, OpenAPI, versionado | breaking change sin versión → rechazo |
| A2.6 JAVA-010 `architecture` | ArchUnit, límites de capas (**módulo único**; multi-módulo solo si hay ≥2 módulos reales) | controller→repository directo → test ArchUnit falla |

Cada dominio: agente + tool + prompt + workflow skill + contrato + tests +
benchmarks de routing. La verificación de A2.1/A2.2 incluye Postgres real vía
Testcontainers (absorbe esa parte de la antigua A4.3).
**Esfuerzo:** M cada uno (batch L, architecture S-M).

### P3 — Gobierno y adopción

- **A3.1 JAVA-014:** rúbrica Java. Los **checks de puerta viven en `init.sh`**
  (`mvnw verify` + `contextLoads` + migraciones validadas + job de prueba +
  actuator exposure), porque `harness finish` solo lee su informe; los
  R-criterios (transacciones, concurrencia, N+1, idempotencia, restartability,
  versionado de API, records) van a `rubric.py` + `reviewer.md`, con casos
  canónicos testeados.
- **A3.2 JAVA-004:** `lider/explorer/implementer/reviewer.md` Java (protocolo
  `./mvnw`, idiomas Spring, patrones batch) + espejos `.claude/`.
- **A3.3 JAVA-015:** reviewer como check de PR (**depende de A1.2**: es un
  workflow), config IntelliJ sincronizada con Spotless/Checkstyle, escalera de
  fricción remapeada (`tag_release`/`publish` critical; merge por PR no),
  DevTools.

### P4 — Estratégico

**A4.1 — Eliminar el árbol Python/DS (decisión previa necesaria)**
- **A:** eliminar paquete/tests/tools/corpus ML/agentes DS, fijar
  `language=java` y desenrollar los condicionales de `init.sh`/Makefile/
  AGENTS.md/copier.yml. La matriz Python del CI se desmonta a la vez.
- **B:** mantenerlo como legacy excluido.
Recomendación: **A**, pero **después de cerrar H1** (CI Java verde + agentes
podados): hasta entonces la matriz Python es la red de seguridad. Esfuerzo L
(no M): toca CI, condicionales, docs y tests del template.

**A4.2 — Gradle (JAVA-001b):** segundo build tool; no bloquea nada.
**A4.3 — Segunda ronda E2E:** `copier update` desde el fork, render
interactivo y perfil `manual`, JDK 21 ejecutado en CI, `make` vía CI Linux
(F12 queda resuelto por cobertura, no por herramienta local).

---

## 4. Hitos (revisados)

| Hito | Contenido | Criterio de salida |
|---|---|---|
| **H0** | A0.1 + A0.2 + A0.3 | F6/F7/F9/F10 cerrados; versión alineada + tag |
| **H1** | A1.1 + A1.1b + A1.2 + A1.3 | `make check`/`mutation`/`security` funcionan; CI Java verde en el fork; agentes Java; `prompts-check` verde |
| **H2** | A2.1–A2.4 | migrations/batch/security/ops con agente y casos canónicos (incl. Postgres real) |
| **H3** | A2.5–A2.6 + A3.1–A3.3 | rúbrica Java, prompts y DX; flujo Gherkin→reviewer completo |
| **H4** | A4.1–A4.3 | repo 100% Java (si se aprueba), Gradle y 2ª ronda E2E |

## 5. Riesgos (revisados)

- **R1 — PIT lento:** perfil `mutation` fuera de `verify`, incremental.
- **R2 — OWASP/NVD:** Trivy+OSV como principal (sin API key); OWASP opcional.
- **R3 — Testcontainers/Docker:** perfil `integration` opcional; unit con H2.
- **R4 — Reescritura de agentes:** portar suites agente a agente; ramas
  language-aware preservan el verde Python.
- **R5 — Eliminar árbol Python:** solo tras H1; desmontar CI Python en el
  mismo paso que se elimina el árbol.
- **R6 — JDK 25:** matriz 17/21; 25 cuando Spring Boot lo soporte.
- **R7 — JaCoCo vs semilla:** test semilla + exclusiones + umbral configurable
  (A1.1).
- **R8 — Fórmula de conteo de agentes:** actualizar en A1.3 o `prompts-check`
  falla en CI.
- **R9 — Actions desactivados en forks:** paso manual documentado en A1.2.

## 6. Próximo paso

Ejecutar **H0**: A0.3 (versionado, 10 min) → A0.1 (semilla de backlog) →
A0.2 (fixes language-aware). Al cerrar H0, el informe E2E queda sin hallazgos
abiertos y se arranca A1.1, que es lo que convierte la puerta en una garantía
real para Java.

## 7. Estado de ejecución

- **H0 — COMPLETADO (Nov 2026).**
  - A0.3: versión del fork fijada a `2.0.0` (pyproject, README, copier.yml),
    tag `v2.0.0`.
  - A0.1: backlog Java condicional (SCOPE/ARCH/DB/JOB/API/SEC/OBS/CI).
  - A0.2: agentes language-aware: `commit_feature`/`bump_version` con
    `pom.xml`, `suggest_commit_message` con untracked, `doctor`/`env` con
    checks Java.
  - **F15 corregido:** `template/.copier-answers.yml` (copier no lo generaba;
    sin él `copier update` y `language`/`project_slug` estaban rotos).
  - Verificado en render limpio: doctor 8/8 Java, `next_version=0.1.1`,
    untracked detectado, `harness next` propone SCOPE-001 Java.
