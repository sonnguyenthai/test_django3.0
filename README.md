- Guide: https://flynn.gg/blog/software-best-practices-python-2019/
- `Python 3.8.0` via `pyenv`
- Using `poetry` to python manages packages and dependencies: https://poetry.eustace.io/docs/
.Notes: `poetry 0.12.17` hasn't supported `python 3.8` yet.
- Steps:
    * install `pyenv`, `poetry`
    * create project directory
    * create virtualenv inside the project root with: `python -m venv .venv`
    * activate virtualenv: `source .venv/bin/activate`
    * Initialize `poetry` in the project: `poetry init`
    * Add packages with `poetry`: `poetry add django==3.0b1`
    * Add packages for dev with `poetry`: `poetry add -D sphinx`
    * Remove packages with `poetry`: `poetry remove django`
    * Install all dependencies with `poetry`: `poetry install`
- All configurations are in `pyproject.toml`     
- Install `black`: `poetry add -D black` then add configurations as in `pyproject.toml`
- Install `isort`: `poetry add -D isort` then add configurations as in `pyproject.toml`
- Install `pre-commit`: `poetry add -D pre-commit`
- Setup `pre-commit`:
    * create file `.pre-commit-config.yaml` as in the project
    * run `pre-commit install` to start `pre-commit`
    
