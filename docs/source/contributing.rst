Contributing
============

We welcome contributions to Indigobot! This document provides guidelines and instructions for contributing to the project.

Setting Up Development Environment
----------------------------------

1. Fork the repository on GitHub
2. Clone your fork locally:

   .. code-block:: bash

      git clone https://github.com/Project-Indigo-HQ/indigobot.git
      cd indigobot

3. Set up a virtual environment:

   .. code-block:: bash

      python -m venv venv
      source venv/bin/activate  # On Windows: venv\Scripts\activate
      pip install -r requirements.txt
      pip install -r requirements-dev.txt
      pip install -e .

4. Set up pre-commit hooks:

   .. code-block:: bash

      pre-commit install

Coding Standards
----------------

- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Write docstrings for all functions, classes, and modules
- Keep functions focused on a single responsibility
- Write unit tests for new functionality

Pull Request Process
--------------------

1. Create a new branch for your feature or bugfix:

   .. code-block:: bash

      git checkout -b feature/your-feature-name

2. Make your changes and commit them with clear, descriptive commit messages

3. Run tests to ensure your changes don't break existing functionality:

   .. code-block:: bash

      pytest

4. Push your branch to your fork:

   .. code-block:: bash

      git push origin feature/your-feature-name

5. Open a pull request against the main repository's main branch

6. Ensure the PR description clearly describes the problem and solution

7. Wait for code review and address any feedback

Updating the docs
-----------------

- Update documentation for any changed functionality
- Add examples for new features
- Build and check documentation locally:

  .. code-block:: bash

     cd docs
     make html
     # Open docs/build/html/index.html in your browser

Reporting Issues
----------------

- Use the GitHub issue tracker to report bugs
- Include detailed steps to reproduce the issue
- Mention your environment (OS, Python version, etc.)
- If possible, include a minimal code example that reproduces the issue
