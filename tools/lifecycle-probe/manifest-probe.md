# Manifest install-post probe

This inert SDK-only RPM fixture tests the production manifest hook after RPM
postprocessing. It compiles one trivial C program, packages the current public
runtime scripts without executing them and deliberately changes one fixture
file in install-post. The checker reads the RPM CPIO payload; it never installs
or executes the packaged ELF. Original fixture work uses the repository license.

Use an existing approved SDK and explicit installed target. The SDK provides its
cross compiler independently of the target RPM package database. No dependency
installation is part of these commands. Start from the runtime repository root:

```sh
python3 tools/lifecycle-probe/prepare-manifest-probe.py "$PWD/build/manifest-probe"
"$SAILFISH_SDK_ROOT/bin/sfdk" -c "target=$SAILFISH_SDK_TARGET" build-shell rpmbuild -bb \
  --define "_topdir $PWD/build/manifest-probe/probe-rpm" \
  --define "_sourcedir $PWD/build/manifest-probe" \
  "$PWD/build/manifest-probe/probe.spec"
"$SAILFISH_SDK_ROOT/bin/sfdk" -c "target=$SAILFISH_SDK_TARGET" build-shell \
  python3 "$PWD/build/manifest-probe/check-probe.py"
```

Preparation refuses an existing output directory and copies only the named
public runtime inputs. It substitutes the current production install-post hook
into the template; this is not a second runtime recipe. Outputs and logs remain
under ignored build directories. This probe does not establish the full GnuPG
package build, installation lifecycle or device acceptance.
