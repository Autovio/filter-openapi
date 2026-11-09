# Filter OpenAPI Specifications

A command-line tool to filter and modify OpenAPI specification files. This tool is designed to help you tailor OpenAPI specifications for specific use cases by filtering out APIs and other information you do not need. A compliant OpenAPI specification is
always produced.

## Features

- **Filter Out Paths by Tags**: Keep only the API paths that are associated with a specific set of tags. Allows you to remove large groups of API that are organized by tag.
- **Filter Endpoints**: For any endpoints/paths left after filtering by tag, you can precisely control which endpoints (and which HTTP methods for those endpoints) are included in the final specification.
- **Remove Unreferenced Schemas**: Clean up your OpenAPI document by removing any schemas that are no longer referenced after filtering.
- **Remove `x-oaiMeta` Properties**: Strip out `x-oaiMeta` properties, which are often specific to internal tooling and not needed for public consumption.
- **Filter Top-Level Tags**: Ensure the top-level `tags` array only contains tags that are present in the filtered paths.

## Installation

This project requires Python 3.12+ and has no third-party runtime dependencies.

## Configuration

The tool's behavior is controlled by a JSON configuration file. You can create your own `config.json` based on the provided `config.example.json`.

Here's an overview of the configuration options:

- **`allowedTags`**: An array of strings representing the tags to keep. Any path that does not have at least one of these tags will be removed.

  ```json
  "allowedTags": [
      "Chat",
      "Completions"
  ]
  ```

- **`pathFilters`**: An object where each key is a path in the OpenAPI specification (e.g., `/chat/completions`). The value is an object with an `allowedMethods` array, specifying which HTTP methods to keep (e.g., `"POST"`). An empty `allowedMethods` array will cause the entire path to be removed.

  ```json
  "pathFilters": {
      "/chat/completions": {
          "allowedMethods": [
              "POST"
          ]
      },
      "/chat/completions/{completion_id}": {
          "allowedMethods": []
      }
  }
  ```

- **`options`**: An object to control additional features.
  - `removeXOaiMeta`: Set to `true` to remove all `x-oaiMeta` fields from the specification.
  - `removeUnreferencedSchemas`: Set to `true` to automatically remove any schemas in `components/schemas` that are not referenced by any of the remaining endpoints.

  ```json
  "options": {
      "removeXOaiMeta": true,
      "removeUnreferencedSchemas": true
  }
  ```

## Usage

The tool is run from the command line and accepts the following arguments:

- `input_file`: (Required) The path to the input OpenAPI JSON file.
- `-c` or `--config`: (Required) The path to your `config.json` file.
- `-o` or `--output`: (Optional) The path to the output file. If not provided, the modified JSON will be printed to standard output.
- `-v` or `--verbose`: (Optional) Enable verbose logging.

### Example

```bash
python -m filter_openapi openai.json --config config.json --output openapi_filtered.json
```

This command will:
1. Read the `openai.json` file.
2. Apply the transformations defined in `config.json`.
3. Write the resulting specification to `openapi_filtered.json`.
