# Contributing

This project uses **uv** for Python dependency management and **shadcn/ui** for frontend components.

## Setup
Install uv and run `uv sync` to install dependencies.

Run `pre-commit install` to install the pre-commit hooks.

## Frontend Development
The frontend uses shadcn/ui components for consistent design. When adding new UI components:
- Check if a shadcn/ui component exists for your use case
- Follow the existing component patterns in `frontend/src/components/ui/`
- Use Tailwind CSS classes for styling
- Ensure components are accessible and follow the design system

## Commit messages

type(scope/[subscope]): Title starting with uppercase and sentence ending with period.
More than 80 charactes use the body of the commit message.

Scope and subscopes are optional.

DO NOT use a bunch of different types: feat, fix, refactor should be more than enough.

## Release new version

Run script `scripts/release.sh <type_of_release>`

Types supported are `major`, `minor` and `patch`. Semver practices must be followed.
This release process deals with updating everything, including changelog generation.
