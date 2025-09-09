
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
