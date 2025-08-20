This project uses astral's uv for python management:

- Use 'uv sync' to download dependencies and create a .venv folder.
- Use 'uv run <command>' to run a command.
- Use 'uv add <package>' to add a package.
- Use 'uv remove <package>' to remove a package.
- Use 'uv help' to get help.

It also uses alembic for database migrations, but as an agent, you do not have acecss to the database. Simply include
the command that should be run, but you are not to manage the migration as an agent.