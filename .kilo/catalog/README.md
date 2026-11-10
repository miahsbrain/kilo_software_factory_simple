# Specialist skill catalogue

67 upstream specialist skills, kept as **files to read on demand**, not as skills the loader
picks up. Kilo only scans directories named `skill`/`skills` inside a config directory, so
`.kilo/catalog/` is invisible to the skill loader: none of these 67 skills enters the system
prompt, and none of them costs context until an agent opens it.

**How to use it.** Read this index first, find the row that matches the task, then read that
skill's `SKILL.md`:

    .kilo/catalog/<skill>/SKILL.md        # the skill
    .kilo/catalog/<skill>/references/     # its reference material

**Precedence.** Where a catalogue skill and `AGENTS.md` disagree, `AGENTS.md` wins. The
repository's rules, its stack decisions and its boundaries come first; the catalogue is
specialist background, not policy.

**Attribution.** Every skill is MIT licensed, © 2025 Jeffallan, from
https://github.com/Jeffallan/claude-skills (`django-storages-s3` carries its contributor's
author line upstream). Each `SKILL.md` keeps its upstream frontmatter and carries a header
that maps the Claude Code tool names onto this harness.

## The catalogue

| Skill | What it covers | When to read it |
|---|---|---|
| `angular-architect` | Angular 17+ standalone components, lazy routing and guards, NgRx, RxJS, bundle size | the task is Angular |
| `api-designer` | REST and GraphQL API design, OpenAPI specifications, API architecture | the task is designing an API surface |
| `architecture-designer` | high-level system architecture, design review, architectural trade-offs | the task is a structural design decision |
| `atlassian-mcp` | Atlassian project tracking and documentation through MCP | the task integrates with Jira/Confluence |
| `chaos-engineer` | chaos experiments, failure injection, game days, rollback runbooks | the task is resilience testing |
| `cli-developer` | CLI tools, argument parsing, interactive prompts | the task is a command-line tool |
| `cloud-architect` | cloud architectures, migration plans, cost optimisation, disaster recovery | the task spans AWS/Azure/GCP |
| `code-documenter` | docstrings, OpenAPI/Swagger, JSDoc, doc portals, user guides | the task is documentation |
| `code-reviewer` | diff review for bugs, security, smells, N+1 queries, naming | the task is reviewing a diff |
| `cpp-pro` | C++20/23, templates, metaprogramming, high-performance systems | the task is C++ |
| `csharp-developer` | C#/.NET 8+, ASP.NET Core, Blazor | the task is C# or .NET |
| `database-optimizer` | query tuning and performance across PostgreSQL and MySQL | the task is slow queries |
| `debugging-wizard` | error-message parsing, stack-trace tracing, hypothesis-driven isolation | the task is an unexplained failure |
| `devops-engineer` | Dockerfiles, CI/CD pipelines, Kubernetes manifests, Terraform/Pulumi | the task is delivery infrastructure |
| `django-expert` | Django applications and DRF APIs | the task is Django |
| `django-storages-s3` | Django static/media storage on S3, STORAGES settings, presigned URLs | the task is Django file storage |
| `dotnet-core-expert` | .NET 8 minimal APIs, clean architecture, cloud-native services | the task is .NET |
| `embedded-systems` | microcontroller firmware, RTOS applications, power consumption | the task is embedded |
| `fastapi-expert` | async Python APIs with FastAPI and Pydantic v2 | the task is FastAPI |
| `feature-forge` | requirements workshops, user stories, EARS requirements, acceptance criteria | the task starts from a feature request |
| `fine-tuning-expert` | LLM fine-tuning, custom model training, foundation-model adaptation | the task trains a model |
| `flutter-expert` | cross-platform apps with Flutter 3+ and Dart | the task is Flutter |
| `fullstack-guardian` | full-stack security layered across frontend and backend | the task touches both ends and auth |
| `game-developer` | game systems, Unity/Unreal features, game performance | the task is a game |
| `golang-pro` | goroutines and channels, gRPC/REST services, pprof, idiomatic Go | the task is Go |
| `graphql-architect` | GraphQL schemas, Apollo Federation, real-time subscriptions | the task is GraphQL |
| `java-architect` | Spring Boot 3.x, enterprise Java services, reactive programming | the task is Java |
| `javascript-pro` | modern ES2023+, async/await, ESM, Node.js APIs | the task is JavaScript |
| `kotlin-specialist` | coroutines, Flow, multiplatform, Compose UI, Ktor, type-safe DSLs | the task is Kotlin |
| `kubernetes-specialist` | deploying and managing Kubernetes workloads | the task is Kubernetes |
| `laravel-specialist` | Laravel 10+, Eloquent, Sanctum, Horizon, API resources, Livewire | the task is Laravel |
| `legacy-modernizer` | incremental migration, service boundaries, dependency maps, facades | the task is an ageing codebase |
| `mcp-developer` | building and extending MCP servers and clients | the task is an MCP integration |
| `microservices-architect` | bounded-context decomposition, communication patterns, resilience | the task splits a monolith |
| `ml-pipeline` | experiment tracking, training orchestration, feature stores, model registries | the task is ML infrastructure |
| `monitoring-expert` | monitoring systems, log pipelines, Prometheus/Grafana, alerts, tracing | the task is observability |
| `nestjs-expert` | NestJS modules, controllers, services, DTOs, guards, interceptors | the task is NestJS |
| `nextjs-developer` | Next.js 14+ App Router, server components, server actions | the task is Next.js |
| `pandas-pro` | DataFrame operations, analysis, manipulation, transformation | the task is pandas |
| `php-pro` | PHP 8.3+, Laravel, Symfony | the task is PHP |
| `playwright-expert` | Playwright E2E tests, test infrastructure, flaky-test debugging | the task is browser testing |
| `postgres-pro` | PostgreSQL query tuning, replication, advanced database features | the task is PostgreSQL |
| `prompt-engineer` | prompt templates, structured output schemas, evaluation rubrics | the task is prompt engineering |
| `python-pro` | Python 3.11+ with type safety, async programming, error handling | the task is Python |
| `rag-architect` | chunking, embeddings, vector stores, hybrid search, reranking | the task is a RAG system |
| `rails-expert` | Rails 7+, Active Record tuning, Turbo, Action Cable, Sidekiq, RSpec | the task is Rails |
| `react-expert` | React 18+, JSX/TSX, Server Components, hooks, state management | the task is React |
| `react-native-expert` | React Native and Expo apps, build and debug | the task is React Native |
| `rust-engineer` | idiomatic Rust, memory safety, zero-cost abstractions | the task is Rust |
| `salesforce-developer` | Apex, Lightning Web Components, SOQL, triggers, batch jobs | the task is Salesforce |
| `secure-code-guardian` | auth and authorisation, input hardening, OWASP Top 10, JWT/CORS/CSP | the task is a security-sensitive path |
| `security-reviewer` | vulnerability identification, severity ratings, audit reports | the task is a security audit |
| `shopify-expert` | Shopify themes, custom apps, OAuth, webhooks, Storefront API | the task is Shopify |
| `spark-engineer` | Spark jobs, performance tuning, cluster configuration | the task is Spark |
| `spec-miner` | reverse-engineering specifications out of an existing codebase | the task is undocumented code |
| `spring-boot-engineer` | Spring Boot 3.x, REST controllers, Spring Security 6, JPA, WebFlux | the task is Spring Boot |
| `sql-pro` | SQL query optimisation, schema design, performance troubleshooting | the task is SQL |
| `sre-engineer` | SLOs, error budgets, incident response, capacity models | the task is production reliability |
| `swift-expert` | SwiftUI, protocol-oriented architecture, async/await, actors | the task is Apple platforms |
| `terraform-engineer` | infrastructure as code with Terraform | the task is Terraform |
| `test-master` | test files, mocking, coverage, test architecture, test plans | the task is test strategy or coverage |
| `the-fool` | structured critical reasoning against an idea, plan or proposal | the task needs a challenge before it is built |
| `typescript-pro` | advanced type systems, type guards, utility and branded types, tRPC | the task is TypeScript |
| `vue-expert` | Vue 3 Composition API, Nuxt 3, Pinia, Quasar/Capacitor, PWA | the task is Vue |
| `vue-expert-js` | Vue 3 with plain JavaScript composables and Vite — no TypeScript | the task is Vue in JavaScript |
| `websocket-engineer` | real-time communication with WebSockets or Socket.IO | the task is real-time |
| `wordpress-pro` | themes and plugins, Gutenberg blocks, WooCommerce, REST API, hardening | the task is WordPress |
