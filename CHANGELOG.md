v0.2.0
- Add MultiVersionsCheckpoints (the GenericFileCheckpoints only allow you store single version)
- Set the default of MulitContentsManager to use MultiVersionsCheckpoints
- Recursive rename contents cross content managers, previously we only move the top layer contents.

v0.1.2
- import notebook.transutils to avoid issue of "name '_' is not defined"

v0.1.1
- avoid user renaming the virtual directory

v0.1.0
- initial version
