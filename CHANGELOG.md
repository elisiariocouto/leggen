
## 2026.8.0 (2026/08/17)

### Bug Fixes

- **api:** Preserve stored secrets when masked values are submitted. ([875802a0](https://github.com/elisiariocouto/leggen/commit/875802a0559a084e915adb21a956944e6290f8d4))
- **api:** Preserve stored account logos when a logo fetch fails. ([5dcdb6d8](https://github.com/elisiariocouto/leggen/commit/5dcdb6d81b999513807fc878b21162e3bffe6df6))
- **api:** Stop the composite-key migration from dropping snake_case transactions. ([30301917](https://github.com/elisiariocouto/leggen/commit/3030191791e9ebb9fdaa53eae61bf89c74673175))
- **api:** Enforce the sync "already running" guard across all SyncService instances. ([86664dd5](https://github.com/elisiariocouto/leggen/commit/86664dd5204b1775845b4ea2aa56444f4ac63a9c))
- **api:** Enable SQLite foreign keys, WAL mode, and busy timeout on all connections. ([94f599fd](https://github.com/elisiariocouto/leggen/commit/94f599fdd7fc448a3ecafdb6386ebda2b350c031))
- **api:** Fix the high-priority backend bugs from the code review. ([8eaf54c9](https://github.com/elisiariocouto/leggen/commit/8eaf54c93f3058077c472bbafcebff68ba6f7b47))
- **api:** Request the bank's maximum consent validity when connecting. ([a6dc944b](https://github.com/elisiariocouto/leggen/commit/a6dc944b89ae4aa319ac719bf0c7d6f62cfb1d04))
- **api:** Count updated transactions during sync and skip unchanged rewrites. ([2c99ede5](https://github.com/elisiariocouto/leggen/commit/2c99ede592af5c6eaf33f6e40708c0e7395d2ddc))
- **api:** Sanitize error responses, return 409 for concurrent syncs and paginate sync operations. ([d79d3002](https://github.com/elisiariocouto/leggen/commit/d79d3002a79b59268b753b77422a90557af0ab42))
- **api:** Stop leaking exception details from the health endpoint. ([979a282d](https://github.com/elisiariocouto/leggen/commit/979a282db4b74088522cc5f908b84e29ca834654))
- **api:** Let notification filters and S3 backup config be cleared. ([12599465](https://github.com/elisiariocouto/leggen/commit/12599465297daf4e41939232cda95517ad095e02))
- **api:** Report timeout causes and make sync request timeouts configurable. ([68d93338](https://github.com/elisiariocouto/leggen/commit/68d9333837479e0a732c01a0809224b85b2ac121))
- **api:** Preserve backup schedule when updating sync schedule. ([01142dda](https://github.com/elisiariocouto/leggen/commit/01142dda56c4a7593c94c7bb2a4738e870f8a716))
- **api:** Make schedule regression test robust to singleton state. ([905703e4](https://github.com/elisiariocouto/leggen/commit/905703e45630035993423a57308d8e5d9295d2b7))
- **api:** Scope EnableBanking service to the app instead of the request. ([5dde7849](https://github.com/elisiariocouto/leggen/commit/5dde784991282b0ff00d6ff5f023e93587f18b6d))
- **api:** Address review comments on the bug sweep. ([e45fdfa6](https://github.com/elisiariocouto/leggen/commit/e45fdfa6ce5cf6e438327eaf27a05fc49cf18f8f))
- **api:** Correct counterparty extraction and average transaction stat. ([e0c77f1c](https://github.com/elisiariocouto/leggen/commit/e0c77f1c193895831f22d3138bb92cb89f09bdcf))
- **cli:** Restore the bank command group so bank add/delete are reachable. ([e520b73c](https://github.com/elisiariocouto/leggen/commit/e520b73c696e4ddfca5bd19bd2bed1e85db313e1))
- **cli:** Stop help output from requiring a config file or creating a database. ([d15fca5f](https://github.com/elisiariocouto/leggen/commit/d15fca5f05980494db79ad3b3336ef0747310df9))
- **cli:** Let generate_auth_config and generate_sample_db run without a valid config. ([5c3d72c7](https://github.com/elisiariocouto/leggen/commit/5c3d72c7c63b964318d2626046582858b9e35fbd))
- **cli:** Exit non-zero on errors and simplify API client handling. ([ce41964a](https://github.com/elisiariocouto/leggen/commit/ce41964aa42fe6b6d6b692ab4299126ca39bdd22))
- **cli:** Send the state parameter when redeeming a bank callback. ([7514e400](https://github.com/elisiariocouto/leggen/commit/7514e40072335f55d1f68a19325fce8229d6f8fa))
- **cli:** Propagate path flags to server reload workers. ([a5cf3672](https://github.com/elisiariocouto/leggen/commit/a5cf3672126c3724552d28c9329207b50d9371da))
- **frontend:** Check the actual backup response fields instead of a phantom success flag. ([e0921ab4](https://github.com/elisiariocouto/leggen/commit/e0921ab46c8562b7cf69a7ddafeee80d8d8c9b38))
- **frontend:** Allow saving a disabled service configuration. ([02a4c38d](https://github.com/elisiariocouto/leggen/commit/02a4c38d2ad6dddb2db00684c1d3f31d05037ef9))
- **frontend:** Fix the high-priority frontend bugs from the code review. ([03a7a6c9](https://github.com/elisiariocouto/leggen/commit/03a7a6c91a0b571848567055572e0452b6df590d))
- **frontend:** Unify dark mode colors, confirmations, loading and error feedback. ([73fcd4a9](https://github.com/elisiariocouto/leggen/commit/73fcd4a930a292b8d57cb8b76bd1335b940690cd))
- **frontend:** Use npm ci and Node 22 in the Docker image and CI. ([946edce8](https://github.com/elisiariocouto/leggen/commit/946edce8af6c46eefd5c8f99f4e8d5e456bad96a))
- **frontend:** Upgrade recharts to v3 and drop the obsolete serialize-javascript override. ([911b516a](https://github.com/elisiariocouto/leggen/commit/911b516af70e49e54736f062e92f5e254657768c))
- **frontend:** Version the package with the project CalVer and bump it on release. ([8996bdf2](https://github.com/elisiariocouto/leggen/commit/8996bdf2bb183478eedbdf3c7c180c080e8575d7))
- **frontend:** Resolve chart colors through theme tokens. ([95da62e0](https://github.com/elisiariocouto/leggen/commit/95da62e093fbf1d5856e88d5f51046dedb8cb1ce))
- **frontend:** Correct invalid HTML nesting in sync header. ([173e71a0](https://github.com/elisiariocouto/leggen/commit/173e71a0c3cba7598073d50469e5c10cda113440))
- **frontend:** Make transaction rows keyboard-accessible. ([3254812a](https://github.com/elisiariocouto/leggen/commit/3254812a62dbe39d885c67fa8123a38abb47dfb6))
- **frontend:** Pad the transaction detail sheet body. ([4551a5f1](https://github.com/elisiariocouto/leggen/commit/4551a5f197fbc1e5e57dcaba06566b5be1d22d12))
-  Drop dev dependencies from the Docker image and fix the .dockerignore compose entry. ([a623ced7](https://github.com/elisiariocouto/leggen/commit/a623ced7741e1a25f2750a77eaaf60139e7b09f0))


### Documentation

-  Add code review checklist and refresh agent guidelines. ([7434333a](https://github.com/elisiariocouto/leggen/commit/7434333a096ecc50198a17714235a7572b7fc63b))
-  Mark dead code and simplification review items as fixed. ([e40e93f0](https://github.com/elisiariocouto/leggen/commit/e40e93f0780dcadf2fe8f452aa1f4c3bdd13f534))
-  Check off the fixed high-priority items in the review checklist. ([f12d760e](https://github.com/elisiariocouto/leggen/commit/f12d760ea36539688de4fa0c2777f98d8aa33dc3))
-  Check off the fixed frontend consistency items in the review checklist. ([33b8c407](https://github.com/elisiariocouto/leggen/commit/33b8c4076d1fafa0f1ab12fe813c258f188f5005))
-  Check off the fixed CI and dependency items in the review checklist. ([f8a8c5c3](https://github.com/elisiariocouto/leggen/commit/f8a8c5c3cc7051935fc188cbe9b514a53a90c16e))
-  Check off the Tailwind migration in the review checklist. ([a66f72f1](https://github.com/elisiariocouto/leggen/commit/a66f72f16e5b9320e047eb2382d7b7588340001e))
-  Check off the consent validity, deep-link, database config and updated-count items. ([5ed31b72](https://github.com/elisiariocouto/leggen/commit/5ed31b721a49cacba8ce4e7508a2416ca7869a3e))
-  Add S3 backups to README features, require Node 20.19+ and check off review items. ([5623207d](https://github.com/elisiariocouto/leggen/commit/5623207d16492f3607a9f957722e980e8521d1fa))
-  Add roadmap task list. ([4a382c5b](https://github.com/elisiariocouto/leggen/commit/4a382c5b79ee2410be403e9cb4caabcfe3307219))
-  Mark API error consistency as done. ([473ae19a](https://github.com/elisiariocouto/leggen/commit/473ae19a187f27943cafc7199229abb9b5b3e046))
-  Mark clearable settings as done. ([1fd7788e](https://github.com/elisiariocouto/leggen/commit/1fd7788e445ac08a00f5f241cf3abb7fcbd96af1))
-  Correct roadmap items that drifted from the code. ([e627d6b3](https://github.com/elisiariocouto/leggen/commit/e627d6b30f8a4ffa65e4cf2b5e70cb09eae32aea))
-  Ground the non-root Dockerfile item in the compose mounts. ([ec191f08](https://github.com/elisiariocouto/leggen/commit/ec191f08a9e82b20d2dcac9c7eb5433f67e52adc))


### Features

- **api:** Add scheduled S3 database backups. ([01511d66](https://github.com/elisiariocouto/leggen/commit/01511d6642c0956777c88add16b4b2bf2d074a17))
- **api:** Support per-account sync via account_ids. ([339c2ccf](https://github.com/elisiariocouto/leggen/commit/339c2ccf1dd797a76a9c0617d084bc710ac1ab29))
- **api:** Add unified error response schema and exception handlers. ([5de54cca](https://github.com/elisiariocouto/leggen/commit/5de54cca35b7b2ccbbfd3d17ac50bb95abb614e0))
- **api:** Document the error schema across all OpenAPI operations. ([f422b0de](https://github.com/elisiariocouto/leggen/commit/f422b0de01643f41e494ebd77e45cd41c4fab097))
- **api:** Add analytics endpoints for cash flow, net worth, merchants and recurring. ([fc95412d](https://github.com/elisiariocouto/leggen/commit/fc95412db11410de146cea6b5246272c5c1ecdb6))
- **frontend:** Add a formatted transaction detail view. ([0e85575b](https://github.com/elisiariocouto/leggen/commit/0e85575b48d30e60e571f88951ebc6b8f85809fb))
- **frontend:** Surface structured API errors. ([9c8af1a0](https://github.com/elisiariocouto/leggen/commit/9c8af1a08e7be90605c74be54a3677fb39ac7b1c))
- **frontend:** Add a remove action for the S3 backup configuration. ([e795d9ea](https://github.com/elisiariocouto/leggen/commit/e795d9ea02c9ed1ae438fe811a78f415ad3f96ac))
- **frontend:** Put transaction filters in the URL. ([3bdc3447](https://github.com/elisiariocouto/leggen/commit/3bdc3447d413d161d53638a0ae9642c20b3816c7))
- **frontend:** Put analytics filters in the URL. ([b00852dd](https://github.com/elisiariocouto/leggen/commit/b00852dde35effb2da66396c4aa31a3f40879f59))
- **frontend:** Rebuild analytics around cash flow, net worth, merchants and recurring. ([2a02e7aa](https://github.com/elisiariocouto/leggen/commit/2a02e7aa45b2241b88591b6811a16c1d02a266d3))
-  Run ruff and mypy in CI and gate releases on tests. ([f433a084](https://github.com/elisiariocouto/leggen/commit/f433a084918ffaff7954130c49e884c45bdfda50))
-  Generate frontend API types from the OpenAPI schema. ([889f5486](https://github.com/elisiariocouto/leggen/commit/889f548676cc60d8ce03cb254939ea143dc4d778))


### Miscellaneous Tasks

- **frontend:** Upgrade ESLint to 10 and fix what its new rules caught. ([e2c84764](https://github.com/elisiariocouto/leggen/commit/e2c84764993973b7ad2836b30c9086efc85ced02))
- **frontend:** Upgrade Vite to 8. ([28bdb515](https://github.com/elisiariocouto/leggen/commit/28bdb5155dc6f2d44f7454846c4b5af27cc8bafe))
- **frontend:** Upgrade TypeScript to 6. ([6996064e](https://github.com/elisiariocouto/leggen/commit/6996064ef897feea789cedafa9a9daf5f03fa436))
- **frontend:** Upgrade lucide-react and react-day-picker. ([61703309](https://github.com/elisiariocouto/leggen/commit/61703309a125ca9d51922bab243a3e3a68355e28))
- **frontend:** Upgrade the shadcn CLI to 4. ([c8df976a](https://github.com/elisiariocouto/leggen/commit/c8df976a0b1f58817fd0c3e5c460f6237a35038a))
-  Bump backend dependencies. ([af5da30b](https://github.com/elisiariocouto/leggen/commit/af5da30b163b7e0d7b693a0ab897b9720d32e7be))
-  Bump frontend dependencies. ([5ff3f2a8](https://github.com/elisiariocouto/leggen/commit/5ff3f2a84027b883880ece72b7ad1a97ba6aaf37))
-  Cleanup roadmap. ([59a04f96](https://github.com/elisiariocouto/leggen/commit/59a04f9696baa6389e726fd096de6c6b362a4be6))
-  Fix stale and missing ignore entries. ([aa15cc9b](https://github.com/elisiariocouto/leggen/commit/aa15cc9b4c4451fba3c97b663f298d7b86e4daea))
-  Bump dependencies. ([69bb1417](https://github.com/elisiariocouto/leggen/commit/69bb14171822b3ca563e645b6658c50fb118990b))
-  Add justfile consolidating dev commands. ([daeb23a3](https://github.com/elisiariocouto/leggen/commit/daeb23a3e9c2a81d7fbc36a07c5db9d3db83aa30))
-  Upgrade Python dependencies and modernize type syntax. ([eb58522d](https://github.com/elisiariocouto/leggen/commit/eb58522d62a306f0e6712a467a840b318f654876))
-  Add shadcn skills. ([42b45b03](https://github.com/elisiariocouto/leggen/commit/42b45b030b31606ef641b475733aa1d2318c133e))


### Performance

- **frontend:** Lazy-load the analytics route. ([3dc8eef2](https://github.com/elisiariocouto/leggen/commit/3dc8eef29e749573e5a6b36c89140d2abefee4c1))


### Refactor

- **api:** Delete dead code and Pydantic v1 config blocks. ([bd9c6e91](https://github.com/elisiariocouto/leggen/commit/bd9c6e91da69d08030e73f014134dba44d20718f))
- **api:** Deduplicate schema creation and move keyword extraction to utils. ([02a5f8c9](https://github.com/elisiariocouto/leggen/commit/02a5f8c9c3e2afa567163f5fa4b9aa9e50c7908e))
- **api:** Reuse the HTTP client and cache EnableBanking JWT and bank lists. ([6b3971e7](https://github.com/elisiariocouto/leggen/commit/6b3971e7e83279272a617fe4329c9d1d40afd2da))
- **api:** Remove the always-true GET /auth/status endpoint. ([ff17e51e](https://github.com/elisiariocouto/leggen/commit/ff17e51ed9dd310e7bfce1e7889117e981d6f6a9))
- **api:** Replace error-string matching with typed domain errors. ([ff46fe5e](https://github.com/elisiariocouto/leggen/commit/ff46fe5e5b0c7e15beb19ed988edb533830e33af))
- **api:** Validate category_id filter with a query pattern. ([e13ec084](https://github.com/elisiariocouto/leggen/commit/e13ec08438b900ea941504fccb7f644d64fe5923))
- **api:** Drop the unused test-notification message field. ([30d2730f](https://github.com/elisiariocouto/leggen/commit/30d2730f24dbb69f53104ec967b834830b785270))
- **api:** Trust the global exception handlers in routes. ([4942c98d](https://github.com/elisiariocouto/leggen/commit/4942c98d5f25c677247001a2c3bfbc82ba7cf773))
- **api:** Aggregate transaction stats in SQL. ([3c702a7c](https://github.com/elisiariocouto/leggen/commit/3c702a7cb6f6072a0f8cb30da0b2478f80a24cf7))
- **api:** Fetch latest balances in one query. ([6debff41](https://github.com/elisiariocouto/leggen/commit/6debff4198de235a93dbc285838685120ad30540))
- **api:** Batch transaction persistence and type remaining responses. ([9f6d2b75](https://github.com/elisiariocouto/leggen/commit/9f6d2b751f87551b94b7e84c09b6b2ea9aa24ff3))
- **api:** Apply review findings to the backend cleanup. ([825a144f](https://github.com/elisiariocouto/leggen/commit/825a144fecb045f11999b221d0e9e78a7b46a1e7))
- **api:** Validate account ownership in batch persistence. ([96bb601c](https://github.com/elisiariocouto/leggen/commit/96bb601c6b6411589b73de7774088882b6968652))
- **cli:** Unify config loading through the singleton. ([76a7974d](https://github.com/elisiariocouto/leggen/commit/76a7974d32bfdb4a1cde5dc5f06d5bd7cefaa0dc))
- **frontend:** Remove dead components and unused dependencies. ([413b1840](https://github.com/elisiariocouto/leggen/commit/413b184060854903bb66bbb28a21a8682ef4a960))
- **frontend:** Migrate Tailwind CSS from v3 to v4. ([3708fba9](https://github.com/elisiariocouto/leggen/commit/3708fba902049af9b7025e4a610c7e9217e1bc49))
- **frontend:** Remove dead deep-link search params from the transactions route. ([e1785324](https://github.com/elisiariocouto/leggen/commit/e17853243d001ad04f7dd50e0407ce83e98300da))
- **frontend:** Remove dead code and stale skeleton. ([6f650670](https://github.com/elisiariocouto/leggen/commit/6f6506702f58e5d9f2ef30d95e1925fef005108e))
- **frontend:** Centralize React Query keys and invalidation. ([82fba5b6](https://github.com/elisiariocouto/leggen/commit/82fba5b6bad3eb9289b780bd627a5856a43087fc))
- **frontend:** Guard routes in beforeLoad instead of an effect. ([91f0eb72](https://github.com/elisiariocouto/leggen/commit/91f0eb722e81334dcf26f9068bf6a72a1822408a))
- **frontend:** Express money direction as semantic tokens. ([b7a2bf09](https://github.com/elisiariocouto/leggen/commit/b7a2bf0926d313aebaddfbabdd4f3ef003aacb03))
- **frontend:** Share markup between the two breakpoint layouts. ([9023bef7](https://github.com/elisiariocouto/leggen/commit/9023bef772059817fd981972c76aba69336d01ed))
- **frontend:** Drop @tanstack/react-table. ([c6576501](https://github.com/elisiariocouto/leggen/commit/c6576501664cb3c34b4351bfdd702f8b0353cc3a))
- **frontend:** Convert theme tokens to oklch for Base UI. ([03e76107](https://github.com/elisiariocouto/leggen/commit/03e76107c24cab04f62b6ca42c296408f6544b47))
- **frontend:** Migrate leaf UI wrappers to Base UI. ([7eb64d8f](https://github.com/elisiariocouto/leggen/commit/7eb64d8f8389043ff5303d87ca5739e86a075850))
- **frontend:** Migrate overlays and form controls to Base UI. ([812afb54](https://github.com/elisiariocouto/leggen/commit/812afb5432ca401190a803189205403e816a1ad1))
- **frontend:** Drop Radix UI and switch the registry to base-nova. ([2891c6ff](https://github.com/elisiariocouto/leggen/commit/2891c6ff98b04f72789f0eaec8e424af33f160d7))
-  Remove the no-op database config section. ([0ccd7dca](https://github.com/elisiariocouto/leggen/commit/0ccd7dca5f63dd1670132a6a49af231506a537fc))
-  Replace deprecated Pydantic dict() calls with model_dump. ([76a8091a](https://github.com/elisiariocouto/leggen/commit/76a8091a79ad7fed1153bcbc0b488d8f9ca32c5d))



## 2026.3.5 (2026/03/16)

### Bug Fixes

- **frontend:** Improve mobile responsiveness for accounts, S3 backup, and header. ([f011ae75](https://github.com/elisiariocouto/leggen/commit/f011ae750c45e7032fa2caf46289dc57ff9570c8))


### Features

-  Add category filters and analytics breakdown. ([429fe747](https://github.com/elisiariocouto/leggen/commit/429fe7473f4a9e8bb60de71182298ef29d9414eb))


### Miscellaneous Tasks

-  Update README.md with new categorization and authentication features. ([2f04c6d0](https://github.com/elisiariocouto/leggen/commit/2f04c6d075122aa2352928fe745b4668b23f9975))
-  Update dependencies. ([a1c966e7](https://github.com/elisiariocouto/leggen/commit/a1c966e7eec69ba31f05b0063ecd52e409be4e67))



## 2026.3.4 (2026/03/10)

### Bug Fixes

- **frontend:** Prevent PWA from caching health endpoint responses. ([08fae853](https://github.com/elisiariocouto/leggen/commit/08fae853ef327053c73344b6d6f30200fb8982c4))
-  Address PR review comments for authentication. ([57da95cc](https://github.com/elisiariocouto/leggen/commit/57da95ccaa7489ba1325fa540f49fffb7359eff0))
-  Add API key auth to CLI client and reject placeholder config values. ([574e91d2](https://github.com/elisiariocouto/leggen/commit/574e91d231ae75437da46c18ae76916477e00b5c))
-  Read API key from ctx.obj and normalize base64url in JWT decoding. ([ec073fba](https://github.com/elisiariocouto/leggen/commit/ec073fbac9b634f31132e68ff2bfeb3779c53f39))


### Features

- **cli:** Prompt for username in generate-auth-config command. ([20f6c896](https://github.com/elisiariocouto/leggen/commit/20f6c896f459077031a01af7b86ada090630cf0b))
- **frontend:** Add user avatar and logout button to sidebar. ([10830223](https://github.com/elisiariocouto/leggen/commit/108302232a3772973f6d2a7c81ccc70eb9b3ab83))
-  Add single-user authentication with JWT and API key support. ([13925e18](https://github.com/elisiariocouto/leggen/commit/13925e18372a023ab59fe20b4841db790622fb94))



## 2026.3.3 (2026/03/09)

### Bug Fixes

- **api:** Resolve ambiguous column name in transaction filter clause. ([e6f08e42](https://github.com/elisiariocouto/leggen/commit/e6f08e429eb9ef9defa671189c99d5d9b8fd5bde))
- **frontend:** Fix type error in transaction stats query parameters. ([bc26f804](https://github.com/elisiariocouto/leggen/commit/bc26f804d4655ba9bf54d48de1e4ce2d0807fa3d))
-  Address PR review comments for transaction categorization. ([9840a05a](https://github.com/elisiariocouto/leggen/commit/9840a05aa5d912cfefc0dc5f166277207d6051a3))
-  Use API stats endpoint for transaction page totals instead of client-side calculation. ([d2878352](https://github.com/elisiariocouto/leggen/commit/d28783525dfcfb67a5cf1000594915fd2d83d3ad))


### Features

-  Add transaction categorization with keyword-based learning. ([1739ad08](https://github.com/elisiariocouto/leggen/commit/1739ad08d3e8a77206a02b4e0714c79273d4e45b))
-  Add bulk categorization and removal by transaction description. ([812e30e0](https://github.com/elisiariocouto/leggen/commit/812e30e0b7cbced88847b13b44d9a94da5a42588))
-  Add `exclude_from_stats` flag to categories with "Inter-account" default. ([0e6f8ebd](https://github.com/elisiariocouto/leggen/commit/0e6f8ebd5b7b17a17532e02f393daf32b04e9885))


### Refactor

- **frontend:** Consolidate transactions page into single-card layout. ([5aeee70f](https://github.com/elisiariocouto/leggen/commit/5aeee70fb9a613fe41201a57d85464b9b14c886c))



## 2026.3.2 (2026/03/08)

### Bug Fixes

-  Use timezone-aware datetime in expiry notification test. ([9814e494](https://github.com/elisiariocouto/leggen/commit/9814e4949f7c5d10981d720134cdb32c412b2283))


### Features

-  Add account deletion with soft-delete and UI management. ([5f6b6636](https://github.com/elisiariocouto/leggen/commit/5f6b66364b1a1e779ec8724677e8208b05038037))
-  Add pre-expiry warnings for bank connections. ([0a337f81](https://github.com/elisiariocouto/leggen/commit/0a337f8141fadde51a4effe9b335386ddff64d85))


### Refactor

- **frontend:** Remove unused dependency and split build chunks. ([6d6c8fc2](https://github.com/elisiariocouto/leggen/commit/6d6c8fc25e7c02a581277876742e358d34806b39))



## 2026.3.1 (2026/03/04)

### Features

- **frontend:** Add split sync button with full history option and rename route to /sync. ([4e63ccae](https://github.com/elisiariocouto/leggen/commit/4e63ccae9df182725e2856dae25537be1b12643d))
-  Add sync schedule configuration to settings UI and API. ([0ea2a6b3](https://github.com/elisiariocouto/leggen/commit/0ea2a6b31c8a95ccaa7f2b855b54ad26f15a6986))


### Miscellaneous Tasks

-  Update dependencies. ([322123fc](https://github.com/elisiariocouto/leggen/commit/322123fcb85c48a3387c84631afa940b3586cdee))


### Refactor

- **api:** Remove unnecessary abstractions and simplify backend. ([d1cffbdd](https://github.com/elisiariocouto/leggen/commit/d1cffbddc9de5a276afab9a5f4837d846142f54d))
- **api:** Simplify backend abstractions and flatten modules. ([d64f1bc8](https://github.com/elisiariocouto/leggen/commit/d64f1bc82e5a1dc5a7600434246cf87253acf84d))



## 2026.3.0 (2026/03/03)

### Features

- **frontend:** Improve visual consistency across UI pages. ([0263d04e](https://github.com/elisiariocouto/leggen/commit/0263d04e811f7677dd3970dfb27dc4903f275048))


### Refactor

- **api:** Remove unused and duplicated API endpoints. ([71b44bc9](https://github.com/elisiariocouto/leggen/commit/71b44bc94cf55739232ba77feba54aef3d86ded7))



## 2026.2.0 (2026/02/28)

### Features

-  Migrate from GoCardless to EnableBanking. ([e998a942](https://github.com/elisiariocouto/leggen/commit/e998a942d1198369cb8163448b525e2e8012d36c))
-  Improve EnableBanking integration with PSU types, sync refinements, and API cleanup. ([e54e12d6](https://github.com/elisiariocouto/leggen/commit/e54e12d6143ebf7e0cb3c0e4f5b6579be2568d90))


### Miscellaneous Tasks

-  Cleanup agent instructions. ([0baf78af](https://github.com/elisiariocouto/leggen/commit/0baf78af80f415b40f9967275dd33db3e548ef63))
-  Update python dependencies and reformat code. ([3ddbc809](https://github.com/elisiariocouto/leggen/commit/3ddbc8098a88011e5a3b8cec28490407d2cc7ce0))



## 2026.1.0 (2026/01/07)

### Bug Fixes

- **frontend:** Remove unused import in TransactionDistribution ([96644000](https://github.com/elisiariocouto/leggen/commit/966440006a9f369044a63883e8defea09197c99f))
- **frontend:** Blur balances in Account Management page. ([5de9badf](https://github.com/elisiariocouto/leggen/commit/5de9badfde264afa5782d68564d9938b17d0a203))
- **frontend:** Blur balances in transactions page cards. ([07edfeaf](https://github.com/elisiariocouto/leggen/commit/07edfeaf25200305ba02c6aca8915e273e04184c))
- **frontend:** Prevent full transactions page reload on search. ([18ee52bd](https://github.com/elisiariocouto/leggen/commit/18ee52bdffd9ba73cc5db4bfb2afdab08145a4ef))
-  Resolve all lint warnings and type errors across frontend and backend. ([159cba50](https://github.com/elisiariocouto/leggen/commit/159cba508e749de13bb709201b542f3a8fb052a7))
-  Address code review feedback on notification error handling. ([88037f32](https://github.com/elisiariocouto/leggen/commit/88037f328d48cfd3e8bbd01c98fa22324e278262))


### Features

- **cli:** Add log level configuration with flag and environment variable. ([c765accf](https://github.com/elisiariocouto/leggen/commit/c765accfd7e447a3a27d232edfb58310d1df9e43))
- **frontend:** Add balance visibility toggle with blur effect ([a592b827](https://github.com/elisiariocouto/leggen/commit/a592b827aa0c5ce17b204e140cc8f88d35eed811))
- **frontend:** Fix search focus issue and add transaction statistics. ([2c85722f](https://github.com/elisiariocouto/leggen/commit/2c85722fd010f0345a77dde3f403c7a3b1683238))
-  Add sync error and account expiry notifications. ([1a2ec45f](https://github.com/elisiariocouto/leggen/commit/1a2ec45f89b59942ea792552a220ccab12b4ba90))


### Miscellaneous Tasks

- **ci:** Fix workflow permissions. ([cbbc3165](https://github.com/elisiariocouto/leggen/commit/cbbc316537a901735899ec2145d79ca2718362d7))
-  Merge sample data scripts. ([31abe68b](https://github.com/elisiariocouto/leggen/commit/31abe68b2a15e0f1333e4d4bd173ce7594b78ad0))
-  Update dependencies. ([a75365d8](https://github.com/elisiariocouto/leggen/commit/a75365d80530a685443899bc29eb32b1ec26bc91))


### Refactor

- **api:** Improve database connection management and reduce boilerplate. ([267db8ac](https://github.com/elisiariocouto/leggen/commit/267db8ac632a0da33c1dd2ea74cbc0a343d48d5c))
- **api:** Split DatabaseService into repository pattern. ([5f879910](https://github.com/elisiariocouto/leggen/commit/5f87991076757d510132aec0488a1cc7873dd62d))
- **api:** Remove DatabaseService layer and implement dependency injection. ([9dc63579](https://github.com/elisiariocouto/leggen/commit/9dc635790596c90e01d1515577000282bae05114))
- **api:** Update all modified files with dependency injection changes. ([9e9b1cf1](https://github.com/elisiariocouto/leggen/commit/9e9b1cf15f6762f6f363ebbc60279634147086ee))
- **frontend:** Address code review feedback on focus and currency handling. ([c8b161e7](https://github.com/elisiariocouto/leggen/commit/c8b161e7f2727f799e2fad7c5033a46edf759b75))
-  Remove API response wrapper pattern. ([fabea404](https://github.com/elisiariocouto/leggen/commit/fabea404efbcd33927d400582e4ac5e928ff3828))
-  Replace magic numbers with named constants. ([d58894d0](https://github.com/elisiariocouto/leggen/commit/d58894d07c805b227b28e421fa9f132fdec3ea86))
-  Consolidate service layer with dedicated data processors. ([fbb3eb9e](https://github.com/elisiariocouto/leggen/commit/fbb3eb9e64bbb2a5f55dad84f69171411147377b))



## 2025.11.0 (2025/11/22)

### Bug Fixes

- **frontend:** Apply iOS safe area insets to body element instead of individual components. ([d2bc179d](https://github.com/elisiariocouto/leggen/commit/d2bc179d5937172a01ebbfffd35e7617f0ac32af))
-  Fallback to internal_transaction_id when bank transactions do not have transaction_id. ([b1b348ba](https://github.com/elisiariocouto/leggen/commit/b1b348badb5d1ea9c01ef9ecab1003252165468c))



## 2025.10.2 (2025/10/06)

### Bug Fixes

- **frontend:** Improve nginx config. ([d78f4811](https://github.com/elisiariocouto/leggen/commit/d78f4811922df7e637abe65b1d0b1157dd331c3c))
- **frontend:** Include default mime types. ([7c06a1d8](https://github.com/elisiariocouto/leggen/commit/7c06a1d8b9bca3da2c481d9e89e7564cfffe32a3))



## 2025.10.1 (2025/10/05)

### Bug Fixes

- **frontend:** Fix PWA caching system, remove prompts. ([1cd63731](https://github.com/elisiariocouto/leggen/commit/1cd63731a35a1c77a59d7ae1a898ad8f22e362e4))


### Documentation

-  Improve documentation, add gif showing web app. ([0750c41b](https://github.com/elisiariocouto/leggen/commit/0750c41b7b6634900ec19b1701d58b06346028e3))


### Refactor

- **frontend:** Standardize button styling using shadcn Button component. ([38fddeb2](https://github.com/elisiariocouto/leggen/commit/38fddeb281588de41d8ff6292c1dd48443a059a4))



## 2025.10.0 (2025/10/01)

### Bug Fixes

- **gocardless:** Increase timeout to 30 seconds, some requests take some time. ([ca7968cc](https://github.com/elisiariocouto/leggen/commit/ca7968cc3c625e243fe2d75590a9e56f3100072b))



## 2025.9.26 (2025/09/30)

### Debug

-  Log different sets of GoCardless rate limits. ([8802d247](https://github.com/elisiariocouto/leggen/commit/8802d24789cbb8e854d857a0d7cc89a25a26f378))



## 2025.9.25 (2025/09/30)

### Bug Fixes

- **api:** Fix S3 backup path-style configuration and improve UX. ([22ec0e36](https://github.com/elisiariocouto/leggen/commit/22ec0e36b11e5b017075bee51de0423a53ec4648))


### Features

- **api:** Add S3 backup functionality to backend ([7f2a4634](https://github.com/elisiariocouto/leggen/commit/7f2a4634c51814b6785433a25ce42d20aea0558c))
- **frontend:** Add S3 backup UI and complete backup functionality ([01229130](https://github.com/elisiariocouto/leggen/commit/0122913052793bcbf011cb557ef182be21c5de93))
- **frontend:** Add ability to list backups and create a backup on demand. ([473f126d](https://github.com/elisiariocouto/leggen/commit/473f126d3e699521172539f2ca0bff0579ccee51))


### Miscellaneous Tasks

-  Log more rate limit headers. ([d36568da](https://github.com/elisiariocouto/leggen/commit/d36568da540d4fb4ae1fa10b322a3fa77dcc5360))



## 2025.9.24 (2025/09/25)

### Features

- **frontend:** Add comprehensive bank account management system. ([ef7c026d](https://github.com/elisiariocouto/leggen/commit/ef7c026db9911cc3be8d5f48e42a4d7beb4b9d0a))



## 2025.9.24 (2025/09/25)

### Features

- **frontend:** Add comprehensive bank account management system. ([ef7c026d](https://github.com/elisiariocouto/leggen/commit/ef7c026db9911cc3be8d5f48e42a4d7beb4b9d0a))



## 2025.9.23 (2025/09/24)

### Bug Fixes

- **cli:** Fix API URL handling for subpaths and improve client robustness. ([ae5d034d](https://github.com/elisiariocouto/leggen/commit/ae5d034d4b1da785e3dc240c1d60c2cae7de8010))
-  Correct sync trigger types from manual to scheduled/retry. ([460c5af6](https://github.com/elisiariocouto/leggen/commit/460c5af6ea343ef5685b716413d01d7a30fa9acf))


### Features

- **frontend:** Add version-based cache invalidation for PWA updates ([d4edf69f](https://github.com/elisiariocouto/leggen/commit/d4edf69f2cea2515a00435ee974116948057148d))



## 2025.9.23 (2025/09/24)

### Bug Fixes

- **cli:** Fix API URL handling for subpaths and improve client robustness. ([ae5d034d](https://github.com/elisiariocouto/leggen/commit/ae5d034d4b1da785e3dc240c1d60c2cae7de8010))
-  Correct sync trigger types from manual to scheduled/retry. ([460c5af6](https://github.com/elisiariocouto/leggen/commit/460c5af6ea343ef5685b716413d01d7a30fa9acf))


### Features

- **frontend:** Add version-based cache invalidation for PWA updates ([d4edf69f](https://github.com/elisiariocouto/leggen/commit/d4edf69f2cea2515a00435ee974116948057148d))



## 2025.9.22 (2025/09/24)

### Bug Fixes

- **api:** Add automatic token refresh on 401 errors in GoCardless service. ([36d698f7](https://github.com/elisiariocouto/leggen/commit/36d698f7ce05c7db0e4b07dd07979de2c70b053e))
- **api:** Fix banks API test fixtures to match GoCardless response format. ([24792744](https://github.com/elisiariocouto/leggen/commit/24792744f9660063e1a3abb9ed8e925fea9a5e60))


### Features

- **api:** Add separate sync failure notifications. ([e4e3f885](https://github.com/elisiariocouto/leggen/commit/e4e3f885eab1d45b0e10465ca04eb3f74e9c5a4d))
- **api:** Add bank logo support and fix banks endpoint type errors. ([b9ca74e7](https://github.com/elisiariocouto/leggen/commit/b9ca74e7e67c3877728b749a42f15f0c0d906561))
- **frontend:** Improve System page and TransactionsTable UX. ([62cd55e4](https://github.com/elisiariocouto/leggen/commit/62cd55e48fff7c2f5db9dd8230a7bd500e8f6eed))


### Miscellaneous Tasks

-  Add pre-commit instructions to AGENTS.md. ([a8f70412](https://github.com/elisiariocouto/leggen/commit/a8f704129b2453e604cf2ab776791ba1e91e6fc7))



## 2025.9.22 (2025/09/24)

### Bug Fixes

- **api:** Add automatic token refresh on 401 errors in GoCardless service. ([36d698f7](https://github.com/elisiariocouto/leggen/commit/36d698f7ce05c7db0e4b07dd07979de2c70b053e))
- **api:** Fix banks API test fixtures to match GoCardless response format. ([24792744](https://github.com/elisiariocouto/leggen/commit/24792744f9660063e1a3abb9ed8e925fea9a5e60))


### Features

- **api:** Add separate sync failure notifications. ([e4e3f885](https://github.com/elisiariocouto/leggen/commit/e4e3f885eab1d45b0e10465ca04eb3f74e9c5a4d))
- **api:** Add bank logo support and fix banks endpoint type errors. ([b9ca74e7](https://github.com/elisiariocouto/leggen/commit/b9ca74e7e67c3877728b749a42f15f0c0d906561))
- **frontend:** Improve System page and TransactionsTable UX. ([62cd55e4](https://github.com/elisiariocouto/leggen/commit/62cd55e48fff7c2f5db9dd8230a7bd500e8f6eed))


### Miscellaneous Tasks

-  Add pre-commit instructions to AGENTS.md. ([a8f70412](https://github.com/elisiariocouto/leggen/commit/a8f704129b2453e604cf2ab776791ba1e91e6fc7))



## 2025.9.21 (2025/09/22)

### Bug Fixes

- **frontend:** Remove duplicate padding from Analytics page for consistent layout ([27f3f2db](https://github.com/elisiariocouto/leggen/commit/27f3f2dbba91777234769cca08de5dbe8b378f10))


### Features

- **frontend:** Implement notification settings with separate drawers and improved design. ([c332642e](https://github.com/elisiariocouto/leggen/commit/c332642e648cb0a29100b500c03e17ae322845f8))



## 2025.9.21 (2025/09/22)

### Bug Fixes

- **frontend:** Remove duplicate padding from Analytics page for consistent layout ([27f3f2db](https://github.com/elisiariocouto/leggen/commit/27f3f2dbba91777234769cca08de5dbe8b378f10))


### Features

- **frontend:** Implement notification settings with separate drawers and improved design. ([c332642e](https://github.com/elisiariocouto/leggen/commit/c332642e648cb0a29100b500c03e17ae322845f8))



## 2025.9.20 (2025/09/22)

### Features

- **api:** Add sync operations tracking and database storage ([61f95920](https://github.com/elisiariocouto/leggen/commit/61f9592095220f47b758e19a63d70096deb35a92))
- **frontend:** Rename notifications page to System Status and add sync operations section ([3f2ff21e](https://github.com/elisiariocouto/leggen/commit/3f2ff21eac2c24e04d5957bbd15a6b8a5d0c021d))
-  Consolidate version display to use health endpoint. ([76a30d23](https://github.com/elisiariocouto/leggen/commit/76a30d23af07466ecfd571e7b7bb6724412652c1))


### Refactor

- **frontend:** Reorganize pages with tabbed Settings and focused System page ([65404848](https://github.com/elisiariocouto/leggen/commit/65404848aa27cfcb11a371c194ca533b17cb08ff))



## 2025.9.20 (2025/09/22)

### Features

- **api:** Add sync operations tracking and database storage ([61f95920](https://github.com/elisiariocouto/leggen/commit/61f9592095220f47b758e19a63d70096deb35a92))
- **frontend:** Rename notifications page to System Status and add sync operations section ([3f2ff21e](https://github.com/elisiariocouto/leggen/commit/3f2ff21eac2c24e04d5957bbd15a6b8a5d0c021d))
-  Consolidate version display to use health endpoint. ([76a30d23](https://github.com/elisiariocouto/leggen/commit/76a30d23af07466ecfd571e7b7bb6724412652c1))


### Refactor

- **frontend:** Reorganize pages with tabbed Settings and focused System page ([65404848](https://github.com/elisiariocouto/leggen/commit/65404848aa27cfcb11a371c194ca533b17cb08ff))



## 2025.9.19 (2025/09/21)

### Bug Fixes

- **frontend:** Close mobile sidebar on navigation item click ([dd24a0e0](https://github.com/elisiariocouto/leggen/commit/dd24a0e0d34c3b2ff37bc75b50162768b4d15cc5))
- **frontend:** Resolve mobile horizontal scroll in Time Period filters ([4ce56fdc](https://github.com/elisiariocouto/leggen/commit/4ce56fdc042b0dbf3442a1ab201392700add90d6))


### Features

- **frontend:** Add version display in header near connection status ([340e1a32](https://github.com/elisiariocouto/leggen/commit/340e1a3235916566a4e403e9ec7b82ea799fbffd))



## 2025.9.19 (2025/09/21)

### Bug Fixes

- **frontend:** Close mobile sidebar on navigation item click ([dd24a0e0](https://github.com/elisiariocouto/leggen/commit/dd24a0e0d34c3b2ff37bc75b50162768b4d15cc5))
- **frontend:** Resolve mobile horizontal scroll in Time Period filters ([4ce56fdc](https://github.com/elisiariocouto/leggen/commit/4ce56fdc042b0dbf3442a1ab201392700add90d6))


### Features

- **frontend:** Add version display in header near connection status ([340e1a32](https://github.com/elisiariocouto/leggen/commit/340e1a3235916566a4e403e9ec7b82ea799fbffd))



## 2025.9.18 (2025/09/19)

### Documentation

-  Add instructions for shadcn/ui. ([83bb3fce](https://github.com/elisiariocouto/leggen/commit/83bb3fcef20d21a210bc53ce77aa533d37771668))


### Features

- **frontend:** Transform layout to use shadcn dashboard-01 with iOS PWA safe area support. ([fbb9e332](https://github.com/elisiariocouto/leggen/commit/fbb9e33279028a6a7ccf46c3696a012ec16a9ca7))



## 2025.9.18 (2025/09/19)

### Documentation

-  Add instructions for shadcn/ui. ([83bb3fce](https://github.com/elisiariocouto/leggen/commit/83bb3fcef20d21a210bc53ce77aa533d37771668))


### Features

- **frontend:** Transform layout to use shadcn dashboard-01 with iOS PWA safe area support. ([fbb9e332](https://github.com/elisiariocouto/leggen/commit/fbb9e33279028a6a7ccf46c3696a012ec16a9ca7))



## 2025.9.17 (2025/09/18)

### Bug Fixes

- **api:** Prevent duplicate notifications for existing transactions during sync. ([25747d7d](https://github.com/elisiariocouto/leggen/commit/25747d7d372e291090764a6814f9d8d0b76aea3b))


### Miscellaneous Tasks

-  Format files. ([848eccb3](https://github.com/elisiariocouto/leggen/commit/848eccb35b910c8121d15611547dca8da0b12756))



## 2025.9.17 (2025/09/18)

### Bug Fixes

- **api:** Prevent duplicate notifications for existing transactions during sync. ([25747d7d](https://github.com/elisiariocouto/leggen/commit/25747d7d372e291090764a6814f9d8d0b76aea3b))


### Miscellaneous Tasks

-  Format files. ([848eccb3](https://github.com/elisiariocouto/leggen/commit/848eccb35b910c8121d15611547dca8da0b12756))



## 2025.9.16 (2025/09/18)

### Bug Fixes

- **frontend:** Add iOS safe area support for PWA sticky header ([6589c2dd](https://github.com/elisiariocouto/leggen/commit/6589c2dd666f8605cf6d1bf9ad7277734d4cd302))



## 2025.9.16 (2025/09/18)

### Bug Fixes

- **frontend:** Add iOS safe area support for PWA sticky header ([6589c2dd](https://github.com/elisiariocouto/leggen/commit/6589c2dd666f8605cf6d1bf9ad7277734d4cd302))



## 2025.9.15 (2025/09/18)

### Features

- **frontend:** Add settings page with account management functionality. ([056c33b9](https://github.com/elisiariocouto/leggen/commit/056c33b9c5cfbc2842cc2dd4ca8c4e3959a2be80))


### Refactor

- **frontend:** Simplify filter bar UI and remove advanced filters popover. ([be4f7f8c](https://github.com/elisiariocouto/leggen/commit/be4f7f8cecfe2564abdf0ce1be08497e5a6d7b68))



## 2025.9.15 (2025/09/18)

### Features

- **frontend:** Add settings page with account management functionality. ([056c33b9](https://github.com/elisiariocouto/leggen/commit/056c33b9c5cfbc2842cc2dd4ca8c4e3959a2be80))


### Refactor

- **frontend:** Simplify filter bar UI and remove advanced filters popover. ([be4f7f8c](https://github.com/elisiariocouto/leggen/commit/be4f7f8cecfe2564abdf0ce1be08497e5a6d7b68))



## 2025.9.14 (2025/09/18)

### Bug Fixes

- **config:** Remove aliases for configuration keys that were disabling telegram notifications in some cases. ([61442a59](https://github.com/elisiariocouto/leggen/commit/61442a598fa7f38c568e3df7e1d924ed85df7491))


### Miscellaneous Tasks

- **ci:** Prevent double GitHub Actions runs on new releases. ([30d7c2ed](https://github.com/elisiariocouto/leggen/commit/30d7c2ed4e9aff144837a1f0ed67a8ded0b5d72a))



## 2025.9.14 (2025/09/18)

### Bug Fixes

- **config:** Remove aliases for configuration keys that were disabling telegram notifications in some cases. ([61442a59](https://github.com/elisiariocouto/leggen/commit/61442a598fa7f38c568e3df7e1d924ed85df7491))


### Miscellaneous Tasks

- **ci:** Prevent double GitHub Actions runs on new releases. ([30d7c2ed](https://github.com/elisiariocouto/leggen/commit/30d7c2ed4e9aff144837a1f0ed67a8ded0b5d72a))



## 2025.9.13 (2025/09/17)

### Bug Fixes

- **frontend:** Resolve linting issue in skeleton component ([fb310a59](https://github.com/elisiariocouto/leggen/commit/fb310a5953cf51d1cac181529311e76a0f4ea9ee))
- **frontend:** Add index signature to PieDataPoint interface. ([81d7d163](https://github.com/elisiariocouto/leggen/commit/81d7d16301dafc62a95f63036819565ffb90ddb5))
- **frontend:** Resolve dual scroll and excessive whitespace issues on transactions page. ([8ab76081](https://github.com/elisiariocouto/leggen/commit/8ab760815c9ae072b8c2cb2460e31144b193e0b3))
- **frontend:** Remove broken running balance feature in transactions table. ([155a48d7](https://github.com/elisiariocouto/leggen/commit/155a48d7dc86b3f453ba6f8c37edf63c0b76c755))


### Features

- **frontend:** Complete shadcn migration of skeleton and styling components ([c83386b1](https://github.com/elisiariocouto/leggen/commit/c83386b1d5b165910abe8b391ca483e5b48cd35f))
- **frontend:** Add comprehensive PWA capabilities with dynamic theme support ([86891441](https://github.com/elisiariocouto/leggen/commit/86891441d65e13757f343cabc39ccdb3ca6adc75))
- **frontend:** Add PWA install prompts, update notifications, and app shortcuts ([3049a8cd](https://github.com/elisiariocouto/leggen/commit/3049a8cd2fa80c14f970884fb14df2ab88c418dd))
- **frontend:** Update brand identity with new logo and color scheme. ([2825dba2](https://github.com/elisiariocouto/leggen/commit/2825dba2e944b3fe31aaa33127b770e7474ce021))
- **frontend:** Update analytics cards to match home page design consistency. ([d9a39c30](https://github.com/elisiariocouto/leggen/commit/d9a39c30ab1248a9fdacff068d401c3daff3f6a5))


### Miscellaneous Tasks

-  Enable browsermcp and shadcn MCP servers. ([5a626b53](https://github.com/elisiariocouto/leggen/commit/5a626b53947f7e2d1544faf3ee06f8a0f1fb5d7a))


### Refactor

- **frontend:** Replace LoadingSpinner with shadcn skeleton components. ([84e609a7](https://github.com/elisiariocouto/leggen/commit/84e609a774ddc0caf9f84eaf1e8cdce021c82785))



## 2025.9.13 (2025/09/17)

### Bug Fixes

- **frontend:** Resolve linting issue in skeleton component ([fb310a59](https://github.com/elisiariocouto/leggen/commit/fb310a5953cf51d1cac181529311e76a0f4ea9ee))
- **frontend:** Add index signature to PieDataPoint interface. ([81d7d163](https://github.com/elisiariocouto/leggen/commit/81d7d16301dafc62a95f63036819565ffb90ddb5))
- **frontend:** Resolve dual scroll and excessive whitespace issues on transactions page. ([8ab76081](https://github.com/elisiariocouto/leggen/commit/8ab760815c9ae072b8c2cb2460e31144b193e0b3))
- **frontend:** Remove broken running balance feature in transactions table. ([155a48d7](https://github.com/elisiariocouto/leggen/commit/155a48d7dc86b3f453ba6f8c37edf63c0b76c755))


### Features

- **frontend:** Complete shadcn migration of skeleton and styling components ([c83386b1](https://github.com/elisiariocouto/leggen/commit/c83386b1d5b165910abe8b391ca483e5b48cd35f))
- **frontend:** Add comprehensive PWA capabilities with dynamic theme support ([86891441](https://github.com/elisiariocouto/leggen/commit/86891441d65e13757f343cabc39ccdb3ca6adc75))
- **frontend:** Add PWA install prompts, update notifications, and app shortcuts ([3049a8cd](https://github.com/elisiariocouto/leggen/commit/3049a8cd2fa80c14f970884fb14df2ab88c418dd))
- **frontend:** Update brand identity with new logo and color scheme. ([2825dba2](https://github.com/elisiariocouto/leggen/commit/2825dba2e944b3fe31aaa33127b770e7474ce021))
- **frontend:** Update analytics cards to match home page design consistency. ([d9a39c30](https://github.com/elisiariocouto/leggen/commit/d9a39c30ab1248a9fdacff068d401c3daff3f6a5))


### Miscellaneous Tasks

-  Enable browsermcp and shadcn MCP servers. ([5a626b53](https://github.com/elisiariocouto/leggen/commit/5a626b53947f7e2d1544faf3ee06f8a0f1fb5d7a))


### Refactor

- **frontend:** Replace LoadingSpinner with shadcn skeleton components. ([84e609a7](https://github.com/elisiariocouto/leggen/commit/84e609a774ddc0caf9f84eaf1e8cdce021c82785))



## 2025.9.12 (2025/09/15)


## 2025.9.12 (2025/09/15)


## 2025.9.11 (2025/09/15)

### Bug Fixes

- **config:** Add Pydantic validation and fix telegram config field mappings. ([2c6e0995](https://github.com/elisiariocouto/leggen/commit/2c6e0995968c9c9917992fd15ec10a89933c0c21))
- **config:** Fix example config file. ([d09cf6d0](https://github.com/elisiariocouto/leggen/commit/d09cf6d04ccb6233981f273cd88e0b8ffe074d71))
- **docs:** Remove test files and update gitignore ([692bee57](https://github.com/elisiariocouto/leggen/commit/692bee574ee8de16496a3c733bad53be3b256990))
- **frontend:** Align balance calculation between sidebar and Analytics page ([35b6d98e](https://github.com/elisiariocouto/leggen/commit/35b6d98e6a37b1e9caf8a232ffe66380e7203cad))
- **frontend:** Add ignore rules for eslint on shadcn components. ([74a700ff](https://github.com/elisiariocouto/leggen/commit/74a700ff87b2504c3d394cddd9935c56c3c7a00d))
-  Resolve all CI failures - linting, typing, and test issues ([c8f0a103](https://github.com/elisiariocouto/leggen/commit/c8f0a103c6ccdb722bbab1ac6973827b41fddc19))


### Features

- **analytics:** Fix transaction limits and improve chart legends ([e136fc4b](https://github.com/elisiariocouto/leggen/commit/e136fc4b75243b35a77bc0bf0260808006987d7a))
- **docs:** Add comprehensive copilot agent setup instructions ([c6ac4455](https://github.com/elisiariocouto/leggen/commit/c6ac4455f848dd429100dd3fc6d43de8c4e5aa6b))
- **docs:** Add configuration file setup to agent instructions ([482f16c7](https://github.com/elisiariocouto/leggen/commit/482f16c77eef1f477ba49475fe30f809de9a05d7))
- **frontend:** Enhance transactions page with advanced filtering and UI improvements. ([969776fb](https://github.com/elisiariocouto/leggen/commit/969776fb53261acca2f77b0c761584e201fde118))
- **frontend:** Replace heavy filter UI with modern shadcn/ui inline filter bar. ([eb27f191](https://github.com/elisiariocouto/leggen/commit/eb27f19196d92a6ae5220b81709fded499a12f4f))
- **frontend:** Complete shadcn/ui migration with dark mode support and analytics updates. ([66db34c7](https://github.com/elisiariocouto/leggen/commit/66db34c712300ff4b5dbe7e06246f16d6f6a8469))


### Miscellaneous Tasks

-  Sort imports, fix deprecated pydantic option. ([2467cb2f](https://github.com/elisiariocouto/leggen/commit/2467cb2f5af07a7262b3221bf61b58ad4017659a))
-  Check import order using ruff. ([da98b7b2](https://github.com/elisiariocouto/leggen/commit/da98b7b2b77c5b37792dedff11f8256da3b086f7))


### Refactor

- **analytics:** Simplify analytics endpoints and eliminate client-side processing. ([077e2bb1](https://github.com/elisiariocouto/leggen/commit/077e2bb1adbdb73ffde17635bd918cd40fe7fb5a))
-  Unify leggen and leggend packages into single leggen package ([318ca517](https://github.com/elisiariocouto/leggen/commit/318ca517f7ea599b37a8deb47ad80218fbae008f))
-  Consolidate database layer and eliminate wrapper complexity. ([5ae3a51d](https://github.com/elisiariocouto/leggen/commit/5ae3a51d8138b9aa28dbceabf575ab2577402e70))



## 2025.9.11 (2025/09/15)

### Bug Fixes

- **config:** Add Pydantic validation and fix telegram config field mappings. ([2c6e0995](https://github.com/elisiariocouto/leggen/commit/2c6e0995968c9c9917992fd15ec10a89933c0c21))
- **config:** Fix example config file. ([d09cf6d0](https://github.com/elisiariocouto/leggen/commit/d09cf6d04ccb6233981f273cd88e0b8ffe074d71))
- **docs:** Remove test files and update gitignore ([692bee57](https://github.com/elisiariocouto/leggen/commit/692bee574ee8de16496a3c733bad53be3b256990))
- **frontend:** Align balance calculation between sidebar and Analytics page ([35b6d98e](https://github.com/elisiariocouto/leggen/commit/35b6d98e6a37b1e9caf8a232ffe66380e7203cad))
- **frontend:** Add ignore rules for eslint on shadcn components. ([74a700ff](https://github.com/elisiariocouto/leggen/commit/74a700ff87b2504c3d394cddd9935c56c3c7a00d))
-  Resolve all CI failures - linting, typing, and test issues ([c8f0a103](https://github.com/elisiariocouto/leggen/commit/c8f0a103c6ccdb722bbab1ac6973827b41fddc19))


### Features

- **analytics:** Fix transaction limits and improve chart legends ([e136fc4b](https://github.com/elisiariocouto/leggen/commit/e136fc4b75243b35a77bc0bf0260808006987d7a))
- **docs:** Add comprehensive copilot agent setup instructions ([c6ac4455](https://github.com/elisiariocouto/leggen/commit/c6ac4455f848dd429100dd3fc6d43de8c4e5aa6b))
- **docs:** Add configuration file setup to agent instructions ([482f16c7](https://github.com/elisiariocouto/leggen/commit/482f16c77eef1f477ba49475fe30f809de9a05d7))
- **frontend:** Enhance transactions page with advanced filtering and UI improvements. ([969776fb](https://github.com/elisiariocouto/leggen/commit/969776fb53261acca2f77b0c761584e201fde118))
- **frontend:** Replace heavy filter UI with modern shadcn/ui inline filter bar. ([eb27f191](https://github.com/elisiariocouto/leggen/commit/eb27f19196d92a6ae5220b81709fded499a12f4f))
- **frontend:** Complete shadcn/ui migration with dark mode support and analytics updates. ([66db34c7](https://github.com/elisiariocouto/leggen/commit/66db34c712300ff4b5dbe7e06246f16d6f6a8469))


### Miscellaneous Tasks

-  Sort imports, fix deprecated pydantic option. ([2467cb2f](https://github.com/elisiariocouto/leggen/commit/2467cb2f5af07a7262b3221bf61b58ad4017659a))
-  Check import order using ruff. ([da98b7b2](https://github.com/elisiariocouto/leggen/commit/da98b7b2b77c5b37792dedff11f8256da3b086f7))


### Refactor

- **analytics:** Simplify analytics endpoints and eliminate client-side processing. ([077e2bb1](https://github.com/elisiariocouto/leggen/commit/077e2bb1adbdb73ffde17635bd918cd40fe7fb5a))
-  Unify leggen and leggend packages into single leggen package ([318ca517](https://github.com/elisiariocouto/leggen/commit/318ca517f7ea599b37a8deb47ad80218fbae008f))
-  Consolidate database layer and eliminate wrapper complexity. ([5ae3a51d](https://github.com/elisiariocouto/leggen/commit/5ae3a51d8138b9aa28dbceabf575ab2577402e70))



## 2025.9.10 (2025/09/13)

### Miscellaneous Tasks

- **frontend:** Update dependencies. ([06cf02f4](https://github.com/elisiariocouto/leggen/commit/06cf02f43ff72e4e01692e3a94a06be48d9acb1f))



## 2025.9.10 (2025/09/13)

### Miscellaneous Tasks

- **frontend:** Update dependencies. ([06cf02f4](https://github.com/elisiariocouto/leggen/commit/06cf02f43ff72e4e01692e3a94a06be48d9acb1f))



## 2025.9.9 (2025/09/11)

### Bug Fixes

- **core:** Handle permission errors gracefully in database path creation. ([4006dd12](https://github.com/elisiariocouto/leggen/commit/4006dd128e0896b338cb93fad60a1eca90c1873d))


### Features

- **frontend:** Improve transactions table mobile UX with responsive card layout ([1e94333d](https://github.com/elisiariocouto/leggen/commit/1e94333d8f0275542ae7fd6e49fb8b7f03ad3d11))
- **frontend:** Improve transactions table mobile UX with responsive card layout ([1c901a9d](https://github.com/elisiariocouto/leggen/commit/1c901a9ddab0f6515dce56df8cce74518805a6bb))
-  Remove config.toml file - should be created when needed ([a5d10b35](https://github.com/elisiariocouto/leggen/commit/a5d10b3539e7cfc649b0fee05b12c4a03681e135))


### Refactor

- **core:** Integrate directory creation with database path retrieval and remove backup file. ([7d9744a4](https://github.com/elisiariocouto/leggen/commit/7d9744a40e7898e5bbe52e2e9f54317aa5c1cdd6))



## 2025.9.9 (2025/09/11)

### Bug Fixes

- **core:** Handle permission errors gracefully in database path creation. ([4006dd12](https://github.com/elisiariocouto/leggen/commit/4006dd128e0896b338cb93fad60a1eca90c1873d))


### Features

- **frontend:** Improve transactions table mobile UX with responsive card layout ([1e94333d](https://github.com/elisiariocouto/leggen/commit/1e94333d8f0275542ae7fd6e49fb8b7f03ad3d11))
- **frontend:** Improve transactions table mobile UX with responsive card layout ([1c901a9d](https://github.com/elisiariocouto/leggen/commit/1c901a9ddab0f6515dce56df8cce74518805a6bb))
-  Remove config.toml file - should be created when needed ([a5d10b35](https://github.com/elisiariocouto/leggen/commit/a5d10b3539e7cfc649b0fee05b12c4a03681e135))


### Refactor

- **core:** Integrate directory creation with database path retrieval and remove backup file. ([7d9744a4](https://github.com/elisiariocouto/leggen/commit/7d9744a40e7898e5bbe52e2e9f54317aa5c1cdd6))



## 2025.9.8 (2025/09/11)

### Bug Fixes

-  Change branch name from develop to dev in CI workflow ([f4bf549b](https://github.com/elisiariocouto/leggen/commit/f4bf549b99197d70104abf5731ab1ccb67cc9a69))


### Features

-  Update CI workflow to use Node.js 20 instead of 18 ([e4e04ea3](https://github.com/elisiariocouto/leggen/commit/e4e04ea34ea568c08292562243b6e6c08234d918))



## 2025.9.8 (2025/09/11)

### Bug Fixes

-  Change branch name from develop to dev in CI workflow ([f4bf549b](https://github.com/elisiariocouto/leggen/commit/f4bf549b99197d70104abf5731ab1ccb67cc9a69))


### Features

-  Update CI workflow to use Node.js 20 instead of 18 ([e4e04ea3](https://github.com/elisiariocouto/leggen/commit/e4e04ea34ea568c08292562243b6e6c08234d918))



## 2025.9.7 (2025/09/11)

### Bug Fixes

-  Simplify notification settings and fix notification test on dashboard. ([91020e32](https://github.com/elisiariocouto/leggen/commit/91020e32ea836ee8af4aeaf5d49525c24b566aed))


### Features

- **frontend:** Implement TanStack Table for transactions view ([544527f2](https://github.com/elisiariocouto/leggen/commit/544527f28284fb9644bec6e721fa5da8ce10739f))
-  Improve transactions API pagination and search ([2d6800ef](https://github.com/elisiariocouto/leggen/commit/2d6800eff8e484d3d175225f94d854706584a773))



## 2025.9.7 (2025/09/11)

### Bug Fixes

-  Simplify notification settings and fix notification test on dashboard. ([91020e32](https://github.com/elisiariocouto/leggen/commit/91020e32ea836ee8af4aeaf5d49525c24b566aed))


### Features

- **frontend:** Implement TanStack Table for transactions view ([544527f2](https://github.com/elisiariocouto/leggen/commit/544527f28284fb9644bec6e721fa5da8ce10739f))
-  Improve transactions API pagination and search ([2d6800ef](https://github.com/elisiariocouto/leggen/commit/2d6800eff8e484d3d175225f94d854706584a773))



## 2025.9.6 (2025/09/10)

### Features

- **db:** Migrate transactions table to composite primary key ([a00d6ce2](https://github.com/elisiariocouto/leggen/commit/a00d6ce2ce2c4a070e9fae56c0cea58b3aab6cec))



## 2025.9.6 (2025/09/10)

### Features

- **db:** Migrate transactions table to composite primary key ([a00d6ce2](https://github.com/elisiariocouto/leggen/commit/a00d6ce2ce2c4a070e9fae56c0cea58b3aab6cec))



## 2025.9.5 (2025/09/10)

### Bug Fixes

-  Correct composite key migration check ([c0ee21d6](https://github.com/elisiariocouto/leggen/commit/c0ee21d6fa8d5d61c029bd9334a7674fce99f729))



## 2025.9.5 (2025/09/10)

### Bug Fixes

-  Correct composite key migration check ([c0ee21d6](https://github.com/elisiariocouto/leggen/commit/c0ee21d6fa8d5d61c029bd9334a7674fce99f729))



## 2025.9.4 (2025/09/10)

### Bug Fixes

- **api:** Resolve duplicate transactions with composite key migration ([13e92ccd](https://github.com/elisiariocouto/leggen/commit/13e92ccd3497bacf3b8639f6332cd3f4b682bd0a))


### Features

- **api:** Add currency extraction and account name updates ([d9c50d12](https://github.com/elisiariocouto/leggen/commit/d9c50d129825529e0fb6477e5b62c0f990523bca))
- **frontend:** Adapt to composite key transaction structure ([61fafecb](https://github.com/elisiariocouto/leggen/commit/61fafecb780a877a69ecca27ea95a1494669b70d))
- **frontend:** Add account name editing functionality ([aa97f368](https://github.com/elisiariocouto/leggen/commit/aa97f36819f15f1afc34f45642abdc6e2ce6c883))
- **frontend:** Implement TanStack Router with mobile sidebar ([ca41b7af](https://github.com/elisiariocouto/leggen/commit/ca41b7af0a5e50e0350857a4ace7979b7b29eab2))
- **web:** Add modal to view raw transaction. ([433ba3fa](https://github.com/elisiariocouto/leggen/commit/433ba3faf9937613786e66e9ee13152f96d00c43))



## 2025.9.4 (2025/09/10)

### Bug Fixes

- **api:** Resolve duplicate transactions with composite key migration ([13e92ccd](https://github.com/elisiariocouto/leggen/commit/13e92ccd3497bacf3b8639f6332cd3f4b682bd0a))


### Features

- **api:** Add currency extraction and account name updates ([d9c50d12](https://github.com/elisiariocouto/leggen/commit/d9c50d129825529e0fb6477e5b62c0f990523bca))
- **frontend:** Adapt to composite key transaction structure ([61fafecb](https://github.com/elisiariocouto/leggen/commit/61fafecb780a877a69ecca27ea95a1494669b70d))
- **frontend:** Add account name editing functionality ([aa97f368](https://github.com/elisiariocouto/leggen/commit/aa97f36819f15f1afc34f45642abdc6e2ce6c883))
- **frontend:** Implement TanStack Router with mobile sidebar ([ca41b7af](https://github.com/elisiariocouto/leggen/commit/ca41b7af0a5e50e0350857a4ace7979b7b29eab2))
- **web:** Add modal to view raw transaction. ([433ba3fa](https://github.com/elisiariocouto/leggen/commit/433ba3faf9937613786e66e9ee13152f96d00c43))



## 2025.9.4 (2025/09/10)

### Bug Fixes

- **api:** Resolve duplicate transactions with composite key migration ([13e92ccd](https://github.com/elisiariocouto/leggen/commit/13e92ccd3497bacf3b8639f6332cd3f4b682bd0a))


### Features

- **api:** Add currency extraction and account name updates ([d9c50d12](https://github.com/elisiariocouto/leggen/commit/d9c50d129825529e0fb6477e5b62c0f990523bca))
- **frontend:** Adapt to composite key transaction structure ([61fafecb](https://github.com/elisiariocouto/leggen/commit/61fafecb780a877a69ecca27ea95a1494669b70d))
- **frontend:** Add account name editing functionality ([aa97f368](https://github.com/elisiariocouto/leggen/commit/aa97f36819f15f1afc34f45642abdc6e2ce6c883))
- **frontend:** Implement TanStack Router with mobile sidebar ([ca41b7af](https://github.com/elisiariocouto/leggen/commit/ca41b7af0a5e50e0350857a4ace7979b7b29eab2))
- **web:** Add modal to view raw transaction. ([433ba3fa](https://github.com/elisiariocouto/leggen/commit/433ba3faf9937613786e66e9ee13152f96d00c43))



## 2025.9.3 (2025/09/10)

### Miscellaneous Tasks

- **ci:** Fix GitHub Actions syntax. ([90e58734](https://github.com/elisiariocouto/leggen/commit/90e58734adb9638efd695719321874658529561d))



## 2025.9.3 (2025/09/10)

### Miscellaneous Tasks

- **ci:** Fix GitHub Actions syntax. ([90e58734](https://github.com/elisiariocouto/leggen/commit/90e58734adb9638efd695719321874658529561d))



## 2025.9.2 (2025/09/10)

### Bug Fixes

- **ci:** Prevent duplicate Docker tags in GitHub Actions ([53e08e8e](https://github.com/elisiariocouto/leggen/commit/53e08e8e4b909b4895b5a447cfbce515893d31a5))


### Features

- **docker:** Add Docker containerization for React frontend ([84fe79b3](https://github.com/elisiariocouto/leggen/commit/84fe79b37b4f154fa0758f8d037cdba0d166dd3b))



## 2025.9.2 (2025/09/10)

### Bug Fixes

- **ci:** Prevent duplicate Docker tags in GitHub Actions ([53e08e8e](https://github.com/elisiariocouto/leggen/commit/53e08e8e4b909b4895b5a447cfbce515893d31a5))


### Features

- **docker:** Add Docker containerization for React frontend ([84fe79b3](https://github.com/elisiariocouto/leggen/commit/84fe79b37b4f154fa0758f8d037cdba0d166dd3b))



## 2025.9.1 (2025/09/09)

### Bug Fixes

-  Handle duplicate transactionId values in migration ([8fabaf7b](https://github.com/elisiariocouto/leggen/commit/8fabaf7b86fde921c61266568ecb0403d3102671))


### Miscellaneous Tasks

-  Improve AGENTS.md. ([3270dc45](https://github.com/elisiariocouto/leggen/commit/3270dc4585e6b33d55aef0deecd849753d36fa74))


### Refactor

-  Remove unused hide_missing_ids functionality ([8006e5e1](https://github.com/elisiariocouto/leggen/commit/8006e5e1f6373aae39d3c38068d694e142bc85a5))



## 2025.9.1 (2025/09/09)

### Bug Fixes

-  Handle duplicate transactionId values in migration ([8fabaf7b](https://github.com/elisiariocouto/leggen/commit/8fabaf7b86fde921c61266568ecb0403d3102671))


### Miscellaneous Tasks

-  Improve AGENTS.md. ([3270dc45](https://github.com/elisiariocouto/leggen/commit/3270dc4585e6b33d55aef0deecd849753d36fa74))


### Refactor

-  Remove unused hide_missing_ids functionality ([8006e5e1](https://github.com/elisiariocouto/leggen/commit/8006e5e1f6373aae39d3c38068d694e142bc85a5))



## 2025.9.0 (2025/09/09)

### Bug Fixes

- **cli:** Show transactions without internal ID when using --full. ([46f3f5c4](https://github.com/elisiariocouto/leggen/commit/46f3f5c4984224c3f4b421e1a06dcf44d4f211e0))
-  Do not install development dependencies. ([73d6bd32](https://github.com/elisiariocouto/leggen/commit/73d6bd32dbc59608ef1472dc65d9e18450f00896))
-  Implement proper GoCardless authentication and add dev features ([f0fee4fd](https://github.com/elisiariocouto/leggen/commit/f0fee4fd82e1c788614d73fcd0075f5e16976650))
-  Make internal transcation ID optional. ([6bce7eb6](https://github.com/elisiariocouto/leggen/commit/6bce7eb6be5f9a5286eb27e777fbf83a6b1c5f8d))
-  Resolve 404 balances endpoint and currency formatting errors ([417b7753](https://github.com/elisiariocouto/leggen/commit/417b77539fc275493d55efb29f92abcea666b210))
-  Merge account details into balance data to prevent unknown/N/A values ([eaaea6e4](https://github.com/elisiariocouto/leggen/commit/eaaea6e4598e9c81997573e19f4ef1c58ebe320f))
-  Use account status for balance records instead of hardcoded 'active' ([541cb262](https://github.com/elisiariocouto/leggen/commit/541cb262ee5783eedf2b154c148c28ec89845da5))


### Documentation

-  Update README for new web architecture ([4018b263](https://github.com/elisiariocouto/leggen/commit/4018b263f27c2b59af31428d7a0878280a291c85))


### Features

-  Transform to web architecture with FastAPI backend ([91f53b35](https://github.com/elisiariocouto/leggen/commit/91f53b35b18740869ee9cebfac394db2e12db099))
-  Add comprehensive test suite with 46 passing tests ([34e793c7](https://github.com/elisiariocouto/leggen/commit/34e793c75c8df1e57ea240b92ccf0843a80c2a14))
-  Add mypy to pre-commit. ([ec8ef834](https://github.com/elisiariocouto/leggen/commit/ec8ef8346add878f3ff4e8ed928b952d9b5dd584))
-  Implement database-first architecture to minimize GoCardless API calls ([155c3055](https://github.com/elisiariocouto/leggen/commit/155c30559f4cacd76ef01e50ec29ee436d3f9d56))
-  Implement dynamic API connection status ([cb2e70e4](https://github.com/elisiariocouto/leggen/commit/cb2e70e42d1122e9c2e5420b095aeb1e55454c24))
-  Add automatic balance timestamp migration mechanism ([34501f5f](https://github.com/elisiariocouto/leggen/commit/34501f5f0d3b3dff68364b60be77bfb99071b269))
-  Improve notification filters configuration format ([2191fe90](https://github.com/elisiariocouto/leggen/commit/2191fe906659f4fd22c25b6cb9fbb95c03472f00))
-  Add notifications view and update branding ([abf39abe](https://github.com/elisiariocouto/leggen/commit/abf39abe74b75d8cb980109fbcbdd940066cc90b))
-  Make API URL configurable and improve code quality ([37949a4e](https://github.com/elisiariocouto/leggen/commit/37949a4e1f25a2656f6abef75ba942f7b205c130))
-  Change versioning scheme to calver. ([f2e05484](https://github.com/elisiariocouto/leggen/commit/f2e05484dc688409b6db6bd16858b066d3a16976))


### Miscellaneous Tasks

-  Implement code review suggestions and format code. ([de3da84d](https://github.com/elisiariocouto/leggen/commit/de3da84dffd83e0b232cf76836935a66eb704aee))


### Refactor

-  Remove MongoDB support, simplify to SQLite-only architecture ([47164e85](https://github.com/elisiariocouto/leggen/commit/47164e854600dfcac482449769b1d2e55c842570))
-  Remove unused amount_threshold and keywords from notification filters ([95709978](https://github.com/elisiariocouto/leggen/commit/957099786cb0e48c9ffbda11b3172ec9fae9ac37))



## 2025.9.0 (2025/09/09)

### Bug Fixes

- **cli:** Show transactions without internal ID when using --full. ([46f3f5c4](https://github.com/elisiariocouto/leggen/commit/46f3f5c4984224c3f4b421e1a06dcf44d4f211e0))
-  Do not install development dependencies. ([73d6bd32](https://github.com/elisiariocouto/leggen/commit/73d6bd32dbc59608ef1472dc65d9e18450f00896))
-  Implement proper GoCardless authentication and add dev features ([f0fee4fd](https://github.com/elisiariocouto/leggen/commit/f0fee4fd82e1c788614d73fcd0075f5e16976650))
-  Make internal transcation ID optional. ([6bce7eb6](https://github.com/elisiariocouto/leggen/commit/6bce7eb6be5f9a5286eb27e777fbf83a6b1c5f8d))
-  Resolve 404 balances endpoint and currency formatting errors ([417b7753](https://github.com/elisiariocouto/leggen/commit/417b77539fc275493d55efb29f92abcea666b210))
-  Merge account details into balance data to prevent unknown/N/A values ([eaaea6e4](https://github.com/elisiariocouto/leggen/commit/eaaea6e4598e9c81997573e19f4ef1c58ebe320f))
-  Use account status for balance records instead of hardcoded 'active' ([541cb262](https://github.com/elisiariocouto/leggen/commit/541cb262ee5783eedf2b154c148c28ec89845da5))


### Documentation

-  Update README for new web architecture ([4018b263](https://github.com/elisiariocouto/leggen/commit/4018b263f27c2b59af31428d7a0878280a291c85))


### Features

-  Transform to web architecture with FastAPI backend ([91f53b35](https://github.com/elisiariocouto/leggen/commit/91f53b35b18740869ee9cebfac394db2e12db099))
-  Add comprehensive test suite with 46 passing tests ([34e793c7](https://github.com/elisiariocouto/leggen/commit/34e793c75c8df1e57ea240b92ccf0843a80c2a14))
-  Add mypy to pre-commit. ([ec8ef834](https://github.com/elisiariocouto/leggen/commit/ec8ef8346add878f3ff4e8ed928b952d9b5dd584))
-  Implement database-first architecture to minimize GoCardless API calls ([155c3055](https://github.com/elisiariocouto/leggen/commit/155c30559f4cacd76ef01e50ec29ee436d3f9d56))
-  Implement dynamic API connection status ([cb2e70e4](https://github.com/elisiariocouto/leggen/commit/cb2e70e42d1122e9c2e5420b095aeb1e55454c24))
-  Add automatic balance timestamp migration mechanism ([34501f5f](https://github.com/elisiariocouto/leggen/commit/34501f5f0d3b3dff68364b60be77bfb99071b269))
-  Improve notification filters configuration format ([2191fe90](https://github.com/elisiariocouto/leggen/commit/2191fe906659f4fd22c25b6cb9fbb95c03472f00))
-  Add notifications view and update branding ([abf39abe](https://github.com/elisiariocouto/leggen/commit/abf39abe74b75d8cb980109fbcbdd940066cc90b))
-  Make API URL configurable and improve code quality ([37949a4e](https://github.com/elisiariocouto/leggen/commit/37949a4e1f25a2656f6abef75ba942f7b205c130))
-  Change versioning scheme to calver. ([f2e05484](https://github.com/elisiariocouto/leggen/commit/f2e05484dc688409b6db6bd16858b066d3a16976))


### Miscellaneous Tasks

-  Implement code review suggestions and format code. ([de3da84d](https://github.com/elisiariocouto/leggen/commit/de3da84dffd83e0b232cf76836935a66eb704aee))


### Refactor

-  Remove MongoDB support, simplify to SQLite-only architecture ([47164e85](https://github.com/elisiariocouto/leggen/commit/47164e854600dfcac482449769b1d2e55c842570))
-  Remove unused amount_threshold and keywords from notification filters ([95709978](https://github.com/elisiariocouto/leggen/commit/957099786cb0e48c9ffbda11b3172ec9fae9ac37))



## 0.6.11 (2025/02/23)

### Bug Fixes

-  Add workdir to dockerfile last stage. ([355fa5cf](https://github.com/elisiariocouto/leggen/commit/355fa5cfb6ccc4ca225d921cdc2ad77d6bb9b2e6))



## 0.6.10 (2025/01/14)

### Bug Fixes

- **ci:** Install uv before publishing. ([74800944](https://github.com/elisiariocouto/leggen/commit/7480094419697a46515a88a635d4e73820b0d283))



## 0.6.9 (2025/01/14)

### Miscellaneous Tasks

-  Setup PyPI Trusted Publishing. ([ca29d527](https://github.com/elisiariocouto/leggen/commit/ca29d527c9e5f9391dfcad6601ad9c585b511b47))



## 0.6.8 (2025/01/13)

### Miscellaneous Tasks

-  Migrate from Poetry to uv, bump dependencies and python version. ([33006f8f](https://github.com/elisiariocouto/leggen/commit/33006f8f437da2b9b3c860f22a1fda2a2e5b19a1))
-  Fix typo in release script. ([eb734018](https://github.com/elisiariocouto/leggen/commit/eb734018964d8281450a8713d0a15688d2cb42bf))



## 0.6.7 (2024/09/15)

### Bug Fixes

- **notifications/telegram:** Escape characters when notifying via Telegram. ([7efbccfc](https://github.com/elisiariocouto/leggen/commit/7efbccfc90ea601da9029909bdd4f21640d73e6a))


### Miscellaneous Tasks

-  Bump dependencies. ([75ca7f17](https://github.com/elisiariocouto/leggen/commit/75ca7f177fb9992395e576ba9038a63e90612e5c))



## 0.6.6 (2024/08/21)

### Bug Fixes

- **commands/status:** Handle exception when no `last_accessed` is returned from GoCardless API. ([c70a4e5c](https://github.com/elisiariocouto/leggen/commit/c70a4e5cb87a19a5a0ed194838e323c6246856ab))
- **notifications/telegram:** Escape parenthesis. ([a29bd1ab](https://github.com/elisiariocouto/leggen/commit/a29bd1ab683bc9e068aefb722e9e87bb4fe6aa76))


### Miscellaneous Tasks

-  Update dependencies, use ruff to format code. ([59346334](https://github.com/elisiariocouto/leggen/commit/59346334dbe999ccfd70f6687130aaedb50254fa))


## 0.6.5 (2024/07/05)

### Bug Fixes

- **sync:** Continue on account deactivation. ([758a3a22](https://github.com/elisiariocouto/leggen/commit/758a3a2257c490a92fb0b0673c74d720ad7e87f7))


### Miscellaneous Tasks

-  Bump dependencies. ([effabf06](https://github.com/elisiariocouto/leggen/commit/effabf06954b08e05e3084fdbc54518ea5d947dc))


## 0.6.4 (2024/06/07)

### Bug Fixes

- **sync:** Correctly calculate days left. ([6c44beda](https://github.com/elisiariocouto/leggen/commit/6c44beda672242714bab1100b1f0576cdce255ca))


## 0.6.3 (2024/06/07)

### Features

- **sync:** Correctly calculate days left, based on the default 90 days period. ([3cb38e2e](https://github.com/elisiariocouto/leggen/commit/3cb38e2e9fb08e07664caa7daa9aa651262bd213))


## 0.6.2 (2024/06/07)

### Bug Fixes

- **sync:** Use timezone-aware datetime objects. ([9402c253](https://github.com/elisiariocouto/leggen/commit/9402c2535baade84128bdfd0fc314d5225bbd822))


## 0.6.1 (2024/06/07)

### Bug Fixes

- **sync:** Get correct parameter for requisition creation time. ([b60ba068](https://github.com/elisiariocouto/leggen/commit/b60ba068cd7facea5f60fca61bf5845cabf0c2c6))


## 0.6.0 (2024/06/07)

### Features

- **sync:** Save account balances in new table. ([332d4d51](https://github.com/elisiariocouto/leggen/commit/332d4d51d00286ecec71703aaa39e590f506d2cb))
- **sync:** Enable expiration notifications. ([3b1738ba](https://github.com/elisiariocouto/leggen/commit/3b1738bae491f78788b37c32d2e733f7741d41f3))


### Miscellaneous Tasks

- **deps:** Bump the pip group across 1 directory with 3 updates ([410e6006](https://github.com/elisiariocouto/leggen/commit/410e600673a1aabcede6f9961c1d10f476ae1077))
- **deps:** Update black, ruff and pre-commit to latest versions. ([7672533e](https://github.com/elisiariocouto/leggen/commit/7672533e8626f5cb04e2bf1f00fbe389f6135f5c))


## 0.5.0 (2024/03/29)

### Features

- **notifications:** Add support for Telegram notifications. ([7401ca62](https://github.com/elisiariocouto/leggen/commit/7401ca62d2ff23c4100ed9d1c8b7450289337553))


### Miscellaneous Tasks

-  Rename docker-compose.yml to compose.yml and remove obsolete 'version' key. ([e46634cf](https://github.com/elisiariocouto/leggen/commit/e46634cf27046bfc8d638a0cd4910a4a8a42648a))


## 0.4.0 (2024/03/28)

### Features

- **notifications:** Add support for transaction filter and notifications via Discord. ([0cb33936](https://github.com/elisiariocouto/leggen/commit/0cb339366cc5965223144d2829312d9416d4bc46))


### Miscellaneous Tasks

- **deps-dev:** Bump black from 24.2.0 to 24.3.0 ([2352ea9e](https://github.com/elisiariocouto/leggen/commit/2352ea9e58f14250b819e02fa59879e7ff200764))
-  Update dependencies. ([3d36198b](https://github.com/elisiariocouto/leggen/commit/3d36198b06eebc9d7480eb020d1a713e8637b31a))


## 0.3.0 (2024/03/08)

### Documentation

-  Improve README.md. ([cb6682ea](https://github.com/elisiariocouto/leggen/commit/cb6682ea2e7e842806f668fdf4ed34fd0278fd04))


### Features

- **commands:** Add new `leggen bank delete` command to delete a bank connection. ([fcb0f1ed](https://github.com/elisiariocouto/leggen/commit/fcb0f1edd7f7ebd556ee31912ba25ee0b01d7edc))
- **commands/bank/add:** Add all supported GoCardless country ISO codes. ([0c8f68ad](https://github.com/elisiariocouto/leggen/commit/0c8f68adfddbda08ee90c58e1c69035a0f873a40))


### Miscellaneous Tasks

-  Update dependencies. ([6d2f1b7b](https://github.com/elisiariocouto/leggen/commit/6d2f1b7b2f2bf4e4e6d64804adccd74dfb38dcf6))


## 0.2.3 (2024/03/06)

### Bug Fixes

-  Print HTTP response body on errors. ([ee30bff5](https://github.com/elisiariocouto/leggen/commit/ee30bff5ef0e40245004e1811a3a62c9caf4f30f))


### Miscellaneous Tasks

-  Update dependencies. ([f7ef4b32](https://github.com/elisiariocouto/leggen/commit/f7ef4b32cae347ae05ae763cb169d6b6c09bde99))


## 0.2.2 (2024/03/01)

### Bug Fixes

- **sync:** Pending dates can be null. ([d8aa1ef9](https://github.com/elisiariocouto/leggen/commit/d8aa1ef90d263771b080194adc9e983b1b3d56fe))


## 0.2.1 (2024/02/29)

### Bug Fixes

-  Fix compose volumes and dependencies. ([460fed3e](https://github.com/elisiariocouto/leggen/commit/460fed3ed0ca694eab6e80f98392edbe5d5b83fd))
-  Deduplicate accounts. ([facf6ac9](https://github.com/elisiariocouto/leggen/commit/facf6ac94e533087846fca297520c311a81b6692))


### Documentation

-  Add NocoDB information to README.md. ([d8fde49d](https://github.com/elisiariocouto/leggen/commit/d8fde49da4e34457a7564655dd42bb6f0d427b4b))


## 0.2.0 (2024/02/27)

### Bug Fixes

- **compose:** Fix ofelia configuration, add sync command as the default. ([433d1737](https://github.com/elisiariocouto/leggen/commit/433d17371ead323ca9b793a2dd5782cca598ffcf))


### Documentation

-  Improve README.md. ([de17cf44](https://github.com/elisiariocouto/leggen/commit/de17cf44ec5260305de8aa053582744ec69d705f))


### Features

-  Add periodic sync, handled by ofelia. ([91c74b04](https://github.com/elisiariocouto/leggen/commit/91c74b0412713ef8305fbe7fcf7c53e4cf8948fe))
-  Change default database engine to SQLite, change schema. ([f9ab3ae0](https://github.com/elisiariocouto/leggen/commit/f9ab3ae0a813f2a512b4f5fa57e0da089f823783))


## 0.1.1 (2024/02/18)

### Bug Fixes

-  Change project name on container registries. ([dab04f4e](https://github.com/elisiariocouto/leggen/commit/dab04f4e3b1d87af5be9138c931bf637637a2535))


## 0.1.0 (2024/02/18)

### Miscellaneous Tasks

-  Initial version. ([ec4f59e0](https://github.com/elisiariocouto/leggen/commit/ec4f59e04766e978f16d1e7b5098c1aa6503bb95))
