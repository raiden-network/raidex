# Raidex Development Guide

Welcome! This guide serves as the guideline to contributing to the Raidex
codebase. It's here to help you understand what development practises we use here
and what are the requirements for a Pull Request to be opened against Raidex

- [Contributing](#contributing)
  - [Creating an Issue](#creating-an-issue)
  - [Creating a Pull Request](#creating-a-pull-request)
- [Development environment setup](#development-environment-setup)
- [Development Guidelines](#development-guidelines)
  - [Coding Style](#coding-style)
  - [Workflow](#workflow)

## Contributing

There are two ways you can contribute to the development. You can either open
an Issue or if you have programming abilities open a Pull Request.

### Creating an Issue

If you experience a problem while using the Raidex or want to request a feature
then you should open an issue against the repository. All issues should
contain:

**For Feature Requests:**

- A description of what you would like to see implemented.
- An explanation of why you believe this would make a good addition to Raidex.

**For Bugs:**

- A short description of the problem.
- Detailed description of your system, SDK version, environment (e.g. Metamask), Wallet version if you are using the wallet.
- What was the exact unexpected thing that occured.
- What you were expecting to happen instead.

## Development environment setup

You can check the [Readme](./readme.md#installation) 

### Testing

The unit tests use jest:

For the sdk you have to run the following:

```bash
    cd raiden
    npm run test

```

For the wallet:

```bash
    cd raiden-wallet
    npm run test:unit
```

Tests are split in unit tests, and integration tests. The first are faster to execute while
the latter test the whole system but are slower to run.

### Testing on the CI

By default whenever you make a Pull Request the linter tests, format checks, unit tests and all the integration tests will run.

### Commiting Rules

For an exhaustive guide read [this](http://chris.beams.io/posts/git-commit/)
guide. It's all really good advice. Some rules that you should always follow though are:

- A commit title not exceeding 50 characters
- A blank line after the title (optional if there is no description)
- A description of what the commit did (optional if the commit is really small)

Why are these rules important? All tools that consume git repos and show you
information treat the first 80 characters as a title. Even Github itself does
this. And the git history looks really nice and neat if these simple rules are
followed.

### Documentation

Code should be documented.

### Coding Style

The code style is enforced by [prettier](https://prettier.io/) which means that in most of the cases you don't actually need to do anything more than running the appropriate task.

To fix any fixable codestyle issue in either SDK or Wallet, you may just run the following command on the respective folder:

```bash
npm run lint
```

Linting plugins available for modern IDEs are also useful in early spotting any mistakes and help keep the code quality level.

### Workflow

When developing a feature, or a bug fix you should always start by writing a
**test** for it, or by modifying existing tests to test for your feature.
Once you see that test failing you should implement the feature and confirm
that all your new tests pass.

Your addition to the test suite should call into the innermost level possible
to test your feature/bugfix. In particular, integration tests should be avoided
in favor of unit tests whenever possible.

Afterwards you should open a Pull Request from your fork or feature branch
against master. You will be given feedback from the core developers of raiden
and you should try to incorporate that feedback into your branch. Once you do
so and all tests pass your feature/fix will be merged.

#### Integrating Pull Requests

When integrating a successful Pull Request into the codebase we have the option
of using either a "Rebase and Merge" or to "Create a Merge commit".
Unfortunately in Github the default option is to "Create a Merge commit". This
is not our preferred option as in this way we can't be sure that the result of
the merge will also have all tests passing, since there may be other patches
merged since the PR opened. But there are many PRs which we definitely know
won't have any conflicts and for which enforcing rebase would make no sense and
only waste our time. As such we provide the option to use both at our own
discretion. So the general guidelines are:

- If there are patches that have been merged to master since the PR was opened,
  on top of which our current PR may have different behaviour then use **Rebase
  and Merge**.
- If there are patches that have been merged to master since the PR was opened
  which touch documentation, infrastucture or completely unrelated parts of the
  code then you can freely use **Create a Merge Commit** and save the time of
  rebasing.
