# Changelog

## [1.1.1] - 2024-07-06

- Fix SafeMIMEText.set_payload() crash on Python 3.13 ([#80](https://github.com/waynerv/flask-mailman/pull/80)).

## [1.1.0] - 2024-4-22

- Add configuration key `MAIL_SEND_OPTIONS` to support setting `mail_options` for `smtplib.SMTP.send_mail`
  (e.g. `SMTPUTF8`) ([#61](https://github.com/waynerv/flask-mailman/pull/61)).
- Pre-encodes FQDN str with punycode to improve compatibility ([#66](https://github.com/waynerv/flask-mailman/pull/66)).
- Migrates as many as possible test cases from Django mail module ([#64](https://github.com/waynerv/flask-mailman/pull/64)).
- Improve way of populating smtp key/cert to avoid TypeError in py>=12 ([#68](https://github.com/waynerv/flask-mailman/pull/68)).

## [1.0.0] - 2023-11-04

- Drop Python 3.6 support.
- Fix compatibility issue with Python 3.10
  ([#31](https://github.com/waynerv/flask-mailman/pull/31)).
- Fix the log file generation issue to ensure that the log filename is random
  ([#30](https://github.com/waynerv/flask-mailman/pull/30)).
- Fix compatibility issue with Python 3.12
  ([#56](https://github.com/waynerv/flask-mailman/issues/56)).
- Support passing `from_email` in tuple format to `send_mail()` function
  ([#35](https://github.com/waynerv/flask-mailman/issues/35)).

## [0.3.0] - 2021-08-08

### Added

- Add support for custom email backend.

## [0.2.4] - 2021-06-15

### Added

- Tox and GitHub workflows to run test, staging and release automatically.

## [0.2.3]

### Added

- Add support for Flask 2.0

### Removed

- Drop support for Python 3.5(due to flask upgrade).

## [0.2.2]

### Changed

- Set `None` as the default value for the `from_email` and `recipient_list` of `send_mail()` function.

## [0.2.0]

A few breaking changes have been made in this version to ensure that API of this extension is basically the same as Django.
Users migrating from Flask-Mail should upgrade with caution.

### Added

- Add documentation site hosted in GitHub Pages.

### Changed

- Set configuration value of in-memory backend to 'locmem'.
- Set MAIL_SERVER default value to 'locaohost'.
- Set MAIL_USE_LOCALTIME default value to False.

### Removed

- Remove `Mail.send()` method and `Message()` class which borrowing from Flask-Mail.
- Remove `mail_admins()` and `mail_managers()` method that come from Django.
