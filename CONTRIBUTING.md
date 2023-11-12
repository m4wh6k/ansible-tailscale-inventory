# Contributing to ansible-tailscale-inventory
Contributions are welcomed! Please feel free to [submit
issues](https://github.com/m4wh6k/ansible-tailscale-inventory/issues) and propose fixes
and changes to the script.

## Development dependencies
- `make`
- `python` 3.8 or higher

Running `make dev` will install more pip dependencies.

## Formatting & Linting
Code is expected to formatted and type annotated to conform with `black`, `mypy`, and
`ruff`. Formatting can be tested with `make test`. Some formatting can be automatically
applied by running `make fmt`.

## Testing
We use `pytest` to ensure the script works as expected as we change things. Simply
running `pytest` with no arguments will test the script. Or, you can run `make test` to
run the full test suite with linting. 

Pytests can be found in the `tests/` dir. The main existing test simply checks that a
given Tailscale status output will produce an Ansible inventory in an expected format.
The expected inputs and outputs are defined in `tests/mock_data.py`. 

For most inventory structure changes it should be adequate to simply update the input
and output data structures in `tests/mock_data.py`. A recommended development workflow
is to update the mock data and then start updating the script to produce the expected
output, running `pytest` along the way until it passes.

A GitHub Actions workflow will test changes on Pull Request. It can also be run
on-demand against branches. The GH Actions workflow will run tests using multiple
versions of python to ensure the script remains compatible.
