# dbt-graph-builder

[![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11-blue)](https://github.com/getindata/dbt-graph-builder)
[![PyPI Version](https://badge.fury.io/py/dbt-graph-builder.svg)](https://pypi.org/project/dbt-graph-builder/)
[![Downloads](https://pepy.tech/badge/dbt-graph-builder)](https://pepy.tech/project/dbt-graph-builder)

## Overview
This library provides a set of tools for building a graph of dbt models and their dependencies. It can be used to create an Airflow DAG for dbt models
or to create a graph of dbt models and their dependencies in a format that can be used by other tools like GCP Workflows.

## Project Organization

- .devcontainer - This directory contains required files for creating a [Codespace](https://github.com/features/codespaces).
- .github
  - workflows - Contains GitHub Actions used for building, testing and publishing.
    - prepare-release.yml - Contains steps to prepare a release.
    - publish.yml - Publish wheels to [https://pypi.org/](https://pypi.org/)
    - test-linting.yml - Build and Test pull requests before commiting to main.
    - template-sync.yml - Update GitHub Repo with enhancments to base template
- docs - collect documents (default format .md)
- src - place new source code here
  - python_package - sample package (this can be deleted when creating a new repository)
- tests - contains Python based test cases to validation src code
- .pre-commit-config.yaml - Contains various pre-check fixes for Python
- MANIFEST.in - Declares additional files to include in Python whl
- pyproject.toml - Python Project Declaration
- README.md - This file

## Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft
trademarks or logos is subject to and must follow
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
