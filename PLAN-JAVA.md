# PLAN-JAVA — Plan de implementación de SPEC-JAVA

Estado: propuesta (v0.1) · sin implementar
Depende de: SPEC-JAVA.md (backlog JAVA-001..JAVA-015 en ROADMAP.md)

---

## 1. Decisión de arquitectura — RESUELTA (Fase 0, ver SPEC §8)

**Medición del spike:** núcleo de gobierno con **0 líneas cambiadas**, `harness`
eval **14/14**, `contracts` **PASS** y puerta verde (`./mvnw verify` +
`contextLoads`) sobre un proyecto Java 17. El smoke solo difiere en `dependency`
y `env` (buscan `pyproject.toml`) y `doctor` (3/8) — ya en la lista de
reescritura de JAVA-005.

**Decisión: A1 — un solo árbol `template/` con variable `language`.** Se
descarta el template hermano (duplicaría el foso) y `_subdirectory` con Jinja
aunque funcione (también duplicaría). Detalle y tabla de evidencia en
SPEC-JAVA.md §8.

El resto del apartado original se conserva como contexto de la decisión:

Antes de tocar el template había una decisión estructural que el spec no
cerraba: **dónde vive físicamente el template Java**.

| Opción | Coste | Riesgo |
|---|---|---|
| **A. Un template con flag `language`** (python\|java) | Todo el contenido Java condicional en Jinja; los ficheros Python actuales no se tocan (solo `_exclude` + `{% if %}` donde sea imprescindible) | Complejidad Jinja creciente; riesgo de regresión en el flagship Python |
| **B. Template hermano `template-java/`** con su propio `copier.yml` | El núcleo de gobierno (agents/, harness/, rubric.py, contracts.py, evals/) se **duplica** y hay que mantenerlo sincronizado | Dos moats que divergen — contra la filosofía del proyecto |
| **C. Núcleo compartido + dos templates finos** | Empaquetar el arnés como dependencia (pip/git) que ambos templates instalan | Abstracción anticipada; packaging nuevo; contra "cero deps" |

**Recomendación: A** — el arnés es el foso del proyecto, y el foso debe tener
una sola fuente de verdad. B duplica exactamente lo que el proyecto se esfuerza
en no duplicar (prompts derivados del código, contratos, rúbrica). C es
abstracción antes de la segunda implementación real.

**Regla de decisión (evidencia, no opinión):** la Fase 0 mide la divergencia
real del núcleo de gobierno al adaptarlo a Java. Si los ficheros compartidos
(`agents/core/`, `harness_agent.py`, `rubric.py`, `contracts.py`, `evals/`)
requieren <20% de líneas cambiadas → opción A. Si ≥20% → reabrir la decisión.

### Preguntas técnicas que responde el spike (Fase 0)

1. ¿`_subdirectory` de copier acepta Jinja? (determina si `template-python/`/
   `template-java/` son posibles sin flag)
2. ¿Cuántas líneas del núcleo cambian para que `./init.sh` + `./mvnw verify`
   pasen en verde sobre un proyecto Java? (la métrica de la regla de decisión)
3. ¿`mvnw` (wrapper) funciona en el render sin Maven instalado globalmente?

---

## 2. Principios de ejecución

- **El template Python permanece verde en cada commit.** Cualquier feature que
  toque `copier.yml`, `_exclude` o `init.sh` se valida con el CI existente
  (`validate_template.py` + matriz smoke all-pairs) antes de cerrarse.
- **Una feature a la vez, con el flujo SDD:** backlog (ROADMAP) → spec
  (SPEC-JAVA.md) → contrato Gherkin → TDD → evidencia → `finish` con rúbrica.
- **Verificación de renders según memory.md:** copier usa el mirror cacheado,
  así que los renders de prueba se hacen copiando template+copier.yml a /tmp
  **sin `.git`**; la suite de agentes no corre sobre el template sin renderizar
  (Jinja2) — se copia a tmp y se quitan los `{% raw %}` con sed.
- **Evidencia real:** cada feature se cierra con la salida de un comando
  (`./init.sh`, `./mvnw verify`, `agents.evals.runner`), no con afirmaciones.
- **D6 del spec:** el Makefile generado es fachada sobre `./mvnw`; cero lógica
  propia.

---

## 3. Fases

### Fase 0 — Spike de viabilidad (medio día, sin tocar el repo)

