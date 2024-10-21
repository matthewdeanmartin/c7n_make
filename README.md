# c7n_make
An opinionated Cloud Custodian build script with examples

## Goals

- Some guidance for creating policy files.
  - Folder structure
  - Naming conventions

Testing
- Localstack and moto testing
- End-to-end testing
- Plugin development

Scripts
- Build scripts (are the artifacts good? Interpolate variables, set defaults, merge)
- Deployment scripts (Send to a custodian runner)

## Structure for policy

- The policy file
- The CC teardown file
- A pytest unit test and fixture to provision the resources, run the policy, assert, and then teardown.

## Structure for a policy collection

- A folder for each policy
- Some sort of templating strategy for creating slightly different versions, e.g. development/production
  - TBD: yq? other?
- Development here can have two meanings, a place to prove your policies, but also the environment where the
  enterprise developers other applications, which might have different levels of strictness.

## Policy Linting

- One policy per file. Policies can be compiled into a single file.
- The name should match the policy.
- Description should be present.

## Build checks

- Validate yaml
- Lint yaml with yamllint. 
- Lint with AI
- Validate policy against schema.

## Testing

- Tests need to be able to create infrastructure and tear it down.
- There isn't a one size fits all way to create infrastructure.
- Code Custodian can't create resources, but it can tear down a lot of resources.
- Each policy needs at least two tests, a pass and a fail. 
- Running on real AWS costs money, so tests should be equally happy to run on 

## License

Some code copy-pasted from the Cloud Custodian project, see source file header.

Rest of code is Apache license for compatibility.