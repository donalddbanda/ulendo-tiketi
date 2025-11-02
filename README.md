# ulendo-tiketi
Ulendo-Tiketi is a bus booking platform for Malawians.

# Contributing

Contributions are welcome from all team members and external collaborators. To maintain code quality and project consistency, please adhere to the following guidelines:

## 1. Branching Strategy
- The `main` branch **must always contain production-ready code**.
- All new features, bug fixes, and experiments **must be developed on a separate branch**.
- Branch naming convention:
  - Features: `feature/<descriptive-name>`
  - Bug fixes: `bugfix/<issue-description>`
  - Documentation: `docs/<topic>`

## 2. Development Workflow
1. **Create a branch** from the latest `main`:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/your-feature-name
   ```
2. **Implement changes** following the coding standards:
   - Backend: PEP 8, type hints, docstrings
   - Frontend: ESLint/Prettier rules (see `frontend/.eslintrc`)
3. **Write tests** for all new endpoints or business logic.
4. **Commit messages** must follow Conventional Commits:
   ```
   feat: add booking cancellation endpoint
   fix: resolve QR code generation error
   docs: update API reference
   ```

## 3. Pull Request Process
1. Push your branch and open a **Pull Request (PR)** to `main`.
2. Ensure the PR:
   - Passes all CI checks (tests, linting)
   - Includes updated documentation where applicable
   - Has a clear description and links to related issues
3. Request review from at least **one backend** and **one frontend** maintainer.
4. Address feedback promptly.
5. Once approved and merged, delete the feature branch.

## 4. Code Reviews
- Focus on functionality, security, performance, and readability.
- All payment, authentication, and booking logic requires **two approvals**.

## 5. Reporting Issues
- Use GitHub Issues with the appropriate template.
- Label issues: `bug`, `enhancement`, `documentation`, `help wanted`.

## 6. Local Development
- Use `uv` for Python dependencies.
- Use `npm` or `pnpm` in `frontend/` as configured.
- Respect `.env` files — never commit secrets.

### FRONT-END:
Refer to the README.md file in the frontend directory.
### BACK-END:
Refer to the README.md file in the backend directory.

By following these guidelines, we ensure a clean, maintainable, and scalable codebase for **Ulendo Tiketi**.



# Ownership
Gomezgani Chirwa and Donald Banda remain the full owners of this codebase. Ulendo Tiketi (name is subject to change) might have the full ownership of it in the future after the creation of the startup, Ulendo Tiketi. When this happens, Gomezgani Chirwa and Donald Banda will no longer have ownership of the codebase. Any change of ownership will lead to the changing or updating of this README.md file.

This is not an open-source codebase. Any use of this codebase without proper permissions/copyrights/licensing will be treated as copyright infringment.