| # | Tarea | Verificación |
|---|---|---|
| 0.1 | Copiar `template/` a /tmp (sin `.git`, `{% raw %}` fuera con sed) y sustituir a mano el esqueleto: `pyproject.toml`→`pom.xml` mínimo (spring-boot 3.x + spring-batch + maven wrapper), `main.py`→Job demo, tests→`contextLoads` | render compila |
| 0.2 | Adaptar `init.sh`: secciones JDK + wrapper + `./mvnw -q verify` + `contextLoads` | puerta en verde |
| 0.3 | **Sin tocar** `agents/core/`, `harness_agent.py`, `rubric.py`, `contracts.py`, `evals/` | diff = 0 en el núcleo |
| 0.4 | Medir divergencia del núcleo sobre el spike (métrica de §1) y probar `_subdirectory` con Jinja | decisión A/B documentada |
| 0.5 | Escribir la decisión en SPEC-JAVA.md (sección "Arquitectura física") | spec actualizada |

**Gate de salida:** render Java en /tmp con `./init.sh` verde y `./mvnw verify`
verde, y decisión A/B documentada con el número medido.

### Fase 1 — Núcleo (JAVA-001, JAVA-002, JAVA-003, JAVA-005)

**JAVA-001 — Template copier.** Variables nuevas en `copier.yml` con
validadores: `build_tool` (maven\|gradle), `java_version` (17\|21\|25),
`base_package` (regex `^[a-z][a-z0-9]*(\.[a-z][a-z0-9]*)+$`), `framework`
(spring-boot-web\|spring-boot-batch\|spring-boot-web+batch\|quarkus\|plain),
`db`, `migrations`, `use_security`, `use_testcontainers`, `use_pit`,
`use_archunit`, `use_observability`. Perfiles `minimo/estandar/completo/manual`
con defaults derivados. `_exclude`: gating Java (pom.xml vs pyproject) y poda
de los 4 agentes DS (`data`, `ml`, `mlflow`, `notebook` + prompts + tests).
`_tasks`: sin sync en minimo/estandar (regla existente). Estructura
`src/main/java/<paquete>/...` + `src/test/java/` + `db/migration/` condicional.
**Evidencia:** render `--defaults` en /tmp completo y `validate_template.py`
verde con el flag nuevo.

**JAVA-002 — Puerta.** `init.sh` con: check JDK (versión ≥ elegida, JAVA_HOME),
wrapper presente y ejecutable, `./mvnw -q verify`, test `contextLoads()`
(`@SpringBootTest`) que arranque el ApplicationContext, `flyway validate`
condicional, esquema `BATCH_*` en la BD de test (o `JobRepository` en memoria
en perfil test). Fallo → el agente PARA (misma filosofía). **Evidencia:**
`./init.sh` en verde sobre el render y un test de puerta roja (build roto →
exit 1).

**JAVA-003 — Backlog.** Plantillas de evidencia (`./mvnw test -Dtest=X`) y
criterios de aceptación batch/migraciones en los seeds de `harness/featureslist.json`
y en `harness_workflow.md`. El esquema JSON no cambia.

**JAVA-005 — Núcleo ejecutor.**
- Podar (con contrato mantenido en CONTRACTS sin registro, patrón ya tolerado):
  `data_agent.py`, `ml_agent.py`, `mlflow_agent.py`, `notebook_agent.py`.
- Reescribir con equivalente JVM: `test_agent.py` (JaCoCo XML + JUnit),
  `doctor_agent.py` (pom/JDK/m2), `dependency_agent.py` (dependency:analyze +
  versions-maven + OWASP), `cicd_agent.py`, `make_agent.py`, `refactor_agent.py`,
  `doc_agent.py` (Javadoc), `graph_agent.py` (ArchUnit/JDeps), `env_agent.py`,
  `plan_agent.py`.
- `contracts.py`: nuevos `owns` (pom.xml → dependency, db/migration/ →
  migrations, configs batch → batch...).
- Port de las suites de tests de cada agente reescrito; benchmarks de routing
  actualizados en `evals/runner.py` (con `_routing` saltando los no registrados).
**Evidencia:** `uv run python -m agents.evals.runner` verde sobre el render
(copiado a tmp + sed).

**Gate de salida de Fase 1:** un proyecto Java renderizado donde la puerta
pasa, los agentes del núcleo responden y los evals están en verde.

### Fase 2 — Pipeline de calidad (JAVA-012)

Makefile generado como fachada: `make test` (`./mvnw test` + JaCoCo ≥80%
enforce), `make lint/format` (Spotless + Checkstyle/PMD), `make typecheck`
(`-Werror` + Error Prone + NullAway), `make security` (OWASP dependency-check +
Trivy + SBOM cyclonedx), `make mutation` (PIT, `targetClasses` por módulo),
`make crap` (crap4j), `make audit` (CPD + ArchUnit), y nuevos `make migrations`,
`make batch-run`, `make context-check`. Plugins configurados en el `pom.xml`
del template. **Evidencia:** cada target ejecutado sobre el render con su
salida; PIT demuestra que mata un mutante de ejemplo.

