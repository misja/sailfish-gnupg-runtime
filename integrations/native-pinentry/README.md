# Native pinentry source inputs

Compatibility changes are maintained in [misja/sailfish-secrets](https://github.com/misja/sailfish-secrets).
sources.json pins the upstream commit, compatibility branch and separate
cache-free prototype. Packaging patches remain in packaging/native-pinentry/.

Clone that fork beside gnupg-runtime as sailfish-secrets, or supply its checkout:
python3 integrations/native-pinentry/prepare.py --checkout /path/to/sailfish-secrets

This verifies the original source hashes and reconstructs the exact cache-free
prototype in ignored upstream/ and prepared/ directories. For compatibility
source use tools/materialize-native-pinentry.py --variant compat. The tool uses
only local Git objects; it does not fetch sources, build, install or touch keys.

The fork ancestry and source bytes match the previous pinned prototype inputs.
This does not establish exact vendor 5.2 source provenance or new runtime acceptance.
