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