### Fase 3 — Dominios de primera clase (JAVA-006..JAVA-011)

Cada dominio sigue el mismo patrón: agente + tool + prompt + workflow skill +
contrato + tests + benchmarks de routing + plantillas de backlog + criterio de
rúbrica. Registro en `orquestador.md`, AGENTS.md y evals (regla de
mantenimiento del proyecto).

- **JAVA-006 `batch`**: `batch_agent.py` + `batch_tool.py`. Acciones
  `validate_job` (restartability + idempotencia), `run_job` (dry-run sobre
  dataset controlado), `explain_failure` (JobExecution/StepExecution),
  `checkpoint`. Owns `*/batch/` + migraciones `BATCH_*`. **Casos canónicos con
  test:** writer sin transacción → rechazo; job relanzado con mismos
  parámetros que duplica → rechazo.
- **JAVA-007 `migrations`**: dueño de `db/migration/`. `create`/`validate`/
  `status`/`undo` (solo con rollback previo). Rechaza checksum cambiado y
  `out-of-order` sin bandera.
- **JAVA-008 `security`**: config Spring Security (JWT, CORS) + sección
  security de `application.yml`. Test de actuator exposure en build prod.
- **JAVA-009 `api`**: reescritura — controllers, DTOs + Bean Validation,
  `@ControllerAdvice`, OpenAPI, versionado `/api/v1`. Smoke: contexto arranca
  y `/actuator/health` responde.
- **JAVA-010 `architecture`**: dueño de tests ArchUnit (límites de capas,
  ciclos, módulos). `touched_files` por módulo.
- **JAVA-011 `ops`**: dueño de Actuator + Micrometer + Logback. Métricas por
  step de batch, MDC/traceId, Prometheus, logging JSON.

**Gate de salida:** los dos casos canónicos del spec rechazados por el arnés
con test que lo demuestra (writer sin TX, job no reiniciable).

### Fase 4 — Gobierno y adopción (JAVA-013, JAVA-014, JAVA-004, JAVA-015)

- **JAVA-013 CI + release:** workflow Java (setup-java, caché `.m2`, matriz
  JDK, service containers Postgres), JaCoCo/PIT upload, SBOM + Trivy, release
  semver con publish a GitHub Packages/Maven Central. Registro del template
  Java en la matriz smoke del CI de dskit (nuevo combo con `language`/flags
  Java).
- **JAVA-014 Rúbrica:** GATE-1 Java (`mvnw verify` + `contextLoads` +
  migraciones + job de prueba + actuator exposure) y R-criterios
  (transacciones, concurrencia, N+1, idempotencia batch, restartability,
  versionado de API, records/immutabilidad) en `rubric.py` y `reviewer.md`.
- **JAVA-004 Razonan:** `lider/explorer/implementer/reviewer.md` + espejos
  `.claude/` (`make assistants-sync`).
- **JAVA-015 DX:** reviewer como check de PR, config IntelliJ sincronizada
  con Spotless/Checkstyle, escalera de fricción remapeada (merge por PR no es
  critical; `critical` = tag/release/publish), DevTools en el bucle local.

**Gate de salida:** CI completa en verde y un flujo end-to-end simulado:
feature de batch pasa por Gherkin → approve → TDD → reviewer → rúbrica → done.

---

## 4. Grafo de dependencias

```
Fase 0 (spike) ──► JAVA-001 ──► JAVA-002 ──► JAVA-005 ──► JAVA-012
                        │            │            │
                        │            └─► JAVA-003 ─┤
                        │                         │
                        └──► JAVA-006..011 (dominios, en paralelo sobre 005)
                                      │
                                      └──► JAVA-014 ──► JAVA-004 / JAVA-015
JAVA-001 ──► JAVA-013 (CI)                          (paralelos)
```

- JAVA-002 y JAVA-003 dependen del render (JAVA-001).
- JAVA-005 necesita el render para probar los agentes contra un proyecto Java.
- Los dominios (JAVA-006..011) se apoyan en JAVA-005; entre sí son
  independientes y pueden ir en paralelo.
- JAVA-014 consolida los criterios que nacen en los dominios.
- JAVA-004 y JAVA-015 son independientes entre sí y solo esperan a JAVA-014.

## 5. Matriz de verificación por fase

| Fase | Comando | Qué prueba |
|---|---|---|
| 0 | render en /tmp → `./init.sh` → `./mvnw verify` | viabilidad del esqueleto |
| 1 | `python .github/scripts/validate_template.py` + renders `--defaults` | el template Java renderiza en todos los perfiles |
| 1 | `uv run python -m agents.evals.runner` sobre render (tmp+sed) | agentes núcleo: smoke, routing, contracts |
| 2 | `make check` / `make mutation` / `make security` en el render | pipeline de calidad JVM completo |
| 3 | casos canónicos (writer sin TX, job no reiniciable) | el arnés rechaza lo que debe rechazar |
| 4 | CI de dskit (matriz ampliada) + CI del proyecto generado | todo junto, incluida la CI que se entrega al usuario |

