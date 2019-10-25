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
