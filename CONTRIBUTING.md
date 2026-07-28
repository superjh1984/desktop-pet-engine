# Contributing

1. Run `python3 -m unittest discover -s tests -v` and `./scripts/check_demo.sh` before submitting code changes.
2. Keep the public template independent from private or restricted demo projects.
3. Do not commit credentials, signed download URLs, local absolute paths, build products, or authentication QR codes.
4. Only contribute visual or audio assets you created or are authorized to redistribute under this repository's license.
5. Include provenance and license information for every added third-party asset.
6. A model entry marked `live` must have a provider adapter and mocked request/response tests. Use `catalog` status until the current official API contract has been reviewed.
7. Provider adapters must resolve keys at runtime from the documented environment variable and must never write or print the key.

By contributing, you agree that your contribution is licensed under Apache License 2.0.
