# [Unreleased]

See the git change-log.

# [1.2.2]

  * Improvements to error reporting in ZINC mode.  The exception now
    reports the correct row and column, along with a depiction of the
    raw data returned and a pointer to the suspected error.

 -- Samuel Toh <samuelt@vrt.com.au>  Mon, 14 May 2018 09:58:37 +1000

# [1.2.1]

  * Add auto-upgrade of grid version; grids now default to v2.0 and
    move to v3.0 if a v3.0 type is encountered.
  * Add grid version type enforcement; if a version is specified for
    a grid, raise an error if an unsupported type is used.

 -- Samuel Toh <samuelt@vrt.com.au>  Tue, 13 Feb 2018 17:05:40 +1000

# [1.2.0]

  * Re-worked on hszinc's parser to support Haystack v3 data structures.
  * Added support for Haystack list.

 -- Samuel Toh <samuelt@vrt.com.au>  Tue, 6 Feb 2018 11:31:21 +1000

# [1.1.2]

  * Bugfix to handling of multi-line strings in JSON serialisation.

 -- Stuart Longland <stuartl@vrt.com.au>  Tue, 15 Aug 2017 15:11:20 +1000

# [0.1.1]

  * Bugfix to `!=` operators on ZINC types.

 -- Stuart Longland <stuartl@vrt.com.au>  Sat, 30 Jul 2016 13:18:19 +1000

# [0.1.0]

  * Add support for `pint` (thanks to Christian Tremblay)
  * Fix handling of `"\$"` escape sequence (issue 7)

 -- Stuart Longland <stuartl@vrt.com.au>  Wed, 29 Jun 2016 11:26:38 +1000

# [0.0.8]

  * Added __hash__ function to Quantity (Credit: Christian Tremblay)

 -- Stuart Longland <stuartl@vrt.com.au>  Tue, 03 May 2016 20:16:27 +1000

# [0.0.7]

  * Tweak package metadata, fix ImportError on running setup.py without
    dependencies installed.

 -- Stuart Longland <stuartl@vrt.com.au>  Sat, 30 Apr 2016 08:38:00 +1000

# [0.0.6]

  * Handle mixed raw UTF-8 and Unicode escape sequences.

 -- Stuart Longland <stuartl@vrt.com.au>  Fri, 29 Apr 2016 16:57:05 +1000

# [0.0.5]

  * Encoding bugfixes
  * `__repr__` for grids

 -- Stuart Longland <stuartl@vrt.com.au>  Thu, 21 Apr 2016 14:19:47 +1000

# [0.0.4]

  * Add support for grids in JSON format.
  * Add documentation in README

 -- Stuart Longland <stuartl@vrt.com.au>  Mon, 18 Jan 2016 13:51:33 +1000

# [0.0.3]

  * More rigorous tests
  * Support for (undocumented!) 'Remove' type
  * Improvements to decoder robustness

 -- Stuart Longland <stuartl@vrt.com.au>  Fri, 15 Jan 2016 06:35:11 +1000

# [0.0.2]

  * Added tests, compatibility with Python 3.x, numerous bugfixes.

 -- Stuart Longland <stuartl@vrt.com.au>  Wed, 13 Jan 2016 08:30:59 +1000

# [0.0.1]

  * Initial version.

 -- Stuart Longland <stuartl@vrt.com.au>  Thu, 07 Jan 2016 13:57:00 +1000

[Unreleased]: https://github.com/vrtsystems/hszinc/compare/HEAD..1.2.2
[1.2.2]: https://github.com/vrtsystems/hszinc/compare/v1.2.1..v1.2.2
[1.2.1]: https://github.com/vrtsystems/hszinc/compare/v1.2.0..v1.2.1
[1.2.0]: https://github.com/vrtsystems/hszinc/compare/v1.1.2..v1.2.0
[1.1.2]: https://github.com/vrtsystems/hszinc/compare/v0.1.1..v1.1.2
[0.1.1]: https://github.com/vrtsystems/hszinc/compare/v0.1.0..v0.1.1
[0.1.0]: https://github.com/vrtsystems/hszinc/compare/v0.0.8..v0.1.0
[0.0.8]: https://github.com/vrtsystems/hszinc/compare/v0.0.7..v0.0.8
[0.0.7]: https://github.com/vrtsystems/hszinc/compare/v0.0.6..v0.0.7
[0.0.6]: https://github.com/vrtsystems/hszinc/compare/v0.0.5..v0.0.6
[0.0.5]: https://github.com/vrtsystems/hszinc/compare/v0.0.4..v0.0.5
[0.0.4]: https://github.com/vrtsystems/hszinc/compare/v0.0.3..v0.0.4
[0.0.3]: https://github.com/vrtsystems/hszinc/compare/v0.0.2..v0.0.3
[0.0.2]: https://github.com/vrtsystems/hszinc/compare/v0.0.1..v0.0.2
[0.0.1]: https://github.com/vrtsystems/hszinc/compare/b677fc57905eae46f2391c37f1217d16859b98a4..v0.0.1