## 6. Riesgos operativos específicos del plan

- **R1 — Matriz smoke de CI:** añadir combos Java (Maven en GitHub Actions)
  alarga los builds y exige `actions/setup-java` + caché `.m2`. Mitigación:
  un combo Java mínimo en la matriz y el resto en `ci-generado`.
- **R2 — Maven sin red/caché:** el render debe poder compilar sin descargar
  medio internet. Mitigación: wrapper + repositorio estándar; el spike lo
  valida.
- **R3 — `{% raw %}` en ficheros Java:** los bloques Jinja del template pueden
  colisionar con sintaxis Java (p. ej. `{%` no existe en Java, pero los
  validadores de copier.yml sí usan Jinja). Riesgo bajo; el render lo detecta.
- **R4 — Fórmulas de conteo de agentes** en prompts/AGENTS.md (`{{ 19 + ... }}`)
  deben recalcularse con los agentes Java. Mitigación: regla existente de
  memoria + `make prompts-check` en CI.
- **R5 — Regresión del flagship:** cada commit de Fase 1..4 debe dejar el
  template Python renderizando y su CI en verde. Si A falla en Fase 0, se
  cae a la opción B antes de tocar nada.

## 7. Criterios de done globales (heredados del spec)

- Render `estandar` Java: `./init.sh` verde, `./mvnw verify` verde, JaCoCo ≥80%.
- `uv run python -m agents.evals.runner` verde sobre el template Java.
- Los 21 agentes del núcleo con contrato; los 6 dominios nuevos con agente +
  contrato + tests + workflow skill.
- El reviewer rechaza (con test) un writer sin transacción y un job no
  reiniciable.
- CI de dskit en verde con la matriz ampliada.

---

## 8. Siguiente paso

Fase 0 (spike) es la primera acción: no toca el repo y resuelve la decisión de
arquitectura con un número medido. Al cerrarla, la decisión A/B queda
documentada en SPEC-JAVA.md y el plan se re-baselina si la métrica obliga a
cambiar de opción.

---

## 9. Estado de implementación

### Fase 0 — COMPLETADA (decisión A1)

Ver SPEC-JAVA.md §8 para la tabla de evidencia.

### Fase 1 — EN CURSO

| Feature | Estado | Evidencia |
|---|---|---|
| JAVA-001 — Template copier | **Hecha (v1, maven)** | `copier.yml` con `language` + 11 variables Java; árbol `src/` + `pom.xml` + wrapper; gating por `_exclude`. Render Java `estandar` en /tmp completo. `gradle` queda para JAVA-001b. |
| JAVA-002 — Puerta | **Hecha** | `./init.sh` del render Java: JDK + wrapper + `./mvnw verify` + `contextLoads`. Verde con 0 avisos. |
| JAVA-003 — Backlog plantillas | Pendiente | Los seeds del backlog siguen siendo los de DS (SCOPE/RESEARCH/EDA/DATA). |
| JAVA-005 — Núcleo ejecutor | Pendiente | Los 32 agentes Python están todavía en el render Java; la poda y reescritura es el siguiente bloque. |

Verificación ejecutada (Nov 2026):

- `validate_template.py`: 212 combos × 450 ficheros → **0 bugs** (incluye 2
  combos Java fijados: `java-estandar` y `java-completo`).
- Render Python `--defaults`: idéntico al anterior salvo líneas en blanco de
  los condicionales nuevos.
- Render Java `--defaults` (language=java, estandar, JDK 17):
  `./init.sh` → **ENTORNO LISTO**, `mvnw verify` verde, `harness` eval
  **14/14**, `contracts` **PASS**.

Notas de implementación (lecciones):

- Los patrones de `_exclude` usan sintaxis gitignore: `tools` sin anclar
  excluía también `agents/tools/`. Todos los patrones de raíz van con `/`.
- `base_package_path` es una variable derivada porque un directorio no puede
  llevar `|` (filtro Jinja) en el nombre en Windows.
- `archunit-junit5` no está en el BOM de Spring Boot: lleva versión propia.
- `validate_template.py` normalizaba mal las rutas en Windows al excluir
  `.vscode/` (JSONC); corregido con `replace("\\", "/")`.
- La matriz smoke de CI queda sin combo Java hasta JAVA-013 (el job `smoke`
  actual es Python-only); el render Java se cubre con los combos fijados de
  `validate_template.py`.
